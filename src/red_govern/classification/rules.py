"""Classification-rule models and loading for Red-Govern."""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any

import yaml

from red_govern.exceptions import ClassificationError


class MatchType(str, Enum):
    """Supported object-classification matching strategies."""

    EXACT = "exact"
    PREFIX = "prefix"
    SUFFIX = "suffix"
    CONTAINS = "contains"
    REGEX = "regex"
    SCHEMA = "schema"


@dataclass(frozen=True, slots=True)
class ClassificationRule:
    """One classification rule."""

    name: str
    priority: int
    match_type: MatchType
    value: str
    case_sensitive: bool = False


@dataclass(frozen=True, slots=True)
class ClassificationDimension:
    """A named classification dimension and its rules."""

    name: str
    rules: tuple[ClassificationRule, ...]


@dataclass(frozen=True, slots=True)
class ClassificationRuleset:
    """Complete classification configuration."""

    version: int
    dimensions: tuple[ClassificationDimension, ...]


def _require_mapping(
    value: object,
    *,
    context: str,
) -> dict[str, Any]:
    """Require and return a string-keyed mapping."""
    if not isinstance(value, dict):
        raise ClassificationError(
            f"{context} must be a mapping."
        )

    if not all(isinstance(key, str) for key in value):
        raise ClassificationError(
            f"{context} must contain string keys."
        )

    return value


def _parse_rule(
    value: object,
    *,
    dimension: str,
    index: int,
) -> ClassificationRule:
    """Parse one classification rule."""
    raw = _require_mapping(
        value,
        context=f"Rule {index} in dimension {dimension}",
    )

    name = raw.get("name")
    priority = raw.get("priority", 100)
    match = _require_mapping(
        raw.get("match"),
        context=f"Match settings for rule {index} in {dimension}",
    )

    match_type_raw = match.get("type")
    match_value = match.get("value")
    case_sensitive = match.get("case_sensitive", False)

    if not isinstance(name, str) or not name.strip():
        raise ClassificationError(
            f"Rule {index} in {dimension} requires a non-empty name."
        )

    if not isinstance(priority, int) or priority < 0:
        raise ClassificationError(
            f"Rule {name} requires a non-negative integer priority."
        )

    try:
        match_type = MatchType(str(match_type_raw))
    except ValueError as exc:
        raise ClassificationError(
            f"Unsupported match type for rule {name}: "
            f"{match_type_raw}"
        ) from exc

    if not isinstance(match_value, str) or not match_value:
        raise ClassificationError(
            f"Rule {name} requires a non-empty match value."
        )

    if not isinstance(case_sensitive, bool):
        raise ClassificationError(
            f"case_sensitive must be true or false for rule {name}."
        )

    if match_type == MatchType.REGEX:
        try:
            re.compile(match_value)
        except re.error as exc:
            raise ClassificationError(
                f"Invalid regular expression for rule {name}: {exc}"
            ) from exc

    return ClassificationRule(
        name=name.strip(),
        priority=priority,
        match_type=match_type,
        value=match_value,
        case_sensitive=case_sensitive,
    )


def load_classification_rules(
    path: Path,
) -> ClassificationRuleset:
    """Load and validate classification rules from YAML."""
    try:
        content = path.read_text(encoding="utf-8")
    except OSError as exc:
        raise ClassificationError(
            f"Unable to read classification rules: {path}"
        ) from exc

    try:
        loaded = yaml.safe_load(content)
    except yaml.YAMLError as exc:
        raise ClassificationError(
            f"Invalid classification YAML: {path}"
        ) from exc

    root = _require_mapping(
        loaded,
        context="Classification configuration",
    )

    version = root.get("classification_version", 1)

    if not isinstance(version, int) or version < 1:
        raise ClassificationError(
            "classification_version must be a positive integer."
        )

    dimensions_raw = _require_mapping(
        root.get("dimensions"),
        context="dimensions",
    )

    dimensions: list[ClassificationDimension] = []

    for dimension_name, dimension_value in dimensions_raw.items():
        dimension_mapping = _require_mapping(
            dimension_value,
            context=f"Dimension {dimension_name}",
        )

        rules_raw = dimension_mapping.get("rules")

        if not isinstance(rules_raw, list):
            raise ClassificationError(
                f"Dimension {dimension_name} must contain a rules list."
            )

        rules = tuple(
            _parse_rule(
                rule,
                dimension=dimension_name,
                index=index,
            )
            for index, rule in enumerate(rules_raw, start=1)
        )

        dimensions.append(
            ClassificationDimension(
                name=dimension_name,
                rules=rules,
            )
        )

    return ClassificationRuleset(
        version=version,
        dimensions=tuple(dimensions),
    )
