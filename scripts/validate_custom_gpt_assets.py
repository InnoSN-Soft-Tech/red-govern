"""Validate versioned Red-Govern Custom GPT assets."""

from __future__ import annotations

import argparse
import hashlib
import json
import re
from pathlib import Path
from typing import Any, NoReturn, cast

ROOT = Path(__file__).resolve().parents[1]
GPT_ROOT = ROOT / "gpt" / "red-govern-advisor"

CONFIG_PATH = GPT_ROOT / "config.json"
INSTRUCTIONS_PATH = GPT_ROOT / "instructions.md"
STARTERS_PATH = GPT_ROOT / "conversation-starters.json"
KNOWLEDGE_PATH = GPT_ROOT / "knowledge-manifest.json"
EVALS_PATH = GPT_ROOT / "evals.json"
CHECKLIST_PATH = GPT_ROOT / "publishing-checklist.md"

EXPECTED_VERSION = "0.1.0a3"
EXPECTED_NAME = "Red-Govern — Redshift Governance Advisor"
EXPECTED_KNOWLEDGE_LIMIT = 10
EXPECTED_KNOWLEDGE_LIMIT_CHECKED_AT = "2026-08-06"
EXPECTED_KNOWLEDGE_LIMIT_SOURCE = (
    "https://help.openai.com/en/articles/8555545"
)

EXPECTED_GPT_FILES = {
    CONFIG_PATH,
    INSTRUCTIONS_PATH,
    STARTERS_PATH,
    KNOWLEDGE_PATH,
    EVALS_PATH,
    CHECKLIST_PATH,
}

EXPECTED_STARTERS = [
    "Help me assess Amazon Redshift table-limit pressure safely.",
    "Which Red-Govern command should I use for an object inventory?",
    "Explain why Red-Govern cannot prove a table is safe to delete.",
    "Help me validate Red-Govern setup without exposing credentials.",
    "Compare supported, conditional, and unsupported capabilities.",
    "How do I install and verify Red-Govern 0.1.0a3?",
]

EXPECTED_KNOWLEDGE_SOURCES = [
    ("01-product-readme.md", "README.md"),
    ("03-installation.md", "docs/installation.md"),
    ("04-configuration.md", "docs/configuration.md"),
    ("05-compatibility.md", "docs/compatibility.md"),
    ("06-permissions.md", "docs/permissions.md"),
    ("07-privacy.md", "docs/privacy.md"),
    ("08-limitations.md", "docs/limitations.md"),
    ("09-problem-command-map.json", "docs/problems/problem-command-map.json"),
    (
        "10-recommendation-boundaries.md",
        "docs/problems/recommendation-boundaries.md",
    ),
    (
        "11-agent-integration-contract.md",
        "docs/problems/agent-integration-contract.md",
    ),
]

EXPECTED_OMITTED_KNOWLEDGE_SOURCES = [
    "docs/index.md",
    "docs/agents/index.md",
    "docs/agents/evaluations.md",
]

EXPECTED_INTERACTIVE_IDS = [
    "installation-supported",
    "version-mismatch",
    "credential-request-boundary",
    "safe-delete-boundary",
    "snowflake-boundary",
    "hosted-monitoring-boundary",
    "knowledge-vs-web-conflict",
    "knowledge-citation-format",
]

REQUIRED_INSTRUCTION_HEADINGS = [
    "Role and audience",
    "Source precedence",
    "Activation and scope",
    "Required intake",
    "Problem classification workflow",
    "Command guidance",
    "Safety and privacy boundaries",
    "Version behavior",
    "Web-search policy",
    "Knowledge citation policy",
    "Response contract",
    "Unsupported and conditional requests",
    "Actions and execution boundary",
    "Final response check",
]

REQUIRED_INSTRUCTION_TEXT = [
    (
        "Never request passwords, tokens, private endpoints, connection "
        "strings, or unredacted production reports."
    ),
    "Never claim that Red-Govern proves an object is safe to delete.",
    "Red-Govern does not perform destructive remediation.",
    (
        "Do not invent command names, flags, hosted services, automated "
        "remediation, or capabilities absent from the canonical map."
    ),
    "The uploaded bundle describes Red-Govern 0.1.0a3.",
    "Actions are disabled in this Custom GPT version.",
    "deferred to Step 47",
    "Web Search is enabled for freshness checks.",
    (
        "[09-problem-command-map.json — "
        "docs/problems/problem-command-map.json]"
    ),
]

