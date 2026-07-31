"""Red-Govern Redshift connection package."""

from red_govern.connections.connection import (
    build_connection_arguments,
    open_connection,
    redshift_connection,
)
from red_govern.connections.session import (
    ConnectionTestResult,
    test_connection,
)

__all__ = [
    "ConnectionTestResult",
    "build_connection_arguments",
    "open_connection",
    "redshift_connection",
    "test_connection",
]
