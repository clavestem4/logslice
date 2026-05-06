"""Tests for logslice.transform."""

import pytest
from datetime import datetime
from logslice.parser import LogEntry
from logslice.transform import (
    redact_message,
    normalize_severity,
    truncate_message,
    apply_transform,
)


def make_entry(message="hello world", severity="INFO", timestamp=None):
    return LogEntry(
        timestamp=timestamp or datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw=f"2024-01-01T12:00:00 {severity} {message}",
    )


class TestRedactMessage:
    def test_replaces_pattern(self):
        entry = make_entry(message="user=alice token=secret123")
        result = redact_message(entry, r"token=\S+")
        assert result.message == "user=alice [REDACTED]"

    def test_custom_replacement(self):
        entry = make_entry(message="ip=192.168.1.1")
        result = redact_message(entry, r"\d+\.\d+\.\d+\.\d+", "***")
        assert result.message == "ip=***"

    def test_no_match_unchanged(self):
        entry = make_entry(message="nothing to redact")
        result = redact_message(entry, r"password=\S+")
        assert result.message == "nothing to redact"

    def test_preserves_other_fields(self):
        entry = make_entry(message="secret=abc", severity="ERROR")
        result = redact_message(entry, r"secret=\S+")
        assert result.severity == "ERROR"
        assert result.timestamp == entry.timestamp

    def test_returns_new_entry(self):
        entry = make_entry(message="token=xyz")
        result = redact_message(entry, r"token=\S+")
        assert result is not entry


class TestNormalizeSeverity:
    def test_uppercases_severity(self):
        entry = make_entry(severity="info")
        result = normalize_severity(entry)
        assert result.severity == "INFO"

    def test_strips_whitespace(self):
        entry = make_entry(severity="  warn  ")
        result = normalize_severity(entry)
        assert result.severity == "WARN"

    def test_already_upper_unchanged(self):
        entry = make_entry(severity="DEBUG")
        result = normalize_severity(entry)
        assert result.severity == "DEBUG"

    def test_none_severity_preserved(self):
        entry = make_entry(severity=None)
        result = normalize_severity(entry)
        assert result.severity is None


class TestTruncateMessage:
    def test_truncates_long_message(self):
        entry = make_entry(message="abcdefghij")
        result = truncate_message(entry, 5)
        assert result.message == "abcde"

    def test_short_message_unchanged(self):
        entry = make_entry(message="hi")
        result = truncate_message(entry, 10)
        assert result.message == "hi"

    def test_exact_length_unchanged(self):
        entry = make_entry(message="hello")
        result = truncate_message(entry, 5)
        assert result.message == "hello"

    def test_zero_length_empties_message(self):
        entry = make_entry(message="something")
        result = truncate_message(entry, 0)
        assert result.message == ""

    def test_negative_raises(self):
        entry = make_entry()
        with pytest.raises(ValueError):
            truncate_message(entry, -1)


class TestApplyTransform:
    def test_applies_to_all_entries(self):
        entries = [make_entry(severity="info"), make_entry(severity="warn")]
        result = apply_transform(entries, normalize_severity)
        assert all(e.severity == e.severity.upper() for e in result)

    def test_drops_none_results(self):
        entries = [make_entry(message="keep"), make_entry(message="drop")]
        result = apply_transform(entries, lambda e: None if e.message == "drop" else e)
        assert len(result) == 1
        assert result[0].message == "keep"

    def test_empty_list_returns_empty(self):
        result = apply_transform([], normalize_severity)
        assert result == []

    def test_preserves_order(self):
        entries = [make_entry(message=str(i)) for i in range(5)]
        result = apply_transform(entries, lambda e: e)
        assert [e.message for e in result] == [str(i) for i in range(5)]
