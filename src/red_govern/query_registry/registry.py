"""Query definitions and registry behaviour for Red-Govern."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum

from red_govern.capabilities import DeploymentType, ViewFamily
from red_govern.exceptions import QueryRegistryError


class QueryPurpose(str, Enum):
    """Supported governance-query purposes."""

    OBJECT_INVENTORY = "object_inventory"
    OBJECT_QUOTA = "object_quota"
    QUERY_HISTORY = "query_history"
    RUNNING_QUERIES = "running_queries"
    QUERY_PERFORMANCE = "query_performance"
    RUNNING_QUERY_METRICS = "running_query_metrics"
    CAPABILITY_PROBE = "capability_probe"


@dataclass(frozen=True, slots=True)
class QueryDefinition:
    """One versioned and capability-aware SQL definition."""

    query_id: str
    purpose: QueryPurpose
    query_version: str
    result_schema: str
    sql: str
    family: ViewFamily
    deployment_types: tuple[DeploymentType, ...]
    required_relations: tuple[str, ...]
    priority: int = 100
    enabled: bool = True

    def validate(self) -> None:
        """Validate query-definition invariants."""
        if not self.query_id.strip():
            raise QueryRegistryError("query_id cannot be empty.")

        if not self.query_version.strip():
            raise QueryRegistryError(
                f"query_version cannot be empty for {self.query_id}."
            )

        if not self.result_schema.strip():
            raise QueryRegistryError(
                f"result_schema cannot be empty for {self.query_id}."
            )

        if not self.sql.strip():
            raise QueryRegistryError(
                f"SQL cannot be empty for {self.query_id}."
            )

        if self.priority < 0:
            raise QueryRegistryError(
                f"priority cannot be negative for {self.query_id}."
            )


class QueryRegistry:
    """In-memory registry of Red-Govern query definitions."""

    def __init__(self) -> None:
        self._queries: dict[str, QueryDefinition] = {}

    def register(self, query: QueryDefinition) -> None:
        """Register one unique query definition."""
        query.validate()

        if query.query_id in self._queries:
            raise QueryRegistryError(
                f"Duplicate query_id: {query.query_id}"
            )

        self._queries[query.query_id] = query

    def get(self, query_id: str) -> QueryDefinition:
        """Return one query definition by identifier."""
        try:
            return self._queries[query_id]
        except KeyError as exc:
            raise QueryRegistryError(
                f"Unknown query_id: {query_id}"
            ) from exc

    def for_purpose(
        self,
        purpose: QueryPurpose,
    ) -> tuple[QueryDefinition, ...]:
        """Return enabled queries for one purpose."""
        return tuple(
            sorted(
                (
                    query
                    for query in self._queries.values()
                    if query.enabled and query.purpose == purpose
                ),
                key=lambda query: query.priority,
                reverse=True,
            )
        )

    def all(self) -> tuple[QueryDefinition, ...]:
        """Return all registered queries."""
        return tuple(self._queries.values())
