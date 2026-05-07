"""CLI sub-commands for managing logslice checkpoints."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from logslice.checkpoint import clear_checkpoint, load_checkpoint


def add_checkpoint_arguments(parser: argparse.ArgumentParser) -> None:
    """Register checkpoint sub-commands on *parser*."""
    sub = parser.add_subparsers(dest="cp_command", metavar="COMMAND")

    show_p = sub.add_parser("show", help="Display the checkpoint for a log file")
    show_p.add_argument("file", help="Path to the log file")
    show_p.add_argument(
        "--dir", default=".logslice", metavar="DIR", help="Checkpoint directory"
    )

    clear_p = sub.add_parser("clear", help="Delete the checkpoint for a log file")
    clear_p.add_argument("file", help="Path to the log file")
    clear_p.add_argument(
        "--dir", default=".logslice", metavar="DIR", help="Checkpoint directory"
    )

    list_p = sub.add_parser("list", help="List all saved checkpoints")
    list_p.add_argument(
        "--dir", default=".logslice", metavar="DIR", help="Checkpoint directory"
    )


def run_checkpoint(args: argparse.Namespace, out=sys.stdout, err=sys.stderr) -> int:
    """Execute the requested checkpoint sub-command. Returns an exit code."""
    command = getattr(args, "cp_command", None)

    if command == "show":
        cp = load_checkpoint(args.file, checkpoint_dir=args.dir)
        if cp is None:
            print(f"No checkpoint found for: {args.file}", file=err)
            return 1
        d = cp.as_dict()
        for key, value in d.items():
            print(f"{key}: {value}", file=out)
        return 0

    if command == "clear":
        removed = clear_checkpoint(args.file, checkpoint_dir=args.dir)
        if removed:
            print(f"Checkpoint cleared for: {args.file}", file=out)
            return 0
        print(f"No checkpoint found for: {args.file}", file=err)
        return 1

    if command == "list":
        dirpath = Path(args.dir)
        if not dirpath.exists():
            print("No checkpoints directory found.", file=err)
            return 1
        files = sorted(dirpath.glob("*.checkpoint.json"))
        if not files:
            print("No checkpoints saved.", file=out)
            return 0
        for f in files:
            print(f.name, file=out)
        return 0

    print("No sub-command given. Use show, clear, or list.", file=err)
    return 2
