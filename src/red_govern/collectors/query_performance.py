"""Completed-query performance collection for Red-Govern."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

from red_govern.capabilities import CapabilityReport, ViewFamily
from red_govern.collectors.query_history import (
    QueryStatus,
    normalise_query_status,
)
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


@dataclass(frozen=True, slots=True)
class QueryPerformanceRecord:
    """One normalised Redshift query-performance record."""

    query_id: str
    user_id: int | None
    user_name: str | None
    database_name: str | None
    status: QueryStatus
    query_type: str | None
    started_at: datetime | None
    ended_at: datetime | None
    elapsed_ms: int | None
    queue_ms: int | None
    execution_ms: int | None
    cpu_ms: int | None
    cpu_usage_percent: float | None
    blocks_read: int | None
    blocks_write: int | None
    temp_blocks_to_disk: int | None
    input_rows: int | None
    output_rows: int | None
    input_bytes: int | None
    output_bytes: int | None
    returned_rows: int | None
    returned_bytes: int | None
    cpu_skew: float | None
    io_skew: float | None
    data_skewness: float | None
    time_skewness: float | None
    alert_count: int | None
    source_family: ViewFamily
    source_query_id: str


@dataclass(frozen=True, slots=True)
class QueryPerformanceResult:
    """Normalised query-performance collection result."""

    records: tuple[QueryPerformanceRecord, ...]
    resolution: QueryResolution

    @property
    def total_queries(self) -> int:
        """Return the total number of performance records."""

        return len(self.records)


def _column_names(cursor: CursorProtocol) -> tuple[str, ...]:
    """Return lower-case DB-API result-column names."""

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
    """Convert DB-API rows into dictionaries."""

    columns = _column_names(cursor)

    if not columns:
        raise RedshiftQueryError(
            "Query-performance SQL returned no column metadata."
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


def _optional_text(value: object) -> str | None:
    """Convert an optional value into non-empty text."""

    if value is None:
        return None

    text = str(value).strip()
    return text or None


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

    if value is None or isinstance(value, bool):
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


def _parse_float(value: object) -> float | None:
    """Parse a non-negative floating-point value."""

    if value is None or isinstance(value, bool):
        return None

    if isinstance(value, int | float):
        return max(float(value), 0.0)

    try:
        return max(float(str(value).strip()), 0.0)
    except ValueError:
        return None


def normalise_query_performance_row(
    row: dict[str, Any],
    *,
    source_family: ViewFamily,
    source_query_id: str,
) -> QueryPerformanceRecord:
    """Normalise one query-performance source row."""

    query_id = _first_present(
        row,
        "query_id",
        "query",
    )

    if query_id is None:
        raise RedshiftQueryError(
            "Query-performance row is missing a query identifier."
        )

    return QueryPerformanceRecord(
        query_id=str(query_id),
        user_id=_parse_int(
            _first_present(
                row,
                "user_id",
                "userid",
            )
        ),
        user_name=_optional_text(
            _first_present(
                row,
                "user_name",
                "username",
            )
        ),
        database_name=_optional_text(
            _first_present(
                row,
                "database_name",
                "database",
            )
        ),
        status=normalise_query_status(
            _first_present(
                row,
                "status",
                "query_status",
            )
        ),
        query_type=_optional_text(
            _first_present(
                row,
                "query_type",
                "query_category",
            )
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
        elapsed_ms=_parse_int(row.get("elapsed_ms")),
        queue_ms=_parse_int(row.get("queue_ms")),
        execution_ms=_parse_int(row.get("execution_ms")),
        cpu_ms=_parse_int(row.get("cpu_ms")),
        cpu_usage_percent=_parse_float(
            row.get("cpu_usage_percent")
        ),
        blocks_read=_parse_int(row.get("blocks_read")),
        blocks_write=_parse_int(row.get("blocks_write")),
        temp_blocks_to_disk=_parse_int(
            row.get("temp_blocks_to_disk")
        ),
        input_rows=_parse_int(row.get("input_rows")),
        output_rows=_parse_int(row.get("output_rows")),
        input_bytes=_parse_int(row.get("input_bytes")),
        output_bytes=_parse_int(row.get("output_bytes")),
        returned_rows=_parse_int(row.get("returned_rows")),
        returned_bytes=_parse_int(row.get("returned_bytes")),
        cpu_skew=_parse_float(row.get("cpu_skew")),
        io_skew=_parse_float(row.get("io_skew")),
        data_skewness=_parse_float(row.get("data_skewness")),
        time_skewness=_parse_float(row.get("time_skewness")),
        alert_count=_parse_int(row.get("alert_count")),
        source_family=source_family,
        source_query_id=source_query_id,
    )


def collect_query_performance(
    config: RedshiftConfig,
    capability_report: CapabilityReport,
) -> QueryPerformanceResult:
    """Collect completed-query performance information."""

    registry = build_builtin_registry()

    resolution = resolve_query(
        registry,
        QueryPurpose.QUERY_PERFORMANCE,
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
                "Query-performance collection failed using "
                f"{resolution.query.query_id}: {safe_message}"
            ) from exc
        finally:
            cursor.close()

    return QueryPerformanceResult(
        records=tuple(
            normalise_query_performance_row(
                row,
                source_family=resolution.selected_family,
                source_query_id=resolution.query.query_id,
            )
            for row in rows
        ),
        resolution=resolution,
    )
