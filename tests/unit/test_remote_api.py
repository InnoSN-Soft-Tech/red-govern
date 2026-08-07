"""Integration tests for the read-only remote metadata ASGI runtime."""

from __future__ import annotations

import ast
import json
import socket
from pathlib import Path
from typing import Any, cast

from fastapi.routing import APIRoute
from fastapi.testclient import TestClient

from red_govern.remote_api import app

ROOT = Path(__file__).resolve().parents[2]
MAP_PATH = ROOT / "docs" / "problems" / "problem-command-map.json"
RESOURCE_MAP_PATH = (
    ROOT
    / "src"
    / "red_govern"
    / "resources"
    / "problem-command-map.json"
)
SOURCE_PATH = ROOT / "src" / "red_govern" / "remote_api.py"


def load_map() -> dict[str, Any]:
    parsed: object = json.loads(MAP_PATH.read_text(encoding="utf-8"))
    assert isinstance(parsed, dict)
    return cast(dict[str, Any], parsed)


def client() -> TestClient:
    return TestClient(app)


def test_runtime_exposes_exactly_four_get_routes() -> None:
    routes = {
        route.path: set(route.methods or set())
        for route in app.routes
        if isinstance(route, APIRoute)
    }

    assert routes == {
        "/v1/meta": {"GET"},
        "/v1/problems": {"GET"},
        "/v1/problems/{problem_id}": {"GET"},
        "/v1/commands": {"GET"},
    }

    assert app.docs_url is None
    assert app.redoc_url is None
    assert app.openapi_url is None


def test_metadata_response_matches_canonical_counts_and_boundaries() -> None:
    mapping = load_map()
    problems = cast(list[dict[str, Any]], mapping["problems"])

    response = client().get("/v1/meta")

    assert response.status_code == 200
    data = response.json()

    assert data["package"] == "red-govern"
    assert data["package_version"] == "0.1.0a3"
    assert data["platform"] == "Amazon Redshift"
    assert data["project_status"] == "alpha"
    assert data["problem_count"] == len(problems)
    assert data["allowed_command_count"] == len(mapping["allowed_commands"])
    assert data["status_counts"] == {
        status: sum(1 for item in problems if item["status"] == status)
        for status in ("supported", "conditional", "unsupported")
    }
    assert data["safety"] == {
        "accepts_credentials": False,
        "accepts_local_configuration": False,
        "remote_redshift_runtime": False,
        "executes_sql": False,
        "executes_commands": False,
        "destructive_remediation": False,
        "safe_to_delete_proof": False,
    }


def test_problem_list_matches_all_canonical_problem_summaries() -> None:
    mapping = load_map()
    canonical = cast(list[dict[str, Any]], mapping["problems"])

    response = client().get("/v1/problems")

    assert response.status_code == 200
    data = response.json()
    assert data["package_version"] == "0.1.0a3"
    assert data["count"] == 21

    expected = [
        {
            key: item[key]
            for key in ("id", "title", "status", "summary", "commands")
        }
        for item in canonical
    ]
    assert data["problems"] == expected


def test_problem_list_status_filter_matches_canonical_counts() -> None:
    mapping = load_map()
    canonical = cast(list[dict[str, Any]], mapping["problems"])

    for status in ("supported", "conditional", "unsupported"):
        response = client().get(
            "/v1/problems",
            params={"status": status},
        )

        assert response.status_code == 200
        data = response.json()
        expected = [item for item in canonical if item["status"] == status]

        assert data["count"] == len(expected)
        assert all(item["status"] == status for item in data["problems"])


def test_invalid_problem_status_is_rejected_without_execution() -> None:
    response = client().get(
        "/v1/problems",
        params={"status": "delete-everything"},
    )

    assert response.status_code == 422


def test_problem_detail_matches_canonical_problem_contract() -> None:
    mapping = load_map()
    canonical = cast(list[dict[str, Any]], mapping["problems"])
    expected = canonical[0]

    response = client().get(f"/v1/problems/{expected['id']}")

    assert response.status_code == 200
    assert response.json() == {
        key: expected[key]
        for key in (
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
    }


def test_unknown_problem_returns_stable_404() -> None:
    response = client().get("/v1/problems/not-a-real-problem")

    assert response.status_code == 404
    assert response.json() == {
        "error": "not_found",
        "message": "Unknown Red-Govern problem id: not-a-real-problem",
    }


def test_command_list_matches_canonical_allowlist_without_execution() -> None:
    mapping = load_map()

    response = client().get("/v1/commands")

    assert response.status_code == 200
    assert response.json() == {
        "package_version": "0.1.0a3",
        "count": 14,
        "commands": mapping["allowed_commands"],
    }


def test_non_get_methods_are_not_exposed() -> None:
    test_client = client()

    assert test_client.post("/v1/meta").status_code == 405
    assert test_client.put("/v1/problems").status_code == 405
    assert test_client.delete("/v1/commands").status_code == 405


def test_packaged_problem_map_mirrors_canonical_map_byte_for_byte() -> None:
    assert RESOURCE_MAP_PATH.read_bytes() == MAP_PATH.read_bytes()


def test_runtime_source_has_no_redshift_sql_or_process_runtime_imports() -> None:
    tree = ast.parse(SOURCE_PATH.read_text(encoding="utf-8"))
    imports: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])

    forbidden = {
        "boto3",
        "keyring",
        "mcp",
        "openai",
        "redshift_connector",
        "subprocess",
    }
    assert not (imports & forbidden)

    source = SOURCE_PATH.read_text(encoding="utf-8")
    for forbidden_text in (
        "execute(",
        "cursor(",
        "subprocess.",
        "os.system",
        "eval(",
        "exec(",
    ):
        assert forbidden_text not in source


def test_runtime_requests_make_no_outbound_socket_connections(
    monkeypatch: Any,
) -> None:
    attempts: list[str] = []

    def blocked(*args: Any, **kwargs: Any) -> Any:
        attempts.append("socket")
        raise AssertionError("Outbound socket access attempted")

    monkeypatch.setattr(socket, "create_connection", blocked)
    monkeypatch.setattr(socket.socket, "connect", blocked)
    monkeypatch.setattr(socket.socket, "connect_ex", blocked)

    test_client = client()

    assert test_client.get("/v1/meta").status_code == 200
    assert test_client.get("/v1/problems").status_code == 200
    assert test_client.get("/v1/commands").status_code == 200

    assert attempts == []
