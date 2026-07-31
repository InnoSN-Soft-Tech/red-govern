"""Redshift connection diagnostics."""

from __future__ import annotations

from dataclasses import dataclass
from time import perf_counter

from red_govern.config.models import RedshiftConfig
from red_govern.connections.connection import redshift_connection
from red_govern.exceptions import RedshiftQueryError
from red_govern.security.redaction import redact_text


@dataclass(frozen=True, slots=True)
class ConnectionTestResult:
    """Result of a Redshift connectivity test."""

    connected: bool
    database: str
    user: str
    version: str
    latency_ms: float


TEST_CONNECTION_SQL = """
SELECT
    current_database() AS database_name,
    current_user AS user_name,
    version() AS server_version
"""


def test_connection(
    config: RedshiftConfig,
) -> ConnectionTestResult:
    """Connect and run a read-only diagnostic query."""
    started = perf_counter()

    with redshift_connection(config) as connection:
        cursor = connection.cursor()

        try:
            cursor.execute(TEST_CONNECTION_SQL)
            row = cursor.fetchone()
        except Exception as exc:
            safe_message = redact_text(str(exc))

            raise RedshiftQueryError(
                f"Connected, but the diagnostic query failed: "
                f"{safe_message}"
            ) from exc
        finally:
            cursor.close()

    elapsed_ms = (perf_counter() - started) * 1_000

    if not row or len(row) < 3:
        raise RedshiftQueryError(
            "The diagnostic query returned an unexpected result."
        )

    return ConnectionTestResult(
        connected=True,
        database=str(row[0]),
        user=str(row[1]),
        version=str(row[2]),
        latency_ms=round(elapsed_ms, 2),
    )
