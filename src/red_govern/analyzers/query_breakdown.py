"""Query-workload breakdown analysis for Red-Govern."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from red_govern.collectors import (
    QueryHistoryRecord,
    QueryHistoryResult,
    QueryStatus,
)


@dataclass(slots=True)
class _MutableBreakdown:
    """Mutable counters used while building a breakdown."""

    total_queries: int = 0
    succeeded_queries: int = 0
    failed_queries: int = 0
    cancelled_queries: int = 0
    running_queries: int = 0
    total_elapsed_ms: int = 0
    timed_queries: int = 0
    total_queue_ms: int = 0
    queued_queries: int = 0


@dataclass(frozen=True, slots=True)
class QueryBreakdownRow:
    """Aggregated query workload for one grouping value."""

    name: str
    total_queries: int
    succeeded_queries: int
    failed_queries: int
    cancelled_queries: int
    running_queries: int
    total_elapsed_ms: int
    timed_queries: int
    total_queue_ms: int
    queued_queries: int

    @property
    def average_elapsed_ms(self) -> float | None:
        """Return average execution time for timed queries."""
        if self.timed_queries == 0:
            return None

        return self.total_elapsed_ms / self.timed_queries

    @property
    def average_queue_ms(self) -> float | None:
        """Return average queue time for queries with queue metrics."""
        if self.queued_queries == 0:
            return None

        return self.total_queue_ms / self.queued_queries

    @property
    def other_queries(self) -> int:
        """Return queries that do not have a recognised public status."""
        recognised = (
            self.succeeded_queries
            + self.failed_queries
            + self.cancelled_queries
            + self.running_queries
        )

        return self.total_queries - recognised


@dataclass(frozen=True, slots=True)
class QueryBreakdownAnalysis:
    """Query workload grouped across supported dimensions."""

    total_queries: int
    by_user: tuple[QueryBreakdownRow, ...]
    by_database: tuple[QueryBreakdownRow, ...]
    by_query_type: tuple[QueryBreakdownRow, ...]


def _normalise_group_name(value: str | None) -> str:
    """Return a safe grouping value."""
    if value is None:
        return "Unknown"

    cleaned = value.strip()

    return cleaned or "Unknown"


def _build_breakdown(
    records: tuple[QueryHistoryRecord, ...],
    selector: Callable[[QueryHistoryRecord], str | None],
) -> tuple[QueryBreakdownRow, ...]:
    """Aggregate query records using one grouping selector."""
    groups: dict[str, _MutableBreakdown] = {}

    for record in records:
        name = _normalise_group_name(selector(record))
        counters = groups.setdefault(
            name,
            _MutableBreakdown(),
        )

        counters.total_queries += 1

        if record.status == QueryStatus.SUCCEEDED:
            counters.succeeded_queries += 1
        elif record.status == QueryStatus.FAILED:
            counters.failed_queries += 1
        elif record.status == QueryStatus.CANCELLED:
            counters.cancelled_queries += 1
        elif record.status == QueryStatus.RUNNING:
            counters.running_queries += 1

        if record.elapsed_ms is not None:
            counters.total_elapsed_ms += record.elapsed_ms
            counters.timed_queries += 1

        if record.queue_ms is not None:
            counters.total_queue_ms += record.queue_ms
            counters.queued_queries += 1

    rows = tuple(
        QueryBreakdownRow(
            name=name,
            total_queries=counters.total_queries,
            succeeded_queries=counters.succeeded_queries,
            failed_queries=counters.failed_queries,
            cancelled_queries=counters.cancelled_queries,
            running_queries=counters.running_queries,
            total_elapsed_ms=counters.total_elapsed_ms,
            timed_queries=counters.timed_queries,
            total_queue_ms=counters.total_queue_ms,
            queued_queries=counters.queued_queries,
        )
        for name, counters in groups.items()
    )

    return tuple(
        sorted(
            rows,
            key=lambda row: (
                -row.total_queries,
                row.name.lower(),
            ),
        )
    )


def analyse_query_breakdown(
    history: QueryHistoryResult,
) -> QueryBreakdownAnalysis:
    """Break query workload down by user, database, and query type."""
    return QueryBreakdownAnalysis(
        total_queries=history.total_queries,
        by_user=_build_breakdown(
            history.records,
            lambda record: record.user_name,
        ),
        by_database=_build_breakdown(
            history.records,
            lambda record: record.database_name,
        ),
        by_query_type=_build_breakdown(
            history.records,
            lambda record: (
                record.query_type.upper()
                if record.query_type is not None
                else None
            ),
        ),
    )
