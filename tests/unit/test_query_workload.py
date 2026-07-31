"""Tests for Red-Govern query-workload analysis."""

from red_govern.analyzers import analyse_query_workload
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
    """Build synthetic query history."""
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
        reason="Synthetic resolution.",
    )

    records = (
        QueryHistoryRecord(
            query_id="1",
            user_name="naman",
            database_name="analytics",
            status=QueryStatus.SUCCEEDED,
            query_type="SELECT",
            started_at=None,
            ended_at=None,
            elapsed_ms=100,
            queue_ms=10,
            error_message=None,
            source_family=ViewFamily.SYS,
            source_query_id=query.query_id,
        ),
        QueryHistoryRecord(
            query_id="2",
            user_name="naman",
            database_name="analytics",
            status=QueryStatus.FAILED,
            query_type="SELECT",
            started_at=None,
            ended_at=None,
            elapsed_ms=300,
            queue_ms=30,
            error_message="failure",
            source_family=ViewFamily.SYS,
            source_query_id=query.query_id,
        ),
    )

    return QueryHistoryResult(
        records=records,
        resolution=resolution,
    )


def test_query_workload_analysis() -> None:
    """Workload statistics should be calculated correctly."""
    analysis = analyse_query_workload(
        build_history()
    )

    assert analysis.total_queries == 2
    assert analysis.succeeded_queries == 1
    assert analysis.failed_queries == 1
    assert analysis.failure_rate == 50.0
    assert analysis.average_elapsed_ms == 200.0
    assert analysis.maximum_elapsed_ms == 300
    assert analysis.average_queue_ms == 20.0
