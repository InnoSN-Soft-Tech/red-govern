"""Normalised Amazon Redshift object-inventory collection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from red_govern.capabilities import CapabilityReport, ViewFamily
from red_govern.config.models import RedshiftConfig
from red_govern.connections.connection import (
    CursorProtocol,
    redshift_connection,
)
from red_govern.exceptions import RedshiftQueryError
from red_govern.query_registry import QueryPurpose, QueryResolution, resolve_query
from red_govern.query_registry.builtin import build_builtin_registry
from red_govern.security.redaction import redact_text


class DatabaseObjectType(str, Enum):
    """Normalised database-object categories."""

    TABLE = "table"
    VIEW = "view"
    MATERIALIZED_VIEW = "materialized_view"
    EXTERNAL_TABLE = "external_table"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class ObjectInventoryRecord:
    """One normalised Redshift database object."""

    database_name: str
    schema_name: str
    object_name: str
    object_type: DatabaseObjectType
    source_family: ViewFamily
    source_query_id: str
    collected_at: datetime
    owner_name: str | None = None
    size_mb: float | None = None
    distribution_style: str | None = None
    sort_key: str | None = None


@dataclass(frozen=True, slots=True)
class ObjectInventoryResult:
    """Complete normalised object-inventory collection."""

    records: tuple[ObjectInventoryRecord, ...]
    resolution: QueryResolution
    collected_at: datetime

    @property
    def total_objects(self) -> int:
        """Return the number of collected objects."""
        return len(self.records)



def normalise_object_type(value: object) -> DatabaseObjectType:
    """Convert source-specific object types to stable internal values."""
    normalised = str(value or "").strip().lower().replace(" ", "_")

    aliases = {
        "base_table": DatabaseObjectType.TABLE,
        "table": DatabaseObjectType.TABLE,
        "view": DatabaseObjectType.VIEW,
        "materialized_view": DatabaseObjectType.MATERIALIZED_VIEW,
        "materialized view": DatabaseObjectType.MATERIALIZED_VIEW,
        "external_table": DatabaseObjectType.EXTERNAL_TABLE,
        "external table": DatabaseObjectType.EXTERNAL_TABLE,
    }

    return aliases.get(normalised, DatabaseObjectType.UNKNOWN)


def _column_names(cursor: CursorProtocol) -> tuple[str, ...]:
    """Return lower-case column names from a DB-API cursor."""
    if not cursor.description:
        return ()

    return tuple(str(column[0]).lower() for column in cursor.description)


def _rows_as_mappings(
    cursor: CursorProtocol,
    rows: list[tuple[Any, ...]],
) -> tuple[dict[str, Any], ...]:
    """Convert DB-API tuples into column-name mappings."""
    columns = _column_names(cursor)

    if not columns:
        raise RedshiftQueryError(
            "Object inventory query returned no column metadata."
        )

    return tuple(dict(zip(columns, row, strict=True)) for row in rows)


def _first_present(
    row: dict[str, Any],
    *names: str,
) -> Any:
    """Return the first available source column."""
    for name in names:
        if name in row:
            return row[name]

    return None


def _normalise_row(
    row: dict[str, Any],
    resolution: QueryResolution,
    collected_at: datetime,
) -> ObjectInventoryRecord:
    """Normalise one source row into the public inventory contract."""
    database_name = _first_present(
        row,
        "table_database",
        "table_catalog",
        "database_name",
    )
    schema_name = _first_present(
        row,
        "table_schema",
        "schema_name",
    )
    object_name = _first_present(
        row,
        "table_name",
        "object_name",
    )
    source_type = _first_present(
        row,
        "table_type",
        "object_type",
    )

    if not database_name or not schema_name or not object_name:
        raise RedshiftQueryError(
            "Object inventory row is missing database, schema, or object name."
        )

    size_value = _first_present(
        row,
        "size_mb",
        "table_size_mb",
    )

    try:
        size_mb = float(size_value) if size_value is not None else None
    except (TypeError, ValueError):
        size_mb = None

    return ObjectInventoryRecord(
        database_name=str(database_name),
        schema_name=str(schema_name),
        object_name=str(object_name),
        object_type=normalise_object_type(source_type),
        source_family=resolution.selected_family,
        source_query_id=resolution.query.query_id,
        collected_at=collected_at,
        owner_name=(
            str(owner)
            if (owner := _first_present(row, "owner_name", "table_owner"))
            else None
        ),
        size_mb=size_mb,
        distribution_style=(
            str(style)
            if (
                style := _first_present(
                    row,
                    "distribution_style",
                    "diststyle",
                )
            )
            else None
        ),
        sort_key=(
            str(sort_key)
            if (
                sort_key := _first_present(
                    row,
                    "sort_key",
                    "sortkey1",
                )
            )
            else None
        ),
    )


def collect_object_inventory(
    config: RedshiftConfig,
    capability_report: CapabilityReport,
) -> ObjectInventoryResult:
    """Resolve, execute, and normalise an object inventory."""
    registry = build_builtin_registry()

    resolution = resolve_query(
        registry,
        QueryPurpose.OBJECT_INVENTORY,
        capability_report,
        config.compatibility,
    )

    collected_at = datetime.now(timezone.utc)

    with redshift_connection(config) as connection:
        cursor = connection.cursor()

        try:
            cursor.execute(resolution.query.sql)
            raw_rows = cursor.fetchall()
            rows = _rows_as_mappings(cursor, list(raw_rows))
        except Exception as exc:
            safe_message = redact_text(str(exc))

            raise RedshiftQueryError(
                "Object inventory collection failed using "
                f"{resolution.query.query_id}: {safe_message}"
            ) from exc
        finally:
            cursor.close()

    records = tuple(
        _normalise_row(row, resolution, collected_at)
        for row in rows
    )

    return ObjectInventoryResult(
        records=records,
        resolution=resolution,
        collected_at=collected_at,
    )
