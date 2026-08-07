"""Contract tests for the read-only remote metadata API definition."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]
CONTRACT_PATH = ROOT / "docs" / "agents" / "remote-metadata-contract.json"
OPENAPI_PATH = ROOT / "docs" / "agents" / "red-govern-metadata.openapi.json"
MAP_PATH = ROOT / "docs" / "problems" / "problem-command-map.json"
GPT_CONFIG_PATH = ROOT / "gpt" / "red-govern-advisor" / "config.json"
PRIVACY_PATH = ROOT / "PRIVACY.md"

EXPECTED_PATHS = {
    "/v1/meta": "getRedGovernMetadata",
    "/v1/problems": "listRedGovernProblems",
    "/v1/problems/{problem_id}": "getRedGovernProblem",
    "/v1/commands": "listRedGovernCommands",
}


def load(path: Path) -> dict[str, Any]:
    parsed: object = json.loads(path.read_text(encoding="utf-8"))
    assert isinstance(parsed, dict)
    return cast(dict[str, Any], parsed)


def test_contract_is_versioned_runtime_implemented_and_not_deployed() -> None:
    contract = load(CONTRACT_PATH)

    assert contract["schema_version"] == "1.0"
    assert contract["package_version"] == "0.1.0a3"
    assert contract["deployment_status"] == "runtime-implemented-not-deployed"
    assert contract["runtime_module"] == "red_govern.remote_api:app"
    assert contract["current_custom_gpt_actions_enabled"] is False
    assert contract["next_step"] == "47.2D"


def test_openapi_surface_is_exactly_four_get_operations() -> None:
    spec = load(OPENAPI_PATH)
    paths = cast(dict[str, Any], spec["paths"])

    assert spec["openapi"] == "3.1.0"
    assert spec["x-red-govern-deployment-status"] == (
        "runtime-implemented-not-deployed"
    )
    assert spec["x-red-govern-runtime"] == "red_govern.remote_api:app"
    assert set(paths) == set(EXPECTED_PATHS)

    observed: dict[str, str] = {}
    for path, item in paths.items():
        assert isinstance(item, dict)
        methods = {
            key
            for key in item
            if key in {"get", "post", "put", "patch", "delete"}
        }
        assert methods == {"get"}
        operation = cast(dict[str, Any], item["get"])
        observed[path] = cast(str, operation["operationId"])
        assert "requestBody" not in operation
        assert operation["security"] == []

    assert observed == EXPECTED_PATHS


def test_openapi_uses_planned_https_server_and_no_authentication() -> None:
    spec = load(OPENAPI_PATH)

    assert spec["servers"] == [
        {
            "url": "https://api.snsoft.tech/red-govern",
            "description": "Planned endpoint; runtime implemented, not deployed",
        }
    ]
    assert spec["security"] == []
    components = cast(dict[str, Any], spec["components"])
    assert "securitySchemes" not in components


def test_request_parameters_are_public_metadata_selectors_only() -> None:
    spec = load(OPENAPI_PATH)
    paths = cast(dict[str, Any], spec["paths"])

    meta = cast(
        dict[str, Any],
        cast(dict[str, Any], paths["/v1/meta"])["get"],
    )
    commands = cast(
        dict[str, Any],
        cast(dict[str, Any], paths["/v1/commands"])["get"],
    )
    problems = cast(
        dict[str, Any],
        cast(dict[str, Any], paths["/v1/problems"])["get"],
    )
    detail = cast(
        dict[str, Any],
        cast(dict[str, Any], paths["/v1/problems/{problem_id}"])["get"],
    )

    assert meta.get("parameters", []) == []
    assert commands.get("parameters", []) == []

    problem_params = cast(list[dict[str, Any]], problems["parameters"])
    assert [item["name"] for item in problem_params] == ["status"]
    assert problem_params[0]["required"] is False
    assert cast(dict[str, Any], problem_params[0]["schema"])["enum"] == [
        "supported",
        "conditional",
        "unsupported",
    ]

    detail_params = cast(list[dict[str, Any]], detail["parameters"])
    assert [item["name"] for item in detail_params] == ["problem_id"]
    assert detail_params[0]["required"] is True


def test_contract_explicitly_excludes_local_file_operations() -> None:
    contract = load(CONTRACT_PATH)

    assert contract["accepts_credentials"] is False
    assert contract["accepts_local_configuration"] is False
    assert contract["remote_redshift_runtime"] is False
    assert contract["excluded_local_operations"] == [
        "validate_config(path)",
        "get_redacted_config(path=<local file>)",
        "run_privacy_audit(path)",
    ]


def test_contract_counts_match_canonical_problem_map() -> None:
    contract = load(CONTRACT_PATH)
    mapping = load(MAP_PATH)
    problems = cast(list[dict[str, Any]], mapping["problems"])

    counts = {
        status: sum(1 for item in problems if item["status"] == status)
        for status in ("supported", "conditional", "unsupported")
    }

    assert contract["status_counts"] == counts
    assert contract["allowed_command_count"] == len(mapping["allowed_commands"])


def test_metadata_example_matches_canonical_counts() -> None:
    spec = load(OPENAPI_PATH)
    mapping = load(MAP_PATH)
    components = cast(dict[str, Any], spec["components"])
    schemas = cast(dict[str, Any], components["schemas"])
    metadata = cast(dict[str, Any], schemas["MetadataResponse"])
    example = cast(dict[str, Any], metadata["example"])

    problems = cast(list[dict[str, Any]], mapping["problems"])
    counts = {
        status: sum(1 for item in problems if item["status"] == status)
        for status in ("supported", "conditional", "unsupported")
    }

    assert example["package_version"] == "0.1.0a3"
    assert example["status_counts"] == counts
    assert example["allowed_command_count"] == len(mapping["allowed_commands"])


def test_privacy_notice_is_nonempty_and_runtime_specific() -> None:
    text = PRIVACY_PATH.read_text(encoding="utf-8")

    assert text.strip()
    assert "remote metadata API runtime is implemented" in text
    assert "hosted endpoint is not deployed" in text
    assert "does not connect to Amazon Redshift" in text
    assert "does not execute SQL" in text
    assert "does not accept local Red-Govern configuration files" in text


def test_custom_gpt_actions_remain_disabled() -> None:
    config = load(GPT_CONFIG_PATH)

    capabilities = cast(dict[str, Any], config["capabilities"])
    actions = cast(dict[str, Any], config["actions"])

    assert capabilities["actions"] is False
    assert actions["enabled"] is False
