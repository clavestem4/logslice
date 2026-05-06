"""Tests for logslice.merge."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import List, Optional

import pytest

from logslice.parser import LogEntry
from logslice.merge import merge_sorted, merge_iter


def make_entry(
    message: str,
    ts: Optional[datetime] = None,
    severity: str = "INFO",
) -> LogEntry:
    return LogEntry(timestamp=ts, severity=severity, message=message, raw=message)


def dt(hour: int, minute: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, tzinfo=timezone.utc)


class TestMergeSorted:
    def test_returns_list(self):
        result = merge_sorted([])
        assert isinstance(result, list)

    def test_empty_streams_return_empty(self):
        assert merge_sorted([], []) == []

    def test_single_stream_sorted(self):
        entries = [
            make_entry("c", dt(3)),
            make_entry("a", dt(1)),
            make_entry("b", dt(2)),
        ]
        result = merge_sorted(entries)
        assert [e.message for e in result] == ["a", "b", "c"]

    def test_two_streams_merged(self):
        s1 = [make_entry("a", dt(1)), make_entry("c", dt(3))]
        s2 = [make_entry("b", dt(2)), make_entry("d", dt(4))]
        result = merge_sorted(s1, s2)
        assert [e.message for e in result] == ["a", "b", "c", "d"]

    def test_reverse_order(self):
        s1 = [make_entry("a", dt(1)), make_entry("b", dt(2))]
        s2 = [make_entry("c", dt(3))]
        result = merge_sorted(s1, s2, reverse=True)
        assert [e.message for e in result] == ["c", "b", "a"]

    def test_entries_without_timestamp_appended_last(self):
        entries = [
            make_entry("no-ts"),
            make_entry("first", dt(1)),
            make_entry("second", dt(2)),
        ]
        result = merge_sorted(entries)
        assert result[-1].message == "no-ts"
        assert result[0].message == "first"

    def test_duplicate_timestamps_preserved(self):
        entries = [
            make_entry("x", dt(1)),
            make_entry("y", dt(1)),
        ]
        result = merge_sorted(entries)
        assert len(result) == 2

    def test_three_streams(self):
        s1 = [make_entry("a", dt(1))]
        s2 = [make_entry("b", dt(2))]
        s3 = [make_entry("c", dt(3))]
        result = merge_sorted(s1, s2, s3)
        assert [e.message for e in result] == ["a", "b", "c"]


class TestMergeIter:
    def _collect(self, *streams):
        return list(merge_iter(*streams))

    def test_empty_yields_nothing(self):
        assert self._collect([]) == []

    def test_single_presorted_stream(self):
        entries = [make_entry(str(i), dt(i)) for i in range(1, 4)]
        result = self._collect(entries)
        assert [e.message for e in result] == ["1", "2", "3"]

    def test_two_presorted_streams_merged(self):
        s1 = [make_entry("a", dt(1)), make_entry("c", dt(3))]
        s2 = [make_entry("b", dt(2)), make_entry("d", dt(4))]
        result = self._collect(s1, s2)
        assert [e.message for e in result] == ["a", "b", "c", "d"]

    def test_no_timestamp_entries_come_last(self):
        s1 = [make_entry("ts", dt(1)), make_entry("no-ts")]
        result = self._collect(s1)
        assert result[0].message == "ts"
        assert result[-1].message == "no-ts"

    def test_returns_iterator(self):
        import types
        result = merge_iter([])
        assert isinstance(result, types.GeneratorType)
