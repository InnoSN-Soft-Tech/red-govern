"""Tests for the Red-Govern command-line interface."""

import re

from typer.testing import CliRunner

from red_govern import __version__
from red_govern.cli.app import app

runner = CliRunner()

_ANSI_ESCAPE_PATTERN = re.compile(
    r"\x1b\[[0-?]*[ -/]*[@-~]"
)


def _strip_ansi(value: str) -> str:
    """Remove terminal styling from captured CLI output."""
    return _ANSI_ESCAPE_PATTERN.sub("", value)


def test_version_command() -> None:
    """The version command should report the installed package version."""
    result = runner.invoke(app, ["version"])

    assert result.exit_code == 0

    plain_output = _strip_ansi(result.stdout)

    assert f"Red-Govern {__version__}" in plain_output

def test_doctor_command() -> None:
    """The doctor command should return the local diagnostic."""
    result = runner.invoke(app, ["doctor"])

    assert result.exit_code == 0
    assert "Red-Govern Doctor" in result.stdout
    assert "Telemetry" in result.stdout
    assert "Disabled" in result.stdout
    assert "Not tested" in result.stdout

def test_no_command_shows_help() -> None:
    """Running without a command should display help."""
    result = runner.invoke(app, [])

    assert result.exit_code in {0,2}
    assert "Local-first governance" in result.stdout


def test_init_command_creates_config(tmp_path) -> None:
    """The init command should create a default configuration file."""
    destination = tmp_path / "red-govern.yml"

    result = runner.invoke(
        app,
        ["init", "--output", str(destination)],
    )

    assert result.exit_code == 0
    assert destination.exists()
    assert "Created configuration" in result.stdout


def test_config_validate_command(tmp_path) -> None:
    """A generated configuration should pass CLI validation."""
    destination = tmp_path / "red-govern.yml"

    create_result = runner.invoke(
        app,
        ["init", "--output", str(destination)],
    )
    validate_result = runner.invoke(
        app,
        ["config-validate", "--config", str(destination)],
    )

    assert create_result.exit_code == 0
    assert validate_result.exit_code == 0
    assert "Configuration is valid" in validate_result.stdout


def test_config_show_uses_packaged_default() -> None:
    """Config-show should display safe packaged defaults."""
    result = runner.invoke(app, ["config-show"])

    assert result.exit_code == 0
    assert "telemetry: false" in result.stdout
    assert "read_only: true" in result.stdout

def test_inventory_requires_valid_authentication(
    tmp_path,
    monkeypatch,
) -> None:
    """Inventory should fail cleanly without authentication."""
    monkeypatch.delenv(
        "RED_GOVERN_REDSHIFT_PASSWORD",
        raising=False,
    )

    destination = tmp_path / "red-govern.yml"

    create_result = runner.invoke(
        app,
        ["init", "--output", str(destination)],
    )
    inventory_result = runner.invoke(
        app,
        ["inventory", "--config", str(destination)],
    )

    assert create_result.exit_code == 0
    assert inventory_result.exit_code == 1
    assert "Inventory collection failed" in inventory_result.stdout

def test_quota_requires_valid_authentication(
    tmp_path,
    monkeypatch,
) -> None:
    """Quota analysis should fail cleanly without authentication."""
    monkeypatch.delenv(
        "RED_GOVERN_REDSHIFT_PASSWORD",
        raising=False,
    )

    destination = tmp_path / "red-govern.yml"

    create_result = runner.invoke(
        app,
        ["init", "--output", str(destination)],
    )

    quota_result = runner.invoke(
        app,
        ["quota", "--config", str(destination)],
    )

    assert create_result.exit_code == 0
    assert quota_result.exit_code == 1
    assert "Quota analysis failed" in quota_result.stdout

def test_changes_fails_without_snapshots(
    tmp_path,
) -> None:
    """Changes should fail cleanly when no snapshot exists."""
    destination = tmp_path / "red-govern.yml"

    create_result = runner.invoke(
        app,
        ["init", "--output", str(destination)],
    )

    text = destination.read_text(encoding="utf-8")
    text = text.replace(
        "~/.red-govern/state/governance.db",
        str(tmp_path / "governance.db"),
    )
    destination.write_text(text, encoding="utf-8")

    result = runner.invoke(
        app,
        ["changes", "--config", str(destination)],
    )

    assert create_result.exit_code == 0
    assert result.exit_code == 1
    assert "Change analysis failed" in result.stdout

def test_json_report_requires_authentication(
    tmp_path,
    monkeypatch,
) -> None:
    """JSON reporting should fail cleanly without authentication."""
    monkeypatch.delenv(
        "RED_GOVERN_REDSHIFT_PASSWORD",
        raising=False,
    )

    config_path = tmp_path / "red-govern.yml"

    create_result = runner.invoke(
        app,
        ["init", "--output", str(config_path)],
    )

    result = runner.invoke(
        app,
        [
            "report",
            "json",
            "--config",
            str(config_path),
            "--output",
            str(tmp_path / "report.json"),
        ],
    )

    assert create_result.exit_code == 0
    assert result.exit_code == 1
    assert (
        "JSON report generation failed"
        in result.stdout
    )

