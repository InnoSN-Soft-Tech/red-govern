"""Red-Govern exception hierarchy."""

from __future__ import annotations


class RedGovernError(Exception):
    """Base exception for Red-Govern."""


class ConfigurationError(RedGovernError):
    """Raised when configuration loading or validation fails."""


class AuthenticationError(RedGovernError):
    """Raised when authentication settings cannot be resolved."""


class RedshiftConnectionError(RedGovernError):
    """Raised when a Redshift connection cannot be established."""


class RedshiftQueryError(RedGovernError):
    """Raised when a Redshift metadata query fails."""


class CapabilityDetectionError(RedGovernError):
    """Raised when Redshift capabilities cannot be determined."""


class UnsupportedCapabilityError(RedGovernError):
    """Raised when the environment cannot provide a requested capability."""


class QueryRegistryError(RedGovernError):
    """Raised when a query definition or registry is invalid."""


class QueryResolutionError(RedGovernError):
    """Raised when no compatible query can be selected."""


class HistoryError(RedGovernError):
    """Raised when local governance history operations fail."""


class ClassificationError(RedGovernError):
    """Raised when classification configuration or execution fails."""


class ClassificationConflictError(ClassificationError):
    """Raised when classification rules produce an unresolved conflict."""


class ReportError(RedGovernError):
    """Raised when governance report generation fails."""