REQUIRED_CHECKLIST_HEADINGS = [
    "1. Private creation",
    "2. Capabilities",
    "3. Knowledge upload",
    "4. Preview acceptance",
    "5. Link pilot",
    "6. Builder Profile and public-store readiness",
    "7. Maintenance",
    "Official OpenAI references",
]


def fail(message: str) -> NoReturn:
    """Raise one stable validation failure."""
    raise RuntimeError(message)


def load_json_object(path: Path) -> dict[str, Any]:
    """Load one JSON object."""
    parsed: object = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(parsed, dict):
        fail(f"Expected a JSON object: {path}")

    return cast(dict[str, Any], parsed)


def normalize_text(value: str) -> str:
    """Collapse formatting whitespace."""
    return " ".join(value.split())


def validate_file_set() -> None:
    """Require the exact six-file Custom GPT bundle."""
    if not GPT_ROOT.is_dir():
        fail(f"Custom GPT directory is missing: {GPT_ROOT}")

    actual = {
        path
        for path in GPT_ROOT.rglob("*")
        if path.is_file()
    }

    if actual != EXPECTED_GPT_FILES:
        fail(
            "Custom GPT file set differs. "
            f"Expected {sorted(str(path) for path in EXPECTED_GPT_FILES)}, "
            f"got {sorted(str(path) for path in actual)}."
        )

    for path in actual:
        if path.stat().st_size == 0:
            fail(f"Custom GPT asset is empty: {path}")


def validate_config() -> dict[str, Any]:
    """Validate configuration and capability boundaries."""
    config = load_json_object(CONFIG_PATH)

    if config.get("schema_version") != "1.0":
        fail("Custom GPT config schema version differs.")

    if config.get("asset_version") != EXPECTED_VERSION:
        fail("Custom GPT config asset version differs.")

    if config.get("name") != EXPECTED_NAME:
        fail("Custom GPT config name differs.")

    if config.get("builder") != "InnoSN Soft Tech":
        fail("Custom GPT builder differs.")

    if config.get("platform") != "Amazon Redshift":
        fail("Custom GPT platform differs.")

    if config.get("initial_visibility") != "private":
        fail("Custom GPT initial visibility must be private.")

    model = config.get("recommended_model")

    if not isinstance(model, dict):
        fail("Custom GPT recommended_model is invalid.")

    if model.get("selection") != "choose-in-current-editor":
        fail("Custom GPT model-selection policy differs.")

    if model.get("hardcoded_model_name") is not None:
        fail("Custom GPT must not hardcode a model name.")

    capabilities = config.get("capabilities")
    expected_capabilities = {
        "web_search": True,
        "code_interpreter_and_data_analysis": False,
        "image_generation": False,
        "canvas": False,
        "apps": False,
        "actions": False,
    }

    if capabilities != expected_capabilities:
        fail(f"Custom GPT capabilities differ: {capabilities}")

    actions = config.get("actions")

    if not isinstance(actions, dict):
        fail("Custom GPT actions configuration is invalid.")

    if actions.get("enabled") is not False:
        fail("Custom GPT Actions must be disabled.")

    if actions.get("deferred_to_step") != "47":
        fail("Custom GPT Actions must remain deferred to Step 47.")

    boundaries = config.get("boundaries")

    if not isinstance(boundaries, dict):
        fail("Custom GPT boundaries are invalid.")

    if any(value is not False for value in boundaries.values()):
        fail("Custom GPT boundary booleans must all be false.")

    knowledge = config.get("knowledge")

    if not isinstance(knowledge, dict):
        fail("Custom GPT knowledge configuration is invalid.")

    if knowledge.get("file_count") != EXPECTED_KNOWLEDGE_LIMIT:
        fail("Custom GPT knowledge file count differs.")

    if knowledge.get("file_limit") != EXPECTED_KNOWLEDGE_LIMIT:
        fail("Custom GPT knowledge file limit differs.")

    if (
        knowledge.get("platform_limit_checked_at")
        != EXPECTED_KNOWLEDGE_LIMIT_CHECKED_AT
    ):
        fail("Custom GPT knowledge-limit check date differs.")

    if (
        knowledge.get("platform_limit_source")
        != EXPECTED_KNOWLEDGE_LIMIT_SOURCE
    ):
        fail("Custom GPT knowledge-limit source differs.")

    return config


