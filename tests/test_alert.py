"""Tests for logslice.alert."""

from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogEntry
from logslice.alert import AlertRule, evaluate_rules, dispatch, process_entries


def make_entry(severity: str = "INFO", message: str = "hello") -> LogEntry:
    return LogEntry(
        timestamp=datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw=f"{severity} {message}",
    )


class TestAlertRuleMatches:
    def test_no_conditions_always_matches(self):
        fired = []
        rule = AlertRule(name="any", callback=lambda e, r: fired.append(e))
        assert rule.matches(make_entry()) is True

    def test_min_severity_passes(self):
        rule = AlertRule(name="r", callback=lambda e, r: None, min_severity="WARN")
        assert rule.matches(make_entry("ERROR")) is True

    def test_min_severity_fails(self):
        rule = AlertRule(name="r", callback=lambda e, r: None, min_severity="ERROR")
        assert rule.matches(make_entry("INFO")) is False

    def test_pattern_matches(self):
        rule = AlertRule(name="r", callback=lambda e, r: None, pattern=r"disk")
        assert rule.matches(make_entry(message="disk full")) is True

    def test_pattern_no_match(self):
        rule = AlertRule(name="r", callback=lambda e, r: None, pattern=r"disk")
        assert rule.matches(make_entry(message="memory ok")) is False

    def test_pattern_case_insensitive(self):
        rule = AlertRule(name="r", callback=lambda e, r: None, pattern=r"DISK")
        assert rule.matches(make_entry(message="disk full")) is True

    def test_combined_severity_and_pattern_both_required(self):
        rule = AlertRule(
            name="r",
            callback=lambda e, r: None,
            min_severity="WARN",
            pattern=r"timeout",
        )
        assert rule.matches(make_entry("ERROR", "connection timeout")) is True
        assert rule.matches(make_entry("INFO", "connection timeout")) is False
        assert rule.matches(make_entry("ERROR", "all good")) is False


class TestEvaluateRules:
    def test_returns_matching_rules(self):
        r1 = AlertRule(name="a", callback=lambda e, r: None, min_severity="ERROR")
        r2 = AlertRule(name="b", callback=lambda e, r: None, min_severity="DEBUG")
        matched = evaluate_rules(make_entry("WARN"), [r1, r2])
        assert len(matched) == 1
        assert matched[0].name == "b"

    def test_empty_rules_returns_empty(self):
        assert evaluate_rules(make_entry(), []) == []


class TestDispatch:
    def test_fires_callback_for_match(self):
        fired: List[LogEntry] = []
        rule = AlertRule(name="r", callback=lambda e, r: fired.append(e))
        count = dispatch(make_entry(), [rule])
        assert count == 1
        assert len(fired) == 1

    def test_no_match_no_callback(self):
        fired: List[LogEntry] = []
        rule = AlertRule(
            name="r",
            callback=lambda e, r: fired.append(e),
            min_severity="CRITICAL",
        )
        count = dispatch(make_entry("DEBUG"), [rule])
        assert count == 0
        assert fired == []

    def test_returns_number_of_alerts_fired(self):
        rules = [
            AlertRule(name="a", callback=lambda e, r: None),
            AlertRule(name="b", callback=lambda e, r: None),
        ]
        assert dispatch(make_entry(), rules) == 2


class TestProcessEntries:
    def test_processes_all_entries(self):
        fired = []
        rule = AlertRule(name="r", callback=lambda e, r: fired.append(e))
        entries = [make_entry() for _ in range(4)]
        total = process_entries(entries, [rule])
        assert total == 4
        assert len(fired) == 4

    def test_empty_entries_returns_zero(self):
        rule = AlertRule(name="r", callback=lambda e, r: None)
        assert process_entries([], [rule]) == 0

    def test_empty_rules_returns_zero(self):
        entries = [make_entry() for _ in range(3)]
        assert process_entries(entries, []) == 0
