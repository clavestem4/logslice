"""Tail support: read the last N entries or follow a log file."""

from __future__ import annotations

import os
import time
from collections import deque
from typing import Callable, Iterator, List, Optional

from logslice.parser import LogEntry, parse_line


def tail_entries(lines: List[str], n: int = 20) -> List[LogEntry]:
    """Return the last *n* parsed log entries from *lines*."""
    if n <= 0:
        return []
    bucket: deque[LogEntry] = deque(maxlen=n)
    for raw in lines:
        entry = parse_line(raw)
        if entry is not None:
            bucket.append(entry)
    return list(bucket)


def tail_file(path: str, n: int = 20) -> List[LogEntry]:
    """Read *path* and return the last *n* parsed log entries."""
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        lines = fh.readlines()
    return tail_entries(lines, n=n)


def follow_file(
    path: str,
    callback: Callable[[LogEntry], None],
    poll_interval: float = 0.25,
    stop_after: Optional[float] = None,
) -> None:
    """Watch *path* for new lines and call *callback* for each parsed entry.

    Blocks until *stop_after* seconds have elapsed (if given) or the caller
    interrupts with KeyboardInterrupt.
    """
    start = time.monotonic()
    with open(path, "r", encoding="utf-8", errors="replace") as fh:
        fh.seek(0, os.SEEK_END)  # start at end
        while True:
            line = fh.readline()
            if line:
                entry = parse_line(line)
                if entry is not None:
                    callback(entry)
            else:
                if stop_after is not None and (time.monotonic() - start) >= stop_after:
                    break
                time.sleep(poll_interval)


def iter_tail(
    path: str,
    n: int = 20,
    follow: bool = False,
    poll_interval: float = 0.25,
) -> Iterator[LogEntry]:
    """Yield the last *n* entries from *path*, then optionally follow."""
    yield from tail_file(path, n=n)
    if follow:
        with open(path, "r", encoding="utf-8", errors="replace") as fh:
            fh.seek(0, os.SEEK_END)
            while True:
                line = fh.readline()
                if line:
                    entry = parse_line(line)
                    if entry is not None:
                        yield entry
                else:
                    time.sleep(poll_interval)
