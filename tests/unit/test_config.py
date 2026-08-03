"""Tests for Red-Govern configuration behaviour."""

import stat
from pathlib import Path

import pytest

from red_govern.config import (
    load_config,
    load_default_config,
    write_default_config,
)
from red_govern.exceptions import ConfigurationError


def test_default_config_is_valid() -> None:
    """The packaged default configuration should validate."""
    config = load_default_config()

    assert config.config_version == 1
    assert config.actions.read_only is True
    assert config.actions.allow_database_writes is False
    assert config.privacy.telemetry is False
    assert config.privacy.capture_query_text is False


def test_write_and_load_default_config(tmp_path: Path) -> None:
    """A generated configuration should be loadable."""
    destination = tmp_path / "red-govern.yml"

    result = write_default_config(destination)
    loaded = load_config(destination)

    assert destination.exists()
    assert result == destination.resolve()
    assert stat.S_IMODE(destination.stat().st_mode) == 0o600
    assert loaded.redshift.connection.port == 5439
    assert loaded.history.backend == "sqlite"


def test_existing_config_is_not_overwritten(tmp_path: Path) -> None:
    """Existing files should be protected unless overwrite is enabled."""
    destination = tmp_path / "red-govern.yml"
    destination.write_text("existing: true", encoding="utf-8")

    with pytest.raises(ConfigurationError):
        write_default_config(destination)


def test_invalid_threshold_order_is_rejected(tmp_path: Path) -> None:
    """Critical threshold must be greater than warning threshold."""
    destination = tmp_path / "invalid.yml"
    destination.write_text(
        """
config_version: 1
governance:
  object_quota:
    enabled: true
    warning_threshold: 0.95
    critical_threshold: 0.90
""",
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError):
        load_config(destination)

def test_json_output_uses_public_json_alias() -> None:
    """The internal json_output field should serialize as json."""
    config = load_default_config()

    assert config.outputs.json_output.enabled is False

    dumped = config.model_dump(mode="json", by_alias=True)

    assert "json" in dumped["outputs"]
    assert "json_output" not in dumped["outputs"]


def test_object_quota_override() -> None:
    """A positive object-quota override should be accepted."""
    config = load_default_config()

    updated = config.model_copy(
        update={
            "governance": config.governance.model_copy(
                update={
                    "object_quota": config.governance.object_quota.model_copy(
                        update={"limit_override": 20000}
                    )
                }
            )
        }
    )

    assert updated.governance.object_quota.limit_override == 20000