"""Tests for logslice.index."""

import json
import os
import textwrap
from datetime import datetime, timezone
from pathlib import Path

import pytest

from logslice.index import (
    IndexEntry,
    LogIndex,
    build_index,
    load_index,
    save_index,
    seek_to_time,
)


LOG_LINES = textwrap.dedent("""\
    2024-01-01T00:00:00 INFO  message one
    2024-01-01T00:01:00 DEBUG message two
    2024-01-01T00:02:00 WARN  message three
    2024-01-01T00:03:00 ERROR message four
    2024-01-01T00:04:00 INFO  message five
    2024-01-01T00:05:00 INFO  message six
""")


@pytest.fixture
def log_file(tmp_path):
    p = tmp_path / "test.log"
    p.write_text(LOG_LINES)
    return str(p)


class TestBuildIndex:
    def test_returns_log_index(self, log_file):
        idx = build_index(log_file, step=1)
        assert isinstance(idx, LogIndex)

    def test_source_matches_path(self, log_file):
        idx = build_index(log_file, step=1)
        assert idx.source == log_file

    def test_entries_have_correct_types(self, log_file):
        idx = build_index(log_file, step=1)
        for e in idx.entries:
            assert isinstance(e.offset, int)
            assert isinstance(e.timestamp, datetime)
            assert isinstance(e.line_number, int)

    def test_step_reduces_entry_count(self, log_file):
        idx_all = build_index(log_file, step=1)
        idx_sparse = build_index(log_file, step=3)
        assert len(idx_sparse) <= len(idx_all)

    def test_offsets_are_non_negative(self, log_file):
        idx = build_index(log_file, step=1)
        for e in idx.entries:
            assert e.offset >= 0

    def test_timestamps_are_monotonic(self, log_file):
        idx = build_index(log_file, step=1)
        ts = [e.timestamp for e in idx.entries]
        assert ts == sorted(ts)

    def test_empty_file_returns_empty_index(self, tmp_path):
        p = tmp_path / "empty.log"
        p.write_text("")
        idx = build_index(str(p), step=1)
        assert len(idx) == 0


class TestSeekToTime:
    def test_returns_none_for_empty_index(self):
        idx = LogIndex(source="x")
        result = seek_to_time(idx, datetime(2024, 1, 1))
        assert result is None

    def test_returns_offset_before_target(self, log_file):
        idx = build_index(log_file, step=1)
        target = datetime(2024, 1, 1, 0, 3, 0)
        offset = seek_to_time(idx, target)
        assert offset is not None
        assert isinstance(offset, int)

    def test_target_before_all_entries_returns_none(self, log_file):
        idx = build_index(log_file, step=1)
        target = datetime(2023, 1, 1)
        assert seek_to_time(idx, target) is None

    def test_target_after_all_entries_returns_last(self, log_file):
        idx = build_index(log_file, step=1)
        target = datetime(2099, 1, 1)
        offset = seek_to_time(idx, target)
        assert offset == idx.entries[-1].offset


class TestSaveLoadIndex:
    def test_round_trip(self, log_file, tmp_path):
        idx = build_index(log_file, step=1)
        idx_path = str(tmp_path / "index.json")
        save_index(idx, idx_path)
        loaded = load_index(idx_path)
        assert loaded.source == idx.source
        assert len(loaded) == len(idx)

    def test_saved_file_is_valid_json(self, log_file, tmp_path):
        idx = build_index(log_file, step=1)
        idx_path = str(tmp_path / "index.json")
        save_index(idx, idx_path)
        with open(idx_path) as fh:
            data = json.load(fh)
        assert "source" in data
        assert "entries" in data

    def test_loaded_timestamps_match(self, log_file, tmp_path):
        idx = build_index(log_file, step=1)
        idx_path = str(tmp_path / "index.json")
        save_index(idx, idx_path)
        loaded = load_index(idx_path)
        for orig, restored in zip(idx.entries, loaded.entries):
            assert orig.timestamp == restored.timestamp


class TestLogIndex:
    def test_len(self):
        idx = LogIndex(source="f")
        idx.entries.append(IndexEntry(0, datetime(2024, 1, 1), 0))
        assert len(idx) == 1

    def test_repr(self):
        idx = LogIndex(source="myfile.log")
        assert "myfile.log" in repr(idx)

    def test_as_dict_keys(self):
        idx = LogIndex(source="f")
        d = idx.as_dict()
        assert "source" in d
        assert "entries" in d
