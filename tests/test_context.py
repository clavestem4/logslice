"""Tests for logslice.context module."""

from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogEntry
from logslice.context import ContextWindow, extract_context, context_around


def make_entry(msg: str, severity: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=msg,
        raw=f"2024-01-01T12:00:00 {severity} {msg}",
    )


ENTRIES: List[LogEntry] = [make_entry(f"msg{i}") for i in range(10)]


class TestExtractContext:
    def test_no_context_returns_entry_only(self):
        windows = extract_context(ENTRIES, [3], before=0, after=0)
        assert len(windows) == 1
        assert windows[0].entry is ENTRIES[3]
        assert windows[0].before == []
        assert windows[0].after == []

    def test_before_context(self):
        windows = extract_context(ENTRIES, [4], before=2, after=0)
        assert windows[0].before == [ENTRIES[2], ENTRIES[3]]
        assert windows[0].after == []

    def test_after_context(self):
        windows = extract_context(ENTRIES, [4], before=0, after=2)
        assert windows[0].after == [ENTRIES[5], ENTRIES[6]]
        assert windows[0].before == []

    def test_symmetric_context(self):
        windows = extract_context(ENTRIES, [5], before=2, after=2)
        assert windows[0].before == [ENTRIES[3], ENTRIES[4]]
        assert windows[0].after == [ENTRIES[6], ENTRIES[7]]

    def test_clamps_before_at_start(self):
        windows = extract_context(ENTRIES, [1], before=5, after=0)
        assert windows[0].before == [ENTRIES[0]]

    def test_clamps_after_at_end(self):
        windows = extract_context(ENTRIES, [8], before=0, after=5)
        assert windows[0].after == [ENTRIES[9]]

    def test_multiple_indices(self):
        windows = extract_context(ENTRIES, [2, 7], before=1, after=1)
        assert len(windows) == 2
        assert windows[0].entry is ENTRIES[2]
        assert windows[1].entry is ENTRIES[7]

    def test_empty_indices_returns_empty(self):
        windows = extract_context(ENTRIES, [], before=2, after=2)
        assert windows == []

    def test_all_entries_flat(self):
        windows = extract_context(ENTRIES, [4], before=1, after=1)
        flat = windows[0].all_entries()
        assert flat == [ENTRIES[3], ENTRIES[4], ENTRIES[5]]


class TestContextAround:
    def test_finds_entry_by_identity(self):
        target = ENTRIES[5]
        window = context_around(ENTRIES, target, before=1, after=1)
        assert window is not None
        assert window.entry is target

    def test_returns_none_for_unknown_entry(self):
        stranger = make_entry("not in list")
        result = context_around(ENTRIES, stranger, before=2, after=2)
        assert result is None

    def test_correct_context_returned(self):
        window = context_around(ENTRIES, ENTRIES[3], before=2, after=2)
        assert window.before == [ENTRIES[1], ENTRIES[2]]
        assert window.after == [ENTRIES[4], ENTRIES[5]]