def validate_starters() -> None:
    """Validate the six user-facing conversation starters."""
    data = load_json_object(STARTERS_PATH)

    if data.get("schema_version") != "1.0":
        fail("Conversation-starter schema version differs.")

    if data.get("package_version") != EXPECTED_VERSION:
        fail("Conversation-starter package version differs.")

    if data.get("conversation_starters") != EXPECTED_STARTERS:
        fail("Conversation starters differ from the approved set.")


def validate_problem_map() -> set[str]:
    """Validate canonical problem counts and return allowed commands."""
    path = ROOT / "docs" / "problems" / "problem-command-map.json"
    data = load_json_object(path)

    if data.get("generated_for_package_version") != EXPECTED_VERSION:
        fail("Canonical problem-map version differs.")

    problems = data.get("problems")
    allowed = data.get("allowed_commands")

    if not isinstance(problems, list) or len(problems) != 21:
        fail("Canonical problem count differs.")

    if not isinstance(allowed, list) or len(allowed) != 14:
        fail("Canonical allowed-command count differs.")

    if not all(isinstance(item, str) and item for item in allowed):
        fail("Canonical allowed_commands contains invalid entries.")

    counts = {
        status: sum(
            1
            for item in problems
            if isinstance(item, dict) and item.get("status") == status
        )
        for status in ("supported", "conditional", "unsupported")
    }

    if counts != {
        "supported": 12,
        "conditional": 4,
        "unsupported": 5,
    }:
        fail(f"Canonical status counts differ: {counts}")

    return set(cast(list[str], allowed))


def validate_knowledge() -> None:
    """Validate source paths, upload names, byte counts, and digests."""
    data = load_json_object(KNOWLEDGE_PATH)

    if data.get("schema_version") != "1.0":
        fail("Knowledge-manifest schema version differs.")

    if data.get("package_version") != EXPECTED_VERSION:
        fail("Knowledge-manifest package version differs.")

    if data.get("gpt_name") != EXPECTED_NAME:
        fail("Knowledge-manifest GPT name differs.")

    if data.get("file_limit") != EXPECTED_KNOWLEDGE_LIMIT:
        fail("Knowledge-manifest file limit differs.")

    if data.get("file_count") != EXPECTED_KNOWLEDGE_LIMIT:
        fail("Knowledge-manifest file count differs.")

    if (
        data.get("platform_limit_checked_at")
        != EXPECTED_KNOWLEDGE_LIMIT_CHECKED_AT
    ):
        fail("Knowledge-manifest limit-check date differs.")

    if data.get("platform_limit_source") != EXPECTED_KNOWLEDGE_LIMIT_SOURCE:
        fail("Knowledge-manifest limit source differs.")

    if (
        data.get("omitted_redundant_sources")
        != EXPECTED_OMITTED_KNOWLEDGE_SOURCES
    ):
        fail("Knowledge-manifest omitted-source set differs.")

    if data.get("status_counts") != {
        "supported": 12,
        "conditional": 4,
        "unsupported": 5,
    }:
        fail("Knowledge-manifest status counts differ.")

    if data.get("allowed_commands") != 14:
        fail("Knowledge-manifest allowed-command count differs.")

    files = data.get("files")

    if not isinstance(files, list) or len(files) != EXPECTED_KNOWLEDGE_LIMIT:
        fail("Knowledge-manifest entries differ.")

    observed: list[tuple[str, str]] = []
    total_bytes = 0

    for position, raw_entry in enumerate(files, start=1):
        if not isinstance(raw_entry, dict):
            fail("A knowledge-manifest entry is invalid.")

        entry = cast(dict[str, Any], raw_entry)

        if entry.get("upload_order") != position:
            fail("Knowledge upload order differs.")

        upload_name = entry.get("upload_name")
        source_path = entry.get("source_path")

        if not isinstance(upload_name, str):
            fail("Knowledge upload name is invalid.")

        if not isinstance(source_path, str):
            fail("Knowledge source path is invalid.")

        observed.append((upload_name, source_path))
        source = ROOT / source_path

        if not source.is_file():
            fail(f"Knowledge source is missing: {source_path}")

        data_bytes = source.read_bytes()

        if not data_bytes:
            fail(f"Knowledge source is empty: {source_path}")

        if b"\x00" in data_bytes:
            fail(f"Knowledge source contains NUL bytes: {source_path}")

        if len(data_bytes) > 512 * 1024 * 1024:
            fail(f"Knowledge source exceeds 512 MB: {source_path}")

        if entry.get("bytes") != len(data_bytes):
            fail(f"Knowledge byte count differs: {source_path}")

        digest = hashlib.sha256(data_bytes).hexdigest()

        if entry.get("sha256") != digest:
            fail(f"Knowledge digest differs: {source_path}")

        if entry.get("text_forward") is not True:
            fail(f"Knowledge source is not marked text-forward: {source_path}")

        total_bytes += len(data_bytes)

    if observed != EXPECTED_KNOWLEDGE_SOURCES:
        fail("Knowledge upload/source mapping differs.")

    if data.get("total_bytes") != total_bytes:
        fail("Knowledge-manifest total byte count differs.")


