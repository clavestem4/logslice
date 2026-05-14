"""Tests for logslice.classify."""

from __future__ import annotations

import pytest
from datetime import datetime

from logslice.parser import LogEntry
from logslice.classify import (
    ClassifyRule,
    classify_entry,
    classify_entries,
    group_by_category,
)


def make_entry(message: str = "hello", severity: str = "INFO") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw=f"2024-01-01T12:00:00 {severity} {message}",
    )


class TestClassifyRuleMatches:
    def test_no_conditions_always_matches(self):
        rule = ClassifyRule(category="any")
        assert rule.matches(make_entry()) is True

    def test_pattern_match(self):
        rule = ClassifyRule(category="db", pattern=r"database")
        assert rule.matches(make_entry("database error")) is True

    def test_pattern_no_match(self):
        rule = ClassifyRule(category="db", pattern=r"database")
        assert rule.matches(make_entry("network timeout")) is False

    def test_pattern_case_insensitive(self):
        rule = ClassifyRule(category="db", pattern=r"DATABASE")
        assert rule.matches(make_entry("database error")) is True

    def test_min_severity_passes(self):
        rule = ClassifyRule(category="critical", min_severity="ERROR")
        assert rule.matches(make_entry(severity="ERROR")) is True
        assert rule.matches(make_entry(severity="CRITICAL")) is True

    def test_min_severity_fails(self):
        rule = ClassifyRule(category="critical", min_severity="ERROR")
        assert rule.matches(make_entry(severity="INFO")) is False

    def test_max_severity_passes(self):
        rule = ClassifyRule(category="low", max_severity="WARNING")
        assert rule.matches(make_entry(severity="DEBUG")) is True
        assert rule.matches(make_entry(severity="WARNING")) is True

    def test_max_severity_fails(self):
        rule = ClassifyRule(category="low", max_severity="WARNING")
        assert rule.matches(make_entry(severity="ERROR")) is False

    def test_combined_pattern_and_severity(self):
        rule = ClassifyRule(category="db_error", pattern=r"db", min_severity="ERROR")
        assert rule.matches(make_entry("db failure", "ERROR")) is True
        assert rule.matches(make_entry("db failure", "INFO")) is False
        assert rule.matches(make_entry("network", "ERROR")) is False


class TestClassifyEntry:
    def test_first_matching_rule_wins(self):
        rules = [
            ClassifyRule(category="first", pattern=r"foo"),
            ClassifyRule(category="second", pattern=r"foo"),
        ]
        assert classify_entry(make_entry("foo bar"), rules) == "first"

    def test_default_when_no_match(self):
        rules = [ClassifyRule(category="x", pattern=r"zzz")]
        assert classify_entry(make_entry("hello"), rules) == "unclassified"

    def test_custom_default(self):
        assert classify_entry(make_entry(), [], default="other") == "other"

    def test_empty_rules_returns_default(self):
        assert classify_entry(make_entry(), []) == "unclassified"


class TestClassifyEntries:
    def test_returns_pairs(self):
        entries = [make_entry("foo"), make_entry("bar")]
        rules = [ClassifyRule(category="foo", pattern=r"foo")]
        result = classify_entries(entries, rules)
        assert result[0][1] == "foo"
        assert result[1][1] == "unclassified"

    def test_empty_entries_returns_empty(self):
        assert classify_entries([], []) == []


class TestGroupByCategory:
    def test_groups_correctly(self):
        entries = [
            make_entry("db error", "ERROR"),
            make_entry("db warning", "WARNING"),
            make_entry("network issue", "ERROR"),
        ]
        rules = [
            ClassifyRule(category="db", pattern=r"db"),
            ClassifyRule(category="network", pattern=r"network"),
        ]
        groups = group_by_category(entries, rules)
        assert len(groups["db"]) == 2
        assert len(groups["network"]) == 1

    def test_unclassified_bucket(self):
        entries = [make_entry("random")]
        groups = group_by_category(entries, [])
        assert "unclassified" in groups
        assert len(groups["unclassified"]) == 1

    def test_empty_entries(self):
        assert group_by_category([], []) == {}
