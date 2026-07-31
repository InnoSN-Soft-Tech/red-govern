"""Capability detection for Amazon Redshift environments."""

from __future__ import annotations

from dataclasses import dataclass

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
            view.relation.lower() == normalised
            and view.available
            and view.accessible
            for view in self.views
        )

    def family_available(self, family: ViewFamily) -> bool:
        """Return whether an accessible relation exists in a family."""
        return any(
            view.family == family
            and view.available
            and view.accessible
            for view in self.views
        )


RELATION_PROBE_SQL = """
SELECT
    to_regclass(%s) IS NOT NULL AS relation_exists
"""


VERSION_SQL = """
SELECT version()
"""


def _probe_relation(cursor: object, relation: str) -> SystemViewCapability:
    """Probe whether a known relation exists and can be read."""
    family = next(
        known_family
        for known_relation, known_family in KNOWN_SYSTEM_RELATIONS
        if known_relation == relation
    )

    try:
        cursor.execute(RELATION_PROBE_SQL, (relation,))  # type: ignore[attr-defined]
        row = cursor.fetchone()  # type: ignore[attr-defined]
        available = bool(row and row[0])
    except Exception as exc:
        return SystemViewCapability(
            relation=relation,
            family=family,
            available=False,
            accessible=False,
            error=redact_text(str(exc)),
        )

    if not available:
        return SystemViewCapability(
            relation=relation,
            family=family,
            available=False,
            accessible=False,
        )

    try:
        cursor.execute(  # type: ignore[attr-defined]
            f"SELECT 1 FROM {relation} LIMIT 1"
        )
        cursor.fetchone()  # type: ignore[attr-defined]
    except Exception as exc:
        return SystemViewCapability(
            relation=relation,
            family=family,
            available=True,
            accessible=False,
            error=redact_text(str(exc)),
        )

    return SystemViewCapability(
        relation=relation,
        family=family,
        available=True,
        accessible=True,
    )


def _infer_deployment_type(
    views: tuple[SystemViewCapability, ...],
) -> DeploymentType:
    """Infer deployment type from environment-specific relations."""
    serverless_usage = next(
        (
            view
            for view in views
            if view.relation == "pg_catalog.sys_serverless_usage"
        ),
        None,
    )

    if (
        serverless_usage is not None
        and serverless_usage.available
        and serverless_usage.accessible
    ):
        return DeploymentType.SERVERLESS

    provisioned_relations = {
        "pg_catalog.stl_query",
        "pg_catalog.stv_inflight",
        "pg_catalog.svl_qlog",
    }

    if any(
        view.relation in provisioned_relations
        and view.available
        and view.accessible
        for view in views
    ):
        return DeploymentType.PROVISIONED

    return DeploymentType.UNKNOWN


def detect_capabilities(
    config: RedshiftConfig,
) -> CapabilityReport:
    """Detect available Redshift system views and deployment indicators."""
    try:
        with redshift_connection(config) as connection:
            cursor = connection.cursor()

            try:
                cursor.execute(VERSION_SQL)
                row = cursor.fetchone()
                server_version = str(row[0]) if row else "unknown"

                views = tuple(
                    _probe_relation(cursor, relation)
                    for relation, _family in KNOWN_SYSTEM_RELATIONS
                )
            finally:
                cursor.close()
    except Exception as exc:
        if isinstance(exc, CapabilityDetectionError):
            raise

        raise CapabilityDetectionError(
            "Unable to detect Redshift capabilities: "
            f"{redact_text(str(exc))}"
        ) from exc

    deployment_type = _infer_deployment_type(views)

    return CapabilityReport(
        deployment_type=deployment_type,
        server_version=server_version,
        views=views,
    )
