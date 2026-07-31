"""Tests for built-in running-query definitions."""

from red_govern.query_registry import QueryPurpose
from red_govern.query_registry.builtin import build_builtin_registry


def test_stv_running_query_definition_excludes_query_text() -> None:
    """Legacy active-query SQL must not expose query text."""
    registry = build_builtin_registry()

    definition = registry.get(
        "running_queries_stv_v1"
    )

    assert (
        definition.purpose
        == QueryPurpose.RUNNING_QUERIES
    )

    normalised_sql = " ".join(
        definition.sql.lower().split()
    )

    assert "pg_catalog.stv_recents" in normalised_sql
    assert "duration / 1000" in normalised_sql
    assert "querytext" not in normalised_sql
    assert "query_text" not in normalised_sql