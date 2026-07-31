"""Local SQLite storage for Red-Govern governance history."""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

SCHEMA_VERSION = 1

SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS schema_version (
    version INTEGER NOT NULL
);

CREATE TABLE IF NOT EXISTS collection_runs (
    run_id INTEGER PRIMARY KEY AUTOINCREMENT,
    collected_at TEXT NOT NULL,
    source_query_id TEXT NOT NULL,
    source_family TEXT NOT NULL,
    total_objects INTEGER NOT NULL,
    status TEXT NOT NULL DEFAULT 'completed'
);

CREATE TABLE IF NOT EXISTS object_snapshots (
    run_id INTEGER NOT NULL,
    database_name TEXT NOT NULL,
    schema_name TEXT NOT NULL,
    object_name TEXT NOT NULL,
    object_type TEXT NOT NULL,
    owner_name TEXT,
    size_mb REAL,
    distribution_style TEXT,
    sort_key TEXT,
    source_family TEXT NOT NULL,
    source_query_id TEXT NOT NULL,
    collected_at TEXT NOT NULL,
    PRIMARY KEY (
        run_id,
        database_name,
        schema_name,
        object_name,
        object_type
    ),
    FOREIGN KEY (run_id) REFERENCES collection_runs(run_id)
);

CREATE INDEX IF NOT EXISTS idx_object_snapshots_identity
ON object_snapshots (
    database_name,
    schema_name,
    object_name,
    object_type
);

CREATE INDEX IF NOT EXISTS idx_object_snapshots_run
ON object_snapshots (run_id);
"""


def expand_database_path(path: Path) -> Path:
    """Expand user paths and return an absolute SQLite path."""
    return path.expanduser().resolve()


def initialise_database(path: Path) -> Path:
    """Create the local history database and required schema."""
    database_path = expand_database_path(path)
    database_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(database_path) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA_SQL)

        existing = connection.execute(
            "SELECT version FROM schema_version LIMIT 1"
        ).fetchone()

        if existing is None:
            connection.execute(
                "INSERT INTO schema_version (version) VALUES (?)",
                (SCHEMA_VERSION,),
            )

        connection.commit()

    return database_path


@contextmanager
def history_connection(path: Path) -> Iterator[sqlite3.Connection]:
    """Yield an initialised SQLite connection."""
    database_path = initialise_database(path)
    connection = sqlite3.connect(database_path)
    connection.row_factory = sqlite3.Row
    connection.execute("PRAGMA foreign_keys = ON")

    try:
        yield connection
        connection.commit()
    except Exception:
        connection.rollback()
        raise
    finally:
        connection.close()
