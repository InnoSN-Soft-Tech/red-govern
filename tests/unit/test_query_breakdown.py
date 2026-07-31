"""Tests for query-workload breakdown analysis."""

from red_govern.analyzers import analyse_query_breakdown
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
    """Build synthetic query history for breakdown tests."""
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
            query_id="query-1",
            user_name="analyst",
            database_name="analytics",
            status=QueryStatus.SUCCEEDED,
            query_type="select",
            started_at=None,
            ended_at=None,
            elapsed_ms=1_000,
            queue_ms=100,
            error_message=None,
            source_family=ViewFamily.SYS,
            source_query_id=query.query_id,
        ),
        QueryHistoryRecord(
            query_id="query-2",
            user_name="analyst",
            database_name="analytics",
            status=QueryStatus.FAILED,
            query_type="SELECT",
            started_at=None,
            ended_at=None,
            elapsed_ms=3_000,
            queue_ms=300,
            error_message="Synthetic failure",
            source_family=ViewFamily.SYS,
            source_query_id=query.query_id,
        ),
        QueryHistoryRecord(
            query_id="query-3",
            user_name="engineer",
            database_name="warehouse",
            status=QueryStatus.CANCELLED,
            query_type="INSERT",
            started_at=None,
            ended_at=None,
            elapsed_ms=2_000,
            queue_ms=None,
            error_message=None,
            source_family=ViewFamily.SYS,
            source_query_id=query.query_id,
        ),
        QueryHistoryRecord(
            query_id="query-4",
            user_name=" ",
            database_name=None,
            status=QueryStatus.RUNNING,
            query_type=None,
            started_at=None,
            ended_at=None,
            elapsed_ms=None,
            queue_ms=None,
            error_message=None,
            source_family=ViewFamily.SYS,
            source_query_id=query.query_id,
        ),
    )

    return QueryHistoryResult(
        records=records,
        resolution=resolution,
    )


def test_query_breakdown_counts_and_averages() -> None:
    """Workload should be aggregated across every supported dimension."""
    analysis = analyse_query_breakdown(
        build_history()
    )

    assert analysis.total_queries == 4

    users = {
        row.name: row
        for row in analysis.by_user
    }

    assert users["analyst"].total_queries == 2
    assert users["analyst"].succeeded_queries == 1
    assert users["analyst"].failed_queries == 1
    assert users["analyst"].average_elapsed_ms == 2_000
    assert users["analyst"].average_queue_ms == 200

    databases = {
        row.name: row
        for row in analysis.by_database
    }

    assert databases["analytics"].total_queries == 2
    assert databases["warehouse"].cancelled_queries == 1

    query_types = {
        row.name: row
        for row in analysis.by_query_type
    }

    assert query_types["SELECT"].total_queries == 2
    assert query_types["INSERT"].total_queries == 1


def test_missing_breakdown_values_are_grouped_as_unknown() -> None:
    """Missing and blank dimension values should use the Unknown group."""
    analysis = analyse_query_breakdown(
        build_history()
    )

    users = {
        row.name: row
        for row in analysis.by_user
    }
    databases = {
        row.name: row
        for row in analysis.by_database
    }
    query_types = {
        row.name: row
        for row in analysis.by_query_type
    }

    assert users["Unknown"].running_queries == 1
    assert databases["Unknown"].total_queries == 1
    assert query_types["Unknown"].total_queries == 1

    assert analysis.by_user[0].name == "analyst"
