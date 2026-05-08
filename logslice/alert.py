"""Alert module: trigger callbacks when log entries match severity or pattern thresholds."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Callable, List, Optional

from logslice.parser import LogEntry
from logslice.filter import severity_rank


@dataclass
class AlertRule:
    """A single alert rule with an optional pattern and minimum severity."""

    name: str
    callback: Callable[[LogEntry, "AlertRule"], None]
    min_severity: Optional[str] = None
    pattern: Optional[str] = None
    _compiled: Optional[re.Pattern] = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.pattern:
            self._compiled = re.compile(self.pattern, re.IGNORECASE)

    def matches(self, entry: LogEntry) -> bool:
        """Return True if the entry satisfies this rule's conditions."""
        if self.min_severity is not None:
            if severity_rank(entry.severity) < severity_rank(self.min_severity):
                return False
        if self._compiled is not None:
            text = entry.message or ""
            if not self._compiled.search(text):
                return False
        return True


def evaluate_rules(entry: LogEntry, rules: List[AlertRule]) -> List[AlertRule]:
    """Return all rules that match the given entry."""
    return [rule for rule in rules if rule.matches(entry)]


def dispatch(entry: LogEntry, rules: List[AlertRule]) -> int:
    """Fire callbacks for every matching rule. Returns number of alerts fired."""
    fired = 0
    for rule in evaluate_rules(entry, rules):
        rule.callback(entry, rule)
        fired += 1
    return fired


def process_entries(entries: List[LogEntry], rules: List[AlertRule]) -> int:
    """Evaluate all entries against all rules. Returns total alerts fired."""
    total = 0
    for entry in entries:
        total += dispatch(entry, rules)
    return total
