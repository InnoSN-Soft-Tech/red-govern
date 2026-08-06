"""Local stdio MCP adapter for Red-Govern's offline-safe typed API.

The adapter exposes structured configuration and privacy tools. It does not
connect to Amazon Redshift, execute SQL, or write files. It never accepts
credentials, private endpoints, connection strings, or destructive actions.
"""

from __future__ import annotations

from mcp.server import MCPServer

import red_govern.api as api
from red_govern import __version__

SERVER_NAME = "red-govern"
SERVER_TITLE = "Red-Govern"
SERVER_DESCRIPTION = (
    "Local, offline-safe Model Context Protocol tools for Red-Govern "
    "configuration and privacy inspection."
)
SERVER_INSTRUCTIONS = (
    "Use only the four published offline-safe tools. Keep credentials and "
    "unredacted production outputs outside the MCP conversation. This server "
    "does not connect to Amazon Redshift, execute SQL, write files, prove that "
    "objects are safe to delete, or perform destructive remediation."
)

mcp = MCPServer(
    name=SERVER_NAME,
    title=SERVER_TITLE,
    description=SERVER_DESCRIPTION,
    instructions=SERVER_INSTRUCTIONS,
    version=__version__,
)


@mcp.tool(
    name="red_govern_get_version",
    title="Get Red-Govern version",
    description=(
        "Return the installed Red-Govern package version and supported platform "
        "without connecting to Amazon Redshift."
    ),
    structured_output=True,
)
def red_govern_get_version() -> api.VersionResult:
    """Return installed package metadata without side effects."""

    return api.get_version()


@mcp.tool(
    name="red_govern_validate_config",
    title="Validate Red-Govern configuration",
    description=(
        "Validate one local Red-Govern YAML file and return a sanitized result. "
        "The file is read but never modified."
    ),
    structured_output=True,
)
def red_govern_validate_config(
    path: str = "red-govern.yml",
) -> api.ConfigValidationResult:
    """Validate one local configuration through the typed API."""

    return api.validate_config(path)


@mcp.tool(
    name="red_govern_get_redacted_config",
    title="Get redacted Red-Govern configuration",
    description=(
        "Return packaged defaults or one local configuration with credentials, "
        "Redshift identities, endpoints, and local paths redacted."
    ),
    structured_output=True,
)
def red_govern_get_redacted_config(
    path: str | None = None,
) -> api.RedactedConfigResult:
    """Return effective configuration safe for an MCP client."""

    return api.get_redacted_config(path)


@mcp.tool(
    name="red_govern_run_privacy_audit",
    title="Run Red-Govern privacy audit",
    description=(
        "Run the local privacy and safety configuration audit and return "
        "structured, sanitized findings without a Redshift connection."
    ),
    structured_output=True,
)
def red_govern_run_privacy_audit(
    path: str = "red-govern.yml",
) -> api.PrivacyAuditApiResult:
    """Return structured privacy findings through the typed API."""

    return api.run_privacy_audit(path)


def main() -> None:
    """Run only the local stdio MCP transport."""

    mcp.run("stdio")


__all__ = ["main", "mcp"]


if __name__ == "__main__":
    main()
