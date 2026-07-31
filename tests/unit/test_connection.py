"""Tests for Red-Govern Redshift connection construction."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from red_govern.config.models import RedshiftConfig
from red_govern.connections.authentication import AuthenticationDetails
from red_govern.connections.connection import (
    build_connection_arguments,
    redshift_connection,
)
from red_govern.exceptions import RedshiftConnectionError


def test_password_connection_arguments() -> None:
    """Password configuration should build safe connector arguments."""
    config = RedshiftConfig.model_validate(
        {
            "connection": {
                "host": "example.redshift.amazonaws.com",
                "database": "analytics",
                "user": "governance_user",
                "port": 5439,
            },
        }
    )

    auth = AuthenticationDetails(
        method="password",
        password="synthetic-password",
    )

    arguments = build_connection_arguments(config, auth)

    assert arguments["host"] == "example.redshift.amazonaws.com"
    assert arguments["database"] == "analytics"
    assert arguments["user"] == "governance_user"
    assert arguments["password"] == "synthetic-password"
    assert arguments["ssl"] is True
    assert arguments["sslmode"] == "verify-full"


def test_profile_connection_arguments() -> None:
    """Profile authentication should enable IAM connector settings."""
    config = RedshiftConfig()

    auth = AuthenticationDetails(
        method="profile",
        aws_profile="development",
        cluster_identifier="example-cluster",
        region="ap-south-1",
    )

    arguments = build_connection_arguments(config, auth)

    assert arguments["iam"] is True
    assert arguments["profile"] == "development"
    assert arguments["cluster_identifier"] == "example-cluster"
    assert arguments["region"] == "ap-south-1"


@patch("red_govern.connections.connection.redshift_connector.connect")
def test_connection_context_always_closes(
    connect_mock: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The connection context should close the connection."""
    monkeypatch.setenv(
        "RED_GOVERN_REDSHIFT_PASSWORD",
        "synthetic-password",
    )

    connection = MagicMock()
    connect_mock.return_value = connection

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

    with redshift_connection(config):
        pass

    connection.close.assert_called_once()


@patch("red_govern.connections.connection.redshift_connector.connect")
def test_connection_error_is_wrapped(
    connect_mock: MagicMock,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Connector errors should become safe Red-Govern errors."""
    monkeypatch.setenv(
        "RED_GOVERN_REDSHIFT_PASSWORD",
        "synthetic-password",
    )

    connect_mock.side_effect = RuntimeError(
        "password=synthetic-password connection failed"
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

    with pytest.raises(RedshiftConnectionError) as captured:  # noqa: SIM117
        with redshift_connection(config):
            pass

    assert "synthetic-password" not in str(captured.value)
    assert "***REDACTED***" in str(captured.value)
