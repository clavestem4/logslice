"""Tests for logslice.filter module."""

from datetime import datetime

import pytest

from logslice.filter import (
    apply_filters,
    filter_by_severity,
    filter_by_time,
    severity_rank,
)
from logslice.parser import LogEntry


def make_entry(ts=None, level="INFO", message="msg", raw="raw"):
    return LogEntry(timestamp=ts, level=level, message=message, raw=raw)


DT_EARLY = datetime(2024, 1, 1, 8, 0, 0)
DT_MID = datetime(2024, 1, 1, 12, 0, 0)
DT_LATE = datetime(2024, 1, 1, 18, 0, 0)


class TestSeverityRank:
    def test_known_levels(self):
        assert severity_rank("DEBUG") < severity_rank("INFO")
        assert severity_rank("INFO") < severity_rank("WARNING")
        assert severity_rank("WARNING") < severity_rank("ERROR")
        assert severity_rank("ERROR") < severity_rank("CRITICAL")

    def test_aliases(self):
        assert severity_rank("WARN") == severity_rank("WARNING")
        assert severity_rank("FATAL") == severity_rank("CRITICAL")

    def test_case_insensitive(self):
        assert severity_rank("debug") == severity_rank("DEBUG")

    def test_unknown_returns_minus_one(self):
        assert severity_rank("VERBOSE") == -1


class TestFilterByTime:
    def setup_method(self):
        self.entries = [
            make_entry(ts=DT_EARLY),
            make_entry(ts=DT_MID),
            make_entry(ts=DT_LATE),
        ]

    def test_no_filters_yields_all(self):
        result = list(filter_by_time(self.entries))
        assert len(result) == 3

    def test_start_filter(self):
        result = list(filter_by_time(self.entries, start=DT_MID))
        assert len(result) == 2
        assert result[0].timestamp == DT_MID

    def test_end_filter(self):
        result = list(filter_by_time(self.entries, end=DT_MID))
        assert len(result) == 2
        assert result[-1].timestamp == DT_MID

    def test_range_filter(self):
        result = list(filter_by_time(self.entries, start=DT_MID, end=DT_MID))
        assert len(result) == 1

    def test_entries_without_timestamp_are_skipped(self):
        entries = [make_entry(ts=None), make_entry(ts=DT_MID)]
        result = list(filter_by_time(entries, start=DT_EARLY))
        assert len(result) == 1


class TestFilterBySeverity:
    def setup_method(self):
        self.entries = [
            make_entry(level="DEBUG"),
            make_entry(level="INFO"),
            make_entry(level="ERROR"),
        ]

    def test_min_level(self):
        result = list(filter_by_severity(self.entries, min_level="INFO"))
        assert len(result) == 2

    def test_max_level(self):
        result = list(filter_by_severity(self.entries, max_level="INFO"))
        assert len(result) == 2

    def test_exact_level(self):
        result = list(filter_by_severity(self.entries, min_level="INFO", max_level="INFO"))
        assert len(result) == 1
        assert result[0].level == "INFO"

    def test_no_filters_yields_all(self):
        result = list(filter_by_severity(self.entries))
        assert len(result) == 3


class TestApplyFilters:
    def test_combined_filters(self):
        entries = [
            make_entry(ts=DT_EARLY, level="DEBUG"),
            make_entry(ts=DT_MID, level="INFO"),
            make_entry(ts=DT_LATE, level="ERROR"),
        ]
        result = apply_filters(entries, start=DT_MID, min_level="INFO")
        assert len(result) == 2

    def test_returns_list(self):
        result = apply_filters([])
        assert isinstance(result, list)
