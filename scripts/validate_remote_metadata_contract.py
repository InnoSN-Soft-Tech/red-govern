"""Validate the implemented, not-yet-deployed remote metadata API."""

from __future__ import annotations

import ast
import json
from pathlib import Path
from typing import Any, NoReturn, cast

ROOT = Path(__file__).resolve().parents[1]
CONTRACT_PATH = ROOT / "docs" / "agents" / "remote-metadata-contract.json"
OPENAPI_PATH = ROOT / "docs" / "agents" / "red-govern-metadata.openapi.json"
DOC_PATH = ROOT / "docs" / "agents" / "remote-metadata-api.md"
MAP_PATH = ROOT / "docs" / "problems" / "problem-command-map.json"
RESOURCE_MAP_PATH = (
    ROOT
    / "src"
    / "red_govern"
    / "resources"
    / "problem-command-map.json"
)
RUNTIME_PATH = ROOT / "src" / "red_govern" / "remote_api.py"
GPT_CONFIG_PATH = ROOT / "gpt" / "red-govern-advisor" / "config.json"
PRIVACY_PATH = ROOT / "PRIVACY.md"
LLMS_PATH = ROOT / "docs" / "llms.txt"
CHANGELOG_PATH = ROOT / "CHANGELOG.md"
CI_PATH = ROOT / ".github" / "workflows" / "ci.yml"
PYPROJECT_PATH = ROOT / "pyproject.toml"

EXPECTED_VERSION = "0.1.0a3"
EXPECTED_SERVER = "https://api.snsoft.tech/red-govern"
EXPECTED_RUNTIME = "red_govern.remote_api:app"
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
    """Raise one stable remote-runtime validation failure."""
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
    """Return canonical problem counts by status."""
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
    """Return canonical command strings."""
    raw = mapping.get("allowed_commands")
    if not isinstance(raw, list):
        fail("Canonical problem map has no allowed_commands list.")
    if not all(isinstance(item, str) and item for item in raw):
        fail("Canonical allowed_commands contains invalid entries.")
    return cast(list[str], raw)


def parameter_names(operation: dict[str, Any]) -> set[str]:
    """Collect OpenAPI request parameter names."""
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
    if contract.get("deployment_status") != "runtime-implemented-not-deployed":
        fail("Remote metadata deployment status differs.")
    if contract.get("runtime_module") != EXPECTED_RUNTIME:
        fail("Remote metadata runtime module differs.")
    if contract.get("planned_server_url") != EXPECTED_SERVER:
        fail("Remote metadata planned server differs.")
    if contract.get("authentication") != "none":
        fail("Remote metadata contract must remain unauthenticated public metadata.")
    if contract.get("current_custom_gpt_actions_enabled") is not False:
        fail("Custom GPT Actions must remain disabled.")
    if contract.get("remote_redshift_runtime") is not False:
        fail("Remote Redshift runtime must remain disabled.")
    if contract.get("accepts_credentials") is not False:
        fail("Remote metadata runtime must not accept credentials.")
    if contract.get("accepts_local_configuration") is not False:
        fail("Remote metadata runtime must not accept local configuration.")
    if contract.get("next_step") != "47.2D":
        fail("Remote metadata contract next step differs.")

    endpoints = contract.get("endpoints")
    if not isinstance(endpoints, list):
        fail("Remote metadata contract endpoints must be a list.")

    observed: dict[str, str] = {}
    for raw in endpoints:
        if not isinstance(raw, dict):
            fail("Remote metadata endpoint entry must be an object.")
        if raw.get("method") != "GET":
            fail("Remote metadata endpoints must all use GET.")
        path = raw.get("path")
        operation_id = raw.get("operation_id")
        if not isinstance(path, str) or not isinstance(operation_id, str):
            fail("Remote metadata endpoint path/operation_id is invalid.")
        observed[path] = operation_id

    if observed != EXPECTED_PATHS:
        fail(f"Remote metadata endpoint set differs: {observed}")

    if contract.get("status_counts") != status_counts(mapping):
        fail("Remote metadata status counts drifted from canonical map.")
    if contract.get("allowed_command_count") != len(allowed_commands(mapping)):
        fail("Remote metadata allowed-command count drifted.")


