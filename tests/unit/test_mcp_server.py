"""Contract tests for the local, offline-safe stdio MCP adapter."""

from __future__ import annotations

import ast
import asyncio
import json
from pathlib import Path
from typing import Any

import pytest
from mcp import Client

import red_govern.mcp_server as mcp_server
from red_govern import __version__
from red_govern.config import write_default_config

EXPECTED_TOOLS = {
    "red_govern_get_redacted_config",
    "red_govern_get_version",
    "red_govern_run_privacy_audit",
    "red_govern_validate_config",
}


def _text_content(result: Any) -> str:
    return "\n".join(
        text
        for item in result.content
        if isinstance((text := getattr(item, "text", None)), str)
    )


def test_mcp_dependency_is_optional_and_entry_point_is_registered() -> None:
    """MCP must not become a mandatory dependency of the base CLI package."""

    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python 3.10
        import tomli as tomllib

    root = Path(__file__).resolve().parents[2]
    parsed = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    project = parsed["project"]
    optional = project["optional-dependencies"]

    assert all(not item.startswith("mcp") for item in project["dependencies"])
    assert optional["mcp"] == ["mcp>=2.0,<3"]
    assert "mcp>=2.0,<3" in optional["all"]
    assert "mcp>=2.0,<3" in optional["dev"]
    assert project["scripts"]["red-govern-mcp"] == "red_govern.mcp_server:main"


def test_server_identity_and_instructions_preserve_safety_boundaries() -> None:
    """Server metadata should state the local and non-destructive boundary."""

    assert mcp_server.mcp.name == "red-govern"
    assert mcp_server.mcp.title == "Red-Govern"
    assert mcp_server.mcp.version == __version__

    instructions = mcp_server.mcp.instructions or ""

    for required in (
        "does not connect to Amazon Redshift",
        "execute SQL",
        "write files",
        "safe to delete",
        "destructive remediation",
    ):
        assert required in instructions


def test_server_lists_exactly_four_offline_safe_tools() -> None:
    """The first MCP surface must match the typed API exactly."""

    async def scenario() -> None:
        async with Client(mcp_server.mcp) as client:
            response = await client.session.list_tools()

        assert {tool.name for tool in response.tools} == EXPECTED_TOOLS
        assert all(tool.output_schema is not None for tool in response.tools)

    asyncio.run(scenario())


def test_version_tool_returns_structured_package_metadata() -> None:
    """Version data should cross the MCP boundary as structured output."""

    async def scenario() -> None:
        async with Client(mcp_server.mcp) as client:
            result = await client.call_tool("red_govern_get_version")

        assert result.is_error is False
        assert result.structured_content == {
            "package": "red-govern",
            "version": __version__,
            "platform": "Amazon Redshift",
            "is_alpha": True,
        }

    asyncio.run(scenario())


def test_validate_config_tool_accepts_safe_generated_configuration(
    tmp_path: Path,
) -> None:
    """A local generated configuration should validate without mutation."""

    config_path = tmp_path / "red-govern.yml"
    write_default_config(config_path)
    before = config_path.read_bytes()

    async def scenario() -> None:
        async with Client(mcp_server.mcp) as client:
            result = await client.call_tool(
                "red_govern_validate_config",
                {"path": str(config_path)},
            )

        assert result.is_error is False
        assert result.structured_content == {
            "valid": True,
            "config_version": 1,
            "source": str(config_path),
        }

    asyncio.run(scenario())
    assert config_path.read_bytes() == before


def test_validate_config_tool_sanitizes_errors(tmp_path: Path) -> None:
    """Invalid values must not be echoed into an MCP error result."""

    config_path = tmp_path / "invalid.yml"
    config_path.write_text(
        """
config_version: 1
redshift:
  connection:
    password: mcp-super-secret-value
""",
        encoding="utf-8",
    )

    async def scenario() -> None:
        async with Client(mcp_server.mcp) as client:
            result = await client.call_tool(
                "red_govern_validate_config",
                {"path": str(config_path)},
            )

        message = _text_content(result)

        assert result.is_error is True
        assert "Configuration validation failed" in message
        assert "mcp-super-secret-value" not in message
        assert "password" not in message.lower()

    asyncio.run(scenario())


def test_redacted_config_tool_hides_sensitive_metadata(tmp_path: Path) -> None:
    """Endpoint, identity, and path values must remain outside MCP output."""

    config_path = tmp_path / "red-govern.yml"
    write_default_config(config_path)
    content = config_path.read_text(encoding="utf-8")
    content = content.replace("    host: null\n", "    host: private.mcp.internal\n")
    content = content.replace("    user: null\n", "    user: private_mcp_user\n")
    config_path.write_text(content, encoding="utf-8")
    before = config_path.read_bytes()

    async def scenario() -> None:
        async with Client(mcp_server.mcp) as client:
            result = await client.call_tool(
                "red_govern_get_redacted_config",
                {"path": str(config_path)},
            )

        assert result.is_error is False
        assert result.structured_content is not None
        serialized = json.dumps(result.structured_content)

        assert "private.mcp.internal" not in serialized
        assert "private_mcp_user" not in serialized
        assert str(Path.home()) not in serialized
        assert "***REDACTED***" in serialized

    asyncio.run(scenario())
    assert config_path.read_bytes() == before


def test_privacy_audit_tool_returns_structured_safe_findings(
    tmp_path: Path,
) -> None:
    """Privacy findings should be structured without exposing env-var names."""

    config_path = tmp_path / "red-govern.yml"
    write_default_config(config_path)

    async def scenario() -> None:
        async with Client(mcp_server.mcp) as client:
            result = await client.call_tool(
                "red_govern_run_privacy_audit",
                {"path": str(config_path)},
            )

        assert result.is_error is False
        assert result.structured_content is not None
        payload = result.structured_content
        serialized = json.dumps(payload)

        assert payload["passed"] is True
        assert payload["warning_count"] == 0
        assert payload["critical_count"] == 0
        assert len(payload["findings"]) == 11
        assert "RED_GOVERN_REDSHIFT_PASSWORD" not in serialized
        assert str(Path.home()) not in serialized

    asyncio.run(scenario())


def test_server_exposes_no_resources_or_prompts() -> None:
    """Step 47.1B should expose tools only, with no broader MCP surface."""

    async def scenario() -> None:
        async with Client(mcp_server.mcp) as client:
            resources = await client.session.list_resources()
            templates = await client.session.list_resource_templates()
            prompts = await client.session.list_prompts()

        assert resources.resources == []
        assert templates.resource_templates == []
        assert prompts.prompts == []

    asyncio.run(scenario())


def test_main_runs_explicit_stdio_transport(monkeypatch: pytest.MonkeyPatch) -> None:
    """The console entry point must not start HTTP, SSE, or a hosted service."""

    transports: list[str] = []

    def fake_run(transport: str = "stdio", **_: Any) -> None:
        transports.append(transport)

    monkeypatch.setattr(mcp_server.mcp, "run", fake_run)

    mcp_server.main()

    assert transports == ["stdio"]


def test_mcp_module_has_no_cli_redshift_or_hosted_runtime_imports() -> None:
    """The adapter must remain thin and presentation-independent."""

    module_path = Path(mcp_server.__file__)
    text = module_path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    imported_roots: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(
                alias.name.split(".", 1)[0]
                for alias in node.names
            )
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert "mcp" in imported_roots
    assert imported_roots.isdisjoint(
        {"fastapi", "openai", "redshift_connector", "rich", "typer", "uvicorn"}
    )
    assert "streamable-http" not in text
    assert "run_sse" not in text
    assert "run_streamable_http" not in text
