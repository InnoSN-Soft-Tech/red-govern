"""Tests for the local Red-Govern history database."""

from pathlib import Path

from red_govern.history import initialise_database


def test_database_initialisation(tmp_path: Path) -> None:
    """Initialisation should create the SQLite database."""
    database_path = tmp_path / "history" / "governance.db"

    result = initialise_database(database_path)

    assert result.exists()
    assert result == database_path.resolve()
