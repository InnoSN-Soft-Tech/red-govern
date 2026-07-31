"""Tests for normalised Redshift query history."""

from red_govern.collectors import (
    QueryStatus,
    normalise_query_status,
)


def test_query_status_normalisation() -> None:
    """Source-specific statuses should become stable values."""
    assert (
        normalise_query_status("success")
        == QueryStatus.SUCCEEDED
    )
    assert (
        normalise_query_status("failed")
        == QueryStatus.FAILED
    )
    assert (
        normalise_query_status("aborted")
        == QueryStatus.CANCELLED
    )
    assert (
        normalise_query_status("running")
        == QueryStatus.RUNNING
    )
    assert (
        normalise_query_status("other")
        == QueryStatus.UNKNOWN
    )
    assert (
        normalise_query_status("planning")
        == QueryStatus.RUNNING
    )
    assert (
        normalise_query_status("queued")
        == QueryStatus.RUNNING
    )
    assert (
        normalise_query_status("returning")
        == QueryStatus.RUNNING
    )
    assert (
        normalise_query_status("Running")
        == QueryStatus.RUNNING
    )
