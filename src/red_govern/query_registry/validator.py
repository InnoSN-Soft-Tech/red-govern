"""Validation helpers for Red-Govern query definitions."""

from __future__ import annotations

import re

from red_govern.exceptions import QueryRegistryError
from red_govern.query_registry.registry import QueryDefinition

WRITE_KEYWORDS = re.compile(
    r"\b("
    r"insert|update|delete|drop|alter|truncate|create|grant|revoke|"
    r"vacuum|analyze|copy|unload|merge|call"
    r")\b",
    re.IGNORECASE,
)


def validate_read_only_query(query: QueryDefinition) -> None:
    """Reject query definitions containing write operations."""
    normalised = query.sql.strip()

    if not normalised:
        raise QueryRegistryError(
            f"SQL cannot be empty for {query.query_id}."
        )

    if WRITE_KEYWORDS.search(normalised):
        raise QueryRegistryError(
            f"Query {query.query_id} contains a blocked SQL keyword."
        )

    first_keyword = normalised.split(maxsplit=1)[0].lower()

    if first_keyword not in {"select", "with"}:
        raise QueryRegistryError(
            f"Query {query.query_id} must begin with SELECT or WITH."
        )
