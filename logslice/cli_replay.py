"""CLI helpers for the *replay* sub-command."""

from __future__ import annotations

import argparse
import sys
from typing import List

from logslice.formatter import format_entry_text
from logslice.replay import ReplayOptions, replay_entries
from logslice.slice import slice_file


def add_replay_arguments(parser: argparse.ArgumentParser) -> None:
    """Register replay-specific arguments on *parser*."""
    parser.add_argument("file", help="Log file to replay")
    parser.add_argument(
        "--speed",
        type=float,
        default=1.0,
        metavar="X",
        help="Replay speed multiplier (default: 1.0)",
    )
    parser.add_argument(
        "--max-delay",
        type=float,
        default=5.0,
        metavar="SEC",
        dest="max_delay",
        help="Maximum inter-entry delay in seconds (default: 5)",
    )
    parser.add_argument(
        "--no-real-time",
        action="store_true",
        dest="no_real_time",
        help="Emit entries immediately without timing delays",
    )
    parser.add_argument(
        "--severity",
        default=None,
        metavar="LEVEL",
        help="Minimum severity level to include",
    )


def run_replay(args: argparse.Namespace, out=sys.stdout) -> int:
    """Execute the replay command and return the number of entries emitted.

    Args:
        args: Parsed CLI arguments (see :func:`add_replay_arguments`).
        out:  Output stream (defaults to *stdout*).

    Returns:
        Total number of log entries emitted.

    Raises:
        SystemExit: If *args.speed* or *args.max_delay* contain invalid values.
    """
    if args.speed <= 0:
        print(
            f"error: --speed must be a positive number, got {args.speed}",
            file=sys.stderr,
        )
        sys.exit(1)

    if args.max_delay < 0:
        print(
            f"error: --max-delay must be non-negative, got {args.max_delay}",
            file=sys.stderr,
        )
        sys.exit(1)

    entries = slice_file(
        args.file,
        min_severity=args.severity,
    )

    options = ReplayOptions(
        speed=args.speed,
        max_delay=args.max_delay,
        real_time=not args.no_real_time,
    )

    count = 0
    for entry in replay_entries(entries, options):
        out.write(format_entry_text(entry) + "\n")
        count += 1

    return count
