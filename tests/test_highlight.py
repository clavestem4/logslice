"""Tests for logslice.highlight module."""

import io
import pytest
from logslice.highlight import (
    colorize,
    highlight_line,
    supports_color,
    COLORS,
    RESET,
    BOLD,
    SEVERITY_STYLES,
)


class TestColorize:
    def test_applies_color_code(self):
        result = colorize("hello", "red")
        assert COLORS["red"] in result
        assert "hello" in result
        assert RESET in result

    def test_applies_bold(self):
        result = colorize("hello", "red", bold=True)
        assert BOLD in result
        assert COLORS["red"] in result

    def test_unknown_color_no_code(self):
        result = colorize("hello", "ultraviolet")
        assert "hello" in result
        assert RESET in result

    def test_no_bold_by_default(self):
        result = colorize("msg", "green")
        assert BOLD not in result


class TestHighlightLine:
    def test_disabled_returns_unchanged(self):
        line = "2024-01-01 ERROR something broke"
        assert highlight_line(line, "error", enabled=False) == line

    def test_none_severity_returns_unchanged(self):
        line = "some log line"
        assert highlight_line(line, None) == line

    def test_unknown_severity_returns_unchanged(self):
        line = "some log line"
        assert highlight_line(line, "verbose") == line

    def test_error_adds_color(self):
        line = "ERROR: disk full"
        result = highlight_line(line, "error")
        assert RESET in result
        assert line in result

    def test_case_insensitive_severity(self):
        line = "WARNING: low memory"
        result_lower = highlight_line(line, "warning")
        result_upper = highlight_line(line, "WARNING")
        assert result_lower == result_upper

    def test_all_known_severities_produce_output(self):
        for sev in SEVERITY_STYLES:
            result = highlight_line("test line", sev)
            assert RESET in result

    def test_info_not_bold(self):
        result = highlight_line("info message", "info")
        assert BOLD not in result

    def test_critical_is_bold(self):
        result = highlight_line("critical failure", "critical")
        assert BOLD in result


class TestSupportsColor:
    def test_plain_stringio_returns_false(self):
        stream = io.StringIO()
        assert supports_color(stream) is False

    def test_stream_without_isatty_returns_false(self):
        class FakeStream:
            pass
        assert supports_color(FakeStream()) is False
