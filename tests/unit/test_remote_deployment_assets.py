"""Tests for provider-neutral remote metadata deployment assets."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, cast

ROOT = Path(__file__).resolve().parents[2]


def load(path: str) -> dict[str, Any]:
    parsed: object = json.loads(
        (ROOT / path).read_text(encoding="utf-8")
    )
    assert isinstance(parsed, dict)
    return cast(dict[str, Any], parsed)


def test_privacy_source_and_public_page_are_identical() -> None:
    assert (ROOT / "PRIVACY.md").read_bytes() == (
        ROOT / "docs" / "privacy.md"
    ).read_bytes()


def test_contract_records_deployment_assets_without_deployment() -> None:
    contract = load("docs/agents/remote-metadata-contract.json")

    assert contract["deployment_status"] == (
        "deployment-assets-ready-not-deployed"
    )
    assert contract["privacy_policy_url"] == (
        "https://innosn-soft-tech.github.io/red-govern/privacy/"
    )
    assert contract["next_step"] == "47.2F"
    assert contract["current_custom_gpt_actions_enabled"] is False
    assert contract["deployment"] == {
        "container_file": "Dockerfile",
        "container_port": 8080,
        "health_path": "/v1/meta",
        "external_base_path": "/red-govern",
        "proxy_strips_external_prefix": True,
        "reverse_proxy_example": "deployment/nginx-red-govern.conf.example",
        "secrets_required": False,
    }


def test_openapi_surface_is_unchanged_and_privacy_url_is_recorded() -> None:
    spec = load("docs/agents/red-govern-metadata.openapi.json")

    assert spec["x-red-govern-deployment-status"] == (
        "deployment-assets-ready-not-deployed"
    )
    assert spec["x-red-govern-privacy-policy-url"] == (
        "https://innosn-soft-tech.github.io/red-govern/privacy/"
    )
    assert spec["security"] == []
    assert set(spec["paths"]) == {
        "/v1/meta",
        "/v1/problems",
        "/v1/problems/{problem_id}",
        "/v1/commands",
    }


def test_dockerfile_uses_non_root_runtime_and_fixed_health_path() -> None:
    text = (ROOT / "Dockerfile").read_text(encoding="utf-8")

    assert "USER redgovern" in text
    assert "EXPOSE 8080" in text
    assert "HEALTHCHECK" in text
    assert "http://127.0.0.1:8080/v1/meta" in text
    assert '"--no-server-header"' in text
    assert '"--no-access-log"' in text
    assert "COPY . " not in text
    assert "COPY .\n" not in text


def test_proxy_example_strips_public_prefix_and_has_edge_controls() -> None:
    text = (
        ROOT / "deployment" / "nginx-red-govern.conf.example"
    ).read_text(encoding="utf-8")

    assert r"rewrite ^/red-govern(/.*)$ $1 break;" in text
    assert "proxy_pass http://127.0.0.1:8080;" in text
    assert "limit_req_zone" in text
    assert "client_max_body_size 16k;" in text
    assert "proxy_hide_header Server;" in text
