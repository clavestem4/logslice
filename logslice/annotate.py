"""Annotation support for log entries — attach labels or notes to entries."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional

from logslice.parser import LogEntry


@dataclass
class AnnotatedEntry:
    """A log entry paired with a set of string labels and an optional note."""

    entry: LogEntry
    labels: List[str] = field(default_factory=list)
    note: Optional[str] = None

    def has_label(self, label: str) -> bool:
        """Return True if *label* is present (case-insensitive)."""
        return label.lower() in (l.lower() for l in self.labels)

    def as_dict(self) -> dict:
        return {
            "timestamp": self.entry.timestamp.isoformat() if self.entry.timestamp else None,
            "severity": self.entry.severity,
            "message": self.entry.message,
            "labels": self.labels,
            "note": self.note,
        }

    def __str__(self) -> str:
        parts = []
        if self.entry.timestamp:
            parts.append(self.entry.timestamp.isoformat())
        if self.entry.severity:
            parts.append(f"[{self.entry.severity}]")
        parts.append(self.entry.message)
        if self.labels:
            parts.append(f"  labels={self.labels}")
        if self.note:
            parts.append(f"  note={self.note!r}")
        return " ".join(parts)


def annotate(
    entries: List[LogEntry],
    labels: Optional[List[str]] = None,
    note: Optional[str] = None,
) -> List[AnnotatedEntry]:
    """Wrap every entry in an AnnotatedEntry with the given labels and note."""
    return [
        AnnotatedEntry(entry=e, labels=list(labels or []), note=note)
        for e in entries
    ]


def filter_by_label(annotated: List[AnnotatedEntry], label: str) -> List[AnnotatedEntry]:
    """Return only entries that carry *label*."""
    return [a for a in annotated if a.has_label(label)]


def label_map(annotated: List[AnnotatedEntry]) -> Dict[str, List[AnnotatedEntry]]:
    """Build a mapping of label -> list of annotated entries."""
    result: Dict[str, List[AnnotatedEntry]] = {}
    for a in annotated:
        for lbl in a.labels:
            result.setdefault(lbl, []).append(a)
    return result
