"""Matching behaviour for Red-Govern classification rules."""

from __future__ import annotations

import re

from red_govern.classification.rules import (
    ClassificationRule,
    MatchType,
)
from red_govern.collectors import ObjectInventoryRecord


def _normalise(
    value: str,
    *,
    case_sensitive: bool,
) -> str:
    """Normalise a classification comparison value."""
    return value if case_sensitive else value.casefold()


def rule_matches(
    rule: ClassificationRule,
    record: ObjectInventoryRecord,
) -> bool:
    """Return whether a rule matches an inventory record."""
    target = (
        record.schema_name
        if rule.match_type == MatchType.SCHEMA
        else record.object_name
    )

    comparison_target = _normalise(
        target,
        case_sensitive=rule.case_sensitive,
    )
    comparison_value = _normalise(
        rule.value,
        case_sensitive=rule.case_sensitive,
    )

    if rule.match_type == MatchType.EXACT:
        return comparison_target == comparison_value

    if rule.match_type == MatchType.PREFIX:
        return comparison_target.startswith(comparison_value)

    if rule.match_type == MatchType.SUFFIX:
        return comparison_target.endswith(comparison_value)

    if rule.match_type == MatchType.CONTAINS:
        return comparison_value in comparison_target

    if rule.match_type == MatchType.SCHEMA:
        return comparison_target == comparison_value

    flags = 0 if rule.case_sensitive else re.IGNORECASE
    return re.search(rule.value, target, flags=flags) is not None