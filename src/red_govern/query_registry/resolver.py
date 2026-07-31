"""Capability-aware query resolution for Red-Govern."""

from __future__ import annotations

from dataclasses import dataclass

from red_govern.capabilities import CapabilityReport, DeploymentType, ViewFamily
from red_govern.config.models import CompatibilityConfig
from red_govern.exceptions import QueryResolutionError
from red_govern.query_registry.registry import (
    QueryDefinition,
    QueryPurpose,
    QueryRegistry,
)


@dataclass(frozen=True, slots=True)
class QueryResolution:
    """Resolved query and the reasoning behind its selection."""

    query: QueryDefinition
    selected_family: ViewFamily
    used_fallback: bool
    reason: str


def _deployment_matches(
    query: QueryDefinition,
    deployment_type: DeploymentType,
) -> bool:
    """Return whether a query supports the detected deployment."""
    if deployment_type == DeploymentType.UNKNOWN:
        return True

    return deployment_type in query.deployment_types


def _relations_available(
    query: QueryDefinition,
    report: CapabilityReport,
) -> bool:
    """Return whether all required relations are accessible."""
    return all(
        report.relation_available(relation)
        for relation in query.required_relations
    )


def resolve_query(
    registry: QueryRegistry,
    purpose: QueryPurpose,
    report: CapabilityReport,
    compatibility: CompatibilityConfig,
) -> QueryResolution:
    """Resolve the highest-priority compatible query."""
    candidates = registry.for_purpose(purpose)

    if not candidates:
        raise QueryResolutionError(
            f"No query definitions are registered for: {purpose.value}"
        )

    compatible = tuple(
        query
        for query in candidates
        if _deployment_matches(query, report.deployment_type)
        and _relations_available(query, report)
    )

    if not compatible:
        missing_details = ", ".join(
            sorted(
                {
                    relation
                    for query in candidates
                    for relation in query.required_relations
                    if not report.relation_available(relation)
                }
            )
        )

        raise QueryResolutionError(
            f"No compatible query is available for {purpose.value}. "
            f"Unavailable relations: {missing_details or 'unknown'}"
        )

    preferred_family = (
        ViewFamily.SYS
        if compatibility.prefer_sys_views
        else compatible[0].family
    )

    preferred = tuple(
        query
        for query in compatible
        if query.family == preferred_family
    )

    if preferred:
        selected = preferred[0]

        return QueryResolution(
            query=selected,
            selected_family=selected.family,
            used_fallback=False,
            reason=(
                f"Selected preferred {selected.family.value} query "
                f"{selected.query_id}."
            ),
        )

    if (
        preferred_family == ViewFamily.SYS
        and not compatibility.allow_legacy_fallbacks
    ):
        raise QueryResolutionError(
            f"The preferred SYS query family is unavailable for "
            f"{purpose.value}, and fallbacks are disabled."
        )

    selected = compatible[0]

    return QueryResolution(
        query=selected,
        selected_family=selected.family,
        used_fallback=True,
        reason=(
            f"Preferred query family was unavailable; selected "
            f"{selected.family.value} fallback {selected.query_id}."
        ),
    )
