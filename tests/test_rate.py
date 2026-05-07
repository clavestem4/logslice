"""Tests for logslice.rate."""

from datetime import datetime, timedelta
from typing import Optional

import pytest

from logslice.parser import LogEntry
from logslice.rate import (
    RateWindow,
    compute_rate,
    rate_exceeded,
    throttle_entries,
)


def make_entry(
    message: str = "test",
    severity: str = "INFO",
    timestamp: Optional[datetime] = None,
) -> LogEntry:
    return LogEntry(
        timestamp=timestamp or datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw=f"2024-01-01T12:00:00 {severity} {message}",
    )


class TestRateWindow:
    def test_allows_entries_within_limit(self):
        window = RateWindow(window_seconds=60, max_entries=3)
        entries = [make_entry(timestamp=datetime(2024, 1, 1, 12, 0, i)) for i in range(3)]
        results = [window.allow(e) for e in entries]
        assert all(results)

    def test_blocks_entry_over_limit(self):
        window = RateWindow(window_seconds=60, max_entries=2)
        entries = [make_entry(timestamp=datetime(2024, 1, 1, 12, 0, i)) for i in range(3)]
        results = [window.allow(e) for e in entries]
        assert results == [True, True, False]

    def test_evicts_old_entries(self):
        window = RateWindow(window_seconds=5, max_entries=2)
        e1 = make_entry(timestamp=datetime(2024, 1, 1, 12, 0, 0))
        e2 = make_entry(timestamp=datetime(2024, 1, 1, 12, 0, 1))
        e3 = make_entry(timestamp=datetime(2024, 1, 1, 12, 0, 10))  # outside window
        window.allow(e1)
        window.allow(e2)
        assert window.allow(e3) is True

    def test_current_count_reflects_window(self):
        window = RateWindow(window_seconds=60, max_entries=10)
        for i in range(4):
            window.allow(make_entry(timestamp=datetime(2024, 1, 1, 12, 0, i)))
        assert window.current_count == 4

    def test_as_dict_keys(self):
        window = RateWindow(window_seconds=30, max_entries=5)
        d = window.as_dict()
        assert "window_seconds" in d
        assert "max_entries" in d
        assert "current_count" in d

    def test_str_contains_window(self):
        window = RateWindow(window_seconds=30, max_entries=5)
        assert "30" in str(window)
        assert "5" in str(window)


class TestThrottleEntries:
    def test_yields_allowed_entries(self):
        entries = [make_entry(f"msg{i}", timestamp=datetime(2024, 1, 1, 12, 0, i)) for i in range(5)]
        result = list(throttle_entries(entries, window_seconds=60, max_entries=3))
        assert len(result) == 3

    def test_preserves_order(self):
        entries = [make_entry(f"msg{i}", timestamp=datetime(2024, 1, 1, 12, 0, i)) for i in range(3)]
        result = list(throttle_entries(entries, window_seconds=60, max_entries=3))
        assert [e.message for e in result] == ["msg0", "msg1", "msg2"]

    def test_empty_input(self):
        result = list(throttle_entries([], window_seconds=60, max_entries=5))
        assert result == []


class TestRateExceeded:
    def test_returns_dropped_entries(self):
        entries = [make_entry(f"msg{i}", timestamp=datetime(2024, 1, 1, 12, 0, i)) for i in range(5)]
        dropped = rate_exceeded(entries, window_seconds=60, max_entries=3)
        assert len(dropped) == 2

    def test_empty_when_all_allowed(self):
        entries = [make_entry(f"msg{i}", timestamp=datetime(2024, 1, 1, 12, 0, i)) for i in range(3)]
        dropped = rate_exceeded(entries, window_seconds=60, max_entries=10)
        assert dropped == []


class TestComputeRate:
    def test_returns_rate(self):
        entries = [
            make_entry(timestamp=datetime(2024, 1, 1, 12, 0, 0)),
            make_entry(timestamp=datetime(2024, 1, 1, 12, 0, 10)),
        ]
        rate = compute_rate(entries)
        assert rate == pytest.approx(2 / 10)

    def test_single_entry_returns_none(self):
        entries = [make_entry(timestamp=datetime(2024, 1, 1, 12, 0, 0))]
        assert compute_rate(entries) is None

    def test_no_timestamps_returns_none(self):
        entries = [LogEntry(timestamp=None, severity="INFO", message="x", raw="x")]
        assert compute_rate(entries) is None

    def test_zero_span_returns_none(self):
        ts = datetime(2024, 1, 1, 12, 0, 0)
        entries = [make_entry(timestamp=ts), make_entry(timestamp=ts)]
        assert compute_rate(entries) is None
