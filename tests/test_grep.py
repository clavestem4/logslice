"""Tests for logslice.grep module."""

import pytest
from datetime import datetime
from logslice.parser import LogEntry
from logslice.grep import (
    compile_pattern,
    matches_entry,
    grep_entries,
    grep_count,
    first_match,
)


def make_entry(message: str, severity: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw=f"2024-01-01T12:00:00 {severity} {message}",
    )


ENTRIES = [
    make_entry("Server started on port 8080"),
    make_entry("Connection refused from 10.0.0.1", "ERROR"),
    make_entry("Request received: GET /health"),
    make_entry("Database connection established"),
    make_entry("Connection timeout after 30s", "WARN"),
]


class TestCompilePattern:
    def test_returns_compiled_regex(self):
        p = compile_pattern(r"\d+")
        assert p.search("port 8080") is not None

    def test_case_sensitive_by_default(self):
        p = compile_pattern("error")
        assert p.search("ERROR") is None

    def test_ignore_case_flag(self):
        p = compile_pattern("error", ignore_case=True)
        assert p.search("ERROR") is not None


class TestMatchesEntry:
    def test_matching_message(self):
        entry = make_entry("Server started")
        p = compile_pattern("started")
        assert matches_entry(entry, p) is True

    def test_non_matching_message(self):
        entry = make_entry("Server started")
        p = compile_pattern("stopped")
        assert matches_entry(entry, p) is False

    def test_none_message_returns_false(self):
        entry = LogEntry(timestamp=None, severity="INFO", message=None, raw="")
        p = compile_pattern("anything")
        assert matches_entry(entry, p) is False


class TestGrepEntries:
    def test_basic_filter(self):
        result = grep_entries(ENTRIES, "Connection")
        assert len(result) == 2

    def test_no_matches_returns_empty(self):
        result = grep_entries(ENTRIES, "unicorn")
        assert result == []

    def test_all_match(self):
        result = grep_entries(ENTRIES, ".+")
        assert len(result) == len(ENTRIES)

    def test_ignore_case(self):
        result = grep_entries(ENTRIES, "connection", ignore_case=True)
        assert len(result) == 2

    def test_case_sensitive_misses(self):
        result = grep_entries(ENTRIES, "connection", ignore_case=False)
        assert len(result) == 0

    def test_invert_match(self):
        result = grep_entries(ENTRIES, "Connection", invert=True)
        assert len(result) == 3

    def test_invert_no_matches_returns_all(self):
        result = grep_entries(ENTRIES, "unicorn", invert=True)
        assert len(result) == len(ENTRIES)

    def test_regex_pattern(self):
        result = grep_entries(ENTRIES, r"port \d+")
        assert len(result) == 1
        assert "8080" in result[0].message

    def test_empty_entries(self):
        result = grep_entries([], "anything")
        assert result == []


class TestGrepCount:
    def test_count_matches(self):
        assert grep_count(ENTRIES, "Connection") == 2

    def test_count_zero(self):
        assert grep_count(ENTRIES, "unicorn") == 0


class TestFirstMatch:
    def test_returns_first(self):
        result = first_match(ENTRIES, "Connection")
        assert result is not None
        assert "Connection refused" in result.message

    def test_no_match_returns_none(self):
        result = first_match(ENTRIES, "unicorn")
        assert result is None

    def test_ignore_case_first_match(self):
        result = first_match(ENTRIES, "server", ignore_case=True)
        assert result is not None
        assert "Server started" in result.message