def validate_openapi(
    spec: dict[str, Any],
    mapping: dict[str, Any],
) -> None:
    """Validate the frozen Action-facing OpenAPI interface."""
    if spec.get("openapi") != "3.1.0":
        fail("OpenAPI version must be 3.1.0.")

    info = spec.get("info")
    if not isinstance(info, dict) or info.get("version") != EXPECTED_VERSION:
        fail("OpenAPI info.version differs.")

    if spec.get("x-red-govern-deployment-status") != (
        "runtime-implemented-not-deployed"
    ):
        fail("OpenAPI deployment marker differs.")

    if spec.get("x-red-govern-runtime") != EXPECTED_RUNTIME:
        fail("OpenAPI runtime marker differs.")

    expected_servers = [
        {
            "url": EXPECTED_SERVER,
            "description": "Planned endpoint; runtime implemented, not deployed",
        }
    ]
    if spec.get("servers") != expected_servers:
        fail("OpenAPI server contract differs.")

    if spec.get("security") != []:
        fail("Remote metadata OpenAPI must use no authentication.")

    paths = spec.get("paths")
    if not isinstance(paths, dict) or set(paths) != set(EXPECTED_PATHS):
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
            fail(f"OpenAPI GET unexpectedly accepts request body: {path}")
        if operation.get("security") != []:
            fail(f"OpenAPI operation is not unauthenticated: {path}")

        names = parameter_names(operation)
        all_request_names.update(names)

        if path == "/v1/problems" and names != {"status"}:
            fail("Problem-list endpoint must expose only status.")
        if path == "/v1/problems/{problem_id}" and names != {"problem_id"}:
            fail("Problem-detail endpoint must expose only problem_id.")
        if path in {"/v1/meta", "/v1/commands"} and names:
            fail(f"Unexpected request parameters on {path}: {sorted(names)}")

    forbidden = all_request_names & FORBIDDEN_REQUEST_NAMES
    if forbidden:
        fail(
            "Remote metadata request surface exposes forbidden inputs: "
            f"{sorted(forbidden)}"
        )

    components = spec.get("components")
    if not isinstance(components, dict):
        fail("OpenAPI components must be an object.")
    if "securitySchemes" in components:
        fail("Remote metadata OpenAPI must not define security schemes.")

    schemas = components.get("schemas")
    if not isinstance(schemas, dict):
        fail("OpenAPI components.schemas must be an object.")

    metadata_schema = schemas.get("MetadataResponse")
    if not isinstance(metadata_schema, dict):
        fail("MetadataResponse schema is invalid.")
    example = metadata_schema.get("example")
    if not isinstance(example, dict):
        fail("MetadataResponse example is missing.")
    if example.get("status_counts") != status_counts(mapping):
        fail("MetadataResponse example status counts drifted.")
    if example.get("allowed_command_count") != len(allowed_commands(mapping)):
        fail("MetadataResponse example command count drifted.")


def validate_runtime_source() -> None:
    """Validate runtime imports, routes, dependency boundary, and resource."""
    if RESOURCE_MAP_PATH.read_bytes() != MAP_PATH.read_bytes():
        fail("Packaged problem map drifts from canonical docs problem map.")

    source = RUNTIME_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".", 1)[0])

    if "fastapi" not in imports or "pydantic" not in imports:
        fail("Remote runtime must use FastAPI and Pydantic.")

    forbidden_imports = {
        "boto3",
        "keyring",
        "mcp",
        "openai",
        "redshift_connector",
        "subprocess",
    }
    unexpected = imports & forbidden_imports
    if unexpected:
        fail(f"Remote runtime imports forbidden surfaces: {sorted(unexpected)}")

    for forbidden in (
        "execute(",
        "cursor(",
        "subprocess.",
        "os.system",
        "eval(",
        "exec(",
    ):
        if forbidden in source:
            fail(f"Remote runtime contains forbidden execution marker: {forbidden}")

    for required in (
        '"/v1/meta"',
        '"/v1/problems"',
        '"/v1/problems/{problem_id}"',
        '"/v1/commands"',
        "docs_url=None",
        "redoc_url=None",
        "openapi_url=None",
    ):
        if required not in source:
            fail(f"Remote runtime omits required surface: {required}")


def validate_pyproject() -> None:
    """Validate optional dependency and package-resource boundaries."""
    text = PYPROJECT_PATH.read_text(encoding="utf-8")

    remote_block = (
        'remote = [\n'
        '    "fastapi>=0.139,<1",\n'
        '    "uvicorn>=0.51,<1",\n'
        ']\n'
    )
    if remote_block not in text:
        fail("Remote optional dependency block is missing or differs.")

    base_block = text.split("dependencies = [", 1)[1].split("]\n", 1)[0]
    if "fastapi" in base_block or "uvicorn" in base_block:
        fail("Remote HTTP dependencies must not enter base dependencies.")

    all_block = text.split("all = [", 1)[1].split("]\n", 1)[0]
    dev_block = text.split("dev = [", 1)[1].split("]\n", 1)[0]

    for required in ("fastapi>=0.139,<1", "uvicorn>=0.51,<1"):
        if required not in all_block:
            fail(f"all extra omits remote dependency: {required}")
        if required not in dev_block:
            fail(f"dev extra omits remote dependency: {required}")

    if "httpx>=0.28,<1" not in dev_block:
        fail("dev extra omits HTTPX runtime-test dependency.")

    if '"src/red_govern/**/*.json",' not in text:
        fail("Wheel build include does not package JSON resources.")


