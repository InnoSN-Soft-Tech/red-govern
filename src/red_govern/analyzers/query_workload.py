"""Query-workload analysis for Red-Govern."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass

from red_govern.collectors import (
    QueryHistoryResult,
    QueryStatus,
)


@dataclass(frozen=True, slots=True)
class QueryStatusCount:
    """Query count for one status."""

    status: QueryStatus
    count: int


@dataclass(frozen=True, slots=True)
class QueryWorkloadAnalysis:
    """Summary of collected Redshift workload."""

    total_queries: int
    succeeded_queries: int
    failed_queries: int
    cancelled_queries: int
    running_queries: int
    unknown_queries: int
    average_elapsed_ms: float | None
    maximum_elapsed_ms: int | None
    average_queue_ms: float | None
    by_status: tuple[QueryStatusCount, ...]

    @property
    def failure_rate(self) -> float:
        """Return failed-query percentage."""
        if self.total_queries == 0:
            return 0.0

        return round(
            self.failed_queries / self.total_queries * 100,
            2,
        )

    @property
    def cancellation_rate(self) -> float:
        """Return cancelled-query percentage."""
        if self.total_queries == 0:
            return 0.0

        return round(
            self.cancelled_queries / self.total_queries * 100,
            2,
        )


def _average(values: list[int]) -> float | None:
    """Return a rounded average for non-empty values."""
    if not values:
        return None

    return round(sum(values) / len(values), 2)


def analyse_query_workload(
    history: QueryHistoryResult,
) -> QueryWorkloadAnalysis:
    """Analyse normalised Redshift query history."""
    counts = Counter(
        record.status
        for record in history.records
    )

    elapsed_values = [
        record.elapsed_ms
        for record in history.records
        if record.elapsed_ms is not None
    ]

    queue_values = [
        record.queue_ms
        for record in history.records
        if record.queue_ms is not None
    ]

    return QueryWorkloadAnalysis(
        total_queries=history.total_queries,
        succeeded_queries=counts[QueryStatus.SUCCEEDED],
        failed_queries=counts[QueryStatus.FAILED],
        cancelled_queries=counts[QueryStatus.CANCELLED],
        running_queries=counts[QueryStatus.RUNNING],
        unknown_queries=counts[QueryStatus.UNKNOWN],
        average_elapsed_ms=_average(elapsed_values),
        maximum_elapsed_ms=(
            max(elapsed_values)
            if elapsed_values
            else None
        ),
        average_queue_ms=_average(queue_values),
        by_status=tuple(
            QueryStatusCount(
                status=status,
                count=counts[status],
            )
            for status in QueryStatus
        ),
    )
