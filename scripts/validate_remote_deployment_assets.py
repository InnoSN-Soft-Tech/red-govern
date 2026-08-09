"""Validate Red-Govern provider-neutral remote deployment assets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, NoReturn, cast

ROOT = Path(__file__).resolve().parents[1]
DOCKERFILE = ROOT / "Dockerfile"
DOCKERIGNORE = ROOT / ".dockerignore"
DEPLOYMENT_DOC = ROOT / "deployment" / "README.md"
NGINX_EXAMPLE = ROOT / "deployment" / "nginx-red-govern.conf.example"
PRIVACY_ROOT = ROOT / "PRIVACY.md"
PRIVACY_DOC = ROOT / "docs" / "privacy.md"
REMOTE_DOC = ROOT / "docs" / "agents" / "remote-metadata-api.md"
CONTRACT_PATH = ROOT / "docs" / "agents" / "remote-metadata-contract.json"
OPENAPI_PATH = ROOT / "docs" / "agents" / "red-govern-metadata.openapi.json"
GPT_CONFIG = ROOT / "gpt" / "red-govern-advisor" / "config.json"
LLMS_PATH = ROOT / "docs" / "llms.txt"
CHANGELOG = ROOT / "CHANGELOG.md"
CI_PATH = ROOT / ".github" / "workflows" / "ci.yml"

EXPECTED_VERSION = "0.1.0a4"
EXPECTED_SERVER = "https://api.snsoft.tech/red-govern"
EXPECTED_PRIVACY = "https://innosn-soft-tech.github.io/red-govern/privacy/"
EXPECTED_STATUS = "deployment-assets-ready-not-deployed"


def fail(message: str) -> NoReturn:
    """Raise a stable deployment-asset validation failure."""
    raise RuntimeError(message)


def load_json(path: Path) -> dict[str, Any]:
    """Load one JSON object."""
    parsed: object = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(parsed, dict):
        fail(f"Expected JSON object: {path}")
    return cast(dict[str, Any], parsed)


def normalized(value: str) -> str:
    """Collapse formatting whitespace."""
    return " ".join(value.split())


def validate_dockerfile() -> None:
    """Validate the container boundary and process contract."""
    text = DOCKERFILE.read_text(encoding="utf-8")

    required = (
        "FROM python:3.13-slim",
        'python -m pip install --no-cache-dir ".[remote]"',
        "addgroup --system redgovern",
        "adduser --system --ingroup redgovern --no-create-home redgovern",
        "USER redgovern",
        "EXPOSE 8080",
        "HEALTHCHECK",
        "http://127.0.0.1:8080/v1/meta",
        '"red_govern.remote_api:app"',
        '"--host", "0.0.0.0"',
        '"--port", "8080"',
        '"--no-server-header"',
        '"--no-access-log"',
        '"--workers", "1"',
    )
    for item in required:
        if item not in text:
            fail(f"Dockerfile omits required deployment boundary: {item}")

    forbidden = (
        "COPY . ",
        "COPY .\n",
        "ENTRYPOINT [\"/bin/sh\"",
        "curl ",
        "wget ",
        "sudo ",
        "AWS_ACCESS_KEY",
        "OPENAI_API_KEY",
        "REDSHIFT_PASSWORD",
    )
    for item in forbidden:
        if item in text:
            fail(f"Dockerfile contains forbidden deployment marker: {item}")


def validate_dockerignore() -> None:
    """Require common local/build artefacts to stay out of image context."""
    lines = {
        line.strip()
        for line in DOCKERIGNORE.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.lstrip().startswith("#")
    }
    for required in (
        ".git",
        ".github",
        ".venv",
        "__pycache__",
        "tests",
        "docs",
        "gpt",
        "dist",
        "site",
    ):
        if required not in lines:
            fail(f".dockerignore omits: {required}")


def validate_privacy() -> None:
    """Keep repository and public privacy policy byte-identical."""
    root_bytes = PRIVACY_ROOT.read_bytes()
    docs_bytes = PRIVACY_DOC.read_bytes()

    if not root_bytes.strip():
        fail("PRIVACY.md is empty.")
    if root_bytes != docs_bytes:
        fail("PRIVACY.md and docs/privacy.md differ.")

    text = normalized(root_bytes.decode("utf-8"))
    for required in (
        "Effective date: 7 August 2026",
        "Public remote metadata API",
        "Technical request metadata",
        "source IP address",
        "does not accept local Red-Govern configuration files",
        "does not connect to Amazon Redshift",
        "does not execute SQL",
        "does not use cookies",
        "does not sell personal data",
        "info@snsoft.tech",
    ):
        if normalized(required) not in text:
            fail(f"Privacy policy omits: {required}")


def validate_proxy() -> None:
    """Validate the documented reverse-proxy and edge controls."""
    text = NGINX_EXAMPLE.read_text(encoding="utf-8")

    for required in (
        "server_name api.snsoft.tech;",
        "limit_req_zone",
        "rate=5r/s",
        "client_max_body_size 16k;",
        "location /red-govern/",
        r"rewrite ^/red-govern(/.*)$ $1 break;",
        "proxy_pass http://127.0.0.1:8080;",
        "proxy_connect_timeout 5s;",
        "proxy_read_timeout 15s;",
        "proxy_hide_header Server;",
        'add_header X-Content-Type-Options "nosniff" always;',
        'add_header Referrer-Policy "no-referrer" always;',
    ):
        if required not in text:
            fail(f"Nginx deployment example omits: {required}")

    for forbidden in (
        "ssl_certificate /etc/letsencrypt/live/",
        "BEGIN PRIVATE KEY",
        "proxy_pass http://redshift",
    ):
        if forbidden in text:
            fail(f"Nginx deployment example contains forbidden marker: {forbidden}")


def validate_contracts() -> None:
    """Validate metadata/OpenAPI status without widening the HTTP surface."""
    contract = load_json(CONTRACT_PATH)
    spec = load_json(OPENAPI_PATH)
    gpt = load_json(GPT_CONFIG)

    if contract.get("package_version") != EXPECTED_VERSION:
        fail("Remote metadata contract version differs.")
    if contract.get("deployment_status") != EXPECTED_STATUS:
        fail("Remote metadata deployment status differs.")
    if contract.get("planned_server_url") != EXPECTED_SERVER:
        fail("Remote metadata planned server differs.")
    if contract.get("privacy_policy_url") != EXPECTED_PRIVACY:
        fail("Remote metadata privacy URL differs.")
    if contract.get("next_step") != "47.2F":
        fail("Remote metadata next step differs.")

    deployment = contract.get("deployment")
    if not isinstance(deployment, dict):
        fail("Remote metadata deployment object is missing.")

    expected_deployment = {
        "container_file": "Dockerfile",
        "container_port": 8080,
        "health_path": "/v1/meta",
        "external_base_path": "/red-govern",
        "proxy_strips_external_prefix": True,
        "reverse_proxy_example": "deployment/nginx-red-govern.conf.example",
        "secrets_required": False,
    }
    if deployment != expected_deployment:
        fail("Remote metadata deployment object differs.")

    if spec.get("x-red-govern-deployment-status") != EXPECTED_STATUS:
        fail("OpenAPI deployment status differs.")
    if spec.get("x-red-govern-privacy-policy-url") != EXPECTED_PRIVACY:
        fail("OpenAPI privacy-policy extension differs.")
    if spec.get("security") != []:
        fail("OpenAPI authentication contract changed.")

    paths = spec.get("paths")
    if not isinstance(paths, dict):
        fail("OpenAPI paths object is invalid.")
    if set(paths) != {
        "/v1/meta",
        "/v1/problems",
        "/v1/problems/{problem_id}",
        "/v1/commands",
    }:
        fail("OpenAPI HTTP surface changed.")

    if gpt.get("capabilities", {}).get("actions") is not False:
        fail("Custom GPT Actions must remain disabled.")
    if gpt.get("actions", {}).get("enabled") is not False:
        fail("Custom GPT actions.enabled must remain false.")


def validate_docs_ci() -> None:
    """Validate deployment documentation, discoverability, and CI."""
    deployment = normalized(DEPLOYMENT_DOC.read_text(encoding="utf-8"))
    remote = normalized(REMOTE_DOC.read_text(encoding="utf-8"))
    llms = normalized(LLMS_PATH.read_text(encoding="utf-8"))
    changelog = CHANGELOG.read_text(encoding="utf-8")
    ci = CI_PATH.read_text(encoding="utf-8")

    for required in (
        "provider-neutral deployment assets",
        "docker build",
        "--read-only",
        "--cap-drop ALL",
        "https://api.snsoft.tech/red-govern",
        "https://innosn-soft-tech.github.io/red-govern/privacy/",
        "/red-govern/*",
        "does not create DNS records",
    ):
        if normalized(required) not in deployment:
            fail(f"Deployment documentation omits: {required}")

    for required in (
        "deployment assets are ready",
        "production API is still not deployed",
        "Dockerfile",
        "public privacy policy",
        "Step 47.2F",
    ):
        if normalized(required) not in remote:
            fail(f"Remote API documentation omits: {required}")

    if "deployment assets ready; public API not deployed" not in llms:
        fail("llms.txt remote deployment status differs.")

    if "Added provider-neutral deployment assets" not in changelog:
        fail("CHANGELOG omits deployment asset entry.")

    if ci.count("Validate remote deployment assets") != 3:
        fail("CI must validate deployment assets in three job groups.")
    if "name: Remote deployment assets" not in ci:
        fail("Dedicated deployment-assets CI job is missing.")
    if "docker build --tag red-govern-remote:ci ." not in ci:
        fail("Deployment-assets CI job does not build the container.")
    if "--read-only" not in ci or "--cap-drop ALL" not in ci:
        fail("Deployment-assets CI run omits container restrictions.")
    if "scripts/validate_remote_deployment_assets.py" not in ci:
        fail("CI does not reference deployment-asset validator.")


def main() -> int:
    """Run all provider-neutral deployment asset validations."""
    for path in (
        DOCKERFILE,
        DOCKERIGNORE,
        DEPLOYMENT_DOC,
        NGINX_EXAMPLE,
        PRIVACY_ROOT,
        PRIVACY_DOC,
        REMOTE_DOC,
        CONTRACT_PATH,
        OPENAPI_PATH,
        GPT_CONFIG,
        LLMS_PATH,
        CHANGELOG,
        CI_PATH,
    ):
        if not path.is_file():
            fail(f"Required deployment asset is missing: {path}")

    validate_dockerfile()
    validate_dockerignore()
    validate_privacy()
    validate_proxy()
    validate_contracts()
    validate_docs_ci()

    print("Remote deployment assets: validated")
    print(f"Package version: {EXPECTED_VERSION}")
    print("Container runtime: non-root redgovern")
    print("Container port: 8080")
    print("Container health path: /v1/meta")
    print("Container access log: disabled")
    print("Container server header: disabled")
    print("Reverse proxy prefix: /red-govern")
    print("Edge rate limiting: documented")
    print("Public privacy policy: source/docs parity passed")
    print(f"Public privacy URL: {EXPECTED_PRIVACY}")
    print("Secrets required by application: no")
    print("Production deployment performed: no")
    print("Custom GPT Actions: disabled")
    print("Remote deployment asset validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
