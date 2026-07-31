"""Configuration validation helpers."""

from __future__ import annotations

from pathlib import Path

from red_govern.config.loader import load_config
from red_govern.config.models import RedGovernConfig


def validate_config(path: Path) -> RedGovernConfig:
    """Load and validate a Red-Govern configuration."""
    return load_config(path)
