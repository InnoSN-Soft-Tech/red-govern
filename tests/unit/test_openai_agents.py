"""Contract tests for the optional OpenAI Agents SDK adapter."""

from __future__ import annotations

import ast
import importlib
import importlib.util
import inspect
import json
import sys
import types
from pathlib import Path
from typing import Any

import pytest

from red_govern import __version__
from red_govern.config import write_default_config
from red_govern.exceptions import ConfigurationError

REAL_AGENTS_AVAILABLE = importlib.util.find_spec("agents") is not None

EXPECTED_TOOLS = {
    "red_govern_get_redacted_config",
    "red_govern_get_version",
    "red_govern_run_privacy_audit",
    "red_govern_validate_config",
}


class _FakeRunContextWrapper:
    @classmethod
    def __class_getitem__(cls, _: object) -> type[_FakeRunContextWrapper]:
        return cls


class _FakeFunctionTool:
    def __init__(
        self,
        *,
        name: str,
        description: str,
        params_json_schema: dict[str, Any],
        wrapped: Any,
        strict_json_schema: bool,
    ) -> None:
        self.name = name
        self.description = description
        self.params_json_schema = params_json_schema
        self.__wrapped__ = wrapped
        self.strict_json_schema = strict_json_schema


class _FakeAgent:
    @classmethod
    def __class_getitem__(cls, _: object) -> type[_FakeAgent]:
        return cls

    def __init__(
        self,
        *,
        name: str,
        instructions: str,
        model: str | None,
        tools: list[Any],
    ) -> None:
        self.name = name
        self.instructions = instructions
        self.model = model
        self.tools = tools


def _fake_function_tool(
    *,
    name_override: str | None = None,
    description_override: str | None = None,
    use_docstring_info: bool = True,
    failure_error_function: Any = None,
    strict_mode: bool = True,
) -> Any:
    del use_docstring_info, failure_error_function

    def decorator(function: Any) -> _FakeFunctionTool:
        signature = inspect.signature(function)
        properties: dict[str, Any] = {}
        required: list[str] = []
        for name, parameter in signature.parameters.items():
            schema: dict[str, Any] = {"type": "string"}
            if parameter.default is None:
                schema = {"anyOf": [{"type": "string"}, {"type": "null"}]}
            properties[name] = schema
            if parameter.default is inspect.Parameter.empty:
                required.append(name)
        payload: dict[str, Any] = {
            "type": "object",
            "properties": properties,
            "additionalProperties": False,
        }
        if required:
            payload["required"] = required
        return _FakeFunctionTool(
            name=name_override or function.__name__,
            description=description_override or function.__doc__ or "",
            params_json_schema=payload,
            wrapped=function,
            strict_json_schema=strict_mode,
        )

    return decorator


def _install_fake_agents() -> None:
    if REAL_AGENTS_AVAILABLE or "agents" in sys.modules:
        return
    module = types.ModuleType("agents")
    module.Agent = _FakeAgent
    module.FunctionTool = _FakeFunctionTool
    module.RunContextWrapper = _FakeRunContextWrapper
    module.function_tool = _fake_function_tool
    sys.modules["agents"] = module


def _adapter() -> Any:
    _install_fake_agents()
    return importlib.import_module("red_govern.openai_agents")


def _raw(tool: Any) -> Any:
    wrapped = getattr(tool, "__wrapped__", None)
    assert callable(wrapped)
    return wrapped


def test_agents_dependency_is_optional_and_isolated_from_mcp_extra() -> None:
    """The current SDK must not create an unsatisfiable combined extra."""

    try:
        import tomllib
    except ModuleNotFoundError:  # pragma: no cover - Python 3.10
        import tomli as tomllib

    root = Path(__file__).resolve().parents[2]
    parsed = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    project = parsed["project"]
    optional = project["optional-dependencies"]
    requirement = "openai-agents>=0.19.4,<0.20"

    assert all(not item.startswith("openai-agents") for item in project["dependencies"])
    assert optional["agents"] == [requirement]
    assert requirement not in optional["all"]
    assert requirement not in optional["dev"]
    assert optional["mcp"] == ["mcp>=2.0,<3"]


def test_adapter_exposes_exactly_four_strict_function_tools() -> None:
    """The Agents surface must match the typed API and reject extra arguments."""

    adapter = _adapter()
    tools = adapter.get_openai_agent_tools()

    assert {tool.name for tool in tools} == EXPECTED_TOOLS
    if REAL_AGENTS_AVAILABLE:
        from agents import FunctionTool

        assert all(isinstance(tool, FunctionTool) for tool in tools)
    else:
        assert all(isinstance(tool, _FakeFunctionTool) for tool in tools)
    assert all(tool.strict_json_schema is True for tool in tools)

    schemas = json.dumps([tool.params_json_schema for tool in tools]).lower()
    for forbidden in (
        "password",
        "token",
        "connection_string",
        "endpoint",
        '"sql"',
        '"command"',
    ):
        assert forbidden not in schemas


