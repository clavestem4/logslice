"""Schema validation for log entries against expected field patterns."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from logslice.parser import LogEntry


@dataclass
class FieldRule:
    """A single validation rule for a parsed log entry field."""

    name: str
    required: bool = True
    pattern: Optional[str] = None
    allowed_values: Optional[List[str]] = None

    def validate(self, value: Any) -> Optional[str]:
        """Return an error string, or None if the value is valid."""
        if value is None or (isinstance(value, str) and value == ""):
            if self.required:
                return f"field '{self.name}' is required but missing"
            return None

        str_value = str(value)

        if self.pattern and not re.search(self.pattern, str_value):
            return f"field '{self.name}' value {str_value!r} does not match pattern {self.pattern!r}"

        if self.allowed_values is not None:
            normalized = str_value.upper()
            allowed = [v.upper() for v in self.allowed_values]
            if normalized not in allowed:
                return (
                    f"field '{self.name}' value {str_value!r} not in "
                    f"allowed values {self.allowed_values!r}"
                )

        return None


@dataclass
class Schema:
    """Collection of field rules used to validate log entries."""

    rules: List[FieldRule] = field(default_factory=list)

    def add_rule(self, rule: FieldRule) -> "Schema":
        self.rules.append(rule)
        return self

    def validate_entry(self, entry: LogEntry) -> List[str]:
        """Return a list of validation error strings for the entry."""
        errors: List[str] = []
        field_map: Dict[str, Any] = {
            "timestamp": entry.timestamp,
            "severity": entry.severity,
            "message": entry.message,
        }
        for rule in self.rules:
            value = field_map.get(rule.name)
            error = rule.validate(value)
            if error:
                errors.append(error)
        return errors


def validate_entries(entries: List[LogEntry], schema: Schema) -> Dict[int, List[str]]:
    """Validate a list of entries; return a dict mapping index to error list."""
    results: Dict[int, List[str]] = {}
    for idx, entry in enumerate(entries):
        errors = schema.validate_entry(entry)
        if errors:
            results[idx] = errors
    return results


SEVERITY_VALUES = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]


def default_schema() -> Schema:
    """Return a sensible default schema for typical structured log entries."""
    return (
        Schema()
        .add_rule(FieldRule(name="message", required=True))
        .add_rule(
            FieldRule(
                name="severity",
                required=False,
                allowed_values=SEVERITY_VALUES,
            )
        )
    )