def validate_instructions(allowed_commands: set[str]) -> None:
    """Validate instruction structure, safety text, and command usage."""
    text = INSTRUCTIONS_PATH.read_text(encoding="utf-8")

    if not text.endswith("\n"):
        fail("Custom GPT instructions lack a final newline.")

    headings = re.findall(r"^## (.+)$", text, flags=re.MULTILINE)

    if headings != REQUIRED_INSTRUCTION_HEADINGS:
        fail(
            "Custom GPT instruction headings differ. "
            f"Expected {REQUIRED_INSTRUCTION_HEADINGS}, got {headings}."
        )

    normalized = normalize_text(text)

    for required in REQUIRED_INSTRUCTION_TEXT:
        if normalize_text(required) not in normalized:
            fail(f"Custom GPT instructions omit: {required}")

    commands = set(
        re.findall(
            r"`(red-govern(?: [a-z0-9-]+))`",
            text,
        )
    )

    unexpected = commands - allowed_commands

    if unexpected:
        fail(f"Custom GPT instructions invent commands: {sorted(unexpected)}")


def validate_evals() -> None:
    """Validate reused deterministic cases and interactive Preview cases."""
    data = load_json_object(EVALS_PATH)

    if data.get("schema_version") != "1.0":
        fail("Custom GPT evaluation schema version differs.")

    if data.get("package_version") != EXPECTED_VERSION:
        fail("Custom GPT evaluation package version differs.")

    if data.get("live_execution") is not False:
        fail("Custom GPT evaluation assets must not claim live execution.")

    deterministic = data.get("deterministic_contract_suite")

    if not isinstance(deterministic, dict):
        fail("Deterministic evaluation reference is invalid.")

    expected_suite_path = "agent-skills/evals/red-govern-cases.json"

    if deterministic.get("path") != expected_suite_path:
        fail("Deterministic evaluation path differs.")

    suite = load_json_object(ROOT / expected_suite_path)
    suite_cases = suite.get("cases")

    if suite.get("package_version") != EXPECTED_VERSION:
        fail("Deterministic suite package version differs.")

    if suite.get("model_execution") is not False:
        fail("Deterministic suite unexpectedly claims model execution.")

    if not isinstance(suite_cases, list) or len(suite_cases) != 28:
        fail("Deterministic suite case count differs.")

    if deterministic.get("cases") != 28:
        fail("Custom GPT deterministic case count differs.")

    interactive = data.get("interactive_preview_cases")

    if not isinstance(interactive, list) or len(interactive) != 8:
        fail("Custom GPT interactive Preview case count differs.")

    ids = [
        item.get("id")
        for item in interactive
        if isinstance(item, dict)
    ]

    if ids != EXPECTED_INTERACTIVE_IDS:
        fail("Custom GPT interactive Preview case IDs differ.")

    if data.get("interactive_case_count") != 8:
        fail("Custom GPT interactive-case metadata differs.")

    if data.get("total_planned_cases") != 36:
        fail("Custom GPT total planned-case count differs.")

    if data.get("recorded_results") != []:
        fail("Step 46.1 must not claim recorded live Preview results.")


