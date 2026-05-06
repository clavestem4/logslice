"""CLI helpers for --tail / --follow integration."""

from __future__ import annotations

import sys
from typing import List, Optional

from logslice.formatter import render
from logslice.parser import LogEntry
from logslice.tail import follow_file, iter_tail, tail_file


def run_tail(
    path: str,
    n: int = 20,
    follow: bool = False,
    fmt: str = "text",
    color: bool = False,
) -> int:
    """Print the last *n* entries from *path*, optionally following.

    Returns the number of entries printed.
    """
    if not follow:
        entries = tail_file(path, n=n)
        output = render(entries, fmt=fmt, color=color)
        if output:
            sys.stdout.write(output)
            if not output.endswith("\n"):
                sys.stdout.write("\n")
        return len(entries)

    # follow mode — stream directly
    count = 0
    try:
        for entry in iter_tail(path, n=n, follow=True):
            line = render([entry], fmt=fmt, color=color)
            sys.stdout.write(line)
            sys.stdout.flush()
            count += 1
    except KeyboardInterrupt:
        pass
    return count


def add_tail_arguments(parser) -> None:  # type: ignore[type-arg]
    """Attach --tail and --follow arguments to an argparse parser."""
    parser.add_argument(
        "--tail",
        metavar="N",
        type=int,
        default=None,
        help="Show the last N log entries (default: 20 when flag is used).",
    )
    parser.add_argument(
        "--follow",
        "-f",
        action="store_true",
        default=False,
        help="After printing tail entries, watch for new lines.",
    )