def test_excel_report_requires_authentication(
    tmp_path,
    monkeypatch,
) -> None:
    """Excel reporting should fail cleanly without authentication."""
    monkeypatch.delenv(
        "RED_GOVERN_REDSHIFT_PASSWORD",
        raising=False,
    )

    config_path = tmp_path / "red-govern.yml"

    create_result = runner.invoke(
        app,
        ["init", "--output", str(config_path)],
    )

    result = runner.invoke(
        app,
        [
            "report",
            "excel",
            "--config",
            str(config_path),
            "--output",
            str(tmp_path / "report.xlsx"),
        ],
    )

    assert create_result.exit_code == 0
    assert result.exit_code == 1
    assert (
        "Excel report generation failed"
        in result.stdout
    )

def test_privacy_audit_passes_with_defaults(
    tmp_path,
) -> None:
    """Safe default configuration should pass the CLI privacy audit."""
    config_path = tmp_path / "red-govern.yml"

    create_result = runner.invoke(
        app,
        ["init", "--output", str(config_path)],
    )

    result = runner.invoke(
        app,
        [
            "privacy-audit",
            "--config",
            str(config_path),
        ],
    )

    assert create_result.exit_code == 0
    assert result.exit_code == 0
    assert "Red-Govern Privacy Audit" in result.stdout
    assert "Passed" in result.stdout

def test_query_summary_requires_authentication(
    tmp_path,
    monkeypatch,
) -> None:
    """Query summary should fail cleanly without authentication."""
    monkeypatch.delenv(
        "RED_GOVERN_REDSHIFT_PASSWORD",
        raising=False,
    )

    config_path = tmp_path / "red-govern.yml"

    create_result = runner.invoke(
        app,
        ["init", "--output", str(config_path)],
    )

    result = runner.invoke(
        app,
        [
            "queries",
            "summary",
            "--config",
            str(config_path),
        ],
    )

    assert create_result.exit_code == 0
    assert result.exit_code == 1
    assert "Query summary failed" in result.stdout

def test_query_performance_requires_authentication(
    tmp_path,
    monkeypatch,
) -> None:
    """Query-performance analysis should fail cleanly without authentication."""
    monkeypatch.delenv(
        "RED_GOVERN_REDSHIFT_PASSWORD",
        raising=False,
    )

    config_path = tmp_path / "red-govern.yml"

    create_result = runner.invoke(
        app,
        ["init", "--output", str(config_path)],
    )

    result = runner.invoke(
        app,
        [
            "queries",
            "performance",
            "--config",
            str(config_path),
        ],
    )

    assert create_result.exit_code == 0
    assert result.exit_code == 1
    assert "Query-performance analysis failed:" in result.stdout

def test_running_queries_require_authentication(
    tmp_path,
    monkeypatch,
) -> None:
    """Active-query monitoring should fail cleanly without authentication."""
    monkeypatch.delenv(
        "RED_GOVERN_REDSHIFT_PASSWORD",
        raising=False,
    )

    config_path = tmp_path / "red-govern.yml"

    create_result = runner.invoke(
        app,
        ["init", "--output", str(config_path)],
    )

    result = runner.invoke(
        app,
        [
            "queries",
            "running",
            "--config",
            str(config_path),
        ],
    )

    assert create_result.exit_code == 0
    assert result.exit_code == 1
    assert (
        "Running-query collection failed"
        in result.stdout
    )

def test_query_issues_require_authentication(
    tmp_path,
    monkeypatch,
) -> None:
    """Query-issue analysis should fail cleanly without authentication."""
    monkeypatch.delenv(
        "RED_GOVERN_REDSHIFT_PASSWORD",
        raising=False,
    )

    config_path = tmp_path / "red-govern.yml"

    create_result = runner.invoke(
        app,
        ["init", "--output", str(config_path)],
    )

    result = runner.invoke(
        app,
        [
            "queries",
            "issues",
            "--config",
            str(config_path),
            "--slow-seconds",
            "60",
        ],
    )

    assert create_result.exit_code == 0
    assert result.exit_code == 1
    assert "Query-issue analysis failed" in result.stdout

def test_query_breakdown_requires_authentication(
    tmp_path,
    monkeypatch,
) -> None:
    """Query breakdown should fail cleanly without authentication."""
    monkeypatch.delenv(
        "RED_GOVERN_REDSHIFT_PASSWORD",
        raising=False,
    )

    config_path = tmp_path / "red-govern.yml"

    create_result = runner.invoke(
        app,
        ["init", "--output", str(config_path)],
    )

    result = runner.invoke(
        app,
        [
            "queries",
            "breakdown",
            "--config",
            str(config_path),
        ],
    )

    assert create_result.exit_code == 0
    assert result.exit_code == 1
    assert (
        "Query-breakdown analysis failed"
        in result.stdout
    )


def test_query_performance_help_distinguishes_skew_units() -> None:
    """Performance help should expose both skew unit types."""
    result = runner.invoke(
        app,
        ["queries", "performance", "--help"],
    )

    assert result.exit_code == 0

    plain_output = _strip_ansi(result.stdout)

    assert "--skew-ratio" in plain_output
    assert "--skew-percent" in plain_output
