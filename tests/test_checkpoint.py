"""Tests for logslice.checkpoint."""

import json
from datetime import datetime
from pathlib import Path

import pytest

from logslice.checkpoint import (
    Checkpoint,
    clear_checkpoint,
    load_checkpoint,
    save_checkpoint,
)


@pytest.fixture
def tmp_dir(tmp_path):
    return str(tmp_path)


class TestCheckpoint:
    def test_default_offset_is_zero(self):
        cp = Checkpoint(file_path="app.log")
        assert cp.byte_offset == 0

    def test_default_lines_processed_is_zero(self):
        cp = Checkpoint(file_path="app.log")
        assert cp.lines_processed == 0

    def test_default_last_timestamp_is_none(self):
        cp = Checkpoint(file_path="app.log")
        assert cp.last_timestamp is None

    def test_advance_updates_offset(self):
        cp = Checkpoint(file_path="app.log")
        cp.advance(byte_offset=512, timestamp=None)
        assert cp.byte_offset == 512

    def test_advance_updates_timestamp(self):
        cp = Checkpoint(file_path="app.log")
        ts = datetime(2024, 1, 15, 10, 0, 0)
        cp.advance(byte_offset=100, timestamp=ts)
        assert cp.last_timestamp == ts

    def test_advance_accumulates_lines(self):
        cp = Checkpoint(file_path="app.log")
        cp.advance(byte_offset=100, timestamp=None, lines=5)
        cp.advance(byte_offset=200, timestamp=None, lines=3)
        assert cp.lines_processed == 8

    def test_as_dict_contains_expected_keys(self):
        cp = Checkpoint(file_path="app.log", byte_offset=256, lines_processed=10)
        d = cp.as_dict()
        assert "file_path" in d
        assert "byte_offset" in d
        assert "last_timestamp" in d
        assert "lines_processed" in d

    def test_as_dict_null_timestamp(self):
        cp = Checkpoint(file_path="app.log")
        assert cp.as_dict()["last_timestamp"] is None

    def test_as_dict_serializes_timestamp(self):
        ts = datetime(2024, 6, 1, 12, 0, 0)
        cp = Checkpoint(file_path="app.log", last_timestamp=ts)
        assert cp.as_dict()["last_timestamp"] == ts.isoformat()


class TestSaveAndLoad:
    def test_save_creates_file(self, tmp_dir):
        cp = Checkpoint(file_path="server.log", byte_offset=1024)
        path = save_checkpoint(cp, checkpoint_dir=tmp_dir)
        assert path.exists()

    def test_saved_file_is_valid_json(self, tmp_dir):
        cp = Checkpoint(file_path="server.log", byte_offset=1024)
        path = save_checkpoint(cp, checkpoint_dir=tmp_dir)
        data = json.loads(path.read_text())
        assert data["byte_offset"] == 1024

    def test_load_returns_checkpoint(self, tmp_dir):
        cp = Checkpoint(file_path="server.log", byte_offset=2048, lines_processed=100)
        save_checkpoint(cp, checkpoint_dir=tmp_dir)
        loaded = load_checkpoint("server.log", checkpoint_dir=tmp_dir)
        assert loaded is not None
        assert loaded.byte_offset == 2048
        assert loaded.lines_processed == 100

    def test_load_restores_timestamp(self, tmp_dir):
        ts = datetime(2024, 3, 10, 8, 30, 0)
        cp = Checkpoint(file_path="server.log", last_timestamp=ts)
        save_checkpoint(cp, checkpoint_dir=tmp_dir)
        loaded = load_checkpoint("server.log", checkpoint_dir=tmp_dir)
        assert loaded.last_timestamp == ts

    def test_load_missing_returns_none(self, tmp_dir):
        result = load_checkpoint("nonexistent.log", checkpoint_dir=tmp_dir)
        assert result is None

    def test_clear_removes_file(self, tmp_dir):
        cp = Checkpoint(file_path="app.log")
        save_checkpoint(cp, checkpoint_dir=tmp_dir)
        removed = clear_checkpoint("app.log", checkpoint_dir=tmp_dir)
        assert removed is True
        assert load_checkpoint("app.log", checkpoint_dir=tmp_dir) is None

    def test_clear_missing_returns_false(self, tmp_dir):
        result = clear_checkpoint("ghost.log", checkpoint_dir=tmp_dir)
        assert result is False
