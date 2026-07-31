"""Tests for loading Red-Govern classification rules."""

from pathlib import Path

import pytest

from red_govern.classification import (
    MatchType,
    load_classification_rules,
)
from red_govern.exceptions import ClassificationError


def test_rules_are_loaded(tmp_path: Path) -> None:
    """Valid YAML should create a typed ruleset."""
    path = tmp_path / "classification.yml"
    path.write_text(
        """
classification_version: 1

dimensions:
  team:
    rules:
      - name: reader_team
        priority: 100
        match:
          type: prefix
          value: rdr_
""",
        encoding="utf-8",
    )

    ruleset = load_classification_rules(path)

    assert ruleset.version == 1
    assert ruleset.dimensions[0].name == "team"
    assert (
        ruleset.dimensions[0].rules[0].match_type
        == MatchType.PREFIX
    )


def test_invalid_regex_is_rejected(tmp_path: Path) -> None:
    """Invalid regular expressions should fail during loading."""
    path = tmp_path / "classification.yml"
    path.write_text(
        """
classification_version: 1

dimensions:
  team:
    rules:
      - name: invalid
        priority: 100
        match:
          type: regex
          value: "["
""",
        encoding="utf-8",
    )

    with pytest.raises(ClassificationError):
        load_classification_rules(path)
