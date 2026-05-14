"""CLI helpers for the classify feature."""

from __future__ import annotations

import argparse
import json
from typing import List

from logslice.slice import slice_file
from logslice.classify import ClassifyRule, group_by_category
from logslice.formatter import format_entry_text


def add_classify_arguments(parser: argparse.ArgumentParser) -> None:
    """Attach classify-specific arguments to *parser*."""
    parser.add_argument(
        "file",
        help="Log file to classify",
    )
    parser.add_argument(
        "--rule",
        dest="rules",
        metavar="CATEGORY:PATTERN",
        action="append",
        default=[],
        help="Add a rule as CATEGORY:REGEX (may repeat)",
    )
    parser.add_argument(
        "--min-severity",
        default=None,
        help="Global minimum severity filter before classification",
    )
    parser.add_argument(
        "--summary",
        action="store_true",
        help="Print category counts instead of entries",
    )
    parser.add_argument(
        "--json",
        dest="as_json",
        action="store_true",
        help="Output summary as JSON",
    )


def _parse_rules(raw: List[str]) -> List[ClassifyRule]:
    rules = []
    for token in raw:
        if ":" not in token:
            raise ValueError(f"Rule must be CATEGORY:PATTERN, got: {token!r}")
        category, _, pattern = token.partition(":")
        rules.append(ClassifyRule(category=category.strip(), pattern=pattern.strip()))
    return rules


def run_classify(args: argparse.Namespace, out=None) -> int:
    """Execute classify logic; return number of entries processed."""
    import sys

    if out is None:
        out = sys.stdout

    entries = slice_file(args.file, min_severity=args.min_severity)
    rules = _parse_rules(args.rules)
    groups = group_by_category(entries, rules)

    if args.summary or args.as_json:
        counts = {cat: len(ents) for cat, ents in sorted(groups.items())}
        if args.as_json:
            out.write(json.dumps(counts) + "\n")
        else:
            for cat, count in counts.items():
                out.write(f"{cat}: {count}\n")
    else:
        for cat, ents in sorted(groups.items()):
            for entry in ents:
                line = format_entry_text(entry)
                out.write(f"[{cat}] {line}\n")

    return len(entries)
