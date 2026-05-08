"""Tests for logslice.schema."""

from datetime import datetime
from typing import Optional

import pytest

from logslice.parser import LogEntry
from logslice.schema import (
    FieldRule,
    Schema,
    default_schema,
    validate_entries,
    SEVERITY_VALUES,
)


def make_entry(
    message: str = "hello",
    severity: str = "INFO",
    timestamp: Optional[datetime] = None,
    raw: str = "",
) -> LogEntry:
    return LogEntry(
        timestamp=timestamp or datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw=raw or f"INFO {message}",
    )


class TestFieldRule:
    def test_required_missing_returns_error(self):
        rule = FieldRule(name="message", required=True)
        assert rule.validate(None) is not None

    def test_required_empty_string_returns_error(self):
        rule = FieldRule(name="message", required=True)
        assert rule.validate("") is not None

    def test_not_required_missing_returns_none(self):
        rule = FieldRule(name="message", required=False)
        assert rule.validate(None) is None

    def test_pattern_match_returns_none(self):
        rule = FieldRule(name="message", pattern=r"\d+")
        assert rule.validate("error code 42") is None

    def test_pattern_no_match_returns_error(self):
        rule = FieldRule(name="message", pattern=r"^\d+$")
        assert rule.validate("no digits here") is not None

    def test_allowed_values_valid(self):
        rule = FieldRule(name="severity", allowed_values=["INFO", "ERROR"])
        assert rule.validate("INFO") is None

    def test_allowed_values_case_insensitive(self):
        rule = FieldRule(name="severity", allowed_values=["INFO", "ERROR"])
        assert rule.validate("info") is None

    def test_allowed_values_invalid_returns_error(self):
        rule = FieldRule(name="severity", allowed_values=["INFO", "ERROR"])
        error = rule.validate("VERBOSE")
        assert error is not None
        assert "VERBOSE" in error

    def test_error_contains_field_name(self):
        rule = FieldRule(name="message", required=True)
        error = rule.validate(None)
        assert "message" in error


class TestSchema:
    def test_add_rule_returns_self(self):
        schema = Schema()
        result = schema.add_rule(FieldRule(name="message"))
        assert result is schema

    def test_add_rule_increases_count(self):
        schema = Schema()
        schema.add_rule(FieldRule(name="message"))
        assert len(schema.rules) == 1

    def test_validate_entry_no_errors_on_valid(self):
        schema = default_schema()
        entry = make_entry(message="ok", severity="INFO")
        assert schema.validate_entry(entry) == []

    def test_validate_entry_error_on_bad_severity(self):
        schema = default_schema()
        entry = make_entry(severity="VERBOSE")
        errors = schema.validate_entry(entry)
        assert any("severity" in e for e in errors)

    def test_validate_entry_error_on_empty_message(self):
        schema = Schema().add_rule(FieldRule(name="message", required=True))
        entry = make_entry(message="")
        errors = schema.validate_entry(entry)
        assert any("message" in e for e in errors)

    def test_multiple_rules_multiple_errors(self):
        schema = (
            Schema()
            .add_rule(FieldRule(name="message", required=True))
            .add_rule(FieldRule(name="severity", allowed_values=["INFO"]))
        )
        entry = make_entry(message="", severity="ERROR")
        errors = schema.validate_entry(entry)
        assert len(errors) == 2


class TestValidateEntries:
    def test_empty_list_returns_empty_dict(self):
        schema = default_schema()
        assert validate_entries([], schema) == {}

    def test_all_valid_returns_empty_dict(self):
        schema = default_schema()
        entries = [make_entry() for _ in range(5)]
        assert validate_entries(entries, schema) == {}

    def test_invalid_entry_keyed_by_index(self):
        schema = default_schema()
        entries = [make_entry(), make_entry(severity="BAD"), make_entry()]
        result = validate_entries(entries, schema)
        assert 1 in result
        assert 0 not in result
        assert 2 not in result

    def test_multiple_invalid_entries(self):
        schema = default_schema()
        entries = [make_entry(severity="BAD"), make_entry(), make_entry(severity="NOPE")]
        result = validate_entries(entries, schema)
        assert set(result.keys()) == {0, 2}


class TestDefaultSchema:
    def test_severity_values_non_empty(self):
        assert len(SEVERITY_VALUES) > 0

    def test_default_schema_has_rules(self):
        schema = default_schema()
        assert len(schema.rules) >= 1

    def test_default_schema_accepts_known_severities(self):
        schema = default_schema()
        for sev in SEVERITY_VALUES:
            entry = make_entry(severity=sev)
            assert schema.validate_entry(entry) == [], f"failed for severity {sev}"
