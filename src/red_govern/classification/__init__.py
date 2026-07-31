"""Configurable object classification for Red-Govern."""

from red_govern.classification.engine import (
    ClassificationResult,
    DimensionClassification,
    ObjectClassification,
    classify_inventory,
    classify_record,
)
from red_govern.classification.matcher import rule_matches
from red_govern.classification.rules import (
    ClassificationDimension,
    ClassificationRule,
    ClassificationRuleset,
    MatchType,
    load_classification_rules,
)

__all__ = [
    "ClassificationDimension",
    "ClassificationResult",
    "ClassificationRule",
    "ClassificationRuleset",
    "DimensionClassification",
    "MatchType",
    "ObjectClassification",
    "classify_inventory",
    "classify_record",
    "load_classification_rules",
    "rule_matches",
]
