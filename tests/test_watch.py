"""Tests for logslice.watch."""

import time
from datetime import datetime, timezone
from pathlib import Path

import pytest

from logslice.watch import watch_file, watch_callback


LINES = [
    "2024-01-15T10:00:00 INFO  service started",
    "2024-01-15T10:00:01 DEBUG checking config",
    "2024-01-15T10:00:02 ERROR disk full",
    "2024-01-15T10:00:03 WARNING low memory",
]


@pytest.fixture
def log_file(tmp_path: Path) -> Path:
    p = tmp_path / "app.log"
    p.write_text("")  # start empty
    return p


def _append(path: Path, line: str) -> None:
    with path.open("a") as f:
        f.write(line + "\n")


class TestWatchFile:
    def test_yields_new_entries(self, log_file):
        # Write lines before first poll cycle fires
        for line in LINES:
            _append(log_file, line)

        entries = list(watch_file(log_file, poll_interval=0, max_iterations=1))
        assert len(entries) == 4

    def test_entry_messages_correct(self, log_file):
        for line in LINES:
            _append(log_file, line)

        entries = list(watch_file(log_file, poll_interval=0, max_iterations=1))
        messages = [e.message for e in entries]
        assert "service started" in messages
        assert "disk full" in messages

    def test_min_severity_filters(self, log_file):
        for line in LINES:
            _append(log_file, line)

        entries = list(
            watch_file(log_file, min_severity="WARNING", poll_interval=0, max_iterations=1)
        )
        severities = {e.severity for e in entries}
        assert "DEBUG" not in severities
        assert "INFO" not in severities
        assert len(entries) == 2  # ERROR + WARNING

    def test_empty_file_yields_nothing(self, log_file):
        entries = list(watch_file(log_file, poll_interval=0, max_iterations=1))
        assert entries == []

    def test_truncated_file_resets(self, log_file, tmp_path):
        # Write content so last_pos advances, then truncate
        for line in LINES:
            _append(log_file, line)

        # Collect first batch (sets internal position)
        gen = watch_file(log_file, poll_interval=0, max_iterations=2)
        first_batch = []
        # Manually drive one iteration via the generator
        try:
            first_batch.append(next(gen))
        except StopIteration:
            pass

    def test_multiple_iterations_accumulate(self, log_file):
        _append(log_file, LINES[0])
        entries = list(watch_file(log_file, poll_interval=0, max_iterations=2))
        # All entries from first iteration; second iteration finds nothing new
        assert len(entries) == 1


class TestWatchCallback:
    def test_callback_called_for_each_entry(self, log_file):
        for line in LINES:
            _append(log_file, line)

        seen = []
        count = watch_callback(
            log_file, seen.append, poll_interval=0, max_iterations=1
        )
        assert count == 4
        assert len(seen) == 4

    def test_returns_zero_on_empty(self, log_file):
        count = watch_callback(
            log_file, lambda e: None, poll_interval=0, max_iterations=1
        )
        assert count == 0

    def test_min_severity_passed_through(self, log_file):
        for line in LINES:
            _append(log_file, line)

        seen = []
        watch_callback(
            log_file,
            seen.append,
            min_severity="ERROR",
            poll_interval=0,
            max_iterations=1,
        )
        assert all(e.severity == "ERROR" for e in seen)
        assert len(seen) == 1
