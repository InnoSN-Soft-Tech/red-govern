"""Object-classification engine for Red-Govern."""

from __future__ import annotations

from dataclasses import dataclass

from red_govern.classification.matcher import rule_matches
from red_govern.classification.rules import (
    ClassificationDimension,
    ClassificationRule,
    ClassificationRuleset,
)
from red_govern.collectors import (
    ObjectInventoryRecord,
    ObjectInventoryResult,
)


@dataclass(frozen=True, slots=True)
class DimensionClassification:
    """Classification result for one dimension."""

    dimension: str
    label: str | None
    matched_rule: str | None
    priority: int | None
    conflict: bool
    competing_rules: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class ObjectClassification:
    """Classification result for one inventory object."""

    record: ObjectInventoryRecord
    dimensions: tuple[DimensionClassification, ...]

    @property
    def unclassified(self) -> bool:
        """Return whether no dimension produced a label."""
        return all(
            result.label is None
            for result in self.dimensions
        )

    @property
    def has_conflict(self) -> bool:
        """Return whether any dimension has a priority conflict."""
        return any(
            result.conflict
            for result in self.dimensions
        )


@dataclass(frozen=True, slots=True)
class ClassificationResult:
    """Complete classification output for one inventory."""

    objects: tuple[ObjectClassification, ...]

    @property
    def total_objects(self) -> int:
        """Return the number of classified inventory objects."""
        return len(self.objects)

    @property
    def classified_count(self) -> int:
        """Return the number classified in at least one dimension."""
        return sum(
            1
            for result in self.objects
            if not result.unclassified
        )

    @property
    def unclassified_count(self) -> int:
        """Return the number without any classification."""
        return sum(
            1
            for result in self.objects
            if result.unclassified
        )

    @property
    def conflict_count(self) -> int:
        """Return the number containing classification conflicts."""
        return sum(
            1
            for result in self.objects
            if result.has_conflict
        )


def _matching_rules(
    dimension: ClassificationDimension,
    record: ObjectInventoryRecord,
) -> tuple[ClassificationRule, ...]:
    """Return matching rules ordered by priority and name."""
    return tuple(
        sorted(
            (
                rule
                for rule in dimension.rules
                if rule_matches(rule, record)
            ),
            key=lambda rule: (-rule.priority, rule.name),
        )
    )


def _classify_dimension(
    dimension: ClassificationDimension,
    record: ObjectInventoryRecord,
) -> DimensionClassification:
    """Classify one object within one dimension."""
    matches = _matching_rules(dimension, record)

    if not matches:
        return DimensionClassification(
            dimension=dimension.name,
            label=None,
            matched_rule=None,
            priority=None,
            conflict=False,
        )

    highest_priority = matches[0].priority

    highest_matches = tuple(
        rule
        for rule in matches
        if rule.priority == highest_priority
    )

    selected = highest_matches[0]

    return DimensionClassification(
        dimension=dimension.name,
        label=selected.name,
        matched_rule=selected.name,
        priority=selected.priority,
        conflict=len(highest_matches) > 1,
        competing_rules=tuple(
            rule.name
            for rule in highest_matches
        ),
    )


def classify_record(
    record: ObjectInventoryRecord,
    ruleset: ClassificationRuleset,
) -> ObjectClassification:
    """Classify one inventory record across all dimensions."""
    return ObjectClassification(
        record=record,
        dimensions=tuple(
            _classify_dimension(dimension, record)
            for dimension in ruleset.dimensions
        ),
    )


def classify_inventory(
    inventory: ObjectInventoryResult,
    ruleset: ClassificationRuleset,
) -> ClassificationResult:
    """Classify every object in an inventory."""
    return ClassificationResult(
        objects=tuple(
            classify_record(record, ruleset)
            for record in inventory.records
        )
    )
