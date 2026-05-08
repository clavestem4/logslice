"""CLI helpers for running a named pipeline of built-in steps."""

from __future__ import annotations

import argparse
from typing import List

from logslice.filter import filter_by_severity, filter_by_time
from logslice.parser import LogEntry
from logslice.pipeline import Pipeline
from logslice.slice import slice_file
from logslice.formatter import render
from logslice.cli import parse_dt


def add_pipeline_arguments(parser: argparse.ArgumentParser) -> None:
    """Register pipeline-related CLI arguments onto *parser*."""
    parser.add_argument("file", help="Log file to process")
    parser.add_argument("--min-severity", default=None, metavar="LEVEL",
                        help="Minimum severity level to include")
    parser.add_argument("--start", default=None, metavar="DATETIME",
                        help="Earliest timestamp to include")
    parser.add_argument("--end", default=None, metavar="DATETIME",
                        help="Latest timestamp to include")
    parser.add_argument("--format", dest="fmt", default="text",
                        choices=["text", "json", "csv"],
                        help="Output format (default: text)")
    parser.add_argument("--step", dest="steps", action="append", default=[],
                        metavar="STEP",
                        help="Named built-in step to add (dedup, errors-only)")


def _resolve_named_step(name: str):
    """Return a step function for a recognised built-in step name."""
    from logslice.dedupe import deduplicate

    _builtins = {
        "dedup": lambda entries: deduplicate(entries),
        "errors-only": lambda entries: [e for e in entries if e.severity in ("ERROR", "CRITICAL", "FATAL")],
    }
    if name not in _builtins:
        raise ValueError(f"Unknown pipeline step: {name!r}. Available: {list(_builtins)!r}")
    return _builtins[name]


def run_pipeline_cli(args: argparse.Namespace, out=None) -> int:
    """Execute the pipeline and write output.  Returns number of entries emitted."""
    import sys
    out = out or sys.stdout

    entries: List[LogEntry] = slice_file(args.file)

    p = Pipeline(name="cli")

    if args.start or args.end:
        start = parse_dt(args.start) if args.start else None
        end = parse_dt(args.end) if args.end else None
        p.add_step(lambda e, s=start, en=end: filter_by_time(e, start=s, end=en))

    if args.min_severity:
        p.add_step(lambda e, ms=args.min_severity: filter_by_severity(e, min_level=ms))

    for step_name in args.steps:
        p.add_step(_resolve_named_step(step_name))

    result = p.run(entries)
    text = render(result, fmt=args.fmt)
    out.write(text)
    if text and not text.endswith("\n"):
        out.write("\n")
    return len(result)
