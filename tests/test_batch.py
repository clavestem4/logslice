"""Tests for logslice.batch."""

from datetime import datetime, timedelta, timezone
from typing import Optional

import pytest

from logslice.batch import Batch, batch_by_size, batch_by_time, count_batches
from logslice.parser import LogEntry


def make_entry(message: str, severity: str = "INFO", minutes: Optional[int] = None) -> LogEntry:
    ts = None
    if minutes is not None:
        ts = datetime(2024, 1, 1, 0, minutes, 0, tzinfo=timezone.utc)
    return LogEntry(timestamp=ts, severity=severity, message=message, raw=message)


# ---------------------------------------------------------------------------
# Batch dataclass
# ---------------------------------------------------------------------------

class TestBatch:
    def test_size_reflects_entries(self):
        b = Batch(entries=[make_entry("a"), make_entry("b")], index=0)
        assert b.size == 2

    def test_empty_batch_size_zero(self):
        assert Batch().size == 0

    def test_as_dict_contains_index_and_size(self):
        b = Batch(entries=[make_entry("x")], index=3)
        d = b.as_dict()
        assert d["index"] == 3
        assert d["size"] == 1

    def test_as_dict_entries_have_message(self):
        b = Batch(entries=[make_entry("hello")], index=0)
        assert b.as_dict()["entries"][0]["message"] == "hello"


# ---------------------------------------------------------------------------
# batch_by_size
# ---------------------------------------------------------------------------

class TestBatchBySize:
    def test_returns_correct_number_of_batches(self):
        entries = [make_entry(str(i)) for i in range(10)]
        batches = list(batch_by_size(entries, 3))
        assert len(batches) == 4

    def test_last_batch_may_be_smaller(self):
        entries = [make_entry(str(i)) for i in range(7)]
        batches = list(batch_by_size(entries, 3))
        assert batches[-1].size == 1

    def test_batch_index_increments(self):
        entries = [make_entry(str(i)) for i in range(6)]
        batches = list(batch_by_size(entries, 2))
        assert [b.index for b in batches] == [0, 1, 2]

    def test_n_zero_yields_nothing(self):
        entries = [make_entry("a")]
        assert list(batch_by_size(entries, 0)) == []

    def test_n_negative_yields_nothing(self):
        assert list(batch_by_size([make_entry("a")], -1)) == []

    def test_empty_entries_yields_nothing(self):
        assert list(batch_by_size([], 5)) == []

    def test_n_larger_than_list_single_batch(self):
        entries = [make_entry(str(i)) for i in range(3)]
        batches = list(batch_by_size(entries, 100))
        assert len(batches) == 1
        assert batches[0].size == 3


# ---------------------------------------------------------------------------
# batch_by_time
# ---------------------------------------------------------------------------

class TestBatchByTime:
    def test_groups_within_window(self):
        entries = [make_entry(str(i), minutes=i) for i in range(4)]
        batches = list(batch_by_time(entries, timedelta(minutes=5)))
        assert len(batches) == 1
        assert batches[0].size == 4

    def test_splits_across_window(self):
        entries = [make_entry(str(i), minutes=i) for i in range(10)]
        batches = list(batch_by_time(entries, timedelta(minutes=3)))
        assert len(batches) >= 2

    def test_no_timestamp_entries_included_in_current_batch(self):
        e1 = make_entry("ts", minutes=0)
        e2 = make_entry("no-ts")  # no timestamp
        e3 = make_entry("ts2", minutes=1)
        batches = list(batch_by_time([e1, e2, e3], timedelta(minutes=5)))
        assert sum(b.size for b in batches) == 3

    def test_zero_window_yields_nothing(self):
        entries = [make_entry("a", minutes=0)]
        assert list(batch_by_time(entries, timedelta(seconds=0))) == []

    def test_empty_entries_yields_nothing(self):
        assert list(batch_by_time([], timedelta(minutes=1))) == []

    def test_batch_index_increments(self):
        entries = [make_entry(str(i), minutes=i * 5) for i in range(3)]
        batches = list(batch_by_time(entries, timedelta(minutes=3)))
        assert [b.index for b in batches] == list(range(len(batches)))


# ---------------------------------------------------------------------------
# count_batches
# ---------------------------------------------------------------------------

class TestCountBatches:
    def test_exact_division(self):
        entries = [make_entry(str(i)) for i in range(6)]
        assert count_batches(entries, 2) == 3

    def test_remainder_rounds_up(self):
        entries = [make_entry(str(i)) for i in range(7)]
        assert count_batches(entries, 3) == 3

    def test_empty_returns_zero(self):
        assert count_batches([], 5) == 0

    def test_n_zero_returns_zero(self):
        assert count_batches([make_entry("a")], 0) == 0
