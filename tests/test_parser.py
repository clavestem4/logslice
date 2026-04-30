"""Tests for logslice.parser module."""

import pytest
from datetime import datetime
from logslice.parser import parse_line, parse_lines, parse_timestamp, LogEntry


class TestParseTimestamp:
    def test_iso_with_microseconds(self):
        ts = parse_timestamp("2024-03-15T12:34:56.789000")
        assert ts == datetime(2024, 3, 15, 12, 34, 56, 789000)

    def test_iso_without_microseconds(self):
        ts = parse_timestamp("2024-03-15T12:34:56")
        assert ts == datetime(2024, 3, 15, 12, 34, 56)

    def test_space_separator(self):
        ts = parse_timestamp("2024-03-15 08:00:00")
        assert ts == datetime(2024, 3, 15, 8, 0, 0)

    def test_invalid_returns_none(self):
        assert parse_timestamp("not-a-date") is None


class TestParseLine:
    def test_valid_info_entry(self):
        line = "2024-03-15T10:00:00 INFO Application started"
        entry = parse_line(line)
        assert entry is not None
        assert entry.severity == "INFO"
        assert entry.message == "Application started"
        assert entry.timestamp == datetime(2024, 3, 15, 10, 0, 0)

    def test_valid_error_entry(self):
        line = "2024-03-15 14:22:01.500000 ERROR Disk full on /dev/sda1"
        entry = parse_line(line)
        assert entry is not None
        assert entry.severity == "ERROR"
        assert "Disk full" in entry.message

    def test_all_severity_levels(self):
        for level in ("DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"):
            line = f"2024-01-01T00:00:00 {level} test message"
            entry = parse_line(line)
            assert entry is not None
            assert entry.severity == level

    def test_invalid_line_returns_none(self):
        assert parse_line("this is not a log line") is None
        assert parse_line("") is None
        assert parse_line("2024-03-15T10:00:00 TRACE something") is None

    def test_raw_field_preserved(self):
        line = "2024-03-15T10:00:00 INFO Hello world"
        entry = parse_line(line)
        assert entry.raw == line

    def test_trailing_newline_stripped(self):
        line = "2024-03-15T10:00:00 INFO Hello\n"
        entry = parse_line(line)
        assert entry is not None
        assert not entry.raw.endswith("\n")


class TestParseLines:
    def test_skips_invalid_lines(self):
        lines = [
            "2024-03-15T10:00:00 INFO First",
            "garbage line",
            "2024-03-15T10:00:01 ERROR Second",
        ]
        entries = parse_lines(lines)
        assert len(entries) == 2
        assert entries[0].severity == "INFO"
        assert entries[1].severity == "ERROR"

    def test_empty_input(self):
        assert parse_lines([]) == []
