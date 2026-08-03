"""Tests for owner-only local Red-Govern files."""

from __future__ import annotations

import stat
from pathlib import Path

from openpyxl import Workbook

from red_govern.history import initialise_database
from red_govern.reports.excel_report import write_excel_report
from red_govern.reports.json_report import write_json_report


def _permission_mode(path: Path) -> int:
    """Return only the permission bits for a local file."""
    return stat.S_IMODE(path.stat().st_mode)


def test_sqlite_history_is_created_owner_only(
    tmp_path: Path,
) -> None:
    """Local history metadata should begin with mode 600."""
    result = initialise_database(tmp_path / "history" / "governance.db")

    assert _permission_mode(result) == 0o600


def test_json_report_is_created_owner_only(
    tmp_path: Path,
) -> None:
    """Local JSON governance reports should begin with mode 600."""
    result = write_json_report(
        {"report_schema": "permission_test"},
        tmp_path / "reports" / "governance.json",
    )

    assert _permission_mode(result) == 0o600


def test_excel_report_is_created_owner_only(
    tmp_path: Path,
) -> None:
    """Local Excel governance reports should begin with mode 600."""
    workbook = Workbook()

    try:
        result = write_excel_report(
            workbook,
            tmp_path / "reports" / "governance.xlsx",
        )
    finally:
        workbook.close()

    assert _permission_mode(result) == 0o600


def test_existing_file_permissions_are_tightened(
    tmp_path: Path,
) -> None:
    """Existing output targets should be tightened before overwrite."""
    destination = tmp_path / "existing.json"
    destination.write_text("existing", encoding="utf-8")
    destination.chmod(0o644)

    result = write_json_report(
        {"report_schema": "permission_test"},
        destination,
        overwrite=True,
    )

    assert _permission_mode(result) == 0o600
