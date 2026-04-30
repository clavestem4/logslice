"""Tests for logslice.formatter."""

import json
from datetime import datetime, timezone

import pytest

from logslice.parser import LogEntry
from logslice.formatter import (
    format_entry_text,
    format_entry_json,
    format_entry_csv,
    format_entries,
    render,
    SUPPORTED_FORMATS,
)


def make_entry(
    message="hello world",
    severity="INFO",
    ts=None,
    raw=None,
):
    ts = ts or datetime(2024, 6, 1, 12, 0, 0, tzinfo=timezone.utc)
    return LogEntry(timestamp=ts, severity=severity, message=message, raw=raw or message)


class TestFormatEntryText:
    def test_basic(self):
        entry = make_entry()
        result = format_entry_text(entry)
        assert "2024-06-01" in result
        assert "[INFO]" in result
        assert "hello world" in result

    def test_show_raw(self):
        entry = make_entry(raw="RAW LINE")
        assert format_entry_text(entry, show_raw=True) == "RAW LINE"

    def test_no_timestamp(self):
        entry = LogEntry(timestamp=None, severity="WARN", message="oops", raw="oops")
        result = format_entry_text(entry)
        assert "(no timestamp)" in result
        assert "[WARN]" in result

    def test_no_severity(self):
        entry = LogEntry(timestamp=make_entry().timestamp, severity=None, message="msg", raw="msg")
        result = format_entry_text(entry)
        assert "[" not in result
        assert "msg" in result


class TestFormatEntryJson:
    def test_structure(self):
        entry = make_entry()
        data = json.loads(format_entry_json(entry))
        assert "timestamp" in data
        assert "severity" in data
        assert "message" in data

    def test_values(self):
        entry = make_entry(message="test", severity="ERROR")
        data = json.loads(format_entry_json(entry))
        assert data["severity"] == "ERROR"
        assert data["message"] == "test"

    def test_none_timestamp(self):
        entry = LogEntry(timestamp=None, severity="DEBUG", message="x", raw="x")
        data = json.loads(format_entry_json(entry))
        assert data["timestamp"] is None


class TestFormatEntryCsv:
    def test_header_in_format_entries(self):
        lines = format_entries([make_entry()], fmt="csv")
        assert lines[0] == '"timestamp","severity","message"'

    def test_row_count(self):
        entries = [make_entry(), make_entry(message="second")]
        lines = format_entries(entries, fmt="csv")
        assert len(lines) == 3  # header + 2 rows

    def test_quote_escaping(self):
        entry = make_entry(message='say "hello"')
        row = format_entry_csv(entry)
        assert '""' in row


class TestFormatEntries:
    def test_unsupported_format_raises(self):
        with pytest.raises(ValueError, match="Unsupported format"):
            format_entries([make_entry()], fmt="xml")

    def test_empty_list(self):
        assert format_entries([], fmt="text") == []

    def test_json_multiple(self):
        entries = [make_entry(), make_entry(severity="DEBUG", message="dbg")]
        lines = format_entries(entries, fmt="json")
        assert len(lines) == 2
        assert all(json.loads(l) for l in lines)


class TestRender:
    def test_newline_joined(self):
        entries = [make_entry(message="a"), make_entry(message="b")]
        result = render(entries, fmt="text")
        assert "\n" in result

    def test_empty(self):
        assert render([], fmt="json") == ""
