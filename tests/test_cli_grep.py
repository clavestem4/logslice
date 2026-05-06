"""Tests for logslice.cli_grep module."""

import io
import pytest
from datetime import datetime
from logslice.parser import LogEntry
from logslice.cli_grep import run_grep, add_grep_arguments
import argparse


def make_entry(message: str, severity: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 6, 1, 10, 0, 0),
        severity=severity,
        message=message,
        raw=f"2024-06-01T10:00:00 {severity} {message}",
    )


ENTRIES = [
    make_entry("Application boot complete"),
    make_entry("Failed to connect to database", "ERROR"),
    make_entry("Retrying database connection", "WARN"),
    make_entry("Health check passed"),
    make_entry("Shutting down gracefully"),
]


class TestRunGrep:
    def test_returns_match_count(self):
        out = io.StringIO()
        count = run_grep(ENTRIES, "database", ignore_case=True, out=out)
        assert count == 2

    def test_output_contains_messages(self):
        out = io.StringIO()
        run_grep(ENTRIES, "database", ignore_case=True, out=out)
        text = out.getvalue()
        assert "database" in text.lower()

    def test_count_only_prints_number(self):
        out = io.StringIO()
        run_grep(ENTRIES, "database", ignore_case=True, count_only=True, out=out)
        assert out.getvalue().strip() == "2"

    def test_no_match_returns_zero(self):
        out = io.StringIO()
        count = run_grep(ENTRIES, "unicorn", out=out)
        assert count == 0

    def test_no_match_count_only_prints_zero(self):
        out = io.StringIO()
        run_grep(ENTRIES, "unicorn", count_only=True, out=out)
        assert out.getvalue().strip() == "0"

    def test_invert_returns_non_matching(self):
        out = io.StringIO()
        count = run_grep(ENTRIES, "database", ignore_case=True, invert=True, out=out)
        assert count == 3

    def test_json_format_output(self):
        out = io.StringIO()
        run_grep(ENTRIES, "Health", fmt="json", out=out)
        text = out.getvalue()
        assert "Health" in text

    def test_empty_entries_returns_zero(self):
        out = io.StringIO()
        count = run_grep([], "anything", out=out)
        assert count == 0

    def test_case_sensitive_misses(self):
        out = io.StringIO()
        count = run_grep(ENTRIES, "DATABASE", ignore_case=False, out=out)
        assert count == 0


class TestAddGrepArguments:
    def _make_parser(self):
        p = argparse.ArgumentParser()
        add_grep_arguments(p)
        return p

    def test_pattern_required(self):
        p = self._make_parser()
        with pytest.raises(SystemExit):
            p.parse_args([])

    def test_pattern_parsed(self):
        p = self._make_parser()
        args = p.parse_args(["error"])
        assert args.pattern == "error"

    def test_ignore_case_default_false(self):
        p = self._make_parser()
        args = p.parse_args(["error"])
        assert args.ignore_case is False

    def test_ignore_case_flag(self):
        p = self._make_parser()
        args = p.parse_args(["-i", "error"])
        assert args.ignore_case is True

    def test_invert_flag(self):
        p = self._make_parser()
        args = p.parse_args(["-v", "error"])
        assert args.invert is True

    def test_count_flag(self):
        p = self._make_parser()
        args = p.parse_args(["-c", "error"])
        assert args.count is True

    def test_format_default_text(self):
        p = self._make_parser()
        args = p.parse_args(["error"])
        assert args.format == "text"
