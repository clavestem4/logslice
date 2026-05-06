"""Tests for logslice.cli."""

import textwrap
import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime, timezone

from logslice.cli import main, build_parser, parse_dt
from logslice.parser import LogEntry


SAMPLE_LOG = textwrap.dedent("""\
    2024-06-01T10:00:00 INFO  server started
    2024-06-01T10:05:00 DEBUG heartbeat
    2024-06-01T10:10:00 ERROR disk full
    2024-06-01T10:15:00 WARNING high memory
""")


@pytest.fixture
def log_file(tmp_path):
    f = tmp_path / "app.log"
    f.write_text(SAMPLE_LOG)
    return str(f)


class TestParseDt:
    def test_iso_t_separator(self):
        dt = parse_dt("2024-06-01T12:00:00")
        assert dt.year == 2024
        assert dt.hour == 12

    def test_space_separator(self):
        dt = parse_dt("2024-06-01 12:00:00")
        assert dt.minute == 0

    def test_date_only(self):
        dt = parse_dt("2024-06-01")
        assert dt.day == 1

    def test_invalid_raises(self):
        import argparse
        with pytest.raises(argparse.ArgumentTypeError):
            parse_dt("not-a-date")


class TestBuildParser:
    def test_defaults(self):
        p = build_parser()
        args = p.parse_args(["myfile.log"])
        assert args.file == "myfile.log"
        assert args.start is None
        assert args.end is None
        assert args.min_severity is None
        assert args.fmt == "text"
        assert args.raw is False


class TestMain:
    def test_basic_run(self, log_file):
        rc = main([log_file])
        assert rc == 0

    def test_json_format(self, log_file, capsys):
        rc = main([log_file, "--format", "json"])
        assert rc == 0
        out = capsys.readouterr().out
        import json
        lines = [l for l in out.strip().splitlines() if l]
        assert all(json.loads(l) for l in lines)

    def test_csv_format(self, log_file, capsys):
        rc = main([log_file, "--format", "csv"])
        assert rc == 0
        out = capsys.readouterr().out
        assert out.splitlines()[0] == '"timestamp","severity","message"'

    def test_min_severity_filter(self, log_file, capsys):
        rc = main([log_file, "--min-severity", "ERROR"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "ERROR" in out
        assert "DEBUG" not in out
        assert "INFO" not in out

    def test_file_not_found(self, capsys):
        rc = main(["nonexistent_file.log"])
        assert rc == 1
        err = capsys.readouterr().err
        assert "not found" in err

    def test_empty_output_no_print(self, log_file, capsys):
        rc = main([log_file, "--start", "2099-01-01"])
        assert rc == 0
        out = capsys.readouterr().out
        assert out == ""

    def test_start_end_range_filter(self, log_file, capsys):
        """Only entries within the given time range should appear in output."""
        rc = main([log_file, "--start", "2024-06-01T10:04:00", "--end", "2024-06-01T10:11:00"])
        assert rc == 0
        out = capsys.readouterr().out
        assert "heartbeat" in out
        assert "disk full" in out
        assert "server started" not in out
        assert "high memory" not in out
