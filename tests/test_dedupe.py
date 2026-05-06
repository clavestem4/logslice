"""Tests for logslice.dedupe."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from logslice.parser import LogEntry
from logslice.dedupe import (
    count_duplicates,
    deduplicate,
    entry_fingerprint,
)


def make_entry(
    message: str,
    severity: str | None = "INFO",
    ts: datetime | None = None,
) -> LogEntry:
    if ts is None:
        ts = datetime(2024, 1, 1, 0, 0, 0, tzinfo=timezone.utc)
    return LogEntry(timestamp=ts, severity=severity, message=message, raw=message)


# ---------------------------------------------------------------------------
# entry_fingerprint
# ---------------------------------------------------------------------------

class TestEntryFingerprint:
    def test_same_message_same_severity_equal(self):
        a = make_entry("disk full", "ERROR")
        b = make_entry("disk full", "ERROR")
        assert entry_fingerprint(a) == entry_fingerprint(b)

    def test_different_message_different_fp(self):
        a = make_entry("disk full", "ERROR")
        b = make_entry("disk ok", "ERROR")
        assert entry_fingerprint(a) != entry_fingerprint(b)

    def test_different_severity_different_fp(self):
        a = make_entry("msg", "ERROR")
        b = make_entry("msg", "WARN")
        assert entry_fingerprint(a) != entry_fingerprint(b)

    def test_timestamp_ignored(self):
        ts1 = datetime(2024, 1, 1, tzinfo=timezone.utc)
        ts2 = datetime(2024, 6, 15, tzinfo=timezone.utc)
        a = make_entry("msg", "INFO", ts=ts1)
        b = make_entry("msg", "INFO", ts=ts2)
        assert entry_fingerprint(a) == entry_fingerprint(b)

    def test_none_severity_handled(self):
        a = make_entry("msg", severity=None)
        fp = entry_fingerprint(a)
        assert isinstance(fp, str) and len(fp) == 32


# ---------------------------------------------------------------------------
# deduplicate – keep="first"
# ---------------------------------------------------------------------------

class TestDeduplicateFirst:
    def test_no_duplicates_unchanged(self):
        entries = [make_entry("a"), make_entry("b"), make_entry("c")]
        result = list(deduplicate(entries))
        assert len(result) == 3

    def test_duplicates_removed(self):
        entries = [make_entry("a"), make_entry("a"), make_entry("b")]
        result = list(deduplicate(entries))
        assert len(result) == 2
        assert result[0].message == "a"
        assert result[1].message == "b"

    def test_keeps_first_occurrence(self):
        ts1 = datetime(2024, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
        ts2 = datetime(2024, 1, 1, 0, 0, 2, tzinfo=timezone.utc)
        entries = [make_entry("dup", ts=ts1), make_entry("dup", ts=ts2)]
        result = list(deduplicate(entries, keep="first"))
        assert len(result) == 1
        assert result[0].timestamp == ts1

    def test_max_seen_evicts_old_fingerprints(self):
        # With max_seen=1, the second unique message evicts the first;
        # a third occurrence of the first message is treated as new.
        entries = [make_entry("a"), make_entry("b"), make_entry("a")]
        result = list(deduplicate(entries, keep="first", max_seen=1))
        assert len(result) == 3

    def test_invalid_keep_raises(self):
        with pytest.raises(ValueError, match="keep must be"):
            list(deduplicate([], keep="middle"))


# ---------------------------------------------------------------------------
# deduplicate – keep="last"
# ---------------------------------------------------------------------------

class TestDeduplicateLast:
    def test_keeps_last_occurrence(self):
        ts1 = datetime(2024, 1, 1, 0, 0, 1, tzinfo=timezone.utc)
        ts2 = datetime(2024, 1, 1, 0, 0, 2, tzinfo=timezone.utc)
        entries = [make_entry("dup", ts=ts1), make_entry("dup", ts=ts2)]
        result = list(deduplicate(entries, keep="last"))
        assert len(result) == 1
        assert result[0].timestamp == ts2

    def test_empty_input(self):
        assert list(deduplicate([], keep="last")) == []


# ---------------------------------------------------------------------------
# count_duplicates
# ---------------------------------------------------------------------------

class TestCountDuplicates:
    def test_no_duplicates(self):
        entries = [make_entry("a"), make_entry("b")]
        counts = count_duplicates(entries)
        assert all(v == 1 for v in counts.values())

    def test_counts_correctly(self):
        entries = [make_entry("x")] * 4 + [make_entry("y")] * 2
        counts = count_duplicates(entries)
        values = sorted(counts.values(), reverse=True)
        assert values == [4, 2]

    def test_empty_input(self):
        assert count_duplicates([]) == {}
