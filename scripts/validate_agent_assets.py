"""Validate Red-Govern Skills, adapters, evaluations, and distribution."""

from __future__ import annotations

import hashlib
import json
import re
from pathlib import Path
from typing import Any, NoReturn, cast

ROOT = Path(__file__).resolve().parents[1]
PORTABLE_ROOT = ROOT / "agent-skills" / "red-govern"
SKILL_PATH = PORTABLE_ROOT / "SKILL.md"
REFERENCE_ROOT = PORTABLE_ROOT / "references"
CLAUDE_ROOT = ROOT / ".claude" / "skills" / "red-govern"

EVALUATION_PATH = (
    ROOT / "agent-skills" / "evals" / "red-govern-cases.json"
)
DISTRIBUTION_README = (
    ROOT / "agent-skills" / "distribution" / "README.md"
)
DIST_ROOT = ROOT / "agent-skills" / "dist"
ARCHIVE_PATH = DIST_ROOT / "red-govern-0.1.0a3.zip"
SHA_PATH = DIST_ROOT / "red-govern-0.1.0a3.sha256"
MANIFEST_PATH = DIST_ROOT / "manifest.json"

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

SKILL_RELATIVE_PATHS = [
    Path("SKILL.md"),
    Path("references/agent-integration-contract.md"),
    Path("references/problem-command-map.json"),
    Path("references/problem-command-map.schema.json"),
    Path("references/recommendation-boundaries.md"),
]

ADAPTER_PATHS = {
    "agents": ROOT / "AGENTS.md",
    "claude": ROOT / "CLAUDE.md",
    "gemini": ROOT / "GEMINI.md",
    "copilot": ROOT / ".github" / "copilot-instructions.md",
}

AGENT_DOC_PATHS = [
    ROOT / "docs" / "agents" / "index.md",
    ROOT / "docs" / "agents" / "installation.md",
    ROOT / "docs" / "agents" / "evaluations.md",
]

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

