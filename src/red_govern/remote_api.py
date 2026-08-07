"""Read-only ASGI runtime for Red-Govern public metadata."""

from __future__ import annotations

import json
from functools import lru_cache
from importlib.resources import files
from typing import Any, Literal, cast

from fastapi import FastAPI
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict

PACKAGE_VERSION = "0.1.0a3"
ProblemStatus = Literal["supported", "conditional", "unsupported"]

_DOCUMENTATION = "https://innosn-soft-tech.github.io/red-govern/"
_REPOSITORY = "https://github.com/InnoSN-Soft-Tech/red-govern"
_PYPI = "https://pypi.org/project/red-govern/"

_DETAIL_FIELDS = (
    "id",
    "title",
    "status",
    "summary",
    "user_intents",
    "commands",
    "workflow",
    "prerequisites",
    "outputs",
    "caveats",
    "agent_guidance",
    "manual_alternative",
)
_SUMMARY_FIELDS = ("id", "title", "status", "summary", "commands")


class _StrictModel(BaseModel):
    """Forbid accidental response-surface expansion."""

    model_config = ConfigDict(extra="forbid")


class StatusCounts(_StrictModel):
    """Canonical problem counts by support status."""

    supported: int
    conditional: int
    unsupported: int


class SafetyBoundaries(_StrictModel):
    """Fixed safety boundaries for the public metadata runtime."""

    accepts_credentials: Literal[False] = False
    accepts_local_configuration: Literal[False] = False
    remote_redshift_runtime: Literal[False] = False
    executes_sql: Literal[False] = False
    executes_commands: Literal[False] = False
    destructive_remediation: Literal[False] = False
    safe_to_delete_proof: Literal[False] = False


class MetadataResponse(_StrictModel):
    """Versioned Red-Govern public metadata."""

    package: Literal["red-govern"] = "red-govern"
    package_version: str
    platform: Literal["Amazon Redshift"] = "Amazon Redshift"
    project_status: Literal["alpha"] = "alpha"
    documentation: str
    repository: str
    pypi: str
    problem_count: int
    status_counts: StatusCounts
    allowed_command_count: int
    safety: SafetyBoundaries


class ProblemSummary(_StrictModel):
    """Public summary for one canonical Red-Govern problem."""

    id: str
    title: str
    status: ProblemStatus
    summary: str
    commands: list[str]


class ProblemDetail(_StrictModel):
    """Full public canonical problem contract."""

    id: str
    title: str
    status: ProblemStatus
    summary: str
    user_intents: list[str]
    commands: list[str]
    workflow: list[str]
    prerequisites: list[str]
    outputs: list[str]
    caveats: list[str]
    agent_guidance: str
    manual_alternative: str


class ProblemListResponse(_StrictModel):
    """Versioned problem-list response."""

    package_version: str
    count: int
    problems: list[ProblemSummary]


class CommandListResponse(_StrictModel):
    """Versioned canonical command allowlist response."""

    package_version: str
    count: int
    commands: list[str]


class ErrorResponse(_StrictModel):
    """Stable not-found response."""

    error: Literal["not_found"] = "not_found"
    message: str


@lru_cache(maxsize=1)
def _load_problem_map() -> dict[str, Any]:
    """Load and minimally validate the packaged canonical problem map."""
    resource = files("red_govern.resources").joinpath(
        "problem-command-map.json"
    )
    parsed: object = json.loads(resource.read_text(encoding="utf-8"))

    if not isinstance(parsed, dict):
        raise RuntimeError("Packaged problem map must be a JSON object.")

    mapping = cast(dict[str, Any], parsed)

    if mapping.get("generated_for_package_version") != PACKAGE_VERSION:
        raise RuntimeError("Packaged problem map version differs.")

    problems = mapping.get("problems")
    commands = mapping.get("allowed_commands")

    if not isinstance(problems, list) or len(problems) != 21:
        raise RuntimeError("Packaged problem map must contain 21 problems.")

    if not isinstance(commands, list) or len(commands) != 14:
        raise RuntimeError("Packaged problem map must contain 14 commands.")

    return mapping


