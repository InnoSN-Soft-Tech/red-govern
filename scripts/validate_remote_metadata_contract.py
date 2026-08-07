"""Validate the contract-only Red-Govern remote metadata API surface."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, NoReturn, cast

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "agents" / "remote-metadata-contract.json"
OPENAPI_PATH = ROOT / "docs" / "agents" / "red-govern-metadata.openapi.json"
DOC_PATH = ROOT / "docs" / "agents" / "remote-metadata-api.md"
MAP_PATH = ROOT / "docs" / "problems" / "problem-command-map.json"
GPT_CONFIG_PATH = ROOT / "gpt" / "red-govern-advisor" / "config.json"
PRIVACY_PATH = ROOT / "PRIVACY.md"
LLMS_PATH = ROOT / "docs" / "llms.txt"
CHANGELOG_PATH = ROOT / "CHANGELOG.md"
CI_PATH = ROOT / ".github" / "workflows" / "ci.yml"

EXPECTED_VERSION = "0.1.0a3"
EXPECTED_SERVER = "https://api.snsoft.tech/red-govern"
EXPECTED_PATHS = {
    "/v1/meta": "getRedGovernMetadata",
    "/v1/problems": "listRedGovernProblems",
    "/v1/problems/{problem_id}": "getRedGovernProblem",
    "/v1/commands": "listRedGovernCommands",
}
EXPECTED_STATUS_COUNTS = {
    "supported": 12,
    "conditional": 4,
    "unsupported": 5,
}
FORBIDDEN_REQUEST_NAMES = {
    "password",
    "token",
    "credential",
    "credentials",
    "connection",
    "connection_string",
    "endpoint",
    "host",
    "database",
    "user",
    "username",
    "config",
    "configuration",
    "path",
    "file",
    "sql",
    "query",
    "query_text",
    "command",
    "commands",
    "redshift",
}


def fail(message: str) -> NoReturn:
    """Raise a stable contract-validation failure."""
    raise RuntimeError(message)


def load_object(path: Path) -> dict[str, Any]:
    """Load one JSON object."""
    parsed: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        fail(f"Expected JSON object: {path}")
    return cast(dict[str, Any], parsed)


def normalize_text(value: str) -> str:
    """Collapse formatting whitespace."""
    return " ".join(value.split())


def status_counts(mapping: dict[str, Any]) -> dict[str, int]:
    """Return canonical problem counts by support status."""
    raw = mapping.get("problems")
    if not isinstance(raw, list):
        fail("Canonical problem map has no problems list.")
    return {
        status: sum(
            1
            for item in raw
            if isinstance(item, dict) and item.get("status") == status
        )
        for status in EXPECTED_STATUS_COUNTS
    }


def allowed_commands(mapping: dict[str, Any]) -> list[str]:
    """Return canonical allowed commands."""
    raw = mapping.get("allowed_commands")
    if not isinstance(raw, list):
        fail("Canonical problem map has no allowed_commands list.")
    if not all(isinstance(item, str) and item for item in raw):
        fail("Canonical allowed_commands contains invalid entries.")
    return cast(list[str], raw)


def parameter_names(operation: dict[str, Any]) -> set[str]:
    """Collect request parameter names for one OpenAPI operation."""
    raw = operation.get("parameters", [])
    if not isinstance(raw, list):
        fail("OpenAPI operation parameters must be a list.")
    names: set[str] = set()
    for item in raw:
        if not isinstance(item, dict):
            fail("OpenAPI parameter entry must be an object.")
        name = item.get("name")
        if not isinstance(name, str) or not name:
            fail("OpenAPI parameter name must be a non-empty string.")
        names.add(name)
    return names


def validate_contract(
    contract: dict[str, Any],
    mapping: dict[str, Any],
) -> None:
    """Validate the machine-readable remote metadata contract."""
    if contract.get("schema_version") != "1.0":
        fail("Remote metadata contract schema_version differs.")
    if contract.get("package_version") != EXPECTED_VERSION:
        fail("Remote metadata contract package version differs.")
    if contract.get("deployment_status") != "contract-only-not-deployed":
        fail("Remote metadata deployment status differs.")
    if contract.get("planned_server_url") != EXPECTED_SERVER:
        fail("Remote metadata planned server differs.")
    if contract.get("authentication") != "none":
        fail("Remote metadata contract must remain public read-only metadata.")
    if contract.get("current_custom_gpt_actions_enabled") is not False:
        fail("Custom GPT Actions must remain disabled during contract-only phase.")
    if contract.get("remote_redshift_runtime") is not False:
        fail("Remote Redshift runtime must remain disabled.")
    if contract.get("accepts_credentials") is not False:
        fail("Remote metadata contract must not accept credentials.")
    if contract.get("accepts_local_configuration") is not False:
        fail("Remote metadata contract must not accept local configuration.")
    if contract.get("next_step") != "47.2C":
        fail("Remote metadata contract next step differs.")

    endpoints = contract.get("endpoints")
    if not isinstance(endpoints, list):
        fail("Remote metadata contract endpoints must be a list.")

    observed: dict[str, str] = {}
    for raw in endpoints:
        if not isinstance(raw, dict):
            fail("Remote metadata endpoint entry must be an object.")
        method = raw.get("method")
        path = raw.get("path")
        operation_id = raw.get("operation_id")
        if method != "GET":
            fail("Remote metadata endpoints must all use GET.")
        if not isinstance(path, str) or not isinstance(operation_id, str):
            fail("Remote metadata endpoint path/operation_id is invalid.")
        observed[path] = operation_id

    if observed != EXPECTED_PATHS:
        fail(f"Remote metadata endpoint set differs: {observed}")

    if contract.get("status_counts") != status_counts(mapping):
        fail("Remote metadata contract status counts drifted from canonical map.")

    commands = allowed_commands(mapping)
    if contract.get("allowed_command_count") != len(commands):
        fail("Remote metadata allowed-command count drifted.")

    expected_excluded = [
        "validate_config(path)",
        "get_redacted_config(path=<local file>)",
        "run_privacy_audit(path)",
    ]
    if contract.get("excluded_local_operations") != expected_excluded:
        fail("Excluded local operation set differs.")


def validate_openapi(
    spec: dict[str, Any],
    mapping: dict[str, Any],
) -> None:
    """Validate the contract-only OpenAPI document."""
    if spec.get("openapi") != "3.1.0":
        fail("OpenAPI version must be 3.1.0.")

    info = spec.get("info")
    if not isinstance(info, dict):
        fail("OpenAPI info must be an object.")
    if info.get("version") != EXPECTED_VERSION:
        fail("OpenAPI info.version differs.")
    if spec.get("x-red-govern-deployment-status") != "contract-only-not-deployed":
        fail("OpenAPI deployment marker differs.")

    expected_servers = [
        {
            "url": EXPECTED_SERVER,
            "description": "Planned endpoint; not deployed",
        }
    ]
    if spec.get("servers") != expected_servers:
        fail("OpenAPI server contract differs.")

    if spec.get("security") != []:
        fail("Contract-only public metadata OpenAPI must use no authentication.")

    paths = spec.get("paths")
    if not isinstance(paths, dict):
        fail("OpenAPI paths must be an object.")
    if set(paths) != set(EXPECTED_PATHS):
        fail("OpenAPI path set differs.")

    all_request_names: set[str] = set()

    for path, expected_operation_id in EXPECTED_PATHS.items():
        path_item = paths.get(path)
        if not isinstance(path_item, dict):
            fail(f"OpenAPI path item is invalid: {path}")

        methods = {
            key.lower()
            for key in path_item
            if key.lower()
            in {
                "get",
                "post",
                "put",
                "patch",
                "delete",
                "options",
                "head",
                "trace",
            }
        }
        if methods != {"get"}:
            fail(f"OpenAPI path is not GET-only: {path}")

        operation = path_item.get("get")
        if not isinstance(operation, dict):
            fail(f"OpenAPI GET operation is missing: {path}")
        if operation.get("operationId") != expected_operation_id:
            fail(f"OpenAPI operationId differs for {path}")
        if "requestBody" in operation:
            fail(f"OpenAPI GET operation unexpectedly accepts a request body: {path}")
        if operation.get("security") != []:
            fail(f"OpenAPI operation is not explicitly unauthenticated: {path}")

        names = parameter_names(operation)
        all_request_names.update(names)

        if path == "/v1/problems":
            if names != {"status"}:
                fail("Problem-list endpoint must expose only the status filter.")
        elif path == "/v1/problems/{problem_id}":
            if names != {"problem_id"}:
                fail("Problem-detail endpoint must expose only problem_id.")
        elif names:
            fail(f"Unexpected request parameters on {path}: {sorted(names)}")

        responses = operation.get("responses")
        if not isinstance(responses, dict) or "200" not in responses:
            fail(f"OpenAPI success response missing for {path}")

    forbidden = {
        name.lower()
        for name in all_request_names
        if name.lower() in FORBIDDEN_REQUEST_NAMES
    }
    if forbidden:
        fail(
            "Remote metadata request surface exposes forbidden inputs: "
            f"{sorted(forbidden)}"
        )

    components = spec.get("components")
    if not isinstance(components, dict):
        fail("OpenAPI components must be an object.")
    if "securitySchemes" in components:
        fail("Contract-only metadata OpenAPI must not define security schemes.")

    schemas = components.get("schemas")
    if not isinstance(schemas, dict):
        fail("OpenAPI components.schemas must be an object.")

    expected_schemas = {
        "ProblemStatus",
        "StatusCounts",
        "SafetyBoundaries",
        "MetadataResponse",
        "ProblemSummary",
        "ProblemDetail",
        "ProblemListResponse",
        "CommandListResponse",
        "ErrorResponse",
    }
    if set(schemas) != expected_schemas:
        fail("OpenAPI component schema set differs.")

    problem_list = paths["/v1/problems"]
    if not isinstance(problem_list, dict):
        fail("Problem-list path is invalid.")
    operation = problem_list.get("get")
    if not isinstance(operation, dict):
        fail("Problem-list GET is invalid.")
    params = operation.get("parameters")
    if not isinstance(params, list) or len(params) != 1:
        fail("Problem-list status parameter differs.")
    status_parameter = params[0]
    if not isinstance(status_parameter, dict):
        fail("Problem-list status parameter is invalid.")
    status_schema = status_parameter.get("schema")
    if not isinstance(status_schema, dict):
        fail("Problem-list status schema is invalid.")
    if status_schema.get("enum") != [
        "supported",
        "conditional",
        "unsupported",
    ]:
        fail("Problem-list status enum differs.")

    metadata_schema = schemas.get("MetadataResponse")
    if not isinstance(metadata_schema, dict):
        fail("MetadataResponse schema is invalid.")
    example = metadata_schema.get("example")
    if not isinstance(example, dict):
        fail("MetadataResponse example is missing.")
    if example.get("package_version") != EXPECTED_VERSION:
        fail("MetadataResponse example version differs.")
    if example.get("status_counts") != status_counts(mapping):
        fail("MetadataResponse example status counts drifted.")
    if example.get("allowed_command_count") != len(allowed_commands(mapping)):
        fail("MetadataResponse example command count drifted.")


def validate_privacy() -> None:
    """Require a non-empty privacy notice for future deployment."""
    text = PRIVACY_PATH.read_text(encoding="utf-8")
    if not text.strip():
        fail("PRIVACY.md is empty.")

    normalized = normalize_text(text)
    for required in (
        "Red-Govern is local-first",
        "remote metadata API contract is not deployed",
        (
            "does not accept passwords, tokens, credentials, private endpoints, "
            "connection strings, or unredacted production outputs"
        ),
        "does not accept local Red-Govern configuration files",
        "does not connect to Amazon Redshift",
        "does not execute SQL",
        "info@snsoft.tech",
    ):
        if normalize_text(required) not in normalized:
            fail(f"PRIVACY.md omits: {required}")


def validate_docs_and_repository() -> None:
    """Validate documentation, GPT boundary, and CI integration."""
    doc = normalize_text(DOC_PATH.read_text(encoding="utf-8"))
    for required in (
        "contract-only",
        EXPECTED_SERVER,
        "not deployed",
        "GET /v1/meta",
        "GET /v1/problems",
        "GET /v1/problems/{problem_id}",
        "GET /v1/commands",
        "does not execute Red-Govern commands",
        "does not connect to Amazon Redshift",
        "Custom GPT Actions remain disabled",
        "Step 47.2C",
    ):
        if normalize_text(required) not in doc:
            fail(f"Remote metadata documentation omits: {required}")

    llms = LLMS_PATH.read_text(encoding="utf-8")
    changelog = CHANGELOG_PATH.read_text(encoding="utf-8")
    ci = CI_PATH.read_text(encoding="utf-8")

    for required in (
        "/agents/remote-metadata-api/",
        "/agents/red-govern-metadata.openapi.json",
        "/agents/remote-metadata-contract.json",
    ):
        if required not in llms:
            fail(f"llms.txt omits remote metadata resource: {required}")

    if "Defined a contract-only read-only remote metadata API" not in changelog:
        fail("CHANGELOG omits remote metadata API contract entry.")

    gpt_config = load_object(GPT_CONFIG_PATH)
    capabilities = gpt_config.get("capabilities")
    if not isinstance(capabilities, dict):
        fail("Custom GPT capabilities are invalid.")
    if capabilities.get("actions") is not False:
        fail("Custom GPT Actions must remain disabled.")

    actions = gpt_config.get("actions")
    if not isinstance(actions, dict):
        fail("Custom GPT actions config is invalid.")
    if actions.get("enabled") is not False:
        fail("Custom GPT actions.enabled must remain false.")

    if ci.count("Validate remote metadata contract") != 2:
        fail("CI must run the remote metadata validator in two job groups.")
    if ci.count("python scripts/validate_remote_metadata_contract.py") != 2:
        fail("CI remote metadata validator command count differs.")
    if "scripts/validate_remote_metadata_contract.py" not in ci:
        fail("CI MyPy scope omits the remote metadata validator.")


def main() -> int:
    """Run every remote metadata contract validation."""
    for path in (
        CONTRACT_PATH,
        OPENAPI_PATH,
        DOC_PATH,
        MAP_PATH,
        GPT_CONFIG_PATH,
        PRIVACY_PATH,
        LLMS_PATH,
        CHANGELOG_PATH,
        CI_PATH,
    ):
        if not path.is_file():
            fail(f"Required remote metadata contract file is missing: {path}")

    mapping = load_object(MAP_PATH)
    if mapping.get("generated_for_package_version") != EXPECTED_VERSION:
        fail("Canonical problem-map version differs.")
    if status_counts(mapping) != EXPECTED_STATUS_COUNTS:
        fail("Canonical status counts differ.")
    if len(allowed_commands(mapping)) != 14:
        fail("Canonical allowed-command count differs.")

    contract = load_object(CONTRACT_PATH)
    spec = load_object(OPENAPI_PATH)

    validate_contract(contract, mapping)
    validate_openapi(spec, mapping)
    validate_privacy()
    validate_docs_and_repository()

    print("Remote metadata contract version: 1.0")
    print(f"Package version: {EXPECTED_VERSION}")
    print("Remote metadata endpoints: 4")
    print("HTTP methods: GET only")
    print("Authentication: none (public metadata contract)")
    print("Request bodies: 0")
    print("Credential/configuration inputs: 0")
    print("Remote Redshift connections: 0")
    print("SQL execution endpoints: 0")
    print("Command execution endpoints: 0")
    print("Custom GPT Actions: disabled")
    print("Deployment status: contract-only-not-deployed")
    print("PRIVACY.md: populated as future deployment source")
    print("Remote metadata API contract validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
