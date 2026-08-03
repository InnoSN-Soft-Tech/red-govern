"""Query-performance issue analysis for Red-Govern."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from red_govern.collectors.query_performance import QueryPerformanceRecord


class QueryPerformanceIssueType(str, Enum):
    """Supported query-performance issue categories."""

    SLOW_QUERY = "slow_query"
    QUEUE_WAIT = "queue_wait"
    DISK_SPILL = "disk_spill"
    HIGH_CPU = "high_cpu"
    SKEW = "skew"
    REDSHIFT_ALERT = "redshift_alert"


class QueryPerformanceSeverity(str, Enum):
    """Severity assigned to one detected issue."""

    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class QueryPerformanceThresholds:
    """Thresholds used for query-performance analysis."""

    slow_query_ms: int = 60_000
    queue_wait_ms: int = 10_000
    cpu_usage_percent: float = 80.0
    skew_ratio: float = 2.0
    spill_blocks: int = 1
    alert_count: int = 1
    data_time_skew_percent: float = 50.0

    def __post_init__(self) -> None:
        """Reject zero or negative thresholds."""

        values: tuple[tuple[str, float], ...] = (
            ("slow_query_ms", float(self.slow_query_ms)),
            ("queue_wait_ms", float(self.queue_wait_ms)),
            ("cpu_usage_percent", self.cpu_usage_percent),
            ("skew_ratio", self.skew_ratio),
            ("spill_blocks", float(self.spill_blocks)),
            ("alert_count", float(self.alert_count)),
            (
                "data_time_skew_percent",
                self.data_time_skew_percent,
            ),
        )

        for name, value in values:
            if value <= 0:
                raise ValueError(
                    f"{name} must be greater than zero."
                )

        if self.data_time_skew_percent > 100:
            raise ValueError(
                "data_time_skew_percent must not exceed 100."
            )


@dataclass(frozen=True, slots=True)
class QueryPerformanceIssue:
    """One performance issue detected for a Redshift query."""

    query_id: str
    issue_type: QueryPerformanceIssueType
    severity: QueryPerformanceSeverity
    metric_name: str
    metric_value: float
    threshold: float
    message: str


@dataclass(frozen=True, slots=True)
class QueryPerformanceAnalysis:
    """Collection of detected query-performance issues."""

    issues: tuple[QueryPerformanceIssue, ...]

    @property
    def total_issues(self) -> int:
        """Return the total number of detected issues."""

        return len(self.issues)

    @property
    def affected_query_ids(self) -> tuple[str, ...]:
        """Return unique query identifiers containing issues."""

        return tuple(
            sorted(
                {
                    issue.query_id
                    for issue in self.issues
                }
            )
        )

    @property
    def affected_query_count(self) -> int:
        """Return the number of affected queries."""

        return len(self.affected_query_ids)

    @property
    def critical_issue_count(self) -> int:
        """Return the number of critical issues."""

        return sum(
            issue.severity is QueryPerformanceSeverity.CRITICAL
            for issue in self.issues
        )


def _severity(
    value: float,
    threshold: float,
    critical_multiplier: float,
) -> QueryPerformanceSeverity:
    """Determine warning or critical severity."""

    if value >= threshold * critical_multiplier:
        return QueryPerformanceSeverity.CRITICAL

    return QueryPerformanceSeverity.WARNING


def _append_issue(
    issues: list[QueryPerformanceIssue],
    *,
    record: QueryPerformanceRecord,
    issue_type: QueryPerformanceIssueType,
    metric_name: str,
    value: int | float | None,
    threshold: int | float,
    critical_multiplier: float = 2.0,
) -> None:
    """Append an issue when a metric reaches its threshold."""

    if value is None:
        return

    numeric_value = float(value)
    numeric_threshold = float(threshold)

    if numeric_value < numeric_threshold:
        return

    issues.append(
        QueryPerformanceIssue(
            query_id=record.query_id,
            issue_type=issue_type,
            severity=_severity(
                numeric_value,
                numeric_threshold,
                critical_multiplier,
            ),
            metric_name=metric_name,
            metric_value=numeric_value,
            threshold=numeric_threshold,
            message=(
                f"{metric_name.replace('_', ' ')} is "
                f"{numeric_value:g}; threshold is "
                f"{numeric_threshold:g}."
            ),
        )
    )


def analyse_query_performance(
    records: tuple[QueryPerformanceRecord, ...],
    thresholds: QueryPerformanceThresholds | None = None,
) -> QueryPerformanceAnalysis:
    """Analyse completed-query performance records."""

    effective_thresholds = (
        thresholds
        if thresholds is not None
        else QueryPerformanceThresholds()
    )

    issues: list[QueryPerformanceIssue] = []

    for record in records:
        _append_issue(
            issues,
            record=record,
            issue_type=QueryPerformanceIssueType.SLOW_QUERY,
            metric_name="elapsed_ms",
            value=record.elapsed_ms,
            threshold=effective_thresholds.slow_query_ms,
        )

        _append_issue(
            issues,
            record=record,
            issue_type=QueryPerformanceIssueType.QUEUE_WAIT,
            metric_name="queue_ms",
            value=record.queue_ms,
            threshold=effective_thresholds.queue_wait_ms,
        )

        _append_issue(
            issues,
            record=record,
            issue_type=QueryPerformanceIssueType.DISK_SPILL,
            metric_name="temp_blocks_to_disk",
            value=record.temp_blocks_to_disk,
            threshold=effective_thresholds.spill_blocks,
            critical_multiplier=10.0,
        )

        _append_issue(
            issues,
            record=record,
            issue_type=QueryPerformanceIssueType.HIGH_CPU,
            metric_name="cpu_usage_percent",
            value=record.cpu_usage_percent,
            threshold=effective_thresholds.cpu_usage_percent,
            critical_multiplier=1.15,
        )

        ratio_skew_metrics: tuple[
            tuple[str, float | None],
            ...,
        ] = (
            ("cpu_skew", record.cpu_skew),
            ("io_skew", record.io_skew),
        )

        for metric_name, value in ratio_skew_metrics:
            _append_issue(
                issues,
                record=record,
                issue_type=QueryPerformanceIssueType.SKEW,
                metric_name=metric_name,
                value=value,
                threshold=effective_thresholds.skew_ratio,
            )

        percentage_skew_metrics: tuple[
            tuple[str, float | None],
            ...,
        ] = (
            ("data_skewness", record.data_skewness),
            ("time_skewness", record.time_skewness),
        )

        for metric_name, value in percentage_skew_metrics:
            _append_issue(
                issues,
                record=record,
                issue_type=QueryPerformanceIssueType.SKEW,
                metric_name=metric_name,
                value=value,
                threshold=(
                    effective_thresholds.data_time_skew_percent
                ),
                critical_multiplier=1.5,
            )

        _append_issue(
            issues,
            record=record,
            issue_type=QueryPerformanceIssueType.REDSHIFT_ALERT,
            metric_name="alert_count",
            value=record.alert_count,
            threshold=effective_thresholds.alert_count,
            critical_multiplier=5.0,
        )

    severity_rank = {
        QueryPerformanceSeverity.CRITICAL: 0,
        QueryPerformanceSeverity.WARNING: 1,
    }

    issues.sort(
        key=lambda issue: (
            severity_rank[issue.severity],
            issue.query_id,
            issue.issue_type.value,
            issue.metric_name,
        )
    )

    return QueryPerformanceAnalysis(
        issues=tuple(issues),
    )
