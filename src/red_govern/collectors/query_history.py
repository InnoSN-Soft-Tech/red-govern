"""Normalised Amazon Redshift query-history collection."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Any

from red_govern.capabilities import CapabilityReport, ViewFamily
from red_govern.config.models import RedshiftConfig
from red_govern.connections.connection import (
    CursorProtocol,
    redshift_connection,
)
from red_govern.exceptions import RedshiftQueryError
from red_govern.query_registry import (
    QueryPurpose,
    QueryResolution,
    resolve_query,
)
from red_govern.query_registry.builtin import build_builtin_registry
from red_govern.security.redaction import redact_text


class QueryStatus(str, Enum):
    """Normalised query execution states."""

    SUCCEEDED = "succeeded"
    FAILED = "failed"
    CANCELLED = "cancelled"
    RUNNING = "running"
    UNKNOWN = "unknown"


@dataclass(frozen=True, slots=True)
class QueryHistoryRecord:
    """One normalised Redshift query execution."""

    query_id: str
    user_name: str | None
    database_name: str | None
    status: QueryStatus
    query_type: str | None
    started_at: datetime | None
    ended_at: datetime | None
    elapsed_ms: int | None
    queue_ms: int | None
    error_message: str | None
    source_family: ViewFamily
    source_query_id: str


@dataclass(frozen=True, slots=True)
class QueryHistoryResult:
    """Normalised query-history collection."""

    records: tuple[QueryHistoryRecord, ...]
    resolution: QueryResolution

    @property
    def total_queries(self) -> int:
        """Return total collected query executions."""
        return len(self.records)


def normalise_query_status(value: object) -> QueryStatus:
    """Map Redshift-specific states into stable values."""
    normalised = str(value or "").strip().lower()

    aliases = {
        "success": QueryStatus.SUCCEEDED,
        "succeeded": QueryStatus.SUCCEEDED,
        "completed": QueryStatus.SUCCEEDED,
        "failed": QueryStatus.FAILED,
        "error": QueryStatus.FAILED,
        "aborted": QueryStatus.CANCELLED,
        "cancelled": QueryStatus.CANCELLED,
        "canceled": QueryStatus.CANCELLED,
        "planning": QueryStatus.RUNNING,
        "queued": QueryStatus.RUNNING,
        "running": QueryStatus.RUNNING,
        "returning": QueryStatus.RUNNING,
    }

    return aliases.get(normalised, QueryStatus.UNKNOWN)


def _column_names(cursor: CursorProtocol) -> tuple[str, ...]:
    """Return lower-case DB-API column names."""
    if not cursor.description:
        return ()

    return tuple(
        str(column[0]).lower()
        for column in cursor.description
    )


def _rows_as_mappings(
    cursor: CursorProtocol,
    rows: list[tuple[Any, ...]],
) -> tuple[dict[str, Any], ...]:
    """Convert DB-API rows into mappings."""
    columns = _column_names(cursor)

    if not columns:
        raise RedshiftQueryError(
            "Query-history SQL returned no column metadata."
        )

    return tuple(
        dict(zip(columns, row, strict=True))
        for row in rows
    )


def _first_present(
    row: dict[str, Any],
    *names: str,
) -> Any:
    """Return the first matching column value."""
    for name in names:
        if name in row:
            return row[name]

    return None


def _parse_datetime(value: object) -> datetime | None:
    """Parse a datetime value when one is available."""
    if value is None:
        return None

    if isinstance(value, datetime):
        return value

    try:
        return datetime.fromisoformat(str(value))
    except ValueError:
        return None


def _parse_int(value: object) -> int | None:
    """Parse a non-negative integer where possible."""
    if value is None:
        return None

    if isinstance(value, bool):
        return None

    if isinstance(value, int):
        return max(value, 0)

    if isinstance(value, float):
        return max(int(value), 0)

    if isinstance(value, str):
        try:
            return max(int(value.strip()), 0)
        except ValueError:
            return None

    try:
        return max(int(str(value)), 0)
    except ValueError:
        return None


def _normalise_query_row(
    row: dict[str, Any],
    resolution: QueryResolution,
) -> QueryHistoryRecord:
    """Normalise one query-history source row."""
    query_id = _first_present(
        row,
        "query_id",
        "query",
    )

    if query_id is None:
        raise RedshiftQueryError(
            "Query-history row is missing a query identifier."
        )

    error_value = _first_present(
        row,
        "error_message",
        "error",
    )

    return QueryHistoryRecord(
        query_id=str(query_id),
        user_name=(
            str(value)
            if (
                value := _first_present(
                    row,
                    "user_name",
                    "username",
                )
            ) is not None
            else None
        ),
        database_name=(
            str(value)
            if (
                value := _first_present(
                    row,
                    "database_name",
                    "database",
                )
            ) is not None
            else None
        ),
        status=normalise_query_status(
            _first_present(
                row,
                "status",
                "query_status",
            )
        ),
        query_type=(
            str(value)
            if (
                value := _first_present(
                    row,
                    "query_type",
                    "query_category",
                )
            ) is not None
            else None
        ),
        started_at=_parse_datetime(
            _first_present(
                row,
                "start_time",
                "started_at",
            )
        ),
        ended_at=_parse_datetime(
            _first_present(
                row,
                "end_time",
                "ended_at",
            )
        ),
        elapsed_ms=_parse_int(
            _first_present(
                row,
                "elapsed_ms",
                "elapsed_time",
            )
        ),
        queue_ms=_parse_int(
            _first_present(
                row,
                "queue_ms",
                "queue_time",
            )
        ),
        error_message=(
            redact_text(str(error_value))
            if error_value is not None
            else None
        ),
        source_family=resolution.selected_family,
        source_query_id=resolution.query.query_id,
    )

def _collect_for_purpose(
    config: RedshiftConfig,
    capability_report: CapabilityReport,
    purpose: QueryPurpose,
) -> QueryHistoryResult:
    """Resolve and collect query records for one purpose."""
    registry = build_builtin_registry()

    resolution = resolve_query(
        registry,
        purpose,
        capability_report,
        config.compatibility,
    )

    with redshift_connection(config) as connection:
        cursor = connection.cursor()

        try:
            cursor.execute(resolution.query.sql)
            raw_rows = cursor.fetchall()
            rows = _rows_as_mappings(
                cursor,
                list(raw_rows),
            )
        except Exception as exc:
            safe_message = redact_text(str(exc))

            raise RedshiftQueryError(
                "Query collection failed using "
                f"{resolution.query.query_id}: {safe_message}"
            ) from exc
        finally:
            cursor.close()

    return QueryHistoryResult(
        records=tuple(
            _normalise_query_row(row, resolution)
            for row in rows
        ),
        resolution=resolution,
    )

def collect_query_history(
    config: RedshiftConfig,
    capability_report: CapabilityReport,
) -> QueryHistoryResult:
    """Collect recent Redshift query history."""
    return _collect_for_purpose(
        config,
        capability_report,
        QueryPurpose.QUERY_HISTORY,
    )

def collect_running_queries(
    config: RedshiftConfig,
    capability_report: CapabilityReport,
) -> QueryHistoryResult:
    """Collect currently active Redshift queries."""
    return _collect_for_purpose(
        config,
        capability_report,
        QueryPurpose.RUNNING_QUERIES,
    )