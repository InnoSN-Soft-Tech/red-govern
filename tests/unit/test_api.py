"""Tests for the typed, offline-safe Red-Govern Python API."""

from __future__ import annotations

import ast
import json
from pathlib import Path

import pytest

import red_govern.api as api
from red_govern import __version__
from red_govern.config import write_default_config
from red_govern.exceptions import ConfigurationError
from red_govern.security import AuditSeverity


def test_get_version_returns_structured_package_metadata() -> None:
    """Version retrieval should be typed, local, and side-effect free."""

    result = api.get_version()

    assert result.package == "red-govern"
    assert result.version == __version__
    assert result.platform == "Amazon Redshift"
    assert result.is_alpha is True


def test_validate_config_accepts_generated_configuration(
    tmp_path: Path,
) -> None:
    """Generated safe defaults should validate through the API."""

    config_path = tmp_path / "red-govern.yml"
    write_default_config(config_path)

    result = api.validate_config(config_path)

    assert result.valid is True
    assert result.config_version == 1
    assert result.source == str(config_path)


def test_validate_config_sanitizes_rejected_values(
    tmp_path: Path,
) -> None:
    """Validation errors must not echo invalid sensitive values."""

    config_path = tmp_path / "invalid.yml"
    config_path.write_text(
        """
config_version: 1
redshift:
  connection:
    password: super-secret-value
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError) as error:
        api.validate_config(config_path)

    message = str(error.value)

    assert message == f"Configuration validation failed: {config_path}"
    assert "super-secret-value" not in message
    assert "password" not in message.lower()


def test_get_redacted_config_uses_packaged_defaults() -> None:
    """None should load packaged defaults with sensitive fields removed."""

    result = api.get_redacted_config()

    assert result.config_version == 1
    assert result.source == "packaged-default"
    assert (
        result.configuration["redshift"]["authentication"]["password_env"]
        == api.REDACTED
    )
    assert result.configuration["actions"]["read_only"] is True


def test_get_redacted_config_masks_endpoint_identity_and_paths(
    tmp_path: Path,
) -> None:
    """Agent-safe output should mask environment-specific metadata."""

    config_path = tmp_path / "red-govern.yml"
    write_default_config(config_path)

    content = config_path.read_text(encoding="utf-8")
    replacements = {
        "    host: null\n": "    host: private.example.internal\n",
        "    database: dev\n": "    database: confidential_warehouse\n",
        "    user: null\n": "    user: confidential_user\n",
        "    aws_profile: null\n": "    aws_profile: confidential-profile\n",
        "    cluster_identifier: null\n": (
            "    cluster_identifier: private-cluster\n"
        ),
        "    workgroup_name: null\n": (
            "    workgroup_name: private-workgroup\n"
        ),
        "    db_user: null\n": "    db_user: confidential_db_user\n",
    }

    for source, replacement in replacements.items():
        content = content.replace(source, replacement)

    config_path.write_text(content, encoding="utf-8")

    result = api.get_redacted_config(config_path)
    serialized = json.dumps(result.model_dump(mode="json"))

    for sensitive_value in (
        "private.example.internal",
        "confidential_warehouse",
        "confidential_user",
        "confidential-profile",
        "private-cluster",
        "private-workgroup",
        "confidential_db_user",
    ):
        assert sensitive_value not in serialized

    redshift = result.configuration["redshift"]
    authentication = redshift["authentication"]

    assert redshift["profile_name"] == api.REDACTED
    assert redshift["connection"]["host"] == api.REDACTED
    assert redshift["connection"]["database"] == api.REDACTED
    assert redshift["connection"]["user"] == api.REDACTED
    assert authentication["aws_profile"] == api.REDACTED
    assert authentication["cluster_identifier"] == api.REDACTED
    assert authentication["workgroup_name"] == api.REDACTED
    assert authentication["db_user"] == api.REDACTED
    assert result.configuration["history"]["path"] == api.REDACTED
    assert result.configuration["outputs"]["json"]["path"] == api.REDACTED


def test_get_redacted_config_does_not_modify_source_file(
    tmp_path: Path,
) -> None:
    """Reading redacted configuration must not mutate the source."""

    config_path = tmp_path / "red-govern.yml"
    write_default_config(config_path)
    before = config_path.read_bytes()

    api.get_redacted_config(config_path)

    assert config_path.read_bytes() == before


def test_run_privacy_audit_returns_structured_safe_defaults(
    tmp_path: Path,
) -> None:
    """Default safety controls should produce a passing structured audit."""

    config_path = tmp_path / "red-govern.yml"
    write_default_config(config_path)

    result = api.run_privacy_audit(config_path)

    assert result.passed is True
    assert result.warning_count == 0
    assert result.critical_count == 0
    assert len(result.findings) == 11
    assert all(finding.passed for finding in result.findings)
    assert {
        finding.severity for finding in result.findings
    } == {
        AuditSeverity.INFO,
        AuditSeverity.WARNING,
        AuditSeverity.CRITICAL,
    }


def test_run_privacy_audit_reports_warning_and_critical_failures(
    tmp_path: Path,
) -> None:
    """Unsafe effective controls should remain visible and structured."""

    config_path = tmp_path / "red-govern.yml"
    write_default_config(config_path)

    content = config_path.read_text(encoding="utf-8")
    content = content.replace("telemetry: false", "telemetry: true")
    content = content.replace(
        "allow_query_cancellation: false",
        "allow_query_cancellation: true",
    )
    config_path.write_text(content, encoding="utf-8")

    result = api.run_privacy_audit(config_path)

    assert result.passed is False
    assert result.critical_count == 1
    assert result.warning_count == 1

    failed_controls = {
        finding.control
        for finding in result.findings
        if not finding.passed
    }

    assert failed_controls == {"Telemetry", "Query cancellation"}


def test_run_privacy_audit_collapses_home_and_hides_password_env(
    tmp_path: Path,
) -> None:
    """Audit output should not expose the expanded home or env-var name."""

    config_path = tmp_path / "red-govern.yml"
    write_default_config(config_path)

    result = api.run_privacy_audit(config_path)
    serialized = result.model_dump_json()

    assert str(Path.home()) not in serialized
    assert "RED_GOVERN_REDSHIFT_PASSWORD" not in serialized

    password_finding = next(
        finding
        for finding in result.findings
        if finding.control == "Password storage"
    )

    assert (
        password_finding.effective_value
        == "Environment variable configured"
    )


def test_api_module_has_no_cli_or_agent_runtime_imports() -> None:
    """The internal contract must not depend on presentation or MCP."""

    module_path = Path(api.__file__)
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    imported_roots = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", 1)[0]
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert imported_roots.isdisjoint(
        {"typer", "rich", "mcp", "openai"}
    )


def test_public_api_exports_are_exact() -> None:
    """The first public API contract should remain intentionally small."""

    assert set(api.__all__) == {
        "ConfigValidationResult",
        "PrivacyAuditApiResult",
        "PrivacyAuditFindingResult",
        "RedactedConfigResult",
        "VersionResult",
        "get_redacted_config",
        "get_version",
        "run_privacy_audit",
        "validate_config",
    }
