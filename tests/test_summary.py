"""Tests for logslice.summary."""
from datetime import datetime, timezone

import pytest

from logslice.parser import LogEntry
from logslice.summary import LogSummary, summarize


def make_entry(
    severity: str = "INFO",
    timestamp: datetime | None = None,
    message: str = "msg",
) -> LogEntry:
    return LogEntry(
        timestamp=timestamp,
        severity=severity,
        message=message,
        raw=f"{severity} {message}",
    )


DT1 = datetime(2024, 1, 1, 10, 0, 0, tzinfo=timezone.utc)
DT2 = datetime(2024, 1, 1, 11, 0, 0, tzinfo=timezone.utc)
DT3 = datetime(2024, 1, 1, 12, 0, 0, tzinfo=timezone.utc)


class TestSummarize:
    def test_empty_list(self):
        s = summarize([])
        assert s.total == 0
        assert s.by_severity == {}
        assert s.first_timestamp is None
        assert s.last_timestamp is None

    def test_total_count(self):
        entries = [make_entry() for _ in range(5)]
        s = summarize(entries)
        assert s.total == 5

    def test_severity_counts(self):
        entries = [
            make_entry("INFO"),
            make_entry("INFO"),
            make_entry("ERROR"),
            make_entry("debug"),  # should be normalised to upper
        ]
        s = summarize(entries)
        assert s.by_severity["INFO"] == 2
        assert s.by_severity["ERROR"] == 1
        assert s.by_severity["DEBUG"] == 1

    def test_none_severity_becomes_unknown(self):
        entries = [make_entry(severity=None)]
        s = summarize(entries)
        assert s.by_severity.get("UNKNOWN") == 1

    def test_timestamp_range(self):
        entries = [
            make_entry(timestamp=DT2),
            make_entry(timestamp=DT1),
            make_entry(timestamp=DT3),
        ]
        s = summarize(entries)
        assert s.first_timestamp == DT1
        assert s.last_timestamp == DT3

    def test_entries_without_timestamps_ignored_for_range(self):
        entries = [
            make_entry(timestamp=DT1),
            make_entry(timestamp=None),
        ]
        s = summarize(entries)
        assert s.first_timestamp == DT1
        assert s.last_timestamp == DT1

    def test_unparsed_lines_passed_through(self):
        s = summarize([], unparsed_lines=7)
        assert s.unparsed_lines == 7


class TestLogSummaryAsDict:
    def test_keys_present(self):
        s = summarize([make_entry(timestamp=DT1)])
        d = s.as_dict()
        assert set(d.keys()) == {
            "total",
            "by_severity",
            "first_timestamp",
            "last_timestamp",
            "unparsed_lines",
        }

    def test_timestamps_serialised_as_iso(self):
        s = LogSummary(total=1, first_timestamp=DT1, last_timestamp=DT2)
        d = s.as_dict()
        assert d["first_timestamp"] == DT1.isoformat()
        assert d["last_timestamp"] == DT2.isoformat()

    def test_none_timestamps_are_none(self):
        s = LogSummary()
        d = s.as_dict()
        assert d["first_timestamp"] is None
        assert d["last_timestamp"] is None


class TestLogSummaryStr:
    def test_contains_total(self):
        s = summarize([make_entry()])
        assert "Total entries" in str(s)
        assert "1" in str(s)

    def test_contains_severity(self):
        s = summarize([make_entry("WARNING")])
        assert "WARNING" in str(s)

    def test_contains_timestamps_when_present(self):
        s = summarize([make_entry(timestamp=DT1)])
        text = str(s)
        assert "From" in text
        assert "To" in text
