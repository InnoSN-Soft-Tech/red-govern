"""Tests for query-performance issue analysis."""

import pytest

from red_govern.analyzers import (
    QueryPerformanceIssueType,
    QueryPerformanceSeverity,
    QueryPerformanceThresholds,
    analyse_query_performance,
)
from red_govern.capabilities import ViewFamily
from red_govern.collectors import QueryPerformanceRecord
from red_govern.collectors.query_history import QueryStatus


def build_record(
    *,
    query_id: str = "query-1",
    elapsed_ms: int | None = 500,
    queue_ms: int | None = 50,
    cpu_usage_percent: float | None = 20.0,
    temp_blocks_to_disk: int | None = 0,
    cpu_skew: float | None = 1.0,
    io_skew: float | None = 1.0,
    data_skewness: float | None = 1.0,
    time_skewness: float | None = 1.0,
    alert_count: int | None = 0,
) -> QueryPerformanceRecord:
    """Build one synthetic query-performance record."""

    return QueryPerformanceRecord(
        query_id=query_id,
        user_id=None,
        user_name=None,
        database_name="analytics",
        status=QueryStatus.SUCCEEDED,
        query_type="SELECT",
        started_at=None,
        ended_at=None,
        elapsed_ms=elapsed_ms,
        queue_ms=queue_ms,
        execution_ms=None,
        cpu_ms=None,
        cpu_usage_percent=cpu_usage_percent,
        blocks_read=None,
        blocks_write=None,
        temp_blocks_to_disk=temp_blocks_to_disk,
        input_rows=None,
        output_rows=None,
        input_bytes=None,
        output_bytes=None,
        returned_rows=None,
        returned_bytes=None,
        cpu_skew=cpu_skew,
        io_skew=io_skew,
        data_skewness=data_skewness,
        time_skewness=time_skewness,
        alert_count=alert_count,
        source_family=ViewFamily.SYS,
        source_query_id="query_performance_sys_v1",
    )


def test_slow_and_queued_queries_are_flagged() -> None:
    """Elapsed and queue thresholds should produce issues."""

    analysis = analyse_query_performance(
        (
            build_record(
                elapsed_ms=60_000,
                queue_ms=10_000,
            ),
        )
    )

    issue_types = {
        issue.issue_type
        for issue in analysis.issues
    }

    assert QueryPerformanceIssueType.SLOW_QUERY in issue_types
    assert QueryPerformanceIssueType.QUEUE_WAIT in issue_types
    assert analysis.affected_query_ids == ("query-1",)


def test_spill_cpu_skew_and_alerts_are_flagged() -> None:
    """Resource pressure and Redshift alerts should be detected."""

    analysis = analyse_query_performance(
        (
            build_record(
                temp_blocks_to_disk=3,
                cpu_usage_percent=85.0,
                cpu_skew=2.5,
                alert_count=1,
            ),
        )
    )

    issue_types = {
        issue.issue_type
        for issue in analysis.issues
    }

    assert QueryPerformanceIssueType.DISK_SPILL in issue_types
    assert QueryPerformanceIssueType.HIGH_CPU in issue_types
    assert QueryPerformanceIssueType.SKEW in issue_types
    assert QueryPerformanceIssueType.REDSHIFT_ALERT in issue_types


def test_healthy_query_has_no_issues() -> None:
    """Healthy performance values should not create issues."""

    analysis = analyse_query_performance(
        (
            build_record(),
        )
    )

    assert analysis.total_issues == 0
    assert analysis.affected_query_count == 0
    assert analysis.critical_issue_count == 0


def test_extremely_slow_query_is_critical() -> None:
    """A value twice the threshold should be critical."""

    analysis = analyse_query_performance(
        (
            build_record(
                elapsed_ms=120_000,
            ),
        )
    )

    slow_issue = next(
        issue
        for issue in analysis.issues
        if issue.issue_type
        is QueryPerformanceIssueType.SLOW_QUERY
    )

    assert (
        slow_issue.severity
        is QueryPerformanceSeverity.CRITICAL
    )
    assert analysis.critical_issue_count == 1


def test_invalid_threshold_is_rejected() -> None:
    """Threshold values must remain greater than zero."""

    with pytest.raises(
        ValueError,
        match="slow_query_ms must be greater than zero",
    ):
        QueryPerformanceThresholds(
            slow_query_ms=0,
        )
