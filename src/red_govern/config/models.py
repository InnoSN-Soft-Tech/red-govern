"""Typed configuration models for Red-Govern."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    """Base model that rejects unknown configuration fields."""

    model_config = ConfigDict(
        extra="forbid",
        populate_by_name=True,
    )


class ConnectionConfig(StrictModel):
    """Direct Redshift connection settings."""

    host: str | None = None
    port: int = Field(default=5439, ge=1, le=65535)
    database: str = "dev"
    user: str | None = None
    connect_timeout_seconds: int = Field(default=15, ge=1, le=300)
    statement_timeout_seconds: int = Field(default=60, ge=1, le=3600)
    tcp_keepalive: bool = True

class AuthenticationConfig(StrictModel):
    """Authentication settings."""

    method: Literal[
        "auto",
        "password",
        "iam",
        "profile",
        "data_api",
    ] = "auto"

    password_env: str = "RED_GOVERN_REDSHIFT_PASSWORD"
    aws_profile: str | None = None
    cluster_identifier: str | None = None
    workgroup_name: str | None = None
    region: str | None = None
    db_user: str | None = None

    @model_validator(mode="after")
    def validate_authentication_fields(self) -> AuthenticationConfig:
        """Validate authentication-specific configuration."""
        if self.method == "profile" and not self.aws_profile:
            raise ValueError(
                "aws_profile is required when authentication.method is profile"
            )

        if (
            self.method in {"iam", "profile"}
            and not self.cluster_identifier
            and not self.workgroup_name
        ):
            raise ValueError(
                "cluster_identifier or workgroup_name is required "
                "for IAM/profile authentication"
            )

        return self

class CompatibilityConfig(StrictModel):
    """Redshift compatibility-resolution settings."""

    mode: Literal["auto", "manual"] = "auto"
    deployment_type: Literal["auto", "provisioned", "serverless"] = "auto"
    version_override: str | None = None
    prefer_sys_views: bool = True
    allow_legacy_fallbacks: bool = True


class SSLConfig(StrictModel):
    """TLS settings."""

    enabled: bool = True
    mode: Literal["verify-full", "verify-ca", "require"] = "verify-full"


class RedshiftConfig(StrictModel):
    """Redshift connection and environment configuration."""

    profile_name: str = "default"
    connection: ConnectionConfig = Field(default_factory=ConnectionConfig)
    authentication: AuthenticationConfig = Field(default_factory=AuthenticationConfig)
    compatibility: CompatibilityConfig = Field(default_factory=CompatibilityConfig)
    ssl: SSLConfig = Field(default_factory=SSLConfig)



class ObjectQuotaConfig(StrictModel):
    """Object-quota thresholds and optional capacity override."""

    enabled: bool = True
    limit_override: int | None = Field(default=None, ge=1)
    warning_threshold: float = Field(default=0.80, ge=0, le=1)
    critical_threshold: float = Field(default=0.90, ge=0, le=1)

    @model_validator(mode="after")
    def validate_threshold_order(self) -> ObjectQuotaConfig:
        """Ensure critical threshold is greater than warning threshold."""
        if self.critical_threshold <= self.warning_threshold:
            raise ValueError(
                "critical_threshold must be greater than warning_threshold"
            )

        return self

class LifecycleConfig(StrictModel):
    """Object-lifecycle settings."""

    enabled: bool = True
    detect_recreation: bool = True


class QueryMonitoringConfig(StrictModel):
    """Query-monitoring settings."""

    enabled: bool = False
    capture_query_text: bool = False
    redact_literals: bool = True


class GovernanceConfig(StrictModel):
    """Governance feature settings."""

    object_quota: ObjectQuotaConfig = Field(default_factory=ObjectQuotaConfig)
    lifecycle: LifecycleConfig = Field(default_factory=LifecycleConfig)
    query_monitoring: QueryMonitoringConfig = Field(default_factory=QueryMonitoringConfig)


class OperationalRegistryConfig(StrictModel):
    """Operational-table registry settings."""

    source: Literal["excel", "csv", "sqlite", "redshift"] = "excel"
    path: Path = Path("./operational_tables.xlsx")


class ClassificationConfig(StrictModel):
    """Classification settings."""

    enabled: bool = True
    rules_file: Path = Path("./classification.yml")
    operational_registry: OperationalRegistryConfig = Field(
        default_factory=OperationalRegistryConfig
    )


class HistoryConfig(StrictModel):
    """Local history settings."""

    enabled: bool = True
    backend: Literal["sqlite"] = "sqlite"
    path: Path = Path("~/.red-govern/state/governance.db")
    retention_days: int = Field(default=730, ge=1)


class CLIOutputConfig(StrictModel):
    """CLI output settings."""

    enabled: bool = True


class FileOutputConfig(StrictModel):
    """File output settings."""

    enabled: bool = False
    path: Path


class OutputsConfig(StrictModel):
    """Output-adapter settings."""

    cli: CLIOutputConfig = Field(default_factory=CLIOutputConfig)

    json_output: FileOutputConfig = Field(
        default_factory=lambda: FileOutputConfig(path=Path("./reports/red-govern.json")),
        alias="json",
        serialization_alias="json",
    )

    excel: FileOutputConfig = Field(
        default_factory=lambda: FileOutputConfig(path=Path("./reports/red-govern.xlsx"))
    )


class PrivacyConfig(StrictModel):
    """Privacy defaults."""

    telemetry: bool = False
    capture_query_text: bool = False
    redact_literals: bool = True
    external_services: bool = False


class ActionsConfig(StrictModel):
    """Operational-action safeguards."""

    read_only: bool = True
    allow_query_cancellation: bool = False
    allow_database_writes: bool = False


class RedGovernConfig(StrictModel):
    """Root Red-Govern configuration."""

    config_version: int = Field(default=1, ge=1)
    redshift: RedshiftConfig = Field(default_factory=RedshiftConfig)
    governance: GovernanceConfig = Field(default_factory=GovernanceConfig)
    classification: ClassificationConfig = Field(default_factory=ClassificationConfig)
    history: HistoryConfig = Field(default_factory=HistoryConfig)
    outputs: OutputsConfig = Field(default_factory=OutputsConfig)
    privacy: PrivacyConfig = Field(default_factory=PrivacyConfig)
    actions: ActionsConfig = Field(default_factory=ActionsConfig)