COMMON_ADAPTER_TEXT = [
    "Red-Govern does not perform destructive remediation.",
    "Never request credentials or unredacted production outputs.",
    "Do not invent Red-Govern commands, flags, or capabilities.",
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


def digest_bytes(data: bytes) -> str:
    """Return a SHA-256 digest."""
    return hashlib.sha256(data).hexdigest()


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


def validate_claude_mirror() -> None:
    """Require the Claude project Skill to mirror the portable bundle."""
    if not CLAUDE_ROOT.is_dir():
        fail(f"Claude project Skill directory is missing: {CLAUDE_ROOT}")

    expected = {
        CLAUDE_ROOT / relative for relative in SKILL_RELATIVE_PATHS
    }
    actual = {
        path for path in CLAUDE_ROOT.rglob("*") if path.is_file()
    }

    if actual != expected:
        fail(
            "Claude project Skill file set differs. "
            f"Expected {sorted(str(path) for path in expected)}, "
            f"got {sorted(str(path) for path in actual)}."
        )

    for relative in SKILL_RELATIVE_PATHS:
        portable = PORTABLE_ROOT / relative
        mirror = CLAUDE_ROOT / relative

        if portable.read_bytes() != mirror.read_bytes():
            fail(f"Claude project Skill drift detected: {mirror}")


def validate_problem_map() -> tuple[set[str], dict[str, int]]:
    """Validate the bundled problem map and return command/status sets."""
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


def validate_repository_instructions() -> None:
    """Validate repository-wide and platform-specific adapters."""
    for name, path in ADAPTER_PATHS.items():
        if not path.is_file():
            fail(f"Repository adapter is missing: {path}")

        text = path.read_text(encoding="utf-8")
        normalized = normalize_text(text)

        if not text.endswith("\n"):
            fail(f"Repository adapter lacks final newline: {path}")

        if len(text) > 8000:
            fail(f"Repository adapter is unexpectedly large: {path}")

        for required in COMMON_ADAPTER_TEXT:
            if normalize_text(required) not in normalized:
                fail(f"{name} adapter omits safety text: {required}")

    agents = ADAPTER_PATHS["agents"].read_text(encoding="utf-8")
    agents_normalized = normalize_text(agents)

    for required in (
        "docs/problems/problem-command-map.json",
        "agent-skills/red-govern/SKILL.md",
        ".claude/skills/red-govern/",
        ".github/workflows/docs.yml",
        "create a fresh public-safe commit",
        "python scripts/validate_agent_assets.py",
        "mkdocs build --strict",
    ):
        if normalize_text(required) not in agents_normalized:
            fail(f"AGENTS.md omits repository rule: {required}")

    thin_requirements = {
        "claude": [
            "Follow `AGENTS.md`",
            ".claude/skills/red-govern/SKILL.md",
        ],
        "gemini": [
            "Follow `AGENTS.md`",
            "agent-skills/red-govern/SKILL.md",
        ],
        "copilot": [
            "Follow `AGENTS.md`",
            "agent-skills/red-govern/SKILL.md",
        ],
    }

    for name, required_items in thin_requirements.items():
        text = ADAPTER_PATHS[name].read_text(encoding="utf-8")
        normalized = normalize_text(text)

        if len(text) > 2000:
            fail(f"{name} adapter is not thin.")

        if "```" in text:
            fail(f"{name} adapter must not duplicate command blocks.")

        commands = set(
            re.findall(
                r"`(red-govern(?: [a-z0-9-]+))`",
                text,
            )
        )

        if commands:
            fail(
                f"{name} adapter duplicates Red-Govern commands: "
                f"{sorted(commands)}"
            )

        for required in required_items:
            if normalize_text(required) not in normalized:
                fail(f"{name} adapter omits: {required}")


def validate_evaluation_and_docs() -> None:
    """Validate evaluation metadata, installation docs, and legal text."""
    suite = load_json_object(EVALUATION_PATH)

    if suite.get("package_version") != EXPECTED_VERSION:
        fail("Evaluation suite version is unexpected.")

    if suite.get("suite_type") != "deterministic-contract-fixtures":
        fail("Evaluation suite type is unexpected.")

    if suite.get("model_execution") is not False:
        fail("Evaluation suite must not claim live model execution.")

    cases = suite.get("cases")

    if not isinstance(cases, list) or len(cases) != 28:
        fail("Evaluation suite must contain 28 cases.")

    for path in AGENT_DOC_PATHS:
        if not path.is_file():
            fail(f"Agent documentation is missing: {path}")

        text = path.read_text(encoding="utf-8")

        if not text.endswith("\n"):
            fail(f"Agent documentation lacks final newline: {path}")

    if not DISTRIBUTION_README.is_file():
        fail("Distribution README is missing.")

    distribution_text = normalize_text(
        DISTRIBUTION_README.read_text(encoding="utf-8")
    )

    for required in (
        "PolyForm Perimeter License 1.0.1",
        "COMMERCIAL_LICENSE.md",
        "NOTICE",
        "TRADEMARKS.md",
        "does not automatically install, activate, or index Red-Govern",
        "does not execute or score a live language model",
    ):
        if normalize_text(required) not in distribution_text:
            fail(f"Distribution README omits: {required}")


def validate_distribution_metadata() -> None:
    """Validate tracked distribution metadata and archive digest."""
    for path in (ARCHIVE_PATH, SHA_PATH, MANIFEST_PATH):
        if not path.is_file():
            fail(f"Skill distribution output is missing: {path}")

    manifest = load_json_object(MANIFEST_PATH)

    if manifest.get("package_version") != EXPECTED_VERSION:
        fail("Distribution manifest version is unexpected.")

    if manifest.get("artifact") != ARCHIVE_PATH.name:
        fail("Distribution artifact name is unexpected.")

    if manifest.get("deterministic") is not True:
        fail("Distribution manifest is not deterministic.")

    legal_files = manifest.get("legal_files")

    if legal_files != [
        "red-govern/LICENSE.md",
        "red-govern/COMMERCIAL_LICENSE.md",
        "red-govern/NOTICE",
        "red-govern/TRADEMARKS.md",
    ]:
        fail("Distribution legal-file list is unexpected.")

    archive_bytes = ARCHIVE_PATH.read_bytes()
    archive_sha = digest_bytes(archive_bytes)

    if manifest.get("sha256") != archive_sha:
        fail("Distribution manifest digest differs from archive.")

    expected_checksum = f"{archive_sha}  {ARCHIVE_PATH.name}\n"

    if SHA_PATH.read_text(encoding="utf-8") != expected_checksum:
        fail("Distribution checksum file differs.")


def main() -> int:
    """Validate every tracked AI-agent asset."""
    if not SKILL_PATH.is_file():
        fail(f"SKILL.md is missing: {SKILL_PATH}")

    if not REFERENCE_ROOT.is_dir():
        fail(f"Skill reference directory is missing: {REFERENCE_ROOT}")

    validate_reference_equality()
    validate_claude_mirror()
    allowed, status_counts = validate_problem_map()
    metadata = validate_skill_text(allowed)
    validate_repository_instructions()
    validate_evaluation_and_docs()
    validate_distribution_metadata()

    print("Validated portable Skill:", SKILL_PATH)
    print("Skill name:", metadata["name"])
    print("Skill description length:", len(metadata["description"]))
    print("Package version:", EXPECTED_VERSION)
    print("Problem entries: 21")
    print("Supported:", status_counts["supported"])
    print("Conditional:", status_counts["conditional"])
    print("Unsupported:", status_counts["unsupported"])
    print("Allowed commands:", len(allowed))
    print("Portable reference files: 4")
    print("Claude project Skill files: 5")
    print("Repository instruction files: 4")
    print("Evaluation cases: 28")
    print("Agent documentation files: 3")
    print("Distribution legal files: 4")
    print("Cross-agent drift: none")
    print("Portable agent-asset validation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
