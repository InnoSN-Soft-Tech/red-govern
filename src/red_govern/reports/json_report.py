"""Local JSON governance reporting for Red-Govern."""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from red_govern import __version__
from red_govern.analyzers import ObjectQuotaAnalysis
from red_govern.capabilities import CapabilityReport
from red_govern.classification import ClassificationResult
from red_govern.collectors import ObjectInventoryResult
from red_govern.exceptions import ReportError


def _classification_lookup(
    classification: ClassificationResult | None,
) -> dict[tuple[str, str, str, str], dict[str, Any]]:
    """Build an object-identity lookup for classification results."""
    if classification is None:
        return {}

    lookup: dict[tuple[str, str, str, str], dict[str, Any]] = {}

    for item in classification.objects:
        identity = (
            item.record.database_name,
            item.record.schema_name,
            item.record.object_name,
            item.record.object_type.value,
        )

        lookup[identity] = {
            "unclassified": item.unclassified,
            "has_conflict": item.has_conflict,
            "dimensions": [
                {
                    "dimension": dimension.dimension,
                    "label": dimension.label,
                    "matched_rule": dimension.matched_rule,
                    "priority": dimension.priority,
                    "conflict": dimension.conflict,
                    "competing_rules": list(
                        dimension.competing_rules
                    ),
                }
                for dimension in item.dimensions
            ],
        }

    return lookup


def build_json_report(
    *,
    capabilities: CapabilityReport,
    inventory: ObjectInventoryResult,
    quota: ObjectQuotaAnalysis,
    classification: ClassificationResult | None = None,
) -> dict[str, Any]:
    """Build a JSON-serialisable governance report."""
    generated_at = datetime.now(timezone.utc)
    classification_lookup = _classification_lookup(classification)

    objects: list[dict[str, Any]] = []

    for record in inventory.records:
        identity = (
            record.database_name,
            record.schema_name,
            record.object_name,
            record.object_type.value,
        )

        objects.append(
            {
                "database_name": record.database_name,
                "schema_name": record.schema_name,
                "object_name": record.object_name,
                "object_type": record.object_type.value,
                "owner_name": record.owner_name,
                "size_mb": record.size_mb,
                "distribution_style": record.distribution_style,
                "sort_key": record.sort_key,
                "source_family": record.source_family.value,
                "source_query_id": record.source_query_id,
                "collected_at": record.collected_at.isoformat(),
                "classification": classification_lookup.get(identity),
            }
        )

    return {
        "report_schema": "red_govern_json_v1",
        "generated_at": generated_at.isoformat(),
        "generator": {
            "name": "Red-Govern",
            "version": __version__,
            "developer": "InnoSN Soft Tech",
            "local_first": True,
            "telemetry": False,
        },
        "environment": {
            "deployment_type": capabilities.deployment_type.value,
            "server_version": capabilities.server_version,
            "capabilities": [
                {
                    "relation": view.relation,
                    "family": view.family.value,
                    "available": view.available,
                    "accessible": view.accessible,
                    "error": view.error,
                }
                for view in capabilities.views
            ],
        },
        "inventory": {
            "total_objects": inventory.total_objects,
            "collected_at": inventory.collected_at.isoformat(),
            "query_id": inventory.resolution.query.query_id,
            "query_version": (
                inventory.resolution.query.query_version
            ),
            "result_schema": (
                inventory.resolution.query.result_schema
            ),
            "source_family": (
                inventory.resolution.selected_family.value
            ),
            "fallback_used": inventory.resolution.used_fallback,
            "resolution_reason": inventory.resolution.reason,
            "objects": objects,
        },
        "quota": {
            "quota_known": quota.quota_known,
            "quota_limit": quota.quota_limit,
            "current_objects": quota.current_objects,
            "remaining_capacity": quota.remaining_capacity,
            "utilisation_ratio": quota.utilisation_ratio,
            "utilisation_percentage": (
                quota.utilisation_percentage
            ),
            "status": quota.status.value,
            "warning_threshold": quota.warning_threshold,
            "critical_threshold": quota.critical_threshold,
            "by_schema": [
                {
                    "name": item.name,
                    "count": item.count,
                    "percentage_of_inventory": (
                        item.percentage_of_inventory
                    ),
                }
                for item in quota.by_schema
            ],
            "by_object_type": [
                {
                    "name": item.name,
                    "count": item.count,
                    "percentage_of_inventory": (
                        item.percentage_of_inventory
                    ),
                }
                for item in quota.by_object_type
            ],
        },
        "classification": (
            {
                "enabled": True,
                "classified_objects": (
                    classification.classified_count
                ),
                "unclassified_objects": (
                    classification.unclassified_count
                ),
                "conflicting_objects": (
                    classification.conflict_count
                ),
            }
            if classification is not None
            else {
                "enabled": False,
            }
        ),
        "privacy": {
            "credentials_included": False,
            "query_text_included": False,
            "customer_rows_scanned": False,
            "external_transmission": False,
        },
    }


def write_json_report(
    report: dict[str, Any],
    destination: Path,
    *,
    overwrite: bool = False,
) -> Path:
    """Write a governance report to a local JSON file."""
    output_path = destination.expanduser().resolve()

    if output_path.exists() and not overwrite:
        raise ReportError(
            f"Report already exists: {output_path}. "
            "Use --force to replace it."
        )

    try:
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(
            json.dumps(
                report,
                indent=2,
                sort_keys=False,
                ensure_ascii=False,
            )
            + "\n",
            encoding="utf-8",
        )
    except OSError as exc:
        raise ReportError(
            f"Unable to write JSON report: {output_path}"
        ) from exc

    return output_path
