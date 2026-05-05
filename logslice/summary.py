"""Summarize a collection of log entries."""
from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from logslice.parser import LogEntry


@dataclass
class LogSummary:
    total: int = 0
    by_severity: Dict[str, int] = field(default_factory=dict)
    first_timestamp: Optional[datetime] = None
    last_timestamp: Optional[datetime] = None
    unparsed_lines: int = 0

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "by_severity": self.by_severity,
            "first_timestamp": self.first_timestamp.isoformat() if self.first_timestamp else None,
            "last_timestamp": self.last_timestamp.isoformat() if self.last_timestamp else None,
            "unparsed_lines": self.unparsed_lines,
        }

    def __str__(self) -> str:
        lines = [
            f"Total entries : {self.total}",
            f"Unparsed lines: {self.unparsed_lines}",
        ]
        if self.first_timestamp:
            lines.append(f"From          : {self.first_timestamp.isoformat()}")
        if self.last_timestamp:
            lines.append(f"To            : {self.last_timestamp.isoformat()}")
        if self.by_severity:
            lines.append("Severity breakdown:")
            for sev, count in sorted(self.by_severity.items()):
                lines.append(f"  {sev:<10} {count}")
        return "\n".join(lines)


def summarize(entries: List[LogEntry], unparsed_lines: int = 0) -> LogSummary:
    """Build a LogSummary from a list of LogEntry objects."""
    counter: Counter = Counter()
    first_ts: Optional[datetime] = None
    last_ts: Optional[datetime] = None

    for entry in entries:
        sev = (entry.severity or "UNKNOWN").upper()
        counter[sev] += 1
        if entry.timestamp is not None:
            if first_ts is None or entry.timestamp < first_ts:
                first_ts = entry.timestamp
            if last_ts is None or entry.timestamp > last_ts:
                last_ts = entry.timestamp

    return LogSummary(
        total=len(entries),
        by_severity=dict(counter),
        first_timestamp=first_ts,
        last_timestamp=last_ts,
        unparsed_lines=unparsed_lines,
    )
