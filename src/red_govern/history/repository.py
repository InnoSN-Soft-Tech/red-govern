"""Persistence and comparison of Red-Govern object snapshots."""

from __future__ import annotations

import sqlite3
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from red_govern.capabilities import ViewFamily
from red_govern.collectors import (
    DatabaseObjectType,
    ObjectInventoryRecord,
    ObjectInventoryResult,
)
from red_govern.history.database import history_connection


@dataclass(frozen=True, slots=True)
class SnapshotResult:
    """Result of persisting one inventory snapshot."""

    run_id: int
    total_objects: int
    collected_at: datetime


@dataclass(frozen=True, slots=True)
class InventoryChanges:
    """Object changes between the latest two snapshots."""

    current_run_id: int
    previous_run_id: int | None
    added: tuple[ObjectInventoryRecord, ...]
    removed: tuple[ObjectInventoryRecord, ...]

    @property
    def added_count(self) -> int:
        """Return the number of newly observed objects."""
        return len(self.added)

    @property
    def removed_count(self) -> int:
        """Return the number of no-longer-observed objects."""
        return len(self.removed)


def save_inventory_snapshot(
    path: Path,
    inventory: ObjectInventoryResult,
) -> SnapshotResult:
    """Persist a complete object inventory in local SQLite history."""
    with history_connection(path) as connection:
        cursor = connection.execute(
            """
            INSERT INTO collection_runs (
                collected_at,
                source_query_id,
                source_family,
                total_objects,
                status
            )
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                inventory.collected_at.isoformat(),
                inventory.resolution.query.query_id,
                inventory.resolution.selected_family.value,
                inventory.total_objects,
                "completed",
            ),
        )

        if cursor.lastrowid is None:
            raise RuntimeError("SQLite did not return a collection run ID.")

        run_id = cursor.lastrowid

        connection.executemany(
            """
            INSERT INTO object_snapshots (
                run_id,
                database_name,
                schema_name,
                object_name,
                object_type,
                owner_name,
                size_mb,
                distribution_style,
                sort_key,
                source_family,
                source_query_id,
                collected_at
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            [
                (
                    run_id,
                    record.database_name,
                    record.schema_name,
                    record.object_name,
                    record.object_type.value,
                    record.owner_name,
                    record.size_mb,
                    record.distribution_style,
                    record.sort_key,
                    record.source_family.value,
                    record.source_query_id,
                    record.collected_at.isoformat(),
                )
                for record in inventory.records
            ],
        )

    return SnapshotResult(
        run_id=run_id,
        total_objects=inventory.total_objects,
        collected_at=inventory.collected_at,
    )


def _latest_run_ids(
    connection: sqlite3.Connection,
) -> tuple[int | None, int | None]:
    """Return latest and previous completed collection-run identifiers."""
    rows = connection.execute(
        """
        SELECT run_id
        FROM collection_runs
        WHERE status = 'completed'
        ORDER BY run_id DESC
        LIMIT 2
        """
    ).fetchall()

    current = int(rows[0]["run_id"]) if rows else None
    previous = int(rows[1]["run_id"]) if len(rows) > 1 else None

    return current, previous


def _records_for_run(
    connection: sqlite3.Connection,
    run_id: int,
) -> dict[tuple[str, str, str, str], ObjectInventoryRecord]:
    """Load one snapshot keyed by stable object identity."""
    rows = connection.execute(
        """
        SELECT
            database_name,
            schema_name,
            object_name,
            object_type,
            owner_name,
            size_mb,
            distribution_style,
            sort_key,
            source_family,
            source_query_id,
            collected_at
        FROM object_snapshots
        WHERE run_id = ?
        """,
        (run_id,),
    ).fetchall()

    records: dict[
        tuple[str, str, str, str],
        ObjectInventoryRecord,
    ] = {}

    for row in rows:
        record = ObjectInventoryRecord(
            database_name=str(row["database_name"]),
            schema_name=str(row["schema_name"]),
            object_name=str(row["object_name"]),
            object_type=DatabaseObjectType(str(row["object_type"])),
            owner_name=(
                str(row["owner_name"])
                if row["owner_name"] is not None
                else None
            ),
            size_mb=(
                float(row["size_mb"])
                if row["size_mb"] is not None
                else None
            ),
            distribution_style=(
                str(row["distribution_style"])
                if row["distribution_style"] is not None
                else None
            ),
            sort_key=(
                str(row["sort_key"])
                if row["sort_key"] is not None
                else None
            ),
            source_family=ViewFamily(str(row["source_family"])),
            source_query_id=str(row["source_query_id"]),
            collected_at=datetime.fromisoformat(
                str(row["collected_at"])
            ),
        )

        identity = (
            record.database_name,
            record.schema_name,
            record.object_name,
            record.object_type.value,
        )
        records[identity] = record

    return records


def detect_inventory_changes(path: Path) -> InventoryChanges:
    """Compare the latest snapshot with its predecessor."""
    with history_connection(path) as connection:
        current_run_id, previous_run_id = _latest_run_ids(connection)

        if current_run_id is None:
            raise ValueError("No inventory snapshots are available.")

        current = _records_for_run(connection, current_run_id)

        previous = (
            _records_for_run(connection, previous_run_id)
            if previous_run_id is not None
            else {}
        )

    added_keys = current.keys() - previous.keys()
    removed_keys = previous.keys() - current.keys()

    return InventoryChanges(
        current_run_id=current_run_id,
        previous_run_id=previous_run_id,
        added=tuple(
            current[key]
            for key in sorted(added_keys)
        ),
        removed=tuple(
            previous[key]
            for key in sorted(removed_keys)
        ),
    )