def validate_docs_privacy_ci() -> None:
    """Validate docs, privacy, GPT boundary, and dedicated CI."""
    doc = normalize_text(DOC_PATH.read_text(encoding="utf-8"))
    for required in (
        "runtime is implemented",
        "not deployed",
        "red_govern.remote_api:app",
        'python -m pip install --editable ".[remote]"',
        "127.0.0.1",
        "does not connect to Amazon Redshift",
        "Custom GPT Actions remain disabled",
        "Step 47.2D",
    ):
        if normalize_text(required) not in doc:
            fail(f"Remote metadata documentation omits: {required}")

    privacy = normalize_text(PRIVACY_PATH.read_text(encoding="utf-8"))
    for required in (
        "remote metadata API runtime is implemented",
        "hosted endpoint is not deployed",
        "does not accept local Red-Govern configuration files",
        "does not connect to Amazon Redshift",
        "does not execute SQL",
        "info@snsoft.tech",
    ):
        if normalize_text(required) not in privacy:
            fail(f"PRIVACY.md omits: {required}")

    llms = normalize_text(LLMS_PATH.read_text(encoding="utf-8"))
    if "runtime implemented; hosted endpoint not deployed" not in llms:
        fail("llms.txt does not describe the remote runtime status.")

    changelog = CHANGELOG_PATH.read_text(encoding="utf-8")
    if "Implemented the optional FastAPI remote metadata runtime" not in changelog:
        fail("CHANGELOG omits remote runtime implementation entry.")

    gpt = load_object(GPT_CONFIG_PATH)
    capabilities = gpt.get("capabilities")
    actions = gpt.get("actions")

    if not isinstance(capabilities, dict) or capabilities.get("actions") is not False:
        fail("Custom GPT Actions must remain disabled.")
    if not isinstance(actions, dict) or actions.get("enabled") is not False:
        fail("Custom GPT actions.enabled must remain false.")

    ci = CI_PATH.read_text(encoding="utf-8")
    if ci.count("Validate remote metadata contract") != 3:
        fail("CI must validate remote metadata contract in three job groups.")
    if "name: Remote metadata API" not in ci:
        fail("CI remote metadata API job is missing.")
    if 'python -m pip install --editable ".[remote]"' not in ci:
        fail("CI remote metadata API job omits isolated remote install.")
    if (
        "python -m pytest -q tests/unit/test_remote_api.py "
        "tests/unit/test_remote_metadata_contract.py --no-cov"
        not in ci
    ):
        fail("CI remote metadata API test command differs.")


def main() -> int:
    """Run all remote metadata runtime contract checks."""
    for path in (
        CONTRACT_PATH,
        OPENAPI_PATH,
        DOC_PATH,
        MAP_PATH,
        RESOURCE_MAP_PATH,
        RUNTIME_PATH,
        GPT_CONFIG_PATH,
        PRIVACY_PATH,
        LLMS_PATH,
        CHANGELOG_PATH,
        CI_PATH,
        PYPROJECT_PATH,
    ):
        if not path.is_file():
            fail(f"Required remote runtime file is missing: {path}")

    mapping = load_object(MAP_PATH)
    if mapping.get("generated_for_package_version") != EXPECTED_VERSION:
        fail("Canonical problem-map version differs.")
    if status_counts(mapping) != EXPECTED_STATUS_COUNTS:
        fail("Canonical status counts differ.")
    if len(allowed_commands(mapping)) != 14:
        fail("Canonical allowed-command count differs.")

    validate_contract(load_object(CONTRACT_PATH), mapping)
    validate_openapi(load_object(OPENAPI_PATH), mapping)
    validate_runtime_source()
    validate_pyproject()
    validate_docs_privacy_ci()

    print("Remote metadata runtime: implemented")
    print(f"Package version: {EXPECTED_VERSION}")
    print("ASGI runtime: red_govern.remote_api:app")
    print("HTTP framework: FastAPI optional extra")
    print("Remote metadata endpoints: 4")
    print("HTTP methods: GET only")
    print("Authentication: none")
    print("Request bodies: 0")
    print("Credential/configuration inputs: 0")
    print("Remote Redshift connections: 0")
    print("SQL execution endpoints: 0")
    print("Command execution endpoints: 0")
    print("Built-in docs/OpenAPI routes: disabled")
    print("Custom GPT Actions: disabled")
    print("Deployment status: runtime-implemented-not-deployed")
    print("Remote metadata API runtime validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
