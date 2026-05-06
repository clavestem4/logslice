"""Compute per-time-bucket statistics from log entries."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from logslice.parser import LogEntry


@dataclass
class BucketStats:
    """Statistics for a single time bucket."""

    bucket_start: datetime
    total: int = 0
    severity_counts: Dict[str, int] = field(default_factory=dict)

    def as_dict(self) -> dict:
        return {
            "bucket_start": self.bucket_start.isoformat(),
            "total": self.total,
            "severity_counts": dict(self.severity_counts),
        }

    def __str__(self) -> str:
        counts = ", ".join(
            f"{sev}={cnt}" for sev, cnt in sorted(self.severity_counts.items())
        )
        return f"[{self.bucket_start.isoformat()}] total={self.total} ({counts})"


def bucket_key(ts: datetime, interval: timedelta) -> datetime:
    """Round a timestamp down to the nearest bucket boundary."""
    epoch = datetime(1970, 1, 1, tzinfo=ts.tzinfo)
    seconds = int((ts - epoch).total_seconds())
    bucket_seconds = int(interval.total_seconds())
    floored = (seconds // bucket_seconds) * bucket_seconds
    return epoch + timedelta(seconds=floored)


def compute_stats(
    entries: List[LogEntry],
    interval: timedelta = timedelta(minutes=1),
) -> List[BucketStats]:
    """Group entries into time buckets and compute per-bucket statistics.

    Args:
        entries: Parsed log entries (may have None timestamps; those are skipped).
        interval: Bucket width.  Defaults to 1 minute.

    Returns:
        Sorted list of :class:`BucketStats`, one per non-empty bucket.
    """
    buckets: Dict[datetime, BucketStats] = {}

    for entry in entries:
        if entry.timestamp is None:
            continue
        key = bucket_key(entry.timestamp, interval)
        if key not in buckets:
            buckets[key] = BucketStats(bucket_start=key)
        stats = buckets[key]
        stats.total += 1
        sev = (entry.severity or "UNKNOWN").upper()
        stats.severity_counts[sev] = stats.severity_counts.get(sev, 0) + 1

    return [buckets[k] for k in sorted(buckets)]
