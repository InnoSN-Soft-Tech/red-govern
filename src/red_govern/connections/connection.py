"""Amazon Redshift connection construction."""

from __future__ import annotations

from collections.abc import Iterator
from contextlib import contextmanager
from typing import Any, Protocol, cast

import redshift_connector

from red_govern.config.models import RedshiftConfig
from red_govern.connections.authentication import (
    AuthenticationDetails,
    resolve_authentication,
)
from red_govern.exceptions import RedshiftConnectionError
from red_govern.security.redaction import redact_text


class CursorProtocol(Protocol):
    """Minimum cursor behaviour required by Red-Govern."""

    description: Any

    def execute(
        self,
        operation: str,
        args: Any = None,
    ) -> Any:
        """Execute SQL."""

    def fetchone(self) -> Any:
        """Fetch one result."""

    def fetchall(self) -> Any:
        """Fetch all results."""

    def close(self) -> None:
        """Close the cursor."""


class ConnectionProtocol(Protocol):
    """Minimum connection behaviour required by Red-Govern."""

    autocommit: bool

    def cursor(self) -> CursorProtocol:
        """Create a database cursor."""

    def close(self) -> None:
        """Close the database connection."""

    def rollback(self) -> None:
        """Rollback the active transaction."""


def build_connection_arguments(
    config: RedshiftConfig,
    auth: AuthenticationDetails | None = None,
) -> dict[str, Any]:
    """Build connector arguments without logging credential values."""
    resolved = auth or resolve_authentication(config)

    connection = config.connection
    ssl = config.ssl

    arguments: dict[str, Any] = {
        "database": connection.database,
        "port": connection.port,
        "timeout": connection.connect_timeout_seconds,
        "tcp_keepalive": connection.tcp_keepalive,
        "ssl": ssl.enabled,
        "sslmode": ssl.mode,
    }

    if connection.host:
        arguments["host"] = connection.host

    if connection.user:
        arguments["user"] = connection.user

    if resolved.method == "password":
        arguments["password"] = resolved.password

    if resolved.method in {"iam", "profile"}:
        arguments["iam"] = True

        if resolved.aws_profile:
            arguments["profile"] = resolved.aws_profile

        if resolved.cluster_identifier:
            arguments["cluster_identifier"] = (
                resolved.cluster_identifier
            )

        if resolved.workgroup_name:
            arguments["serverless_work_group"] = (
                resolved.workgroup_name
            )

        if resolved.region:
            arguments["region"] = resolved.region

        if resolved.db_user:
            arguments["db_user"] = resolved.db_user

    return arguments


def open_connection(
    config: RedshiftConfig,
) -> ConnectionProtocol:
    """Open a Redshift connection."""
    arguments = build_connection_arguments(config)

    try:
        connection = redshift_connector.connect(**arguments)
    except Exception as exc:
        safe_message = redact_text(str(exc))

        raise RedshiftConnectionError(
            f"Unable to connect to Amazon Redshift: {safe_message}"
        ) from exc

    return cast(ConnectionProtocol, connection)


@contextmanager
def redshift_connection(
    config: RedshiftConfig,
) -> Iterator[ConnectionProtocol]:
    """Yield a Redshift connection and always close it."""
    connection = open_connection(config)

    try:
        yield connection
    finally:
        connection.close()
