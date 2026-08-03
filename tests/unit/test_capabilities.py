"""Tests for Red-Govern capability detection models."""

from red_govern.capabilities.detector import (
    CapabilityReport,
    _relations_for_deployment,
)
from red_govern.capabilities.permissions import summarise_permissions
from red_govern.capabilities.system_views import (
    DeploymentType,
    SystemViewCapability,
    ViewFamily,
)


def test_relation_availability() -> None:
    """Accessible relations should be reported as available."""
    report = CapabilityReport(
        deployment_type=DeploymentType.PROVISIONED,
        server_version="Redshift test",
        views=(
            SystemViewCapability(
                relation="pg_catalog.sys_query_history",
                family=ViewFamily.SYS,
                available=True,
                accessible=True,
            ),
        ),
    )

    assert report.relation_available(
        "pg_catalog.sys_query_history"
    )
    assert report.family_available(ViewFamily.SYS)


def test_permission_summary() -> None:
    """Permission summary should distinguish all probe states."""
    report = CapabilityReport(
        deployment_type=DeploymentType.UNKNOWN,
        server_version="Redshift test",
        views=(
            SystemViewCapability(
                relation="accessible",
                family=ViewFamily.SYS,
                available=True,
                accessible=True,
            ),
            SystemViewCapability(
                relation="restricted",
                family=ViewFamily.SVV,
                available=True,
                accessible=False,
            ),
            SystemViewCapability(
                relation="missing",
                family=ViewFamily.STL,
                available=False,
                accessible=False,
            ),
        ),
    )

    summary = summarise_permissions(report)

    assert summary.accessible_relations == 1
    assert summary.inaccessible_relations == 1
    assert summary.missing_relations == 1


def test_relations_are_filtered_by_configured_deployment() -> None:
    """Deployment-specific probes should avoid irrelevant relations."""
    serverless_relations = {
        relation
        for relation, _family in _relations_for_deployment(
            DeploymentType.SERVERLESS
        )
    }
    provisioned_relations = {
        relation
        for relation, _family in _relations_for_deployment(
            DeploymentType.PROVISIONED
        )
    }

    assert "pg_catalog.sys_serverless_usage" in serverless_relations
    assert "pg_catalog.stl_query" not in serverless_relations
    assert "pg_catalog.stv_recents" not in serverless_relations

    assert "pg_catalog.sys_serverless_usage" not in provisioned_relations
    assert "pg_catalog.stl_query" in provisioned_relations
