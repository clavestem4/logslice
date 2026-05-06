"""Tests for logslice.annotate."""

from datetime import datetime
from logslice.parser import LogEntry
from logslice.annotate import (
    AnnotatedEntry,
    annotate,
    filter_by_label,
    label_map,
)


def make_entry(message: str = "test", severity: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw=f"2024-01-01T12:00:00 {severity} {message}",
    )


class TestAnnotatedEntry:
    def test_has_label_true(self):
        a = AnnotatedEntry(entry=make_entry(), labels=["important", "review"])
        assert a.has_label("important")

    def test_has_label_case_insensitive(self):
        a = AnnotatedEntry(entry=make_entry(), labels=["URGENT"])
        assert a.has_label("urgent")

    def test_has_label_false(self):
        a = AnnotatedEntry(entry=make_entry(), labels=["debug"])
        assert not a.has_label("critical")

    def test_as_dict_keys(self):
        a = AnnotatedEntry(entry=make_entry(), labels=["x"], note="hello")
        d = a.as_dict()
        assert set(d.keys()) == {"timestamp", "severity", "message", "labels", "note"}

    def test_as_dict_values(self):
        e = make_entry(message="boom", severity="ERROR")
        a = AnnotatedEntry(entry=e, labels=["err"], note="needs fix")
        d = a.as_dict()
        assert d["message"] == "boom"
        assert d["severity"] == "ERROR"
        assert d["labels"] == ["err"]
        assert d["note"] == "needs fix"

    def test_str_contains_message(self):
        a = AnnotatedEntry(entry=make_entry(message="disk full"), labels=["alert"])
        assert "disk full" in str(a)

    def test_str_contains_labels(self):
        a = AnnotatedEntry(entry=make_entry(), labels=["alert", "prod"])
        assert "alert" in str(a)

    def test_str_contains_note(self):
        a = AnnotatedEntry(entry=make_entry(), note="investigate me")
        assert "investigate me" in str(a)


class TestAnnotate:
    def test_returns_annotated_entries(self):
        entries = [make_entry(), make_entry()]
        result = annotate(entries, labels=["batch"])
        assert all(isinstance(a, AnnotatedEntry) for a in result)

    def test_length_matches_input(self):
        entries = [make_entry() for _ in range(5)]
        assert len(annotate(entries)) == 5

    def test_labels_applied_to_all(self):
        entries = [make_entry(), make_entry()]
        result = annotate(entries, labels=["tagged"])
        assert all(a.has_label("tagged") for a in result)

    def test_note_applied_to_all(self):
        entries = [make_entry(), make_entry()]
        result = annotate(entries, note="auto-note")
        assert all(a.note == "auto-note" for a in result)

    def test_empty_input(self):
        assert annotate([]) == []

    def test_labels_are_independent_copies(self):
        entries = [make_entry(), make_entry()]
        result = annotate(entries, labels=["x"])
        result[0].labels.append("y")
        assert "y" not in result[1].labels


class TestFilterByLabel:
    def test_returns_matching_entries(self):
        entries = [
            AnnotatedEntry(entry=make_entry(), labels=["hot"]),
            AnnotatedEntry(entry=make_entry(), labels=["cold"]),
        ]
        result = filter_by_label(entries, "hot")
        assert len(result) == 1
        assert result[0].has_label("hot")

    def test_no_match_returns_empty(self):
        entries = [AnnotatedEntry(entry=make_entry(), labels=["x"])]
        assert filter_by_label(entries, "missing") == []


class TestLabelMap:
    def test_groups_by_label(self):
        a1 = AnnotatedEntry(entry=make_entry(), labels=["alpha", "beta"])
        a2 = AnnotatedEntry(entry=make_entry(), labels=["alpha"])
        result = label_map([a1, a2])
        assert len(result["alpha"]) == 2
        assert len(result["beta"]) == 1

    def test_empty_input(self):
        assert label_map([]) == {}
