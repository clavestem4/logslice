"""Tests for logslice.formatter module."""

import json
import pytest
from datetime import datetime
from logslice.parser import LogEntry
from logslice.formatter import (
    format_entry_text,
    format_entry_json,
    format_entry_csv,
    format_entries,
    render,
)
from logslice.highlight import RESET


def make_entry(
    timestamp=None, severity=None, message=None, raw=None
) -> LogEntry:
    ts = datetime.fromisoformat(timestamp) if timestamp else None
    return LogEntry(timestamp=ts, severity=severity, message=message, raw=raw)


class TestFormatEntryText:
    def test_basic(self):
        entry = make_entry("2024-03-01T12:00:00", "info", "server started")
        result = format_entry_text(entry)
        assert "2024-03-01 12:00:00" in result
        assert "[INFO]" in result
        assert "server started" in result

    def test_show_raw(self):
        entry = make_entry(raw="raw original line", message="parsed")
        assert format_entry_text(entry, show_raw=True) == "raw original line"

    def test_no_timestamp(self):
        entry = make_entry(severity="error", message="oops")
        result = format_entry_text(entry)
        assert "[ERROR]" in result
        assert "oops" in result

    def test_empty_entry_returns_raw_or_empty(self):
        entry = make_entry(raw="fallback")
        assert format_entry_text(entry) == "fallback"

    def test_fully_empty_entry(self):
        entry = LogEntry(timestamp=None, severity=None, message=None, raw=None)
        assert format_entry_text(entry) == ""


class TestFormatEntryJson:
    def test_returns_valid_json(self):
        entry = make_entry("2024-01-15T08:30:00", "warning", "disk low")
        data = json.loads(format_entry_json(entry))
        assert data["severity"] == "warning"
        assert data["message"] == "disk low"
        assert "2024-01-15" in data["timestamp"]

    def test_none_fields_are_null(self):
        entry = make_entry()
        data = json.loads(format_entry_json(entry))
        assert data["timestamp"] is None
        assert data["severity"] is None


class TestFormatEntryCsv:
    def test_basic_csv(self):
        entry = make_entry("2024-06-01T10:00:00", "error", "connection refused")
        result = format_entry_csv(entry)
        assert "error" in result
        assert "connection refused" in result

    def test_empty_fields(self):
        entry = make_entry()
        result = format_entry_csv(entry)
        assert result.count(",") >= 2

    def test_message_with_comma_is_quoted(self):
        entry = make_entry(message="hello, world")
        result = format_entry_csv(entry)
        assert '"hello, world"' in result


class TestFormatEntries:
    def test_text_format_no_color(self):
        entries = [make_entry("2024-01-01T00:00:00", "info", "boot")]
        results = list(format_entries(entries, fmt="text", color=False))
        assert len(results) == 1
        assert RESET not in results[0]

    def test_json_format(self):
        entries = [make_entry("2024-01-01T00:00:00", "debug", "trace")]
        results = list(format_entries(entries, fmt="json"))
        data = json.loads(results[0])
        assert data["severity"] == "debug"

    def test_csv_format(self):
        entries = [make_entry("2024-01-01T00:00:00", "info", "ok")]
        results = list(format_entries(entries, fmt="csv"))
        assert "info" in results[0]

    def test_color_enabled_adds_ansi(self):
        entries = [make_entry(severity="error", message="boom")]
        results = list(format_entries(entries, fmt="text", color=True))
        assert RESET in results[0]


class TestRender:
    def test_multiple_entries_joined_by_newline(self):
        entries = [
            make_entry(message="line one"),
            make_entry(message="line two"),
        ]
        result = render(entries, color=False)
        assert "line one" in result
        assert "line two" in result
        assert "\n" in result
