"""CLI support for grep (pattern search) subcommand."""

import sys
from typing import List
from logslice.parser import LogEntry
from logslice.grep import grep_entries
from logslice.formatter import render


def add_grep_arguments(parser) -> None:
    """Register grep-related CLI arguments on an argparse (sub)parser."""
    parser.add_argument(
        "pattern",
        help="Regular expression pattern to search for in log messages.",
    )
    parser.add_argument(
        "-i", "--ignore-case",
        action="store_true",
        default=False,
        help="Perform case-insensitive matching.",
    )
    parser.add_argument(
        "-v", "--invert",
        action="store_true",
        default=False,
        help="Invert match: show entries that do NOT match the pattern.",
    )
    parser.add_argument(
        "-c", "--count",
        action="store_true",
        default=False,
        help="Print only the count of matching entries.",
    )
    parser.add_argument(
        "--format",
        choices=["text", "json", "csv"],
        default="text",
        help="Output format (default: text).",
    )


def run_grep(
    entries: List[LogEntry],
    pattern: str,
    ignore_case: bool = False,
    invert: bool = False,
    count_only: bool = False,
    fmt: str = "text",
    out=None,
) -> int:
    """Execute grep filtering and write output.

    Returns the number of matching entries.
    """
    if out is None:
        out = sys.stdout

    matched = grep_entries(entries, pattern, ignore_case=ignore_case, invert=invert)

    if count_only:
        out.write(f"{len(matched)}\n")
    else:
        output = render(matched, fmt=fmt)
        if output:
            out.write(output)
            if not output.endswith("\n"):
                out.write("\n")

    return len(matched)
