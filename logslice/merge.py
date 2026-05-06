"""Merge and sort log entries from multiple sources by timestamp."""

from __future__ import annotations

import heapq
from typing import Iterable, Iterator, List, Optional

from logslice.parser import LogEntry


def merge_sorted(
    *streams: Iterable[LogEntry],
    reverse: bool = False,
) -> List[LogEntry]:
    """Merge multiple iterables of LogEntry into a single sorted list.

    Entries without a timestamp are appended at the end in the order
    they are encountered.

    Args:
        *streams: One or more iterables of LogEntry objects.
        reverse: If True, sort in descending (newest-first) order.

    Returns:
        A new list of LogEntry objects sorted by timestamp.
    """
    timestamped: List[LogEntry] = []
    no_timestamp: List[LogEntry] = []

    for stream in streams:
        for entry in stream:
            if entry.timestamp is not None:
                timestamped.append(entry)
            else:
                no_timestamp.append(entry)

    timestamped.sort(key=lambda e: e.timestamp, reverse=reverse)  # type: ignore[arg-type]

    return timestamped + no_timestamp


def merge_iter(
    *streams: Iterable[LogEntry],
) -> Iterator[LogEntry]:
    """Lazily merge pre-sorted streams of LogEntry using a min-heap.

    Each input stream must already be sorted in ascending timestamp order.
    Entries without a timestamp are yielded after all timestamped entries.

    Args:
        *streams: Pre-sorted iterables of LogEntry.

    Yields:
        LogEntry objects in merged ascending timestamp order.
    """
    iters = [iter(s) for s in streams]
    heap: list = []
    overflow: List[LogEntry] = []

    def _push(it_index: int, it: Iterator[LogEntry]) -> None:
        try:
            entry = next(it)
            if entry.timestamp is not None:
                heapq.heappush(heap, (entry.timestamp, it_index, entry, it))
            else:
                overflow.append(entry)
                _push(it_index, it)
        except StopIteration:
            pass

    for idx, it in enumerate(iters):
        _push(idx, it)

    while heap:
        ts, idx, entry, it = heapq.heappop(heap)
        yield entry
        _push(idx, it)

    yield from overflow


def merge_files(
    paths: Iterable[str],
    encoding: str = "utf-8",
    reverse: bool = False,
) -> List[LogEntry]:
    """Parse and merge log entries from multiple file paths.

    Args:
        paths: File paths to read.
        encoding: File encoding.
        reverse: If True, return entries in descending order.

    Returns:
        Merged, sorted list of LogEntry objects.
    """
    from logslice.slice import slice_file

    all_streams = [slice_file(p, encoding=encoding) for p in paths]
    return merge_sorted(*all_streams, reverse=reverse)
