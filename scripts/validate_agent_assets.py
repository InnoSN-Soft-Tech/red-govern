"""Validate Red-Govern's portable AI-agent Skill bundle."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, NoReturn, cast

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "agent-skills" / "red-govern"
SKILL_PATH = SKILL_ROOT / "SKILL.md"
REFERENCE_ROOT = SKILL_ROOT / "references"

EXPECTED_NAME = "red-govern"
EXPECTED_VERSION = "0.1.0a3"
EXPECTED_DESCRIPTION = (
    "Guide users and AI agents through safe, version-aware Amazon Redshift "
    "governance workflows with Red-Govern. Use when the problem involves "
    "Redshift inventory, configured quota pressure, classification, privacy "
    "review, query workload inspection, diagnostics, snapshots, change "
    "comparison, or local reports; do not use for destructive remediation, "
    "credential collection, non-Redshift databases, or unsupported hosted "
    "monitoring."
)

REFERENCE_PAIRS = {
    (
        ROOT / "docs" / "problems" / "problem-command-map.json"
    ): REFERENCE_ROOT / "problem-command-map.json",
    (
        ROOT / "docs" / "problems" / "problem-command-map.schema.json"
    ): REFERENCE_ROOT / "problem-command-map.schema.json",
    (
        ROOT / "docs" / "problems" / "recommendation-boundaries.md"
    ): REFERENCE_ROOT / "recommendation-boundaries.md",
    (
        ROOT / "docs" / "problems" / "agent-integration-contract.md"
    ): REFERENCE_ROOT / "agent-integration-contract.md",
}

REQUIRED_SECTIONS = [
    "Purpose and activation",
    "Required inputs",
    "Safety and privacy boundaries",
    "Problem classification",
    "Version and installation checks",
    "Command-selection workflow",
    "Output interpretation",
    "When not to recommend Red-Govern",
    "Examples",
    "Final validation checklist",
]

REQUIRED_SAFETY_TEXT = [
    "Never request passwords, tokens, private endpoints, connection strings, "
    "or unredacted production reports.",
    "Never claim that Red-Govern proves an object is safe to delete.",
    "Red-Govern does not perform destructive remediation.",
    "Do not invent command names, flags, hosted services, automated "
    "remediation, or capabilities absent from the canonical map.",
]

EXPECTED_STATUS_COUNTS = {
    "supported": 12,
    "conditional": 4,
    "unsupported": 5,
}


def fail(message: str) -> NoReturn:
    """Raise a stable validation failure."""
    raise RuntimeError(message)


def normalize_text(value: str) -> str:
    """Collapse formatting whitespace for semantic checks."""
    return " ".join(value.split())


def load_json_object(path: Path) -> dict[str, Any]:
    """Load one JSON object."""
    parsed: object = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(parsed, dict):
        fail(f"Expected a JSON object: {path}")

    return cast(dict[str, Any], parsed)


def parse_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Parse the strict two-key SKILL.md frontmatter."""
    if not text.startswith("---\n"):
        fail("SKILL.md must start with YAML frontmatter.")

    closing = text.find("\n---\n", 4)

    if closing == -1:
        fail("SKILL.md frontmatter is not closed.")

    raw = text[4:closing]
    body = text[closing + 5 :]
    metadata: dict[str, str] = {}

    for line in raw.splitlines():
        if not line.strip():
            continue

        if ":" not in line:
            fail(f"Invalid SKILL.md frontmatter line: {line!r}")

        key, value = line.split(":", 1)
        key = key.strip()
        value = value.strip()

        if not key or not value:
            fail(f"Invalid SKILL.md frontmatter entry: {line!r}")

        if key in metadata:
            fail(f"Duplicate SKILL.md frontmatter key: {key}")

        metadata[key] = value

    return metadata, body


def validate_reference_equality() -> None:
    """Require version-matched byte-for-byte canonical references."""
    expected_paths = set(REFERENCE_PAIRS.values())
    actual_paths = {
        path for path in REFERENCE_ROOT.iterdir() if path.is_file()
    }

    if actual_paths != expected_paths:
        fail(
            "Skill reference-file set differs. "
            f"Expected {[path.name for path in sorted(expected_paths)]}, "
            f"got {[path.name for path in sorted(actual_paths)]}."
        )

    for canonical, reference in REFERENCE_PAIRS.items():
        if not canonical.is_file():
            fail(f"Canonical reference is missing: {canonical}")

        if not reference.is_file():
            fail(f"Skill reference is missing: {reference}")

        if canonical.read_bytes() != reference.read_bytes():
            fail(f"Skill reference drift detected: {reference}")


