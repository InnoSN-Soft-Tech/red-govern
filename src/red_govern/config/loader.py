"""Configuration loading and writing utilities."""

from __future__ import annotations

from pathlib import Path
from typing import Any

import yaml

from red_govern.config.defaults import default_config_resource
from red_govern.config.models import RedGovernConfig
from red_govern.exceptions import ConfigurationError
from red_govern.security.local_files import prepare_private_file


def read_yaml(path: Path) -> dict[str, Any]:
    """Read a YAML mapping from disk."""
    try:
        raw = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(
            f"Unable to read configuration file: {path}"
        ) from exc

    try:
        loaded = yaml.safe_load(raw)
    except yaml.YAMLError as exc:
        raise ConfigurationError(
            f"Invalid YAML in configuration file: {path}"
        ) from exc

    if not isinstance(loaded, dict):
        raise ConfigurationError(
            f"Configuration root must be a mapping: {path}"
        )

    return loaded


def load_config(path: Path) -> RedGovernConfig:
    """Load and validate a Red-Govern configuration file."""
    raw = read_yaml(path)

    try:
        return RedGovernConfig.model_validate(raw)
    except ValueError as exc:
        raise ConfigurationError(
            f"Configuration validation failed: {exc}"
        ) from exc


def load_default_config() -> RedGovernConfig:
    """Load the packaged default configuration."""
    return load_config(default_config_resource())


def write_default_config(
    destination: Path,
    *,
    overwrite: bool = False,
) -> Path:
    """Write the packaged default configuration to a user-selected path."""
    output_path = destination.expanduser().resolve()

    if output_path.exists() and not overwrite:
        raise ConfigurationError(
            f"Configuration already exists: {output_path}"
        )

    try:
        prepare_private_file(output_path)
        content = default_config_resource().read_text(encoding="utf-8")
        output_path.write_text(content, encoding="utf-8")
    except OSError as exc:
        raise ConfigurationError(
            f"Unable to write configuration file: {output_path}"
        ) from exc

    return output_path
