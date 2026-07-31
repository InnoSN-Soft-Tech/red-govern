"""Permission summaries derived from capability probes."""

from __future__ import annotations

from dataclasses import dataclass

from red_govern.capabilities.detector import CapabilityReport


@dataclass(frozen=True, slots=True)
class PermissionSummary:
    """High-level metadata permission summary."""

    accessible_relations: int
    inaccessible_relations: int
    missing_relations: int


def summarise_permissions(
    report: CapabilityReport,
) -> PermissionSummary:
    """Summarise relation access from a capability report."""
    accessible = sum(
        1
        for view in report.views
        if view.available and view.accessible
    )

    inaccessible = sum(
        1
        for view in report.views
        if view.available and not view.accessible
    )

    missing = sum(
        1
        for view in report.views
        if not view.available
    )

    return PermissionSummary(
        accessible_relations=accessible,
        inaccessible_relations=inaccessible,
        missing_relations=missing,
    )
