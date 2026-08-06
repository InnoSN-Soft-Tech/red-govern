"""Typed, presentation-independent Red-Govern API.

The first public API surface is deliberately offline-safe. It validates and
inspects local configuration without connecting to Amazon Redshift or writing
files.

Contract: without connecting to Amazon Redshift or writing files.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Literal, NoReturn, TypeAlias, cast

from pydantic import BaseModel, ConfigDict

from red_govern import __version__
from red_govern.config import (
    RedGovernConfig,
    load_config,
    load_default_config,
)
from red_govern.exceptions import ConfigurationError
from red_govern.security import (
    AuditSeverity,
    audit_privacy,
    redact_mapping,
    redact_text,
)

ConfigPath: TypeAlias = str | Path

DEFAULT_CONFIG_PATH = Path("red-govern.yml")
REDACTED = "***REDACTED***"

_PRIVATE_CONFIG_PATHS: tuple[tuple[str, ...], ...] = (
    ("redshift", "profile_name"),
    ("redshift", "connection", "host"),
    ("redshift", "connection", "database"),
    ("redshift", "connection", "user"),
    ("redshift", "authentication", "aws_profile"),
    ("redshift", "authentication", "cluster_identifier"),
    ("redshift", "authentication", "workgroup_name"),
    ("redshift", "authentication", "db_user"),
    ("classification", "rules_file"),
    ("classification", "operational_registry", "path"),
    ("history", "path"),
    ("outputs", "json", "path"),
    ("outputs", "excel", "path"),
)


class ApiResult(BaseModel):
    """Strict immutable base model for public API results."""

    model_config = ConfigDict(extra="forbid", frozen=True)


class VersionResult(ApiResult):
    """Installed Red-Govern package version."""

    package: Literal["red-govern"] = "red-govern"
    version: str
    platform: Literal["Amazon Redshift"] = "Amazon Redshift"
    is_alpha: bool


class ConfigValidationResult(ApiResult):
    """Successful configuration-validation result."""

    valid: Literal[True] = True
    config_version: int
    source: str


class RedactedConfigResult(ApiResult):
    """Effective configuration with sensitive metadata removed."""

    config_version: int
    source: str
    configuration: dict[str, Any]


class PrivacyAuditFindingResult(ApiResult):
    """One structured privacy-audit finding."""

    control: str
    effective_value: str
    severity: AuditSeverity
    passed: bool
    message: str


class PrivacyAuditApiResult(ApiResult):
    """Structured privacy and safety audit result."""

    passed: bool
    warning_count: int
    critical_count: int
    source: str
    findings: tuple[PrivacyAuditFindingResult, ...]


def _coerce_path(path: ConfigPath) -> Path:
    """Return a local configuration path without resolving symlinks."""

    return Path(path).expanduser()


def _display_path(path: Path) -> str:
    """Return a stable path display with the home directory collapsed."""

    expanded = path.expanduser()
    home = Path.home()

    try:
        relative = expanded.relative_to(home)
    except ValueError:
        return str(path) if not path.is_absolute() else str(expanded)

    return "~" if not relative.parts else str(Path("~") / relative)


def _raise_safe_configuration_error(
    error: ConfigurationError,
    path: Path,
) -> NoReturn:
    """Raise a stable configuration error without leaking input values."""

    message = str(error)

    if message.startswith("Unable to read configuration file:"):
        category = "Unable to read configuration file"
    elif message.startswith("Invalid YAML in configuration file:"):
        category = "Invalid YAML in configuration file"
    elif message.startswith("Configuration root must be a mapping:"):
        category = "Configuration root must be a mapping"
    else:
        category = "Configuration validation failed"

    raise ConfigurationError(
        f"{category}: {_display_path(path)}"
    ) from None


def _load_file_config(path: ConfigPath) -> tuple[RedGovernConfig, str]:
    """Load one file-backed configuration with a safe error contract."""

    local_path = _coerce_path(path)

    try:
        config = load_config(local_path)
    except ConfigurationError as error:
        _raise_safe_configuration_error(error, local_path)

    return config, _display_path(local_path)


def _load_effective_config(
    path: ConfigPath | None,
) -> tuple[RedGovernConfig, str]:
    """Load a file-backed configuration or the packaged defaults."""

    if path is None:
        return load_default_config(), "packaged-default"

    return _load_file_config(path)


def _redact_nested_value(
    values: dict[str, Any],
    field_path: tuple[str, ...],
) -> None:
    """Replace one nested non-null configuration value."""

    current = values

    for segment in field_path[:-1]:
        candidate = current.get(segment)

        if not isinstance(candidate, dict):
            return

        current = cast(dict[str, Any], candidate)

    key = field_path[-1]

    if key in current and current[key] is not None:
        current[key] = REDACTED


def _redacted_configuration(
    config: RedGovernConfig,
) -> dict[str, Any]:
    """Return an effective configuration safe for agent transports."""

    raw = config.model_dump(mode="json", by_alias=True)
    redacted = redact_mapping(raw)

    for field_path in _PRIVATE_CONFIG_PATHS:
        _redact_nested_value(redacted, field_path)

    return redacted


def _collapse_home(value: str) -> str:
    """Collapse an expanded home path inside one audit value."""

    home = str(Path.home())

    if value == home:
        return "~"

    prefix = f"{home}/"

    if value.startswith(prefix):
        return f"~/{value[len(prefix):]}"

    return value


def _safe_audit_value(control: str, value: str) -> str:
    """Redact one audit value for structured API output."""

    if control == "Password storage":
        return "Environment variable configured"

    return _collapse_home(redact_text(value))


def get_version() -> VersionResult:
    """Return the installed Red-Govern version without side effects."""

    stable_pattern = re.compile(r"^\d+\.\d+\.\d+$")

    return VersionResult(
        version=__version__,
        is_alpha=stable_pattern.fullmatch(__version__) is None,
    )


def validate_config(
    path: ConfigPath = DEFAULT_CONFIG_PATH,
) -> ConfigValidationResult:
    """Validate one local configuration file.

    Invalid configuration raises :class:`ConfigurationError` with a sanitized
    message that does not include rejected values.
    """

    config, source = _load_file_config(path)

    return ConfigValidationResult(
        config_version=config.config_version,
        source=source,
    )


def get_redacted_config(
    path: ConfigPath | None = None,
) -> RedactedConfigResult:
    """Return effective configuration with sensitive metadata redacted.

    ``None`` uses the packaged safe defaults, matching ``config-show``.
    """

    config, source = _load_effective_config(path)

    return RedactedConfigResult(
        config_version=config.config_version,
        source=source,
        configuration=_redacted_configuration(config),
    )


def run_privacy_audit(
    path: ConfigPath = DEFAULT_CONFIG_PATH,
) -> PrivacyAuditApiResult:
    """Run the local privacy audit and return structured safe output."""

    config, source = _load_file_config(path)
    result = audit_privacy(config)

    findings = tuple(
        PrivacyAuditFindingResult(
            control=finding.control,
            effective_value=_safe_audit_value(
                finding.control,
                finding.effective_value,
            ),
            severity=finding.severity,
            passed=finding.passed,
            message=redact_text(finding.message),
        )
        for finding in result.findings
    )

    return PrivacyAuditApiResult(
        passed=result.passed,
        warning_count=result.warning_count,
        critical_count=result.critical_count,
        source=source,
        findings=findings,
    )


__all__ = [
    "ConfigValidationResult",
    "PrivacyAuditApiResult",
    "PrivacyAuditFindingResult",
    "RedactedConfigResult",
    "VersionResult",
    "get_redacted_config",
    "get_version",
    "run_privacy_audit",
    "validate_config",
]
