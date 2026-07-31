"""Tests for query-performance row normalisation."""

from datetime import datetime

import pytest

from red_govern.capabilities import ViewFamily
from red_govern.collectors import (
    QueryPerformanceRecord,
    normalise_query_performance_row,
)
from red_govern.collectors.query_history import QueryStatus
from red_govern.exceptions import RedshiftQueryError


def test_sys_query_performance_row_is_normalised() -> None:
    """Modern SYS performance rows should be normalised."""

    record = normalise_query_performance_row(
        {
            "query_id": 501,
            "user_id": 100,
            "user_name": "analyst",
            "database_name": "analytics",
            "status": "success",
            "query_type": "SELECT",
            "start_time": "2026-07-29T12:00:00",
            "end_time": "2026-07-29T12:00:05",
            "elapsed_ms": 5000,
            "queue_ms": 200,
            "execution_ms": 4800,
            "blocks_read": 75,
            "blocks_write": 4,
            "temp_blocks_to_disk": 3,
            "input_rows": 1000,
            "output_rows": 20,
            "input_bytes": 50000,
            "output_bytes": 1000,
            "returned_rows": 20,
            "returned_bytes": 1000,
            "data_skewness": 1.25,
            "time_skewness": 1.1,
            "alert_count": 2,
        },
        source_family=ViewFamily.SYS,
        source_query_id="query_performance_sys_v1",
    )

    assert isinstance(record, QueryPerformanceRecord)
    assert record.query_id == "501"
    assert record.status is QueryStatus.SUCCEEDED
    assert record.started_at == datetime(
        2026,
        7,
        29,
        12,
        0,
    )
    assert record.elapsed_ms == 5000
    assert record.blocks_read == 75
    assert record.alert_count == 2
    assert record.source_family is ViewFamily.SYS


def test_svl_query_performance_row_allows_missing_values() -> None:
    """Legacy SVL rows should safely accept unavailable fields."""

    record = normalise_query_performance_row(
        {
            "query_id": "9001",
            "user_id": "101",
            "status": None,
            "elapsed_ms": "1500",
            "cpu_ms": "800",
            "cpu_usage_percent": "72.5",
            "cpu_skew": "1.4",
            "io_skew": "1.2",
        },
        source_family=ViewFamily.SVL,
        source_query_id="query_performance_svl_v1",
    )

    assert record.query_id == "9001"
    assert record.user_id == 101
    assert record.status is QueryStatus.UNKNOWN
    assert record.elapsed_ms == 1500
    assert record.cpu_ms == 800
    assert record.cpu_usage_percent == 72.5
    assert record.cpu_skew == 1.4
    assert record.user_name is None
    assert record.source_family is ViewFamily.SVL


def test_query_performance_row_requires_query_id() -> None:
    """Rows without a query identifier must be rejected."""

    with pytest.raises(
        RedshiftQueryError,
        match="missing a query identifier",
    ):
        normalise_query_performance_row(
            {
                "elapsed_ms": 100,
                "status": "success",
            },
            source_family=ViewFamily.SYS,
            source_query_id="query_performance_sys_v1",
        )
