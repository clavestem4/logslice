"""Tests for logslice.window."""

from datetime import datetime, timedelta, timezone
from typing import List

import pytest

from logslice.parser import LogEntry
from logslice.window import SlidingWindow, WindowResult, tumbling_windows


def make_entry(message: str, ts: datetime) -> LogEntry:
    return LogEntry(timestamp=ts, severity="INFO", message=message, raw=message)


def dt(minute: int, second: int = 0) -> datetime:
    return datetime(2024, 1, 1, 12, minute, second, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# WindowResult
# ---------------------------------------------------------------------------

class TestWindowResult:
    def test_count_reflects_entries(self):
        entries = [make_entry("a", dt(0)), make_entry("b", dt(1))]
        wr = WindowResult(dt(0), dt(2), entries)
        assert wr.count == 2

    def test_as_dict_keys(self):
        wr = WindowResult(dt(0), dt(1), [])
        d = wr.as_dict()
        assert set(d.keys()) == {"window_start", "window_end", "count", "entries"}

    def test_as_dict_count_zero_for_empty(self):
        wr = WindowResult(dt(0), dt(1), [])
        assert wr.as_dict()["count"] == 0

    def test_str_contains_count(self):
        wr = WindowResult(dt(0), dt(1), [make_entry("x", dt(0))])
        assert "count=1" in str(wr)


# ---------------------------------------------------------------------------
# SlidingWindow
# ---------------------------------------------------------------------------

class TestSlidingWindow:
    def test_push_adds_entry(self):
        sw = SlidingWindow(duration=timedelta(minutes=5))
        sw.push(make_entry("hello", dt(0)))
        assert len(sw) == 1

    def test_evicts_old_entries(self):
        sw = SlidingWindow(duration=timedelta(minutes=2))
        sw.push(make_entry("old", dt(0)))
        sw.push(make_entry("new", dt(3)))  # 3 minutes later — evicts first
        assert len(sw) == 1
        assert sw.current()[0].message == "new"

    def test_entries_within_window_retained(self):
        sw = SlidingWindow(duration=timedelta(minutes=5))
        sw.push(make_entry("a", dt(0)))
        sw.push(make_entry("b", dt(2)))
        sw.push(make_entry("c", dt(4)))
        assert len(sw) == 3

    def test_entry_without_timestamp_ignored(self):
        sw = SlidingWindow(duration=timedelta(minutes=5))
        entry = LogEntry(timestamp=None, severity="INFO", message="no-ts", raw="no-ts")
        sw.push(entry)
        assert len(sw) == 0

    def test_current_returns_copy(self):
        sw = SlidingWindow(duration=timedelta(minutes=5))
        sw.push(make_entry("a", dt(0)))
        snap = sw.current()
        sw.push(make_entry("b", dt(1)))
        assert len(snap) == 1  # snapshot not mutated


# ---------------------------------------------------------------------------
# tumbling_windows
# ---------------------------------------------------------------------------

class TestTumblingWindows:
    def test_empty_entries_yields_nothing(self):
        results = list(tumbling_windows([], timedelta(minutes=1)))
        assert results == []

    def test_single_window(self):
        entries = [make_entry("a", dt(0)), make_entry("b", dt(0, 30))]
        results = list(tumbling_windows(entries, timedelta(minutes=1)))
        assert len(results) == 1
        assert results[0].count == 2

    def test_two_windows(self):
        entries = [
            make_entry("a", dt(0)),
            make_entry("b", dt(1)),
            make_entry("c", dt(2)),
        ]
        results = list(tumbling_windows(entries, timedelta(minutes=1)))
        assert len(results) == 3

    def test_window_boundaries_correct(self):
        entries = [make_entry("a", dt(0))]
        dur = timedelta(minutes=5)
        results = list(tumbling_windows(entries, dur))
        assert results[0].window_end - results[0].window_start == dur

    def test_on_window_callback_called(self):
        seen: List[WindowResult] = []
        entries = [make_entry("x", dt(0)), make_entry("y", dt(2))]
        list(tumbling_windows(entries, timedelta(minutes=1), on_window=seen.append))
        assert len(seen) >= 1

    def test_entries_without_timestamps_skipped(self):
        no_ts = LogEntry(timestamp=None, severity="INFO", message="skip", raw="skip")
        good = make_entry("ok", dt(0))
        results = list(tumbling_windows([no_ts, good], timedelta(minutes=1)))
        assert results[0].count == 1
