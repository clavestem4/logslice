"""Sampling utilities for large log streams."""

from __future__ import annotations

import random
from typing import List, Optional

from logslice.parser import LogEntry


def sample_entries(
    entries: List[LogEntry],
    n: int,
    seed: Optional[int] = None,
) -> List[LogEntry]:
    """Return up to *n* entries chosen at random without replacement.

    The relative order of the chosen entries is preserved.

    Args:
        entries: Source list of log entries.
        n: Maximum number of entries to return.
        seed: Optional random seed for reproducibility.

    Returns:
        A sorted-by-position subset of *entries*.
    """
    if n <= 0:
        return []
    if n >= len(entries):
        return list(entries)

    rng = random.Random(seed)
    indices = sorted(rng.sample(range(len(entries)), n))
    return [entries[i] for i in indices]


def sample_rate(
    entries: List[LogEntry],
    rate: float,
    seed: Optional[int] = None,
) -> List[LogEntry]:
    """Return entries kept with probability *rate* (0.0 – 1.0).

    Args:
        entries: Source list of log entries.
        rate: Fraction of entries to keep, e.g. 0.1 keeps ~10 %.
        seed: Optional random seed for reproducibility.

    Returns:
        A filtered subset of *entries* in original order.
    """
    if rate <= 0.0:
        return []
    if rate >= 1.0:
        return list(entries)

    rng = random.Random(seed)
    return [e for e in entries if rng.random() < rate]


def every_nth(entries: List[LogEntry], n: int) -> List[LogEntry]:
    """Return every *n*-th entry (deterministic, no randomness).

    Args:
        entries: Source list of log entries.
        n: Step size; must be >= 1.

    Returns:
        Entries at indices 0, n, 2n, …
    """
    if n < 1:
        raise ValueError(f"n must be >= 1, got {n}")
    return entries[::n]