def validate_problem_map() -> tuple[set[str], dict[str, int]]:
    """Validate the bundled problem map and return its command/status sets."""
    mapping = load_json_object(
        REFERENCE_ROOT / "problem-command-map.json"
    )

    if mapping.get("generated_for_package_version") != EXPECTED_VERSION:
        fail("Bundled problem map version is unexpected.")

    allowed_raw = mapping.get("allowed_commands")

    if not isinstance(allowed_raw, list):
        fail("Bundled allowed_commands must be a list.")

    if not all(isinstance(item, str) and item for item in allowed_raw):
        fail("Bundled allowed_commands contains invalid entries.")

    allowed = set(cast(list[str], allowed_raw))

    if len(allowed) != 14:
        fail(f"Expected 14 allowed commands, found {len(allowed)}.")

    problems_raw = mapping.get("problems")

    if not isinstance(problems_raw, list):
        fail("Bundled problems must be a list.")

    if len(problems_raw) != 21:
        fail(f"Expected 21 problem entries, found {len(problems_raw)}.")

    status_counts = {key: 0 for key in EXPECTED_STATUS_COUNTS}

    for problem_raw in problems_raw:
        if not isinstance(problem_raw, dict):
            fail("A bundled problem entry is not an object.")

        problem = cast(dict[str, Any], problem_raw)
        status = problem.get("status")

        if not isinstance(status, str) or status not in status_counts:
            fail(
                f"Problem {problem.get('id')} has invalid status: {status}"
            )

        status_counts[status] += 1
        commands = problem.get("commands")

        if not isinstance(commands, list):
            fail(f"Problem {problem.get('id')} commands are invalid.")

        for command in commands:
            if not isinstance(command, str) or command not in allowed:
                fail(
                    f"Problem {problem.get('id')} uses an unapproved "
                    f"command: {command}"
                )

    if status_counts != EXPECTED_STATUS_COUNTS:
        fail(f"Bundled status counts are unexpected: {status_counts}")

    return allowed, status_counts


def validate_skill_text(allowed: set[str]) -> dict[str, str]:
    """Validate SKILL.md metadata, sections, commands, and boundaries."""
    text = SKILL_PATH.read_text(encoding="utf-8")
    metadata, body = parse_frontmatter(text)

    if set(metadata) != {"name", "description"}:
        fail(
            "SKILL.md frontmatter must contain exactly name and "
            "description."
        )

    if metadata["name"] != EXPECTED_NAME:
        fail("SKILL.md name is unexpected.")

    if not re.fullmatch(r"[a-z0-9-]+", metadata["name"]):
        fail("SKILL.md name format is invalid.")

    if len(metadata["name"]) > 64:
        fail("SKILL.md name exceeds 64 characters.")

    if metadata["description"] != EXPECTED_DESCRIPTION:
        fail("SKILL.md description differs from the approved metadata.")

    if len(metadata["description"]) > 1024:
        fail("SKILL.md description exceeds 1024 characters.")

    if "<" in metadata["name"] + metadata["description"]:
        fail("SKILL.md metadata contains an XML marker.")

    if ">" in metadata["name"] + metadata["description"]:
        fail("SKILL.md metadata contains an XML marker.")

    headings = re.findall(r"^## (.+)$", body, flags=re.MULTILINE)

    if headings != REQUIRED_SECTIONS:
        fail(
            "SKILL.md section order differs. "
            f"Expected {REQUIRED_SECTIONS}, got {headings}."
        )

    normalized = normalize_text(body)

    for required in REQUIRED_SAFETY_TEXT:
        if normalize_text(required) not in normalized:
            fail(f"SKILL.md omits safety text: {required}")

    for status in EXPECTED_STATUS_COUNTS:
        if f"`{status}`" not in body:
            fail(f"SKILL.md omits problem status: {status}")

    if EXPECTED_VERSION not in body:
        fail("SKILL.md omits the version-matched package version.")

    for reference_name in (
        "problem-command-map.json",
        "problem-command-map.schema.json",
        "recommendation-boundaries.md",
        "agent-integration-contract.md",
    ):
        if reference_name not in body:
            fail(f"SKILL.md omits reference: {reference_name}")

    skill_commands = set(
        re.findall(
            r"`(red-govern(?: [a-z0-9-]+))`",
            body,
        )
    )

    if skill_commands != allowed:
        fail(
            "SKILL.md command set differs from allowed_commands. "
            f"Missing {sorted(allowed - skill_commands)}, "
            f"unexpected {sorted(skill_commands - allowed)}."
        )

    return metadata


def main() -> int:
    """Validate the portable Red-Govern Skill bundle."""
    if not SKILL_PATH.is_file():
        fail(f"SKILL.md is missing: {SKILL_PATH}")

    if not REFERENCE_ROOT.is_dir():
        fail(f"Skill reference directory is missing: {REFERENCE_ROOT}")

    validate_reference_equality()
    allowed, status_counts = validate_problem_map()
    metadata = validate_skill_text(allowed)

    print("Validated Skill:", SKILL_PATH)
    print("Skill name:", metadata["name"])
    print("Skill description length:", len(metadata["description"]))
    print("Package version:", EXPECTED_VERSION)
    print("Problem entries: 21")
    print("Supported:", status_counts["supported"])
    print("Conditional:", status_counts["conditional"])
    print("Unsupported:", status_counts["unsupported"])
    print("Allowed commands:", len(allowed))
    print("Reference files: 4")
    print("Reference drift: none")
    print("Portable agent-asset validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
