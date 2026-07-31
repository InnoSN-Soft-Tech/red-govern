"""Tests for Red-Govern object classification."""

from datetime import datetime, timezone

import pytest

from red_govern.capabilities import ViewFamily
from red_govern.classification import (
    ClassificationDimension,
    ClassificationRule,
    ClassificationRuleset,
    MatchType,
    classify_record,
    rule_matches,
)
from red_govern.collectors import (
    DatabaseObjectType,
    ObjectInventoryRecord,
)


def build_record(
    name: str = "rdr_weekly_sales",
    schema: str = "prod",
) -> ObjectInventoryRecord:
    """Build a synthetic object record."""
    return ObjectInventoryRecord(
        database_name="analytics",
        schema_name=schema,
        object_name=name,
        object_type=DatabaseObjectType.TABLE,
        source_family=ViewFamily.SVV,
        source_query_id="object_inventory_svv_v1",
        collected_at=datetime.now(timezone.utc),
    )


@pytest.mark.parametrize(
    ("match_type", "value"),
    [
        (MatchType.EXACT, "rdr_weekly_sales"),
        (MatchType.PREFIX, "rdr_"),
        (MatchType.SUFFIX, "_sales"),
        (MatchType.CONTAINS, "weekly"),
        (MatchType.REGEX, r"^rdr_.*_sales$"),
        (MatchType.SCHEMA, "prod"),
    ],
)
def test_supported_match_types(
    match_type: MatchType,
    value: str,
) -> None:
    """All supported rule types should match correctly."""
    rule = ClassificationRule(
        name="reader_team",
        priority=100,
        match_type=match_type,
        value=value,
    )

    assert rule_matches(rule, build_record())


def test_higher_priority_rule_is_selected() -> None:
    """Higher-priority rules should win."""
    ruleset = ClassificationRuleset(
        version=1,
        dimensions=(
            ClassificationDimension(
                name="team",
                rules=(
                    ClassificationRule(
                        name="generic_reader",
                        priority=50,
                        match_type=MatchType.CONTAINS,
                        value="rdr",
                    ),
                    ClassificationRule(
                        name="reader_team",
                        priority=100,
                        match_type=MatchType.PREFIX,
                        value="rdr_",
                    ),
                ),
            ),
        ),
    )

    result = classify_record(build_record(), ruleset)

    assert result.dimensions[0].label == "reader_team"
    assert result.dimensions[0].conflict is False


def test_equal_priority_rules_create_conflict() -> None:
    """Equal top-priority matches should be reported as a conflict."""
    ruleset = ClassificationRuleset(
        version=1,
        dimensions=(
            ClassificationDimension(
                name="team",
                rules=(
                    ClassificationRule(
                        name="reader_a",
                        priority=100,
                        match_type=MatchType.PREFIX,
                        value="rdr_",
                    ),
                    ClassificationRule(
                        name="reader_b",
                        priority=100,
                        match_type=MatchType.CONTAINS,
                        value="weekly",
                    ),
                ),
            ),
        ),
    )

    result = classify_record(build_record(), ruleset)

    assert result.has_conflict is True
    assert result.dimensions[0].competing_rules == (
        "reader_a",
        "reader_b",
    )


def test_unmatched_record_is_unclassified() -> None:
    """Objects with no matching rule should remain unclassified."""
    ruleset = ClassificationRuleset(
        version=1,
        dimensions=(
            ClassificationDimension(
                name="team",
                rules=(
                    ClassificationRule(
                        name="finance",
                        priority=100,
                        match_type=MatchType.PREFIX,
                        value="fin_",
                    ),
                ),
            ),
        ),
    )

    result = classify_record(build_record(), ruleset)

    assert result.unclassified is True
