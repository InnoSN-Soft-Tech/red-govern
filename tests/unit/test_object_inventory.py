"""Tests for normalised object-inventory collection."""


from datetime import datetime, timezone

import pytest

from red_govern.capabilities import ViewFamily
from red_govern.collectors.objects import (
    DatabaseObjectType,
    _normalise_row,
    normalise_object_type,
)
from red_govern.exceptions import RedshiftQueryError
from red_govern.query_registry import (
    QueryDefinition,
    QueryPurpose,
    QueryResolution,
)


def build_resolution() -> QueryResolution:
    """Build a synthetic inventory resolution."""
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


@pytest.mark.parametrize(
    ("source", "expected"),
    [
        ("BASE TABLE", DatabaseObjectType.TABLE),
        ("TABLE", DatabaseObjectType.TABLE),
        ("VIEW", DatabaseObjectType.VIEW),
        (
            "MATERIALIZED VIEW",
            DatabaseObjectType.MATERIALIZED_VIEW,
        ),
        ("EXTERNAL TABLE", DatabaseObjectType.EXTERNAL_TABLE),
        ("something_else", DatabaseObjectType.UNKNOWN),
    ],
)
def test_object_type_normalisation(
    source: str,
    expected: DatabaseObjectType,
) -> None:
    """Source-specific object labels should become stable values."""
    assert normalise_object_type(source) == expected


def test_svv_row_is_normalised() -> None:
    """SVV-style rows should map to the inventory contract."""
    timestamp = datetime.now(timezone.utc)

    record = _normalise_row(
        {
            "table_database": "analytics",
            "table_schema": "sales",
            "table_name": "daily_orders",
            "table_type": "TABLE",
        },
        build_resolution(),
        timestamp,
    )

    assert record.database_name == "analytics"
    assert record.schema_name == "sales"
    assert record.object_name == "daily_orders"
    assert record.object_type == DatabaseObjectType.TABLE
    assert record.source_family == ViewFamily.SVV


def test_information_schema_row_is_normalised() -> None:
    """Information-schema rows should map to the same contract."""
    timestamp = datetime.now(timezone.utc)

    record = _normalise_row(
        {
            "table_catalog": "analytics",
            "table_schema": "finance",
            "table_name": "monthly_summary",
            "table_type": "VIEW",
        },
        build_resolution(),
        timestamp,
    )

    assert record.database_name == "analytics"
    assert record.schema_name == "finance"
    assert record.object_name == "monthly_summary"
    assert record.object_type == DatabaseObjectType.VIEW


def test_missing_identity_columns_are_rejected() -> None:
    """Rows missing required object identity must be rejected."""
    with pytest.raises(RedshiftQueryError):
        _normalise_row(
            {
                "table_schema": "finance",
                "table_name": "monthly_summary",
            },
            build_resolution(),
            datetime.now(timezone.utc),
        )
