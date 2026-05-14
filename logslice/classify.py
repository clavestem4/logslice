"""Entry classification — assign category labels to log entries based on rules."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import List, Optional

from logslice.parser import LogEntry
from logslice.filter import severity_rank


@dataclass
class ClassifyRule:
    """A single classification rule."""

    category: str
    pattern: Optional[str] = None
    min_severity: Optional[str] = None
    max_severity: Optional[str] = None
    _compiled: Optional[re.Pattern] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.pattern:
            self._compiled = re.compile(self.pattern, re.IGNORECASE)

    def matches(self, entry: LogEntry) -> bool:
        """Return True when *entry* satisfies all conditions on this rule."""
        if self._compiled and not self._compiled.search(entry.message):
            return False
        rank = severity_rank(entry.severity)
        if self.min_severity and rank < severity_rank(self.min_severity):
            return False
        if self.max_severity and rank > severity_rank(self.max_severity):
            return False
        return True


def classify_entry(
    entry: LogEntry,
    rules: List[ClassifyRule],
    default: str = "unclassified",
) -> str:
    """Return the category of the first matching rule, or *default*."""
    for rule in rules:
        if rule.matches(entry):
            return rule.category
    return default


def classify_entries(
    entries: List[LogEntry],
    rules: List[ClassifyRule],
    default: str = "unclassified",
) -> List[tuple]:
    """Return a list of (entry, category) pairs."""
    return [(e, classify_entry(e, rules, default)) for e in entries]


def group_by_category(
    entries: List[LogEntry],
    rules: List[ClassifyRule],
    default: str = "unclassified",
) -> dict:
    """Return a dict mapping category -> list[LogEntry]."""
    groups: dict = {}
    for entry, cat in classify_entries(entries, rules, default):
        groups.setdefault(cat, []).append(entry)
    return groups
