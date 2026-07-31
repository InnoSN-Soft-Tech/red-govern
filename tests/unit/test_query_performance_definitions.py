"""Tests for completed-query performance definitions."""

from red_govern.capabilities import ViewFamily
from red_govern.query_registry import QueryPurpose
from red_govern.query_registry.builtin import build_builtin_registry


def test_query_performance_definitions_are_registered() -> None:
    """Both modern and legacy performance definitions should exist."""
    registry = build_builtin_registry()

    definitions = registry.for_purpose(
        QueryPurpose.QUERY_PERFORMANCE
    )

    definitions_by_id = {
        definition.query_id: definition
        for definition in definitions
    }

    assert set(definitions_by_id) == {
        "query_performance_sys_v1",
        "query_performance_svl_v1",
    }

    assert (
        definitions_by_id["query_performance_sys_v1"].family
        is ViewFamily.SYS
    )
    assert (
        definitions_by_id["query_performance_svl_v1"].family
        is ViewFamily.SVL
    )


def test_query_performance_definitions_exclude_query_text() -> None:
    """Performance queries must not collect SQL text."""
    registry = build_builtin_registry()

    definitions = registry.for_purpose(
        QueryPurpose.QUERY_PERFORMANCE
    )

    assert definitions
    assert all(
        "query_text" not in definition.sql.lower()
        for definition in definitions
    )
