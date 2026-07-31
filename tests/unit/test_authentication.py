"""Tests for Red-Govern authentication resolution."""

from __future__ import annotations

import pytest

from red_govern.config.models import RedshiftConfig
from red_govern.connections.authentication import resolve_authentication
from red_govern.exceptions import AuthenticationError


def test_password_authentication_uses_environment_variable(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Password mode should read from the configured environment variable."""
    monkeypatch.setenv(
        "RED_GOVERN_REDSHIFT_PASSWORD",
        "synthetic-password",
    )

    config = RedshiftConfig.model_validate(
        {
            "connection": {
                "host": "example.redshift.amazonaws.com",
                "user": "test_user",
            },
            "authentication": {
                "method": "password",
            },
        }
    )

    resolved = resolve_authentication(config)

    assert resolved.method == "password"
    assert resolved.password == "synthetic-password"


def test_missing_password_is_rejected(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Password mode should fail if its environment variable is absent."""
    monkeypatch.delenv(
        "RED_GOVERN_REDSHIFT_PASSWORD",
        raising=False,
    )

    config = RedshiftConfig.model_validate(
        {
            "authentication": {
                "method": "password",
            },
        }
    )

    with pytest.raises(AuthenticationError):
        resolve_authentication(config)


def test_auto_authentication_prefers_password(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Auto mode should use a configured password before AWS methods."""
    monkeypatch.setenv(
        "RED_GOVERN_REDSHIFT_PASSWORD",
        "synthetic-password",
    )

    config = RedshiftConfig()

    resolved = resolve_authentication(config)

    assert resolved.method == "password"


def test_profile_authentication() -> None:
    """AWS profile authentication should retain non-secret settings."""
    config = RedshiftConfig.model_validate(
        {
            "authentication": {
                "method": "profile",
                "aws_profile": "development",
                "cluster_identifier": "example-cluster",
                "region": "ap-south-1",
            },
        }
    )

    resolved = resolve_authentication(config)

    assert resolved.method == "profile"
    assert resolved.aws_profile == "development"
    assert resolved.cluster_identifier == "example-cluster"
