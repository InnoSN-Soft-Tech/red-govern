"""Tests for Red-Govern JSON governance reports."""

from datetime import datetime, timezone
from pathlib import Path

import pytest

from red_govern.analyzers import analyse_object_quota
from red_govern.capabilities import (
    CapabilityReport,
    DeploymentType,
    ViewFamily,
)
from red_govern.collectors import (
    DatabaseObjectType,
    ObjectInventoryRecord,
    ObjectInventoryResult,
)
from red_govern.config.models import ObjectQuotaConfig
from red_govern.exceptions import ReportError
from red_govern.query_registry import (
    QueryDefinition,
    QueryPurpose,
    QueryResolution,
)
from red_govern.reports import (
    build_json_report,
    write_json_report,
)


def build_inventory() -> ObjectInventoryResult:
    """Build a synthetic object inventory."""
    collected_at = datetime.now(timezone.utc)

    query = QueryDefinition(
        query_id="object_inventory_svv_v1",
        purpose=QueryPurpose.OBJECT_INVENTORY,
        query_version="1.0.0",
        result_schema="object_inventory_v1",
        sql="SELECT 1",
        family=ViewFamily.SVV,
        deployment_types=(),
        required_relations=(),
    )

    resolution = QueryResolution(
        query=query,
        selected_family=ViewFamily.SVV,
        used_fallback=True,
        reason="Synthetic resolution.",
    )

    record = ObjectInventoryRecord(
        database_name="analytics",
        schema_name="sales",
        object_name="orders",
        object_type=DatabaseObjectType.TABLE,
        source_family=ViewFamily.SVV,
        source_query_id=query.query_id,
        collected_at=collected_at,
    )

    return ObjectInventoryResult(
        records=(record,),
        resolution=resolution,
        collected_at=collected_at,
    )


def build_capabilities() -> CapabilityReport:
    """Build a synthetic capability report."""
    return CapabilityReport(
        deployment_type=DeploymentType.PROVISIONED,
        server_version="Redshift test",
        views=(),
    )


def test_json_report_contains_governance_sections() -> None:
    """JSON report should contain its mandatory sections."""
    inventory = build_inventory()
    quota = analyse_object_quota(
        inventory,
        ObjectQuotaConfig(limit_override=100),
    )

    report = build_json_report(
        capabilities=build_capabilities(),
        inventory=inventory,
        quota=quota,
    )

    assert report["report_schema"] == "red_govern_json_v1"
    assert report["inventory"]["total_objects"] == 1
    assert report["quota"]["quota_limit"] == 100
    assert report["privacy"]["credentials_included"] is False


def test_json_report_contains_no_credentials() -> None:
    """Reports must not expose credential-related fields."""
    inventory = build_inventory()
    quota = analyse_object_quota(
        inventory,
        ObjectQuotaConfig(limit_override=100),
    )

    report = build_json_report(
        capabilities=build_capabilities(),
        inventory=inventory,
        quota=quota,
    )

    serialised = str(report).lower()

    assert "password" not in serialised
    assert "access_key" not in serialised
    assert "session_token" not in serialised


def test_json_report_is_written(tmp_path: Path) -> None:
    """A report should be written to local JSON."""
    destination = tmp_path / "reports" / "governance.json"

    result = write_json_report(
        {"report_schema": "test"},
        destination,
    )

    assert result.exists()
    assert '"report_schema": "test"' in result.read_text(
        encoding="utf-8"
    )


def test_existing_json_report_is_protected(
    tmp_path: Path,
) -> None:
    """Existing reports should require explicit overwrite."""
    destination = tmp_path / "governance.json"
    destination.write_text("existing", encoding="utf-8")

    with pytest.raises(ReportError):
        write_json_report(
            {"report_schema": "test"},
            destination,
        )
