"""Tests for logslice.sample."""

from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogEntry
from logslice.sample import every_nth, sample_entries, sample_rate


def make_entry(msg: str, severity: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=msg,
        raw=f"2024-01-01T12:00:00 {severity} {msg}",
    )


ENTRIES: List[LogEntry] = [make_entry(f"msg-{i}") for i in range(20)]


# ---------------------------------------------------------------------------
# sample_entries
# ---------------------------------------------------------------------------

class TestSampleEntries:
    def test_returns_correct_count(self):
        result = sample_entries(ENTRIES, 5, seed=0)
        assert len(result) == 5

    def test_order_preserved(self):
        result = sample_entries(ENTRIES, 10, seed=42)
        indices = [ENTRIES.index(e) for e in result]
        assert indices == sorted(indices)

    def test_n_zero_returns_empty(self):
        assert sample_entries(ENTRIES, 0) == []

    def test_n_negative_returns_empty(self):
        assert sample_entries(ENTRIES, -5) == []

    def test_n_exceeds_length_returns_all(self):
        result = sample_entries(ENTRIES, 1000)
        assert result == ENTRIES

    def test_seed_reproducible(self):
        r1 = sample_entries(ENTRIES, 7, seed=99)
        r2 = sample_entries(ENTRIES, 7, seed=99)
        assert r1 == r2

    def test_different_seeds_may_differ(self):
        r1 = sample_entries(ENTRIES, 7, seed=1)
        r2 = sample_entries(ENTRIES, 7, seed=2)
        # Not guaranteed, but extremely likely with 20 entries
        assert r1 != r2


# ---------------------------------------------------------------------------
# sample_rate
# ---------------------------------------------------------------------------

class TestSampleRate:
    def test_rate_zero_returns_empty(self):
        assert sample_rate(ENTRIES, 0.0) == []

    def test_rate_one_returns_all(self):
        assert sample_rate(ENTRIES, 1.0) == ENTRIES

    def test_rate_above_one_returns_all(self):
        assert sample_rate(ENTRIES, 2.5) == ENTRIES

    def test_rate_below_zero_returns_empty(self):
        assert sample_rate(ENTRIES, -0.5) == []

    def test_approximate_fraction(self):
        big = [make_entry(f"m{i}") for i in range(1000)]
        result = sample_rate(big, 0.5, seed=7)
        assert 400 <= len(result) <= 600

    def test_seed_reproducible(self):
        r1 = sample_rate(ENTRIES, 0.5, seed=3)
        r2 = sample_rate(ENTRIES, 0.5, seed=3)
        assert r1 == r2


# ---------------------------------------------------------------------------
# every_nth
# ---------------------------------------------------------------------------

class TestEveryNth:
    def test_every_1_returns_all(self):
        assert every_nth(ENTRIES, 1) == ENTRIES

    def test_every_2_halves_list(self):
        result = every_nth(ENTRIES, 2)
        assert len(result) == 10
        assert result[0] is ENTRIES[0]
        assert result[1] is ENTRIES[2]

    def test_every_5(self):
        result = every_nth(ENTRIES, 5)
        assert len(result) == 4

    def test_n_zero_raises(self):
        with pytest.raises(ValueError):
            every_nth(ENTRIES, 0)

    def test_n_negative_raises(self):
        with pytest.raises(ValueError):
            every_nth(ENTRIES, -1)

    def test_empty_input(self):
        assert every_nth([], 3) == []
