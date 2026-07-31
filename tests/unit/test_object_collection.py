"""Tests for object-inventory query execution."""

from unittest.mock import MagicMock, patch

from red_govern.capabilities import (
    CapabilityReport,
    DeploymentType,
    SystemViewCapability,
    ViewFamily,
)
from red_govern.collectors import (
    DatabaseObjectType,
    collect_object_inventory,
)
from red_govern.config.models import RedshiftConfig


def build_capability_report() -> CapabilityReport:
    """Build a report supporting the SVV inventory query."""
    return CapabilityReport(
        deployment_type=DeploymentType.PROVISIONED,
        server_version="Redshift test",
        views=(
            SystemViewCapability(
                relation="pg_catalog.svv_tables",
                family=ViewFamily.SVV,
                available=True,
                accessible=True,
            ),
        ),
    )


@patch("red_govern.collectors.objects.redshift_connection")
def test_inventory_collection(
    connection_context_mock: MagicMock,
) -> None:
    """Collected rows should be normalised into inventory records."""
    cursor = MagicMock()
    cursor.description = (
        ("table_database",),
        ("table_schema",),
        ("table_name",),
        ("table_type",),
    )
    cursor.fetchall.return_value = [
        (
            "analytics",
            "sales",
            "daily_orders",
            "TABLE",
        ),
    ]

    connection = MagicMock()
    connection.cursor.return_value = cursor

    connection_context_mock.return_value.__enter__.return_value = (
        connection
    )

    config = RedshiftConfig.model_validate(
        {
            "connection": {
                "host": "example.redshift.amazonaws.com",
            },
        }
    )

    result = collect_object_inventory(
        config,
        build_capability_report(),
    )

    assert result.total_objects == 1
    assert result.records[0].object_name == "daily_orders"
    assert (
        result.records[0].object_type
        == DatabaseObjectType.TABLE
    )

    cursor.execute.assert_called_once()
    cursor.close.assert_called_once()
