"""Summary statistics for a collection of log entries."""

from collections import Counter
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, List, Optional

from logslice.parser import LogEntry


@dataclass
class LogSummary:
    """Aggregated statistics over a list of log entries."""
    total: int = 0
    by_severity: Dict[str, int] = field(default_factory=dict)
    earliest: Optional[datetime] = None
    latest: Optional[datetime] = None
    unparsed: int = 0

    def as_dict(self) -> dict:
        return {
            "total": self.total,
            "by_severity": self.by_severity,
            "earliest": self.earliest.isoformat() if self.earliest else None,
            "latest": self.latest.isoformat() if self.latest else None,
            "unparsed": self.unparsed,
        }

    def __str__(self) -> str:
        lines = [
            f"Total entries : {self.total}",
            f"Unparsed      : {self.unparsed}",
            f"Earliest      : {self.earliest.isoformat() if self.earliest else 'N/A'}",
            f"Latest        : {self.latest.isoformat() if self.latest else 'N/A'}",
            "By severity   :",
        ]
        for sev, count in sorted(self.by_severity.items()):
            lines.append(f"  {sev:<12}: {count}")
        return "\n".join(lines)


def summarize(entries: List[LogEntry]) -> LogSummary:
    """Compute a summary over a list of LogEntry objects.

    Args:
        entries: Parsed log entries.

    Returns:
        A LogSummary with counts, severity breakdown, and time range.
    """
    summary = LogSummary(total=len(entries))
    severity_counter: Counter = Counter()
    timestamps = []

    for entry in entries:
        if entry.severity:
            severity_counter[entry.severity.upper()] += 1
        else:
            summary.unparsed += 1

        if entry.timestamp is not None:
            timestamps.append(entry.timestamp)

    summary.by_severity = dict(severity_counter)

    if timestamps:
        summary.earliest = min(timestamps)
        summary.latest = max(timestamps)

    return summary
