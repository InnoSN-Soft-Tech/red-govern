"""Tests for the Red-Govern query registry."""

import pytest

from red_govern.capabilities import DeploymentType, ViewFamily
from red_govern.exceptions import QueryRegistryError
from red_govern.query_registry import (
    QueryDefinition,
    QueryPurpose,
    QueryRegistry,
    validate_read_only_query,
)
from red_govern.query_registry.builtin import build_builtin_registry


def build_query(query_id: str = "test_query") -> QueryDefinition:
    """Build a valid synthetic query definition."""
    return QueryDefinition(
        query_id=query_id,
        purpose=QueryPurpose.OBJECT_INVENTORY,
        query_version="1.0.0",
        result_schema="object_inventory_v1",
        sql="SELECT 1",
        family=ViewFamily.INFORMATION_SCHEMA,
        deployment_types=(DeploymentType.UNKNOWN,),
        required_relations=(),
        priority=100,
    )


def test_registry_registers_and_returns_query() -> None:
    """Registered queries should be retrievable."""
    registry = QueryRegistry()
    query = build_query()

    registry.register(query)

    assert registry.get("test_query") == query


def test_duplicate_query_is_rejected() -> None:
    """Query identifiers must be unique."""
    registry = QueryRegistry()
    query = build_query()

    registry.register(query)

    with pytest.raises(QueryRegistryError):
        registry.register(query)


def test_write_query_is_rejected() -> None:
    """Write-oriented SQL must not enter the registry."""
    query = QueryDefinition(
        query_id="unsafe",
        purpose=QueryPurpose.OBJECT_INVENTORY,
        query_version="1.0.0",
        result_schema="object_inventory_v1",
        sql="DROP TABLE example",
        family=ViewFamily.INFORMATION_SCHEMA,
        deployment_types=(DeploymentType.UNKNOWN,),
        required_relations=(),
    )

    with pytest.raises(QueryRegistryError):
        validate_read_only_query(query)

def test_running_query_definitions_are_registered() -> None:
    """Both modern and legacy running-query definitions should exist."""
    registry = build_builtin_registry()

    sys_definition = registry.get(
        "running_queries_sys_v1"
    )
    stv_definition = registry.get(
        "running_queries_stv_v1"
    )

    assert (
        sys_definition.purpose
        == QueryPurpose.RUNNING_QUERIES
    )
    assert (
        stv_definition.purpose
        == QueryPurpose.RUNNING_QUERIES
    )


def test_svv_inventory_uses_redshift_table_catalog_column() -> None:
    """SVV inventory should use the real Redshift catalogue column."""
    registry = build_builtin_registry()
    query = registry.get("object_inventory_svv_v1")

    assert "table_catalog AS table_database" in query.sql
    assert "\n    table_database," not in query.sql
    assert "ORDER BY\n    table_catalog" in query.sql
