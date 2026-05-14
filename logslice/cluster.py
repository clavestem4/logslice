"""Cluster similar log entries by message pattern."""

from __future__ import annotations

import re
from collections import defaultdict
from dataclasses import dataclass, field
from typing import Dict, List, Optional

from logslice.parser import LogEntry

# Tokens that are replaced when normalising a message for clustering.
_VARIABLE_RE = re.compile(
    r"(?:"
    r"\b(?:0x[0-9a-fA-F]+|\d+\.\d+\.\d+\.\d+|\d{4}-\d{2}-\d{2}[T ]\d{2}:\d{2}:\d{2}[^\s]*|\d+)\b"
    r"|[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}"
    r")"
)


def message_signature(message: str) -> str:
    """Return a normalised signature for *message* by replacing variable tokens."""
    sig = _VARIABLE_RE.sub("<VAR>", message)
    # Collapse repeated whitespace so minor spacing differences don't split clusters.
    return re.sub(r"\s+", " ", sig).strip()


@dataclass
class Cluster:
    """A group of log entries that share the same message signature."""

    signature: str
    entries: List[LogEntry] = field(default_factory=list)

    @property
    def count(self) -> int:
        return len(self.entries)

    @property
    def severities(self) -> Dict[str, int]:
        counts: Dict[str, int] = defaultdict(int)
        for e in self.entries:
            counts[e.severity or "UNKNOWN"] += 1
        return dict(counts)

    def as_dict(self) -> dict:
        return {
            "signature": self.signature,
            "count": self.count,
            "severities": self.severities,
        }

    def __str__(self) -> str:  # pragma: no cover
        return f"[Cluster count={self.count}] {self.signature}"


def cluster_entries(
    entries: List[LogEntry],
    min_count: int = 1,
    top_n: Optional[int] = None,
) -> List[Cluster]:
    """Group *entries* into clusters by message signature.

    Args:
        entries:   Entries to cluster.
        min_count: Discard clusters with fewer than this many members.
        top_n:     If given, return only the *top_n* largest clusters.

    Returns:
        List of :class:`Cluster` objects sorted by count descending.
    """
    buckets: Dict[str, Cluster] = {}
    for entry in entries:
        sig = message_signature(entry.message or "")
        if sig not in buckets:
            buckets[sig] = Cluster(signature=sig)
        buckets[sig].entries.append(entry)

    result = [
        c for c in buckets.values() if c.count >= min_count
    ]
    result.sort(key=lambda c: c.count, reverse=True)

    if top_n is not None and top_n > 0:
        return result[:top_n]
    return result
