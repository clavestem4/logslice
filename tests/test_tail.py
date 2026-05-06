"""Tests for logslice.tail."""

from __future__ import annotations

import os
import tempfile
import threading
import time
from datetime import datetime, timezone
from typing import List

import pytest

from logslice.parser import LogEntry
from logslice.tail import follow_file, tail_entries, tail_file


RAW_LINES = [
    "2024-01-01T00:00:01Z INFO  alpha",
    "2024-01-01T00:00:02Z DEBUG beta",
    "2024-01-01T00:00:03Z WARN  gamma",
    "2024-01-01T00:00:04Z ERROR delta",
    "2024-01-01T00:00:05Z INFO  epsilon",
]


class TestTailEntries:
    def test_returns_last_n(self):
        result = tail_entries(RAW_LINES, n=3)
        assert len(result) == 3
        assert result[-1].message == "epsilon"

    def test_n_larger_than_list(self):
        result = tail_entries(RAW_LINES, n=100)
        assert len(result) == len(RAW_LINES)

    def test_n_zero_returns_empty(self):
        result = tail_entries(RAW_LINES, n=0)
        assert result == []

    def test_n_negative_returns_empty(self):
        result = tail_entries(RAW_LINES, n=-5)
        assert result == []

    def test_order_preserved(self):
        result = tail_entries(RAW_LINES, n=2)
        messages = [e.message for e in result]
        assert messages == ["delta", "epsilon"]

    def test_unparseable_lines_skipped(self):
        lines = RAW_LINES + ["not a log line at all"]
        result = tail_entries(lines, n=10)
        assert len(result) == len(RAW_LINES)

    def test_returns_log_entries(self):
        result = tail_entries(RAW_LINES, n=2)
        for entry in result:
            assert isinstance(entry, LogEntry)


class TestTailFile:
    def test_reads_file(self, tmp_path):
        log = tmp_path / "app.log"
        log.write_text("\n".join(RAW_LINES))
        result = tail_file(str(log), n=3)
        assert len(result) == 3
        assert result[0].message == "gamma"

    def test_empty_file_returns_empty(self, tmp_path):
        log = tmp_path / "empty.log"
        log.write_text("")
        assert tail_file(str(log)) == []


class TestFollowFile:
    def test_callback_receives_new_entries(self, tmp_path):
        log = tmp_path / "live.log"
        log.write_text("")
        collected: List[LogEntry] = []

        def writer():
            time.sleep(0.1)
            with open(str(log), "a") as fh:
                fh.write("2024-01-01T00:00:10Z INFO  hello\n")

        t = threading.Thread(target=writer, daemon=True)
        t.start()
        follow_file(str(log), callback=collected.append, stop_after=0.6)
        t.join()
        assert len(collected) == 1
        assert collected[0].message == "hello"
