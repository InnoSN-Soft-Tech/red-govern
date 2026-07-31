"""Tests for Red-Govern object-quota analysis."""

from datetime import datetime, timezone

import pytest

from red_govern.analyzers import (
    QuotaStatus,
    analyse_object_quota,
    determine_quota_status,
)
from red_govern.capabilities import ViewFamily
from red_govern.collectors import (
    DatabaseObjectType,
    ObjectInventoryRecord,
    ObjectInventoryResult,
)
from red_govern.config.models import ObjectQuotaConfig
from red_govern.query_registry import (
    QueryDefinition,
    QueryPurpose,
    QueryResolution,
)


def build_resolution() -> QueryResolution:
    """Build a synthetic query resolution."""
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

    return QueryResolution(
        query=query,
        selected_family=ViewFamily.SVV,
        used_fallback=True,
        reason="Synthetic resolution.",
    )


def build_inventory(count: int) -> ObjectInventoryResult:
    """Build an inventory containing synthetic objects."""
    collected_at = datetime.now(timezone.utc)

    records = tuple(
        ObjectInventoryRecord(
            database_name="analytics",
            schema_name=(
                "sales"
                if index % 2 == 0
                else "finance"
            ),
            object_name=f"table_{index}",
            object_type=DatabaseObjectType.TABLE,
            source_family=ViewFamily.SVV,
            source_query_id="object_inventory_svv_v1",
            collected_at=collected_at,
        )
        for index in range(count)
    )

    return ObjectInventoryResult(
        records=records,
        resolution=build_resolution(),
        collected_at=collected_at,
    )


@pytest.mark.parametrize(
    ("ratio", "expected"),
    [
        (None, QuotaStatus.UNKNOWN),
        (0.50, QuotaStatus.HEALTHY),
        (0.80, QuotaStatus.WARNING),
        (0.90, QuotaStatus.CRITICAL),
        (1.00, QuotaStatus.CRITICAL),
        (1.01, QuotaStatus.EXCEEDED),
    ],
)
def test_quota_status(
    ratio: float | None,
    expected: QuotaStatus,
) -> None:
    """Quota ratios should map to stable status values."""
    config = ObjectQuotaConfig(
        warning_threshold=0.80,
        critical_threshold=0.90,
    )

    assert determine_quota_status(ratio, config) == expected


def test_known_quota_analysis() -> None:
    """Known quotas should produce utilisation and remaining capacity."""
    analysis = analyse_object_quota(
        build_inventory(80),
        ObjectQuotaConfig(
            limit_override=100,
            warning_threshold=0.80,
            critical_threshold=0.90,
        ),
    )

    assert analysis.current_objects == 80
    assert analysis.quota_limit == 100
    assert analysis.remaining_capacity == 20
    assert analysis.utilisation_percentage == 80.0
    assert analysis.status == QuotaStatus.WARNING


def test_unknown_quota_analysis() -> None:
    """Unknown quotas should not generate fabricated capacity values."""
    analysis = analyse_object_quota(
        build_inventory(80),
        ObjectQuotaConfig(limit_override=None),
    )

    assert analysis.quota_known is False
    assert analysis.remaining_capacity is None
    assert analysis.utilisation_percentage is None
    assert analysis.status == QuotaStatus.UNKNOWN


def test_schema_breakdown() -> None:
    """Inventory should be grouped by schema."""
    analysis = analyse_object_quota(
        build_inventory(5),
        ObjectQuotaConfig(limit_override=100),
    )

    breakdown = {
        item.name: item.count
        for item in analysis.by_schema
    }

    assert breakdown["sales"] == 3
    assert breakdown["finance"] == 2
