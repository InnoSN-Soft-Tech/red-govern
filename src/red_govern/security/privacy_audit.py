"""Privacy and security posture auditing for Red-Govern."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from red_govern.config.models import RedGovernConfig


class AuditSeverity(str, Enum):
    """Severity levels for privacy-audit findings."""

    INFO = "info"
    WARNING = "warning"
    CRITICAL = "critical"


@dataclass(frozen=True, slots=True)
class AuditFinding:
    """One privacy or security audit finding."""

    control: str
    effective_value: str
    severity: AuditSeverity
    passed: bool
    message: str


@dataclass(frozen=True, slots=True)
class PrivacyAuditResult:
    """Complete Red-Govern privacy audit."""

    findings: tuple[AuditFinding, ...]

    @property
    def passed(self) -> bool:
        """Return whether no critical finding failed."""
        return not any(
            not finding.passed
            and finding.severity == AuditSeverity.CRITICAL
            for finding in self.findings
        )

    @property
    def warning_count(self) -> int:
        """Return the number of failed warning controls."""
        return sum(
            1
            for finding in self.findings
            if not finding.passed
            and finding.severity == AuditSeverity.WARNING
        )

    @property
    def critical_count(self) -> int:
        """Return the number of failed critical controls."""
        return sum(
            1
            for finding in self.findings
            if not finding.passed
            and finding.severity == AuditSeverity.CRITICAL
        )


def _display_path(path: Path) -> str:
    """Return a readable local path without checking existence."""
    return str(path.expanduser())


def audit_privacy(
    config: RedGovernConfig,
) -> PrivacyAuditResult:
    """Evaluate effective privacy and safety configuration."""
    authentication = config.redshift.authentication
    actions = config.actions
    privacy = config.privacy

    findings = (
        AuditFinding(
            control="Telemetry",
            effective_value=str(privacy.telemetry).lower(),
            severity=AuditSeverity.CRITICAL,
            passed=not privacy.telemetry,
            message=(
                "Telemetry is disabled."
                if not privacy.telemetry
                else "Telemetry is enabled and may transmit usage data."
            ),
        ),
        AuditFinding(
            control="External services",
            effective_value=str(privacy.external_services).lower(),
            severity=AuditSeverity.CRITICAL,
            passed=not privacy.external_services,
            message=(
                "External services are disabled."
                if not privacy.external_services
                else "External services are enabled."
            ),
        ),
        AuditFinding(
            control="Query-text capture",
            effective_value=str(privacy.capture_query_text).lower(),
            severity=AuditSeverity.WARNING,
            passed=not privacy.capture_query_text,
            message=(
                "Query text will not be captured."
                if not privacy.capture_query_text
                else "Query text capture is enabled."
            ),
        ),
        AuditFinding(
            control="Query-literal redaction",
            effective_value=str(privacy.redact_literals).lower(),
            severity=AuditSeverity.CRITICAL,
            passed=privacy.redact_literals,
            message=(
                "Query literals are configured for redaction."
                if privacy.redact_literals
                else "Query-literal redaction is disabled."
            ),
        ),
        AuditFinding(
            control="Read-only mode",
            effective_value=str(actions.read_only).lower(),
            severity=AuditSeverity.CRITICAL,
            passed=actions.read_only,
            message=(
                "Read-only mode is enabled."
                if actions.read_only
                else "Read-only mode is disabled."
            ),
        ),
        AuditFinding(
            control="Database writes",
            effective_value=str(actions.allow_database_writes).lower(),
            severity=AuditSeverity.CRITICAL,
            passed=not actions.allow_database_writes,
            message=(
                "Database writes are disabled."
                if not actions.allow_database_writes
                else "Database writes are permitted."
            ),
        ),
        AuditFinding(
            control="Query cancellation",
            effective_value=str(actions.allow_query_cancellation).lower(),
            severity=AuditSeverity.WARNING,
            passed=not actions.allow_query_cancellation,
            message=(
                "Query cancellation is disabled."
                if not actions.allow_query_cancellation
                else "Query cancellation is permitted."
            ),
        ),
        AuditFinding(
            control="Password storage",
            effective_value=f"Environment variable: {authentication.password_env}",
            severity=AuditSeverity.INFO,
            passed=True,
            message=(
                "Only the environment-variable name is configured; "
                "the password value is not stored in YAML."
            ),
        ),
        AuditFinding(
            control="Local history",
            effective_value=_display_path(config.history.path),
            severity=AuditSeverity.INFO,
            passed=True,
            message="Governance history is configured for local storage.",
        ),
        AuditFinding(
            control="JSON reports",
            effective_value=_display_path(config.outputs.json_output.path),
            severity=AuditSeverity.INFO,
            passed=True,
            message="JSON reports are configured for local file output.",
        ),
        AuditFinding(
            control="Excel reports",
            effective_value=_display_path(config.outputs.excel.path),
            severity=AuditSeverity.INFO,
            passed=True,
            message="Excel reports are configured for local file output.",
        ),
    )

    return PrivacyAuditResult(findings=findings)
