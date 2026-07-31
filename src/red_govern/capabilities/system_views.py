"""Known Amazon Redshift system-view capabilities."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class DeploymentType(str, Enum):
    """Supported Amazon Redshift deployment categories."""

    PROVISIONED = "provisioned"
    SERVERLESS = "serverless"
    UNKNOWN = "unknown"


class ViewFamily(str, Enum):
    """Amazon Redshift system-view families."""

    SYS = "sys"
    SVV = "svv"
    STL = "stl"
    STV = "stv"
    SVL = "svl"
    PG_CATALOG = "pg_catalog"
    INFORMATION_SCHEMA = "information_schema"


@dataclass(frozen=True, slots=True)
class SystemViewCapability:
    """Availability of one system relation."""

    relation: str
    family: ViewFamily
    available: bool
    accessible: bool
    error: str | None = None


KNOWN_SYSTEM_RELATIONS: tuple[tuple[str, ViewFamily], ...] = (
    ("pg_catalog.svv_tables", ViewFamily.SVV),
    ("pg_catalog.stv_recents", ViewFamily.STV),
    ("pg_catalog.svv_table_info", ViewFamily.SVV),
    ("pg_catalog.svv_redshift_databases", ViewFamily.SVV),
    ("pg_catalog.sys_query_history", ViewFamily.SYS),
    ("pg_catalog.sys_query_detail", ViewFamily.SYS),
    ("pg_catalog.svl_query_metrics_summary", ViewFamily.SVL),
    ("pg_catalog.stv_query_metrics", ViewFamily.STV),
    ("pg_catalog.sys_connection_log", ViewFamily.SYS),
    ("pg_catalog.sys_session_history", ViewFamily.SYS),
    ("pg_catalog.sys_serverless_usage", ViewFamily.SYS),
    ("pg_catalog.stl_query", ViewFamily.STL),
    ("pg_catalog.stv_inflight", ViewFamily.STV),
    ("pg_catalog.svl_qlog", ViewFamily.SVL),
    ("information_schema.tables", ViewFamily.INFORMATION_SCHEMA),
)