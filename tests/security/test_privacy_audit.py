"""Tests for Red-Govern privacy configuration auditing."""

from red_govern.config import load_default_config
from red_govern.security import AuditSeverity, audit_privacy


def test_default_configuration_passes_privacy_audit() -> None:
    """Safe packaged defaults should pass the privacy audit."""
    config = load_default_config()

    result = audit_privacy(config)

    assert result.passed is True
    assert result.critical_count == 0


def test_database_writes_fail_privacy_audit() -> None:
    """Database-write permission should create a critical failure."""
    config = load_default_config()

    unsafe_actions = config.actions.model_copy(
        update={
            "read_only": False,
            "allow_database_writes": True,
        }
    )

    unsafe_config = config.model_copy(
        update={"actions": unsafe_actions}
    )

    result = audit_privacy(unsafe_config)

    assert result.passed is False
    assert result.critical_count >= 1


def test_query_text_capture_creates_warning() -> None:
    """Query-text capture should be surfaced as a warning."""
    config = load_default_config()

    unsafe_privacy = config.privacy.model_copy(
        update={"capture_query_text": True}
    )

    updated_config = config.model_copy(
        update={"privacy": unsafe_privacy}
    )

    result = audit_privacy(updated_config)

    assert result.warning_count >= 1


def test_password_value_is_not_exposed() -> None:
    """The audit should show only the environment-variable name."""
    config = load_default_config()

    result = audit_privacy(config)

    password_finding = next(
        finding
        for finding in result.findings
        if finding.control == "Password storage"
    )

    assert password_finding.severity == AuditSeverity.INFO
    assert "RED_GOVERN_REDSHIFT_PASSWORD" in (
        password_finding.effective_value
    )
    assert "password=" not in password_finding.effective_value.lower()
