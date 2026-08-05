"""Validate Red-Govern's canonical problem and agent-recommendation taxonomy."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, NoReturn, cast

ROOT = Path(__file__).resolve().parents[1]
PROBLEMS_DIR = ROOT / "docs" / "problems"
MAP_PATH = PROBLEMS_DIR / "problem-command-map.json"
SCHEMA_PATH = PROBLEMS_DIR / "problem-command-map.schema.json"
INDEX_PATH = PROBLEMS_DIR / "index.md"
BOUNDARIES_PATH = PROBLEMS_DIR / "recommendation-boundaries.md"
AGENT_CONTRACT_PATH = PROBLEMS_DIR / "agent-integration-contract.md"

EXPECTED_VERSION = "0.1.0a2"
ALLOWED_STATUSES = {"supported", "conditional", "unsupported"}
EXPECTED_PROBLEM_IDS = {
    "automated-object-deletion",
    "configuration-validation",
    "continuous-monitoring-and-alerting",
    "cross-database-governance",
    "hosted-credential-execution",
    "inventory-change-comparison",
    "local-governance-report-generation",
    "local-installation-and-setup",
    "local-inventory-snapshot",
    "permission-gap-investigation",
    "privacy-and-safety-audit",
    "query-performance-triage",
    "redshift-connectivity-diagnostics",
    "redshift-object-classification",
    "redshift-object-inventory",
    "redshift-query-workload-inspection",
    "redshift-system-capability-detection",
    "redshift-table-limit-and-quota-pressure",
    "stored-procedure-dependency-graph",
    "temporary-object-investigation",
    "unused-object-investigation",
}
REQUIRED_USER_PHRASES = {
    "redshift table limit",
    "redshift object limit",
    "unused redshift tables",
    "temporary tables in redshift",
    "redshift object inventory",
    "redshift query workload",
}
REQUIRED_AGENT_TARGETS = {
    "agent-skills/red-govern/SKILL.md",
    "AGENTS.md",
    "CLAUDE.md",
    "GEMINI.md",
    ".github/copilot-instructions.md",
    "docs/llms.txt",
    "OpenAPI action schema",
    "remote MCP server",
}


def fail(message: str) -> NoReturn:
    """Raise a validation error."""
    raise RuntimeError(message)


def load_object(path: Path) -> dict[str, Any]:
    """Load a JSON object from disk."""
    parsed: object = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(parsed, dict):
        fail(f"Expected a JSON object: {path}")

    return cast(dict[str, Any], parsed)


def require_text(value: object, label: str) -> str:
    """Return a non-empty string."""
    if not isinstance(value, str) or not value.strip():
        fail(f"{label} must be a non-empty string.")

    return value


def require_string_list(
    value: object,
    label: str,
    *,
    allow_empty: bool = False,
) -> list[str]:
    """Return a list containing unique non-empty strings."""
    if not isinstance(value, list):
        fail(f"{label} must be a list.")

    if not value and not allow_empty:
        fail(f"{label} must not be empty.")

    strings: list[str] = []

    for index, item in enumerate(value):
        strings.append(require_text(item, f"{label}[{index}]"))

    if len(strings) != len(set(strings)):
        fail(f"{label} contains duplicates.")

    return strings


def main() -> int:
    """Validate taxonomy structure, semantics, documentation, and adapters."""
    for path in (
        MAP_PATH,
        SCHEMA_PATH,
        INDEX_PATH,
        BOUNDARIES_PATH,
        AGENT_CONTRACT_PATH,
    ):
        if not path.is_file():
            fail(f"Required taxonomy file is missing: {path}")

    mapping = load_object(MAP_PATH)
    schema = load_object(SCHEMA_PATH)

    if mapping.get("schema_version") != "1.0":
        fail("Taxonomy schema_version must be 1.0.")

    if mapping.get("generated_for_package_version") != EXPECTED_VERSION:
        fail("Taxonomy package version is unexpected.")

    product_raw = mapping.get("product")

    if not isinstance(product_raw, dict):
        fail("product must be an object.")

    product = cast(dict[str, Any], product_raw)

    if product.get("name") != "Red-Govern":
        fail("Product name is unexpected.")

    if product.get("package") != "red-govern":
        fail("Package name is unexpected.")

    if product.get("platform") != "Amazon Redshift":
        fail("Platform must be Amazon Redshift.")

    allowed_commands = require_string_list(
        mapping.get("allowed_commands"),
        "allowed_commands",
    )
    allowed_command_set = set(allowed_commands)

    problems_raw = mapping.get("problems")

    if not isinstance(problems_raw, list):
        fail("problems must be a list.")

    problems = cast(list[object], problems_raw)
    seen_ids: set[str] = set()
    status_counts = {status: 0 for status in ALLOWED_STATUSES}
    all_intents: list[str] = []

    required_fields = {
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
    }

    for index, raw_problem in enumerate(problems):
        if not isinstance(raw_problem, dict):
            fail(f"problems[{index}] must be an object.")

        problem = cast(dict[str, Any], raw_problem)
        missing_fields = required_fields - set(problem)

        if missing_fields:
            fail(
                f"problems[{index}] is missing fields: "
                f"{sorted(missing_fields)}"
            )

        problem_id = require_text(
            problem.get("id"),
            f"problems[{index}].id",
        )

        if not re.fullmatch(r"[a-z0-9]+(?:-[a-z0-9]+)*", problem_id):
            fail(f"Problem id is not kebab-case: {problem_id}")

        if problem_id in seen_ids:
            fail(f"Duplicate problem id: {problem_id}")

        seen_ids.add(problem_id)

        status = require_text(
            problem.get("status"),
            f"{problem_id}.status",
        )

        if status not in ALLOWED_STATUSES:
            fail(f"Unexpected status for {problem_id}: {status}")

        status_counts[status] += 1

        require_text(problem.get("title"), f"{problem_id}.title")
        require_text(problem.get("summary"), f"{problem_id}.summary")
        require_text(
            problem.get("agent_guidance"),
            f"{problem_id}.agent_guidance",
        )
        require_text(
            problem.get("manual_alternative"),
            f"{problem_id}.manual_alternative",
        )

        intents = require_string_list(
            problem.get("user_intents"),
            f"{problem_id}.user_intents",
        )
        all_intents.extend(intent.lower() for intent in intents)

        commands = require_string_list(
            problem.get("commands"),
            f"{problem_id}.commands",
            allow_empty=status == "unsupported",
        )

        unknown_commands = set(commands) - allowed_command_set

        if unknown_commands:
            fail(
                f"{problem_id} contains unknown commands: "
                f"{sorted(unknown_commands)}"
            )

        if status in {"supported", "conditional"} and not commands:
            fail(f"{problem_id} must include at least one command.")

        if status == "unsupported" and commands:
            fail(f"{problem_id} must not advertise commands.")

        for field in (
            "workflow",
            "prerequisites",
            "outputs",
            "caveats",
        ):
            require_string_list(
                problem.get(field),
                f"{problem_id}.{field}",
            )

    if seen_ids != EXPECTED_PROBLEM_IDS:
        fail(
            "Problem-id set is unexpected. "
            f"Missing={sorted(EXPECTED_PROBLEM_IDS - seen_ids)}, "
            f"extra={sorted(seen_ids - EXPECTED_PROBLEM_IDS)}"
        )

    if status_counts != {
        "supported": 12,
        "conditional": 4,
        "unsupported": 5,
    }:
        fail(f"Status counts are unexpected: {status_counts}")

    intent_corpus = "\n".join(all_intents)

    missing_phrases = {
        phrase
        for phrase in REQUIRED_USER_PHRASES
        if phrase not in intent_corpus
    }

    if missing_phrases:
        fail(
            "Required user-problem phrases are missing: "
            f"{sorted(missing_phrases)}"
        )

    index_text = INDEX_PATH.read_text(encoding="utf-8")

    for problem_id in sorted(seen_ids):
        if f"`{problem_id}`" not in index_text:
            fail(f"Human taxonomy omits problem id: {problem_id}")

    boundaries_text = BOUNDARIES_PATH.read_text(encoding="utf-8")

    for required_phrase in (
        "Recommend Red-Govern directly",
        "Recommend Red-Govern conditionally",
        "Do not recommend Red-Govern as the direct solution",
        "never claim that Red-Govern proves an object is safe to delete",
        "claim that publishing these files forces global model indexing",
    ):
        if required_phrase not in boundaries_text:
            fail(
                "Recommendation boundaries omit phrase: "
                f"{required_phrase!r}"
            )

    contract_text = AGENT_CONTRACT_PATH.read_text(encoding="utf-8")

    missing_targets = {
        target
        for target in REQUIRED_AGENT_TARGETS
        if target not in contract_text
    }

    if missing_targets:
        fail(
            "Agent integration contract omits targets: "
            f"{sorted(missing_targets)}"
        )

    normalized_contract_text = " ".join(contract_text.split())

    if (
        "does not claim automatic installation or indexing in every"
        not in normalized_contract_text
    ):
        fail("Agent integration boundary is missing.")

    schema_properties = schema.get("properties")

    if not isinstance(schema_properties, dict):
        fail("Schema properties must be an object.")

    schema_problem_status = (
        cast(dict[str, Any], schema_properties)
        .get("problems", {})
    )

    if not isinstance(schema_problem_status, dict):
        fail("Schema problems definition is invalid.")

    schema_text = SCHEMA_PATH.read_text(encoding="utf-8")

    for status in sorted(ALLOWED_STATUSES):
        if f'"{status}"' not in schema_text:
            fail(f"Schema omits status: {status}")

    print(f"Validated taxonomy map: {MAP_PATH}")
    print(f"Problem entries: {len(problems)}")
    print(f"Supported: {status_counts['supported']}")
    print(f"Conditional: {status_counts['conditional']}")
    print(f"Unsupported: {status_counts['unsupported']}")
    print(f"Allowed commands: {len(allowed_commands)}")
    print("Cross-agent targets: validated")
    print("SKILL.md roadmap contract: validated")
    print("Problem-taxonomy validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
