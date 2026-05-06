"""Tests for logslice.pivot."""

from datetime import datetime, timezone

import pytest

from logslice.parser import LogEntry
from logslice.pivot import PivotTable, pivot


def make_entry(
    message: str = "msg",
    severity: str = "INFO",
    ts: datetime | None = None,
    raw: str = "",
) -> LogEntry:
    return LogEntry(
        timestamp=ts,
        severity=severity,
        message=message,
        raw=raw or f"{severity} {message}",
    )


DT_A = datetime(2024, 3, 1, 10, 5, 0, tzinfo=timezone.utc)
DT_B = datetime(2024, 3, 2, 15, 30, 0, tzinfo=timezone.utc)
DT_C = datetime(2024, 3, 1, 10, 55, 0, tzinfo=timezone.utc)


class TestPivotBySeverity:
    def test_groups_by_severity(self):
        entries = [
            make_entry("a", "INFO"),
            make_entry("b", "ERROR"),
            make_entry("c", "INFO"),
        ]
        table = pivot(entries, key="severity")
        assert set(table.group_keys()) == {"INFO", "ERROR"}
        assert len(table.groups["INFO"]) == 2
        assert len(table.groups["ERROR"]) == 1

    def test_empty_entries(self):
        table = pivot([], key="severity")
        assert table.groups == {}
        assert table.group_keys() == []

    def test_unknown_severity_label(self):
        entries = [make_entry("x", severity=None)]
        table = pivot(entries, key="severity")
        assert "UNKNOWN" in table.group_keys()

    def test_group_counts(self):
        entries = [make_entry(severity="WARN")] * 3 + [make_entry(severity="DEBUG")]
        table = pivot(entries, key="severity")
        counts = table.group_counts()
        assert counts["WARN"] == 3
        assert counts["DEBUG"] == 1


class TestPivotByDate:
    def test_groups_by_date(self):
        entries = [
            make_entry(ts=DT_A),
            make_entry(ts=DT_B),
            make_entry(ts=DT_C),
        ]
        table = pivot(entries, key="date")
        assert "2024-03-01" in table.groups
        assert "2024-03-02" in table.groups
        assert len(table.groups["2024-03-01"]) == 2

    def test_no_timestamp_falls_back(self):
        entries = [make_entry(ts=None)]
        table = pivot(entries, key="date")
        assert "no-date" in table.groups


class TestPivotByHour:
    def test_groups_by_hour(self):
        entries = [make_entry(ts=DT_A), make_entry(ts=DT_C), make_entry(ts=DT_B)]
        table = pivot(entries, key="hour")
        assert "2024-03-01T10" in table.groups
        assert len(table.groups["2024-03-01T10"]) == 2


class TestPivotCustomKeyFn:
    def test_custom_key_fn(self):
        entries = [
            make_entry("hello world"),
            make_entry("hello there"),
            make_entry("goodbye"),
        ]
        table = pivot(
            entries,
            key="first_word",
            key_fn=lambda e: e.message.split()[0],
        )
        assert "hello" in table.groups
        assert "goodbye" in table.groups
        assert len(table.groups["hello"]) == 2

    def test_invalid_key_raises(self):
        with pytest.raises(ValueError, match="Unknown pivot key"):
            pivot([], key="nonexistent")


class TestPivotTable:
    def test_as_dict_structure(self):
        entries = [make_entry("m", "INFO", raw="INFO m")]
        table = pivot(entries, key="severity")
        d = table.as_dict()
        assert d["key"] == "severity"
        assert "INFO" in d["groups"]
        assert d["groups"]["INFO"] == ["INFO m"]

    def test_str_representation(self):
        entries = [make_entry(severity="ERROR")]
        table = pivot(entries, key="severity")
        s = str(table)
        assert "severity" in s
        assert "ERROR" in s
        assert "1 entries" in s
