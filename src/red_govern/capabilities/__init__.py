"""Red-Govern capability-detection package."""

from red_govern.capabilities.detector import (
    CapabilityReport,
    detect_capabilities,
)
from red_govern.capabilities.permissions import (
    PermissionSummary,
    summarise_permissions,
)
from red_govern.capabilities.system_views import (
    DeploymentType,
    SystemViewCapability,
    ViewFamily,
)

__all__ = [
    "CapabilityReport",
    "DeploymentType",
    "PermissionSummary",
    "SystemViewCapability",
    "ViewFamily",
    "detect_capabilities",
    "summarise_permissions",
]
