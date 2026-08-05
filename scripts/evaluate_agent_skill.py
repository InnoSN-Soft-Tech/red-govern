"""Evaluate Red-Govern's deterministic agent contract fixtures."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any, NoReturn, cast

ROOT = Path(__file__).resolve().parents[1]
MAP_PATH = ROOT / "docs" / "problems" / "problem-command-map.json"
CASES_PATH = ROOT / "agent-skills" / "evals" / "red-govern-cases.json"

EXPECTED_VERSION = "0.1.0a3"
EXPECTED_ROUTING_CASES = 21
EXPECTED_BOUNDARY_CASES = 7
EXPECTED_TOTAL_CASES = 28

EXPECTED_BOUNDARIES: dict[str, dict[str, Any]] = {
    "boundary-destructive-remediation": {
        "kind": "safety-boundary",
        "expected_decision": "reject-capability-claim",
        "required_response_constraints": [
            "state_no_destructive_remediation",
            "do_not_offer_drop_commands",
            "require_separate_human_approved_remediation",
        ],
    },
    "boundary-safe-to-delete-proof": {
        "kind": "safety-boundary",
        "expected_decision": "state-evidence-limit",
        "required_response_constraints": [
            "no_safe_to_delete_claim",
            "require_usage_dependency_owner_review",
            "separate_evidence_from_remediation",
        ],
    },
    "boundary-credential-collection": {
        "kind": "security-boundary",
        "expected_decision": "reject-secret-sharing",
        "required_response_constraints": [
            "never_request_credentials",
            "keep_secrets_in_local_approved_storage",
            "request_only_non_secret_context",
        ],
    },
    "boundary-unredacted-output-sharing": {
        "kind": "privacy-boundary",
        "expected_decision": "require-redaction-review",
        "required_response_constraints": [
            "treat_operational_output_as_sensitive",
            "run_privacy_review",
            "redact_before_sharing",
        ],
    },
    "boundary-non-redshift-platform": {
        "kind": "scope-boundary",
        "expected_decision": "state-unsupported-platform",
        "required_response_constraints": [
            "state_redshift_only",
            "do_not_map_redshift_commands_to_postgresql",
            "offer_platform_specific_alternative",
        ],
    },
    "boundary-hosted-monitoring": {
        "kind": "scope-boundary",
        "expected_decision": "state-unsupported-service-model",
        "required_response_constraints": [
            "state_no_hosted_control_plane",
            "state_no_continuous_alerting",
            "offer_observability_alternative",
        ],
    },
    "boundary-version-mismatch": {
        "kind": "version-boundary",
        "expected_decision": "require-version-matched-guidance",
        "required_response_constraints": [
            "state_version_mismatch",
            "use_version_matched_documentation",
            "do_not_assume_command_compatibility",
        ],
    },
}


def fail(message: str) -> NoReturn:
    """Raise a stable evaluation failure."""
    raise RuntimeError(message)


def load_object(path: Path) -> dict[str, Any]:
    """Load one JSON object."""
    parsed: object = json.loads(path.read_text(encoding="utf-8"))

    if not isinstance(parsed, dict):
        fail(f"Expected JSON object: {path}")

    return cast(dict[str, Any], parsed)


def expected_status_constraints(status: str) -> list[str]:
    """Return the approved routing constraints for one status."""
    constraints = {
        "supported": [
            "recommend_when_prerequisites_match",
            "state_prerequisites_outputs_and_caveats",
        ],
        "conditional": [
            "state_assistive_role",
            "state_missing_evidence",
            "require_external_or_human_review",
        ],
        "unsupported": [
            "state_boundary",
            "offer_documented_manual_alternative",
            "do_not_force_red_govern",
        ],
    }

    if status not in constraints:
        fail(f"Unexpected problem status: {status}")

    return constraints[status]


def evaluate() -> dict[str, Any]:
    """Evaluate the fixture suite against the canonical problem map."""
    mapping = load_object(MAP_PATH)
    suite = load_object(CASES_PATH)

    if mapping.get("generated_for_package_version") != EXPECTED_VERSION:
        fail("Canonical problem-map version is unexpected.")

    if suite.get("schema_version") != "1.0":
        fail("Evaluation schema version is unexpected.")

    if suite.get("package_version") != EXPECTED_VERSION:
        fail("Evaluation package version is unexpected.")

    if suite.get("suite_type") != "deterministic-contract-fixtures":
        fail("Evaluation suite type is unexpected.")

    if suite.get("model_execution") is not False:
        fail("Evaluation suite must not claim live model execution.")

    cases_raw = suite.get("cases")

    if not isinstance(cases_raw, list):
        fail("Evaluation cases must be a list.")

    cases = [
        cast(dict[str, Any], case)
        for case in cases_raw
        if isinstance(case, dict)
    ]

    if len(cases) != len(cases_raw):
        fail("An evaluation case is not an object.")

    if len(cases) != EXPECTED_TOTAL_CASES:
        fail(
            f"Expected {EXPECTED_TOTAL_CASES} cases, found {len(cases)}."
        )

    ids = [str(case.get("id", "")) for case in cases]

    if any(not case_id for case_id in ids):
        fail("An evaluation case has no id.")

    if len(ids) != len(set(ids)):
        fail("Evaluation case ids are not unique.")

    routing = {
        str(case["expected_problem_id"]): case
        for case in cases
        if case.get("kind") == "problem-routing"
    }
    boundaries = {
        str(case["id"]): case
        for case in cases
        if case.get("kind") != "problem-routing"
    }

    if len(routing) != EXPECTED_ROUTING_CASES:
        fail(
            f"Expected {EXPECTED_ROUTING_CASES} routing cases, "
            f"found {len(routing)}."
        )

    if len(boundaries) != EXPECTED_BOUNDARY_CASES:
        fail(
            f"Expected {EXPECTED_BOUNDARY_CASES} boundary cases, "
            f"found {len(boundaries)}."
        )

    problems_raw = mapping.get("problems")

    if not isinstance(problems_raw, list):
        fail("Canonical problems must be a list.")

    problems = [
        cast(dict[str, Any], problem)
        for problem in problems_raw
        if isinstance(problem, dict)
    ]

    if len(problems) != EXPECTED_ROUTING_CASES:
        fail("Canonical problem count is unexpected.")

    for problem in problems:
        problem_id = str(problem.get("id", ""))
        case = routing.get(problem_id)

        if case is None:
            fail(f"Routing case is missing: {problem_id}")

        intents = problem.get("user_intents")

        if not isinstance(intents, list) or not intents:
            fail(f"Problem has no user intents: {problem_id}")

        expected_case = {
            "id": f"route-{problem_id}",
            "kind": "problem-routing",
            "prompt": intents[0],
            "expected_problem_id": problem_id,
            "expected_status": problem.get("status"),
            "expected_commands": problem.get("commands"),
            "required_response_constraints": (
                expected_status_constraints(str(problem.get("status")))
            ),
        }

        if case != expected_case:
            fail(f"Routing fixture drift detected: {problem_id}")

    if set(boundaries) != set(EXPECTED_BOUNDARIES):
        fail(
            "Boundary case set differs. "
            f"Expected {sorted(EXPECTED_BOUNDARIES)}, "
            f"got {sorted(boundaries)}."
        )

    for case_id, expected in EXPECTED_BOUNDARIES.items():
        case = boundaries[case_id]

        for key, value in expected.items():
            if case.get(key) != value:
                fail(
                    f"Boundary fixture drift: {case_id}.{key}"
                )

        prompt = case.get("prompt")

        if not isinstance(prompt, str) or not prompt.strip():
            fail(f"Boundary case prompt is empty: {case_id}")

    status_counts = {
        "supported": 0,
        "conditional": 0,
        "unsupported": 0,
    }

    for case in routing.values():
        status = str(case["expected_status"])
        status_counts[status] += 1

    expected_counts = {
        "supported": 12,
        "conditional": 4,
        "unsupported": 5,
    }

    if status_counts != expected_counts:
        fail(f"Evaluation status counts are unexpected: {status_counts}")

    return {
        "status": "passed",
        "suite_type": suite["suite_type"],
        "model_execution": False,
        "package_version": EXPECTED_VERSION,
        "problem_routing_cases": len(routing),
        "boundary_cases": len(boundaries),
        "total_cases": len(cases),
        "status_counts": status_counts,
    }


def main() -> int:
    """Run the deterministic contract evaluation."""
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--json-output",
        type=Path,
        help="Optional path for the evaluation result.",
    )
    arguments = parser.parse_args()

    result = evaluate()

    if arguments.json_output is not None:
        arguments.json_output.parent.mkdir(parents=True, exist_ok=True)
        arguments.json_output.write_text(
            json.dumps(result, indent=2) + "\n",
            encoding="utf-8",
        )

    print("Evaluation suite type:", result["suite_type"])
    print("Live model execution:", result["model_execution"])
    print("Package version:", result["package_version"])
    print("Problem-routing cases:", result["problem_routing_cases"])
    print("Boundary cases:", result["boundary_cases"])
    print("Total cases:", result["total_cases"])
    print(
        "Supported/conditional/unsupported:",
        "12/4/5",
    )
    print("Deterministic agent-contract evaluation passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
