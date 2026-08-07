"""Optional OpenAI Agents SDK adapter over Red-Govern's offline-safe API.

The adapter exposes four local function tools and an Agent construction helper.
Importing or constructing the adapter does not run a model. It does not connect
to Amazon Redshift, execute SQL, write files, start a server, or require an OpenAI
API key.
"""

from __future__ import annotations

import json
from typing import Any

from agents import Agent, FunctionTool, RunContextWrapper, function_tool

import red_govern.api as api
from red_govern.exceptions import ConfigurationError

AGENT_NAME = "Red-Govern — Redshift Governance Advisor"
AGENT_INSTRUCTIONS = (
    "Use only the four supplied Red-Govern offline-safe function tools. "
    "Never request passwords, tokens, private endpoints, connection strings, "
    "or unredacted production outputs. These tools do not connect to Amazon "
    "Redshift, execute SQL, write files, prove that an object is safe to delete, "
    "or perform destructive remediation. For operational workflows outside this "
    "surface, explain the boundary and direct the developer to version-matched "
    "Red-Govern documentation rather than inventing commands or capabilities."
)


def _serialize(result: api.ApiResult) -> str:
    """Serialize one typed API result as compact JSON for a function tool."""

    return result.model_dump_json()


def _safe_tool_error(
    _: RunContextWrapper[Any],
    error: Exception,
) -> str:
    """Return a stable model-visible error without echoing exception details."""

    if isinstance(error, ConfigurationError):
        payload = {
            "ok": False,
            "error": "configuration_error",
            "message": (
                "Red-Govern configuration validation failed. "
                "Review the local configuration file directly."
            ),
        }
    else:
        payload = {
            "ok": False,
            "error": "internal_error",
            "message": "Red-Govern tool execution failed safely.",
        }

    return json.dumps(payload, separators=(",", ":"), sort_keys=True)


@function_tool(
    name_override="red_govern_get_version",
    description_override=(
        "Return installed Red-Govern package metadata without connecting to Amazon Redshift."
    ),
    use_docstring_info=False,
    failure_error_function=_safe_tool_error,
    strict_mode=True,
)
def red_govern_get_version() -> str:
    """Return version metadata through the typed API."""

    return _serialize(api.get_version())


@function_tool(
    name_override="red_govern_validate_config",
    description_override=(
        "Validate one local Red-Govern YAML configuration and return a sanitized result."
    ),
    use_docstring_info=False,
    failure_error_function=_safe_tool_error,
    strict_mode=True,
)
def red_govern_validate_config(path: str = "red-govern.yml") -> str:
    """Validate one local configuration without modifying it."""

    return _serialize(api.validate_config(path))


@function_tool(
    name_override="red_govern_get_redacted_config",
    description_override=(
        "Return packaged defaults or one local Red-Govern configuration with "
        "sensitive metadata redacted."
    ),
    use_docstring_info=False,
    failure_error_function=_safe_tool_error,
    strict_mode=True,
)
def red_govern_get_redacted_config(path: str | None = None) -> str:
    """Return effective configuration safe for an agent workflow."""

    return _serialize(api.get_redacted_config(path))


@function_tool(
    name_override="red_govern_run_privacy_audit",
    description_override=(
        "Run the local Red-Govern privacy audit and return sanitized structured findings."
    ),
    use_docstring_info=False,
    failure_error_function=_safe_tool_error,
    strict_mode=True,
)
def red_govern_run_privacy_audit(path: str = "red-govern.yml") -> str:
    """Return structured privacy findings through the typed API."""

    return _serialize(api.run_privacy_audit(path))


def get_openai_agent_tools() -> list[FunctionTool]:
    """Return the exact four offline-safe Red-Govern function tools."""

    return [
        red_govern_get_version,
        red_govern_validate_config,
        red_govern_get_redacted_config,
        red_govern_run_privacy_audit,
    ]


def build_red_govern_agent(*, model: str | None = None) -> Agent[None]:
    """Construct the Red-Govern Agent without executing a model run."""

    return Agent[None](
        name=AGENT_NAME,
        instructions=AGENT_INSTRUCTIONS,
        model=model,
        tools=[
            red_govern_get_version,
            red_govern_validate_config,
            red_govern_get_redacted_config,
            red_govern_run_privacy_audit,
        ],
    )


__all__ = [
    "build_red_govern_agent",
    "get_openai_agent_tools",
    "red_govern_get_redacted_config",
    "red_govern_get_version",
    "red_govern_run_privacy_audit",
    "red_govern_validate_config",
]
