"""Tests for failed, cancelled and slow-query analysis."""

import pytest

from red_govern.analyzers import (
    QueryIssueKind,
    analyse_query_issues,
)
from red_govern.capabilities import ViewFamily
from red_govern.collectors import (
    QueryHistoryRecord,
    QueryHistoryResult,
    QueryStatus,
)
from red_govern.query_registry import (
    QueryDefinition,
    QueryPurpose,
    QueryResolution,
)


def build_history() -> QueryHistoryResult:
    """Build synthetic query history containing several outcomes."""
    query = QueryDefinition(
        query_id="query_history_sys_v1",
        purpose=QueryPurpose.QUERY_HISTORY,
        query_version="1.0.0",
        result_schema="query_history_v1",
        sql="SELECT 1",
        family=ViewFamily.SYS,
        deployment_types=(),
        required_relations=(),
    )

    resolution = QueryResolution(
        query=query,
        selected_family=ViewFamily.SYS,
        used_fallback=False,
        reason="Synthetic test resolution.",
    )

    records = (
        QueryHistoryRecord(
            query_id="slow-query",
            user_name="analyst",
            database_name="analytics",
            status=QueryStatus.SUCCEEDED,
            query_type="SELECT",
            started_at=None,
            ended_at=None,
            elapsed_ms=120_000,
            queue_ms=10_000,
            error_message=None,
            source_family=ViewFamily.SYS,
            source_query_id=query.query_id,
        ),
        QueryHistoryRecord(
            query_id="failed-query",
            user_name="engineer",
            database_name="analytics",
            status=QueryStatus.FAILED,
            query_type="INSERT",
            started_at=None,
            ended_at=None,
            elapsed_ms=2_000,
            queue_ms=100,
            error_message="Permission denied",
            source_family=ViewFamily.SYS,
            source_query_id=query.query_id,
        ),
        QueryHistoryRecord(
            query_id="cancelled-query",
            user_name="analyst",
            database_name="analytics",
            status=QueryStatus.CANCELLED,
            query_type="SELECT",
            started_at=None,
            ended_at=None,
            elapsed_ms=500,
            queue_ms=50,
            error_message=None,
            source_family=ViewFamily.SYS,
            source_query_id=query.query_id,
        ),
        QueryHistoryRecord(
            query_id="healthy-query",
            user_name="analyst",
            database_name="analytics",
            status=QueryStatus.SUCCEEDED,
            query_type="SELECT",
            started_at=None,
            ended_at=None,
            elapsed_ms=1_000,
            queue_ms=25,
            error_message=None,
            source_family=ViewFamily.SYS,
            source_query_id=query.query_id,
        ),
    )

    return QueryHistoryResult(
        records=records,
        resolution=resolution,
    )


def test_query_issue_analysis() -> None:
    """Failed, cancelled and slow queries should be identified."""
    analysis = analyse_query_issues(
        build_history(),
        slow_threshold_ms=60_000,
    )

    assert analysis.total_issues == 3
    assert analysis.failed_count == 1
    assert analysis.cancelled_count == 1
    assert analysis.slow_count == 1

    kinds = {
        issue.kind
        for issue in analysis.issues
    }

    assert kinds == {
        QueryIssueKind.FAILED,
        QueryIssueKind.CANCELLED,
        QueryIssueKind.SLOW,
    }


def test_query_issue_threshold_must_be_positive() -> None:
    """A non-positive slow threshold should be rejected."""
    with pytest.raises(ValueError):
        analyse_query_issues(
            build_history(),
            slow_threshold_ms=0,
        )