def test_agent_constructs_without_openai_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    """Construction and inspection must not require credentials or model execution."""

    monkeypatch.delenv("OPENAI_API_KEY", raising=False)
    adapter = _adapter()
    agent = adapter.build_red_govern_agent()

    assert agent.name == adapter.AGENT_NAME
    assert {tool.name for tool in agent.tools} == EXPECTED_TOOLS


def test_agent_accepts_model_name_without_running_it() -> None:
    """Model selection may be configured without invoking the SDK runtime."""

    adapter = _adapter()
    agent = adapter.build_red_govern_agent(model="gpt-5.6")

    assert agent.model == "gpt-5.6"


def test_version_tool_returns_stable_json() -> None:
    """Version metadata should cross the function-tool boundary as JSON."""

    adapter = _adapter()
    payload = json.loads(_raw(adapter.red_govern_get_version)())

    assert payload == {
        "package": "red-govern",
        "version": __version__,
        "platform": "Amazon Redshift",
        "is_alpha": True,
    }


def test_validate_config_tool_does_not_modify_source(tmp_path: Path) -> None:
    """Configuration validation remains a read-only local operation."""

    adapter = _adapter()
    config_path = tmp_path / "red-govern.yml"
    write_default_config(config_path)
    before = config_path.read_bytes()

    payload = json.loads(_raw(adapter.red_govern_validate_config)(str(config_path)))

    assert payload["valid"] is True
    assert payload["config_version"] == 1
    assert config_path.read_bytes() == before


def test_configuration_and_generic_errors_are_model_safe() -> None:
    """Failure handling must not echo exception text to a model."""

    adapter = _adapter()
    secret = "agents-super-secret-value"

    config_error = json.loads(
        adapter._safe_tool_error(None, ConfigurationError(f"password={secret}"))
    )
    generic_error = json.loads(adapter._safe_tool_error(None, RuntimeError(secret)))

    assert config_error["error"] == "configuration_error"
    assert generic_error["error"] == "internal_error"
    assert secret not in json.dumps(config_error)
    assert secret not in json.dumps(generic_error)
    assert "password" not in json.dumps(config_error).lower()


def test_redacted_config_tool_hides_sensitive_metadata(tmp_path: Path) -> None:
    """Endpoint, identity, and local path values must stay outside tool output."""

    adapter = _adapter()
    config_path = tmp_path / "red-govern.yml"
    write_default_config(config_path)
    content = config_path.read_text(encoding="utf-8")
    content = content.replace("    host: null\n", "    host: private.agents.internal\n")
    content = content.replace("    user: null\n", "    user: private_agents_user\n")
    config_path.write_text(content, encoding="utf-8")

    payload = json.loads(_raw(adapter.red_govern_get_redacted_config)(str(config_path)))
    serialized = json.dumps(payload)

    assert "private.agents.internal" not in serialized
    assert "private_agents_user" not in serialized
    assert str(Path.home()) not in serialized
    assert "***REDACTED***" in serialized


def test_privacy_audit_tool_returns_safe_findings(tmp_path: Path) -> None:
    """Privacy findings should remain structured and sanitized."""

    adapter = _adapter()
    config_path = tmp_path / "red-govern.yml"
    write_default_config(config_path)

    payload = json.loads(_raw(adapter.red_govern_run_privacy_audit)(str(config_path)))
    serialized = json.dumps(payload)

    assert payload["passed"] is True
    assert payload["warning_count"] == 0
    assert payload["critical_count"] == 0
    assert len(payload["findings"]) == 11
    assert "RED_GOVERN_REDSHIFT_PASSWORD" not in serialized
    assert str(Path.home()) not in serialized


def test_agent_instructions_preserve_safety_boundaries() -> None:
    """Agent instructions must not expand Red-Govern authority."""

    adapter = _adapter()
    instructions = adapter.AGENT_INSTRUCTIONS

    for required in (
        "Never request passwords",
        "do not connect to Amazon Redshift",
        "execute SQL",
        "write files",
        "safe to delete",
        "destructive remediation",
        "rather than inventing commands or capabilities",
    ):
        assert required in instructions


def test_adapter_source_has_no_runner_hosted_mcp_or_redshift_runtime() -> None:
    """The adapter must remain a thin function-tool construction layer."""

    adapter = _adapter()
    module_path = Path(adapter.__file__)
    text = module_path.read_text(encoding="utf-8")
    tree = ast.parse(text)
    imported_roots: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])

    assert "agents" in imported_roots
    assert "red_govern" in imported_roots
    assert imported_roots.isdisjoint(
        {"fastapi", "mcp", "openai", "redshift_connector", "rich", "typer", "uvicorn"}
    )

    for forbidden in (
        "Runner",
        "AsyncOpenAI",
        "HostedMCPTool",
        "WebSearchTool",
        "FileSearchTool",
        "ComputerTool",
        "ShellTool",
        "MCPServer",
    ):
        assert forbidden not in text
