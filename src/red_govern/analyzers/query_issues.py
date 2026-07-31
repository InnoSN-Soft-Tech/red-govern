"""Problem-query analysis for Red-Govern."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from red_govern.collectors import (
    QueryHistoryResult,
    QueryStatus,
)


class QueryIssueKind(str, Enum):
    """Supported query-issue categories."""

    FAILED = "failed"
    CANCELLED = "cancelled"
    SLOW = "slow"


@dataclass(frozen=True, slots=True)
class QueryIssue:
    """One query requiring investigation."""

    query_id: str
    kind: QueryIssueKind
    user_name: str | None
    database_name: str | None
    query_type: str | None
    elapsed_ms: int | None
    queue_ms: int | None
    error_message: str | None


@dataclass(frozen=True, slots=True)
class QueryIssueAnalysis:
    """Summary of failed, cancelled and slow queries."""

    issues: tuple[QueryIssue, ...]
    slow_threshold_ms: int

    @property
    def total_issues(self) -> int:
        """Return the total number of detected issues."""
        return len(self.issues)

    @property
    def failed_count(self) -> int:
        """Return the number of failed queries."""
        return sum(
            issue.kind == QueryIssueKind.FAILED
            for issue in self.issues
        )

    @property
    def cancelled_count(self) -> int:
        """Return the number of cancelled queries."""
        return sum(
            issue.kind == QueryIssueKind.CANCELLED
            for issue in self.issues
        )

    @property
    def slow_count(self) -> int:
        """Return the number of otherwise successful slow queries."""
        return sum(
            issue.kind == QueryIssueKind.SLOW
            for issue in self.issues
        )


def analyse_query_issues(
    history: QueryHistoryResult,
    *,
    slow_threshold_ms: int = 60_000,
) -> QueryIssueAnalysis:
    """Identify failed, cancelled and slow query executions."""
    if slow_threshold_ms <= 0:
        raise ValueError(
            "slow_threshold_ms must be greater than zero."
        )

    issues: list[QueryIssue] = []

    for record in history.records:
        if record.status == QueryStatus.FAILED:
            kind = QueryIssueKind.FAILED
        elif record.status == QueryStatus.CANCELLED:
            kind = QueryIssueKind.CANCELLED
        elif (
            record.status == QueryStatus.SUCCEEDED
            and record.elapsed_ms is not None
            and record.elapsed_ms >= slow_threshold_ms
        ):
            kind = QueryIssueKind.SLOW
        else:
            continue

        issues.append(
            QueryIssue(
                query_id=record.query_id,
                kind=kind,
                user_name=record.user_name,
                database_name=record.database_name,
                query_type=record.query_type,
                elapsed_ms=record.elapsed_ms,
                queue_ms=record.queue_ms,
                error_message=record.error_message,
            )
        )

    issues.sort(
        key=lambda issue: issue.elapsed_ms or 0,
        reverse=True,
    )

    return QueryIssueAnalysis(
        issues=tuple(issues),
        slow_threshold_ms=slow_threshold_ms,
    )
