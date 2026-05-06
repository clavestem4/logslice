"""Tests for logslice.export module."""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path

import pytest

from logslice.parser import LogEntry
from logslice.export import (
    export_text,
    export_jsonl,
    export_json,
    export_csv,
    export_entries,
)


def make_entry(msg: str, severity: str = "INFO", ts: str = "2024-01-15T10:00:00") -> LogEntry:
    return LogEntry(
        timestamp=datetime.fromisoformat(ts),
        severity=severity,
        message=msg,
        raw=f"{ts} {severity} {msg}",
    )


ENTRIES = [
    make_entry("startup complete", "INFO"),
    make_entry("disk usage high", "WARN", "2024-01-15T10:01:00"),
    make_entry("connection failed", "ERROR", "2024-01-15T10:02:00"),
]


class TestExportText:
    def test_returns_count(self, tmp_path: Path):
        dest = tmp_path / "out.txt"
        assert export_text(ENTRIES, dest) == 3

    def test_file_has_correct_lines(self, tmp_path: Path):
        dest = tmp_path / "out.txt"
        export_text(ENTRIES, dest)
        lines = dest.read_text().splitlines()
        assert len(lines) == 3
        assert "startup complete" in lines[0]

    def test_empty_entries(self, tmp_path: Path):
        dest = tmp_path / "out.txt"
        assert export_text([], dest) == 0
        assert dest.read_text() == ""


class TestExportJsonl:
    def test_returns_count(self, tmp_path: Path):
        dest = tmp_path / "out.jsonl"
        assert export_jsonl(ENTRIES, dest) == 3

    def test_each_line_is_valid_json(self, tmp_path: Path):
        dest = tmp_path / "out.jsonl"
        export_jsonl(ENTRIES, dest)
        for line in dest.read_text().splitlines():
            obj = json.loads(line)
            assert "message" in obj


class TestExportJson:
    def test_returns_count(self, tmp_path: Path):
        dest = tmp_path / "out.json"
        assert export_json(ENTRIES, dest) == 3

    def test_output_is_array(self, tmp_path: Path):
        dest = tmp_path / "out.json"
        export_json(ENTRIES, dest)
        data = json.loads(dest.read_text())
        assert isinstance(data, list)
        assert len(data) == 3

    def test_severity_present(self, tmp_path: Path):
        dest = tmp_path / "out.json"
        export_json(ENTRIES, dest)
        data = json.loads(dest.read_text())
        assert data[1]["severity"] == "WARN"


class TestExportCsv:
    def test_returns_count(self, tmp_path: Path):
        dest = tmp_path / "out.csv"
        assert export_csv(ENTRIES, dest) == 3

    def test_has_header(self, tmp_path: Path):
        dest = tmp_path / "out.csv"
        export_csv(ENTRIES, dest)
        with dest.open(newline="") as fh:
            reader = csv.reader(fh)
            header = next(reader)
        assert header == ["timestamp", "severity", "message", "raw"]


class TestExportEntries:
    def test_dispatch_text(self, tmp_path: Path):
        dest = tmp_path / "out.txt"
        assert export_entries(ENTRIES, dest, fmt="text") == 3

    def test_dispatch_json(self, tmp_path: Path):
        dest = tmp_path / "out.json"
        export_entries(ENTRIES, dest, fmt="json")
        assert isinstance(json.loads(dest.read_text()), list)

    def test_invalid_format_raises(self, tmp_path: Path):
        dest = tmp_path / "out.xyz"
        with pytest.raises(ValueError, match="Unsupported export format"):
            export_entries(ENTRIES, dest, fmt="xml")  # type: ignore
