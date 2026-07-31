"""Tests for Red-Govern inventory snapshots."""

from datetime import datetime, timezone
from pathlib import Path

from red_govern.capabilities import ViewFamily
from red_govern.collectors import (
    DatabaseObjectType,
    ObjectInventoryRecord,
    ObjectInventoryResult,
)
from red_govern.history import (
    detect_inventory_changes,
    save_inventory_snapshot,
)
from red_govern.query_registry import (
    QueryDefinition,
    QueryPurpose,
    QueryResolution,
)


def build_resolution() -> QueryResolution:
    """Build a synthetic inventory query resolution."""
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


def build_inventory(
    names: tuple[str, ...],
) -> ObjectInventoryResult:
    """Build an inventory from synthetic object names."""
    collected_at = datetime.now(timezone.utc)

    records = tuple(
        ObjectInventoryRecord(
            database_name="analytics",
            schema_name="sales",
            object_name=name,
            object_type=DatabaseObjectType.TABLE,
            source_family=ViewFamily.SVV,
            source_query_id="object_inventory_svv_v1",
            collected_at=collected_at,
        )
        for name in names
    )

    return ObjectInventoryResult(
        records=records,
        resolution=build_resolution(),
        collected_at=collected_at,
    )


def test_first_snapshot_marks_all_objects_as_added(
    tmp_path: Path,
) -> None:
    """Without a prior snapshot, all objects should be new."""
    path = tmp_path / "governance.db"

    save_inventory_snapshot(
        path,
        build_inventory(("orders", "customers")),
    )

    changes = detect_inventory_changes(path)

    assert changes.previous_run_id is None
    assert changes.added_count == 2
    assert changes.removed_count == 0


def test_changes_between_two_snapshots(
    tmp_path: Path,
) -> None:
    """Added and removed objects should be detected."""
    path = tmp_path / "governance.db"

    first = save_inventory_snapshot(
        path,
        build_inventory(("orders", "customers")),
    )

    second = save_inventory_snapshot(
        path,
        build_inventory(("orders", "payments")),
    )

    changes = detect_inventory_changes(path)

    assert changes.current_run_id == second.run_id
    assert changes.previous_run_id == first.run_id

    assert {
        record.object_name
        for record in changes.added
    } == {"payments"}

    assert {
        record.object_name
        for record in changes.removed
    } == {"customers"}


def test_snapshot_records_total_objects(
    tmp_path: Path,
) -> None:
    """Snapshot metadata should include inventory size."""
    path = tmp_path / "governance.db"

    result = save_inventory_snapshot(
        path,
        build_inventory(("orders", "customers", "payments")),
    )

    assert result.total_objects == 3
    assert result.run_id == 1