def _problem_rows() -> list[dict[str, Any]]:
    """Return canonical problem objects."""
    raw = _load_problem_map().get("problems")

    if not isinstance(raw, list) or not all(
        isinstance(item, dict) for item in raw
    ):
        raise RuntimeError("Packaged problem entries are invalid.")

    return cast(list[dict[str, Any]], raw)


def _commands() -> list[str]:
    """Return the canonical command allowlist."""
    raw = _load_problem_map().get("allowed_commands")

    if not isinstance(raw, list) or not all(
        isinstance(item, str) and item for item in raw
    ):
        raise RuntimeError("Packaged allowed_commands is invalid.")

    return cast(list[str], raw)


def _status_counts() -> StatusCounts:
    """Calculate canonical support-status counts."""
    problems = _problem_rows()
    return StatusCounts(
        supported=sum(
            1 for item in problems if item.get("status") == "supported"
        ),
        conditional=sum(
            1 for item in problems if item.get("status") == "conditional"
        ),
        unsupported=sum(
            1 for item in problems if item.get("status") == "unsupported"
        ),
    )


def _problem_summary(raw: dict[str, Any]) -> ProblemSummary:
    """Validate and project one canonical problem summary."""
    projected = {field: raw[field] for field in _SUMMARY_FIELDS}
    return ProblemSummary.model_validate(projected)


def _problem_detail(raw: dict[str, Any]) -> ProblemDetail:
    """Validate and project one canonical problem detail."""
    projected = {field: raw[field] for field in _DETAIL_FIELDS}
    return ProblemDetail.model_validate(projected)


app = FastAPI(
    title="Red-Govern Remote Metadata API",
    version=PACKAGE_VERSION,
    description=(
        "Read-only public Red-Govern metadata. This runtime does not connect "
        "to Amazon Redshift, execute SQL or commands, accept credentials, or "
        "accept local configuration."
    ),
    docs_url=None,
    redoc_url=None,
    openapi_url=None,
)


@app.get(
    "/v1/meta",
    response_model=MetadataResponse,
    operation_id="getRedGovernMetadata",
)
def get_metadata() -> MetadataResponse:
    """Return versioned public package metadata and safety boundaries."""
    problems = _problem_rows()
    commands = _commands()

    return MetadataResponse(
        package_version=PACKAGE_VERSION,
        documentation=_DOCUMENTATION,
        repository=_REPOSITORY,
        pypi=_PYPI,
        problem_count=len(problems),
        status_counts=_status_counts(),
        allowed_command_count=len(commands),
        safety=SafetyBoundaries(),
    )


@app.get(
    "/v1/problems",
    response_model=ProblemListResponse,
    operation_id="listRedGovernProblems",
)
def list_problems(
    status: ProblemStatus | None = None,
) -> ProblemListResponse:
    """List canonical problem summaries, optionally filtered by status."""
    rows = _problem_rows()

    if status is not None:
        rows = [item for item in rows if item.get("status") == status]

    problems = [_problem_summary(item) for item in rows]
    return ProblemListResponse(
        package_version=PACKAGE_VERSION,
        count=len(problems),
        problems=problems,
    )


@app.get(
    "/v1/problems/{problem_id}",
    response_model=ProblemDetail,
    responses={404: {"model": ErrorResponse}},
    operation_id="getRedGovernProblem",
)
def get_problem(
    problem_id: str,
) -> ProblemDetail | JSONResponse:
    """Return one canonical problem contract or a stable 404 response."""
    for item in _problem_rows():
        if item.get("id") == problem_id:
            return _problem_detail(item)

    error = ErrorResponse(
        message=f"Unknown Red-Govern problem id: {problem_id}"
    )
    return JSONResponse(
        status_code=404,
        content=error.model_dump(mode="json"),
    )


@app.get(
    "/v1/commands",
    response_model=CommandListResponse,
    operation_id="listRedGovernCommands",
)
def list_commands() -> CommandListResponse:
    """Return the canonical command allowlist without executing commands."""
    commands = _commands()
    return CommandListResponse(
        package_version=PACKAGE_VERSION,
        count=len(commands),
        commands=commands,
    )
