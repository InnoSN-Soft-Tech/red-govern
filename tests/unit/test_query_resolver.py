"""Tests for capability-aware query resolution."""

import pytest

from red_govern.capabilities import (
    CapabilityReport,
    DeploymentType,
    SystemViewCapability,
    ViewFamily,
)
from red_govern.config.models import CompatibilityConfig
from red_govern.exceptions import QueryResolutionError
from red_govern.query_registry import QueryPurpose, resolve_query
from red_govern.query_registry.builtin import build_builtin_registry


def build_report(
    *views: SystemViewCapability,
) -> CapabilityReport:
    """Build a synthetic capability report."""
    return CapabilityReport(
        deployment_type=DeploymentType.PROVISIONED,
        server_version="Redshift test",
        views=views,
    )

def test_svv_inventory_query_is_selected() -> None:
    """SVV inventory should be preferred over information schema."""
    report = build_report(
        SystemViewCapability(
            relation="pg_catalog.svv_tables",
            family=ViewFamily.SVV,
            available=True,
            accessible=True,
        ),
        SystemViewCapability(
            relation="information_schema.tables",
            family=ViewFamily.INFORMATION_SCHEMA,
            available=True,
            accessible=True,
        ),
    )

    resolution = resolve_query(
        build_builtin_registry(),
        QueryPurpose.OBJECT_INVENTORY,
        report,
        CompatibilityConfig(),
    )

    assert resolution.query.query_id == "object_inventory_svv_v1"
    assert resolution.used_fallback is True

def test_information_schema_is_used_when_svv_is_missing() -> None:
    """Information schema should provide the final metadata fallback."""
    report = build_report(
        SystemViewCapability(
            relation="pg_catalog.svv_tables",
            family=ViewFamily.SVV,
            available=False,
            accessible=False,
        ),
        SystemViewCapability(
            relation="information_schema.tables",
            family=ViewFamily.INFORMATION_SCHEMA,
            available=True,
            accessible=True,
        ),
    )

    resolution = resolve_query(
        build_builtin_registry(),
        QueryPurpose.OBJECT_INVENTORY,
        report,
        CompatibilityConfig(),
    )

    assert (
        resolution.query.query_id
        == "object_inventory_information_schema_v1"
    )

def test_running_query_sys_definition_is_selected() -> None:
    """SYS_QUERY_HISTORY should be selected for active-query monitoring."""
    report = build_report(
        SystemViewCapability(
            relation="pg_catalog.sys_query_history",
            family=ViewFamily.SYS,
            available=True,
            accessible=True,
        ),
    )

    resolution = resolve_query(
        build_builtin_registry(),
        QueryPurpose.RUNNING_QUERIES,
        report,
        CompatibilityConfig(),
    )

    assert (
        resolution.query.query_id
        == "running_queries_sys_v1"
    )
    assert resolution.query.purpose == QueryPurpose.RUNNING_QUERIES
    assert resolution.selected_family == ViewFamily.SYS
    assert resolution.used_fallback is False

def test_running_query_stv_fallback_is_selected() -> None:
    """STV_RECENTS should be used when SYS history is unavailable."""
    report = build_report(
        SystemViewCapability(
            relation="pg_catalog.sys_query_history",
            family=ViewFamily.SYS,
            available=False,
            accessible=False,
        ),
        SystemViewCapability(
            relation="pg_catalog.stv_recents",
            family=ViewFamily.STV,
            available=True,
            accessible=True,
        ),
    )

    resolution = resolve_query(
        build_builtin_registry(),
        QueryPurpose.RUNNING_QUERIES,
        report,
        CompatibilityConfig(),
    )

    assert (
        resolution.query.query_id
        == "running_queries_stv_v1"
    )
    assert resolution.query.purpose == QueryPurpose.RUNNING_QUERIES
    assert resolution.selected_family == ViewFamily.STV
    assert resolution.used_fallback is True

def test_running_query_resolution_fails_without_any_source() -> None:
    """Running-query resolution should fail without SYS or STV access."""
    report = build_report(
        SystemViewCapability(
            relation="pg_catalog.sys_query_history",
            family=ViewFamily.SYS,
            available=False,
            accessible=False,
        ),
        SystemViewCapability(
            relation="pg_catalog.stv_recents",
            family=ViewFamily.STV,
            available=False,
            accessible=False,
        ),
    )

    with pytest.raises(QueryResolutionError):
        resolve_query(
            build_builtin_registry(),
            QueryPurpose.RUNNING_QUERIES,
            report,
            CompatibilityConfig(),
        )

def test_resolution_fails_without_required_relations() -> None:
    """Resolution must fail when no query requirements are met."""
    report = build_report()

    with pytest.raises(QueryResolutionError):
        resolve_query(
            build_builtin_registry(),
            QueryPurpose.OBJECT_INVENTORY,
            report,
            CompatibilityConfig(),
        )
