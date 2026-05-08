"""Tests for logslice.replay."""

from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import patch

import pytest

from logslice.parser import LogEntry
from logslice.replay import ReplayOptions, _delay_seconds, replay_count, replay_entries


def make_entry(msg: str, ts: datetime | None = None, severity: str = "INFO") -> LogEntry:
    return LogEntry(timestamp=ts, severity=severity, message=msg, raw=msg)


def dt(hour: int, minute: int, second: int = 0) -> datetime:
    return datetime(2024, 1, 1, hour, minute, second, tzinfo=timezone.utc)


# ---------------------------------------------------------------------------
# _delay_seconds
# ---------------------------------------------------------------------------

class TestDelaySeconds:
    def test_no_timestamps_returns_zero(self):
        prev = make_entry("a")
        cur = make_entry("b")
        assert _delay_seconds(prev, cur, ReplayOptions()) == 0.0

    def test_same_timestamp_returns_zero(self):
        ts = dt(12, 0, 0)
        prev = make_entry("a", ts)
        cur = make_entry("b", ts)
        assert _delay_seconds(prev, cur, ReplayOptions()) == 0.0

    def test_one_second_gap_speed_one(self):
        prev = make_entry("a", dt(12, 0, 0))
        cur = make_entry("b", dt(12, 0, 1))
        assert _delay_seconds(prev, cur, ReplayOptions(speed=1.0)) == pytest.approx(1.0)

    def test_speed_doubles_halves_delay(self):
        prev = make_entry("a", dt(12, 0, 0))
        cur = make_entry("b", dt(12, 0, 4))
        assert _delay_seconds(prev, cur, ReplayOptions(speed=2.0)) == pytest.approx(2.0)

    def test_max_delay_caps_result(self):
        prev = make_entry("a", dt(12, 0, 0))
        cur = make_entry("b", dt(12, 1, 0))  # 60-second gap
        opts = ReplayOptions(speed=1.0, max_delay=3.0)
        assert _delay_seconds(prev, cur, opts) == 3.0

    def test_real_time_false_returns_zero(self):
        prev = make_entry("a", dt(12, 0, 0))
        cur = make_entry("b", dt(12, 0, 5))
        opts = ReplayOptions(real_time=False)
        assert _delay_seconds(prev, cur, opts) == 0.0

    def test_negative_delta_returns_zero(self):
        prev = make_entry("a", dt(12, 0, 5))
        cur = make_entry("b", dt(12, 0, 0))
        assert _delay_seconds(prev, cur, ReplayOptions()) == 0.0


# ---------------------------------------------------------------------------
# replay_entries
# ---------------------------------------------------------------------------

class TestReplayEntries:
    def test_yields_all_entries(self):
        entries = [make_entry(f"msg{i}") for i in range(5)]
        opts = ReplayOptions(real_time=False)
        result = list(replay_entries(entries, opts))
        assert len(result) == 5

    def test_order_preserved(self):
        entries = [make_entry(f"msg{i}", dt(12, 0, i)) for i in range(4)]
        opts = ReplayOptions(real_time=False)
        result = list(replay_entries(entries, opts))
        assert [e.message for e in result] == ["msg0", "msg1", "msg2", "msg3"]

    def test_empty_input_yields_nothing(self):
        assert list(replay_entries([], ReplayOptions(real_time=False))) == []

    def test_on_emit_called_for_each_entry(self):
        seen = []
        entries = [make_entry(f"m{i}") for i in range(3)]
        opts = ReplayOptions(real_time=False, on_emit=seen.append)
        list(replay_entries(entries, opts))
        assert len(seen) == 3

    def test_sleep_called_with_delay(self):
        entries = [
            make_entry("a", dt(12, 0, 0)),
            make_entry("b", dt(12, 0, 2)),
        ]
        opts = ReplayOptions(speed=1.0, real_time=True)
        with patch("logslice.replay.time.sleep") as mock_sleep:
            list(replay_entries(entries, opts))
        mock_sleep.assert_called_once_with(pytest.approx(2.0))

    def test_no_sleep_for_first_entry(self):
        entries = [make_entry("only", dt(12, 0, 0))]
        opts = ReplayOptions(real_time=True)
        with patch("logslice.replay.time.sleep") as mock_sleep:
            list(replay_entries(entries, opts))
        mock_sleep.assert_not_called()

    def test_default_options_used_when_none(self):
        entries = [make_entry("x")]
        with patch("logslice.replay.time.sleep"):
            result = list(replay_entries(entries))
        assert len(result) == 1


# ---------------------------------------------------------------------------
# replay_count
# ---------------------------------------------------------------------------

class TestReplayCount:
    def test_returns_correct_count(self):
        entries = [make_entry(f"m{i}") for i in range(7)]
        opts = ReplayOptions(real_time=False)
        assert replay_count(entries, opts) == 7

    def test_empty_returns_zero(self):
        assert replay_count([], ReplayOptions(real_time=False)) == 0
