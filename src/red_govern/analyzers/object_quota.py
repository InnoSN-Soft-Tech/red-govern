"""Object-quota and capacity analysis for Red-Govern."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass
from enum import Enum

from red_govern.collectors import ObjectInventoryResult
from red_govern.config.models import ObjectQuotaConfig


class QuotaStatus(str, Enum):
    """Normalised object-quota health states."""

    UNKNOWN = "unknown"
    HEALTHY = "healthy"
    WARNING = "warning"
    CRITICAL = "critical"
    EXCEEDED = "exceeded"


@dataclass(frozen=True, slots=True)
class QuotaBreakdown:
    """Object counts grouped by one dimension."""

    name: str
    count: int
    percentage_of_inventory: float


@dataclass(frozen=True, slots=True)
class ObjectQuotaAnalysis:
    """Object-capacity analysis for one inventory collection."""

    current_objects: int
    quota_limit: int | None
    remaining_capacity: int | None
    utilisation_ratio: float | None
    utilisation_percentage: float | None
    status: QuotaStatus
    warning_threshold: float
    critical_threshold: float
    by_schema: tuple[QuotaBreakdown, ...]
    by_object_type: tuple[QuotaBreakdown, ...]

    @property
    def quota_known(self) -> bool:
        """Return whether an applicable quota was provided."""
        return self.quota_limit is not None


def _create_breakdowns(
    counts: Counter[str],
    total: int,
) -> tuple[QuotaBreakdown, ...]:
    """Convert grouped counts into sorted quota breakdowns."""
    return tuple(
        QuotaBreakdown(
            name=name,
            count=count,
            percentage_of_inventory=(
                round((count / total) * 100, 2)
                if total > 0
                else 0.0
            ),
        )
        for name, count in sorted(
            counts.items(),
            key=lambda item: (-item[1], item[0]),
        )
    )


def determine_quota_status(
    utilisation_ratio: float | None,
    config: ObjectQuotaConfig,
) -> QuotaStatus:
    """Determine quota health from utilisation and configured thresholds."""
    if utilisation_ratio is None:
        return QuotaStatus.UNKNOWN

    if utilisation_ratio > 1:
        return QuotaStatus.EXCEEDED

    if utilisation_ratio >= config.critical_threshold:
        return QuotaStatus.CRITICAL

    if utilisation_ratio >= config.warning_threshold:
        return QuotaStatus.WARNING

    return QuotaStatus.HEALTHY


def analyse_object_quota(
    inventory: ObjectInventoryResult,
    config: ObjectQuotaConfig,
) -> ObjectQuotaAnalysis:
    """Analyse object utilisation against an optional configured quota."""
    current_objects = inventory.total_objects
    quota_limit = config.limit_override

    schema_counts = Counter(
        record.schema_name
        for record in inventory.records
    )

    object_type_counts = Counter(
        record.object_type.value
        for record in inventory.records
    )

    if quota_limit is None:
        remaining_capacity = None
        utilisation_ratio = None
        utilisation_percentage = None
    else:
        remaining_capacity = quota_limit - current_objects
        utilisation_ratio = current_objects / quota_limit
        utilisation_percentage = round(utilisation_ratio * 100, 2)

    return ObjectQuotaAnalysis(
        current_objects=current_objects,
        quota_limit=quota_limit,
        remaining_capacity=remaining_capacity,
        utilisation_ratio=utilisation_ratio,
        utilisation_percentage=utilisation_percentage,
        status=determine_quota_status(
            utilisation_ratio,
            config,
        ),
        warning_threshold=config.warning_threshold,
        critical_threshold=config.critical_threshold,
        by_schema=_create_breakdowns(
            schema_counts,
            current_objects,
        ),
        by_object_type=_create_breakdowns(
            object_type_counts,
            current_objects,
        ),
    )
