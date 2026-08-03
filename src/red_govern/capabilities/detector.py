"""Capability detection for Amazon Redshift environments."""

from __future__ import annotations

from contextlib import suppress
from dataclasses import dataclass
from typing import Any

from red_govern.capabilities.system_views import (
    KNOWN_SYSTEM_RELATIONS,
    DeploymentType,
    SystemViewCapability,
    ViewFamily,
)
from red_govern.config.models import RedshiftConfig
from red_govern.connections.connection import redshift_connection
from red_govern.exceptions import CapabilityDetectionError
from red_govern.security.redaction import redact_text


@dataclass(frozen=True, slots=True)
class CapabilityReport:
    """Detected Redshift environment capabilities."""

    deployment_type: DeploymentType
    server_version: str
    views: tuple[SystemViewCapability, ...]

    def relation_available(self, relation: str) -> bool:
        """Return whether a relation exists and is accessible."""
        normalised = relation.lower()

        return any(
            view.relation.lower() == normalised and view.available and view.accessible
            for view in self.views
        )

    def family_available(self, family: ViewFamily) -> bool:
        """Return whether an accessible relation exists in a family."""
        return any(
            view.family == family and view.available and view.accessible for view in self.views
        )


VERSION_SQL = """
SELECT version()
"""


_MISSING_RELATION_MARKERS = (
    "does not exist",
    "relation does not exist",
    "relation not found",
    "table does not exist",
    "undefined table",
)


_SERVERLESS_ONLY_RELATIONS = frozenset(
    {
        "pg_catalog.sys_serverless_usage",
    }
)


_PROVISIONED_ONLY_RELATIONS = frozenset(
    {
        "pg_catalog.stv_recents",
        "pg_catalog.svl_query_metrics_summary",
        "pg_catalog.stv_query_metrics",
        "pg_catalog.stl_query",
        "pg_catalog.stv_inflight",
        "pg_catalog.svl_qlog",
    }
)


def _relations_for_deployment(
    deployment_type: DeploymentType | None,
) -> tuple[tuple[str, ViewFamily], ...]:
    """Return relations applicable to the configured deployment."""
    if deployment_type is DeploymentType.SERVERLESS:
        return tuple(
            item for item in KNOWN_SYSTEM_RELATIONS if item[0] not in _PROVISIONED_ONLY_RELATIONS
        )

    if deployment_type is DeploymentType.PROVISIONED:
        return tuple(
            item for item in KNOWN_SYSTEM_RELATIONS if item[0] not in _SERVERLESS_ONLY_RELATIONS
        )

    return KNOWN_SYSTEM_RELATIONS


def _safe_rollback(connection: Any) -> None:
    """Rollback a failed capability probe without masking its error."""
    with suppress(Exception):
        connection.rollback()


def _probe_relation(
    connection: Any,
    relation: str,
    family: ViewFamily,
) -> SystemViewCapability:
    """Probe a fixed known relation using a harmless zero-row read.

    Amazon Redshift does not reliably expose all system relations through
    PostgreSQL relation-registry helpers such as to_regclass(). Directly
    compiling a SELECT is therefore the most reliable existence and access
    test.

    Relation names come only from KNOWN_SYSTEM_RELATIONS and are not
    user-controlled.
    """
    cursor = connection.cursor()

    try:
        cursor.execute(f"SELECT 1 FROM {relation} LIMIT 0")
    except Exception as exc:
        _safe_rollback(connection)

        redacted_error = redact_text(str(exc))
        normalised_error = redacted_error.lower()

        missing = any(marker in normalised_error for marker in _MISSING_RELATION_MARKERS)

        return SystemViewCapability(
            relation=relation,
            family=family,
            available=not missing,
            accessible=False,
            error=redacted_error,
        )
    finally:
        cursor.close()

    return SystemViewCapability(
        relation=relation,
        family=family,
        available=True,
        accessible=True,
    )


def _configured_deployment_type(
    config: RedshiftConfig,
) -> DeploymentType | None:
    """Return an explicit configured deployment type when present."""
    configured = config.compatibility.deployment_type
    value = getattr(configured, "value", configured)
    normalised = str(value).lower()

    if normalised == DeploymentType.SERVERLESS.value:
        return DeploymentType.SERVERLESS

    if normalised == DeploymentType.PROVISIONED.value:
        return DeploymentType.PROVISIONED

    return None


def _infer_deployment_type(
    views: tuple[SystemViewCapability, ...],
) -> DeploymentType:
    """Infer deployment type from environment-specific relations."""
    serverless_usage = next(
        (view for view in views if view.relation == "pg_catalog.sys_serverless_usage"),
        None,
    )

    if serverless_usage is not None and serverless_usage.available and serverless_usage.accessible:
        return DeploymentType.SERVERLESS

    provisioned_relations = {
        "pg_catalog.stl_query",
        "pg_catalog.stv_inflight",
        "pg_catalog.svl_qlog",
    }

    if any(
        view.relation in provisioned_relations and view.available and view.accessible
        for view in views
    ):
        return DeploymentType.PROVISIONED

    return DeploymentType.UNKNOWN


def detect_capabilities(
    config: RedshiftConfig,
) -> CapabilityReport:
    """Detect available Redshift system views and deployment indicators."""
    configured_deployment_type = _configured_deployment_type(config)

    try:
        with redshift_connection(config) as connection:
            version_cursor = connection.cursor()

            try:
                version_cursor.execute(VERSION_SQL)
                row = version_cursor.fetchone()
                server_version = str(row[0]) if row else "unknown"
            finally:
                version_cursor.close()

            views = tuple(
                _probe_relation(
                    connection,
                    relation,
                    family,
                )
                for relation, family in _relations_for_deployment(configured_deployment_type)
            )
    except Exception as exc:
        if isinstance(exc, CapabilityDetectionError):
            raise

        raise CapabilityDetectionError(
            f"Unable to detect Redshift capabilities: {redact_text(str(exc))}"
        ) from exc

    deployment_type = configured_deployment_type or _infer_deployment_type(views)

    return CapabilityReport(
        deployment_type=deployment_type,
        server_version=server_version,
        views=views,
    )
