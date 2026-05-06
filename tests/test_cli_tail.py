"""Tests for logslice.cli_tail."""

from __future__ import annotations

import argparse
import sys
from io import StringIO

import pytest

from logslice.cli_tail import add_tail_arguments, run_tail

RAW_LOG = "\n".join(
    [
        "2024-03-01T10:00:01Z INFO  starting up",
        "2024-03-01T10:00:02Z DEBUG loading config",
        "2024-03-01T10:00:03Z WARN  disk usage high",
        "2024-03-01T10:00:04Z ERROR connection refused",
        "2024-03-01T10:00:05Z INFO  retry ok",
    ]
)


@pytest.fixture()
def log_file(tmp_path):
    p = tmp_path / "app.log"
    p.write_text(RAW_LOG)
    return str(p)


class TestRunTail:
    def test_returns_entry_count(self, log_file, capsys):
        count = run_tail(log_file, n=3)
        assert count == 3

    def test_output_contains_messages(self, log_file, capsys):
        run_tail(log_file, n=2)
        out = capsys.readouterr().out
        assert "retry ok" in out
        assert "connection refused" in out

    def test_n_larger_than_file(self, log_file, capsys):
        count = run_tail(log_file, n=100)
        assert count == 5

    def test_n_zero_no_output(self, log_file, capsys):
        count = run_tail(log_file, n=0)
        assert count == 0
        out = capsys.readouterr().out
        assert out.strip() == ""

    def test_json_format(self, log_file, capsys):
        run_tail(log_file, n=1, fmt="json")
        out = capsys.readouterr().out
        assert "retry ok" in out
        assert '"message"' in out

    def test_csv_format(self, log_file, capsys):
        run_tail(log_file, n=1, fmt="csv")
        out = capsys.readouterr().out
        assert "retry ok" in out


class TestAddTailArguments:
    def test_tail_argument_registered(self):
        p = argparse.ArgumentParser()
        add_tail_arguments(p)
        args = p.parse_args(["--tail", "10"])
        assert args.tail == 10

    def test_follow_argument_registered(self):
        p = argparse.ArgumentParser()
        add_tail_arguments(p)
        args = p.parse_args(["--follow"])
        assert args.follow is True

    def test_follow_short_flag(self):
        p = argparse.ArgumentParser()
        add_tail_arguments(p)
        args = p.parse_args(["-f"])
        assert args.follow is True

    def test_defaults(self):
        p = argparse.ArgumentParser()
        add_tail_arguments(p)
        args = p.parse_args([])
        assert args.tail is None
        assert args.follow is False
