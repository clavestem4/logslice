"""Tests for logslice.slice — slice_file and slice_text integration."""

import os
import tempfile
import pytest
from datetime import datetime, timezone

from logslice.slice import slice_file, slice_text
from logslice.parser import LogEntry


SAMPLE_LOG = """\
2024-01-15T08:00:00Z INFO  Server started
2024-01-15T08:05:00Z DEBUG Loaded config from /etc/app.conf
2024-01-15T08:10:00Z INFO  Listening on port 8080
2024-01-15T08:15:00Z WARNING High memory usage detected
2024-01-15T08:20:00Z ERROR Failed to connect to database
2024-01-15T08:25:00Z INFO  Retrying database connection
2024-01-15T08:30:00Z CRITICAL Database connection lost
2024-01-15T08:35:00Z INFO  Shutdown initiated
"""


@pytest.fixture
def log_file(tmp_path):
    """Write SAMPLE_LOG to a temporary file and return its path."""
    p = tmp_path / "app.log"
    p.write_text(SAMPLE_LOG)
    return str(p)


def dt(s):
    """Parse an ISO timestamp string into a UTC-aware datetime."""
    return datetime.fromisoformat(s.replace("Z", "+00:00"))


# ---------------------------------------------------------------------------
# slice_text
# ---------------------------------------------------------------------------

class TestSliceText:
    def test_returns_list_of_log_entries(self):
        entries = slice_text(SAMPLE_LOG)
        assert all(isinstance(e, LogEntry) for e in entries)

    def test_all_entries_parsed(self):
        entries = slice_text(SAMPLE_LOG)
        assert len(entries) == 8

    def test_filter_by_start(self):
        entries = slice_text(SAMPLE_LOG, start=dt("2024-01-15T08:20:00Z"))
        severities = [e.severity for e in entries]
        assert "DEBUG" not in severities
        assert "ERROR" in severities
        assert len(entries) == 4

    def test_filter_by_end(self):
        entries = slice_text(SAMPLE_LOG, end=dt("2024-01-15T08:10:00Z"))
        assert len(entries) == 3
        assert entries[-1].severity == "INFO"

    def test_filter_by_start_and_end(self):
        entries = slice_text(
            SAMPLE_LOG,
            start=dt("2024-01-15T08:10:00Z"),
            end=dt("2024-01-15T08:25:00Z"),
        )
        assert len(entries) == 4
        assert entries[0].severity == "INFO"   # 08:10
        assert entries[-1].severity == "INFO"  # 08:25

    def test_filter_by_min_severity(self):
        entries = slice_text(SAMPLE_LOG, min_severity="WARNING")
        severities = {e.severity for e in entries}
        assert severities == {"WARNING", "ERROR", "CRITICAL"}

    def test_filter_by_min_severity_critical(self):
        entries = slice_text(SAMPLE_LOG, min_severity="CRITICAL")
        assert len(entries) == 1
        assert entries[0].severity == "CRITICAL"

    def test_combined_time_and_severity(self):
        entries = slice_text(
            SAMPLE_LOG,
            start=dt("2024-01-15T08:10:00Z"),
            end=dt("2024-01-15T08:30:00Z"),
            min_severity="WARNING",
        )
        severities = [e.severity for e in entries]
        assert "INFO" not in severities
        assert "DEBUG" not in severities
        assert "WARNING" in severities
        assert "ERROR" in severities
        assert "CRITICAL" in severities

    def test_empty_input(self):
        assert slice_text("") == []

    def test_unparseable_lines_skipped(self):
        text = "not a log line\n" + SAMPLE_LOG
        entries = slice_text(text)
        # Unparseable lines produce entries with no timestamp; they should
        # still be returned when no filters are applied.
        assert len(entries) >= 8

    def test_no_filters_returns_all(self):
        entries = slice_text(SAMPLE_LOG)
        assert len(entries) == 8


# ---------------------------------------------------------------------------
# slice_file
# ---------------------------------------------------------------------------

class TestSliceFile:
    def test_reads_file_and_returns_entries(self, log_file):
        entries = slice_file(log_file)
        assert len(entries) == 8

    def test_file_not_found_raises(self):
        with pytest.raises(FileNotFoundError):
            slice_file("/nonexistent/path/to/file.log")

    def test_filter_forwarded_to_slice_text(self, log_file):
        entries = slice_file(log_file, min_severity="ERROR")
        severities = {e.severity for e in entries}
        assert severities == {"ERROR", "CRITICAL"}

    def test_time_filter_forwarded(self, log_file):
        entries = slice_file(
            log_file,
            start=dt("2024-01-15T08:25:00Z"),
            end=dt("2024-01-15T08:35:00Z"),
        )
        assert len(entries) == 3