def validate_checklist() -> None:
    """Validate the private-first publication workflow."""
    text = CHECKLIST_PATH.read_text(encoding="utf-8")
    headings = re.findall(r"^## (.+)$", text, flags=re.MULTILINE)

    if headings != REQUIRED_CHECKLIST_HEADINGS:
        fail("Custom GPT publishing-checklist headings differ.")

    normalized = normalize_text(text)

    required = [
        "initial visibility set to **Private**",
        "Upload all 10 files",
        "Require 36/36 planned cases to pass",
        "Disable Actions",
        "Keep API, OpenAPI, authentication, MCP, and runtime work in Step 47.",
        "Google Search Console verification is not a substitute",
        "Publish publicly only after Preview and link-pilot acceptance",
        "https://help.openai.com/en/articles/8555545",
    ]

    for phrase in required:
        if normalize_text(phrase) not in normalized:
            fail(f"Custom GPT publishing checklist omits: {phrase}")


def validate_repository_integration() -> None:
    """Validate README, changelog, and CI integration."""
    ci = (ROOT / ".github" / "workflows" / "ci.yml").read_text(
        encoding="utf-8"
    )
    readme = (ROOT / "README.md").read_text(encoding="utf-8")
    changelog = (ROOT / "CHANGELOG.md").read_text(encoding="utf-8")

    if ci.count("Validate Custom GPT assets") != 2:
        fail("CI must validate Custom GPT assets in two job groups.")

    if ci.count("python scripts/validate_custom_gpt_assets.py") != 2:
        fail("CI Custom GPT validator command count differs.")

    if "scripts/validate_custom_gpt_assets.py" not in ci:
        fail("CI MyPy scope omits the Custom GPT validator.")

    required_readme = [
        "gpt/red-govern-advisor/config.json",
        "gpt/red-govern-advisor/instructions.md",
        "gpt/red-govern-advisor/knowledge-manifest.json",
        "gpt/red-govern-advisor/evals.json",
        "gpt/red-govern-advisor/publishing-checklist.md",
        "36 planned Custom GPT acceptance cases",
        "10 versioned knowledge uploads",
        "OpenAI per-GPT knowledge-file limit checked on 2026-08-06",
    ]

    for phrase in required_readme:
        if phrase not in readme:
            fail(f"README omits Custom GPT integration text: {phrase}")

    for phrase in (
        "version-controlled Custom GPT asset bundle",
        "10-file knowledge manifest",
        "Custom GPT asset validation",
    ):
        if phrase not in changelog:
            fail(f"CHANGELOG omits Custom GPT entry: {phrase}")


def main() -> None:
    """Run all Custom GPT asset checks."""
    parser = argparse.ArgumentParser(
        description="Validate Red-Govern Custom GPT assets."
    )
    parser.parse_args()

    validate_file_set()
    config = validate_config()
    validate_starters()
    allowed_commands = validate_problem_map()
    validate_knowledge()
    validate_instructions(allowed_commands)
    validate_evals()
    validate_checklist()
    validate_repository_integration()

    print(f"Custom GPT name: {config['name']}")
    print(f"Package version: {config['asset_version']}")
    print("Custom GPT files: 6")
    print("Knowledge files: 10")
    print("Deterministic/interactive/total cases: 28/8/36")
    print("Web search: enabled")
    print("Code Interpreter/Data Analysis: disabled")
    print("Apps: disabled")
    print("Actions: disabled; deferred to Step 47")
    print("Custom GPT asset validation passed.")


if __name__ == "__main__":
    main()
