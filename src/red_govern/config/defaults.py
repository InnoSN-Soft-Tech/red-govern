"""Access to packaged Red-Govern configuration resources."""

from __future__ import annotations

from importlib.resources import files
from pathlib import Path


def default_config_resource() -> Path:
    """Return the packaged default configuration path."""
    resource = files("red_govern.resources").joinpath("default_config.yml")
    return Path(str(resource))


def classification_example_resource() -> Path:
    """Return the packaged classification example path."""
    resource = files("red_govern.resources").joinpath(
        "classification.example.yml"
    )
    return Path(str(resource))
