"""Tests for logslice.throttle."""

from datetime import datetime, timedelta
from typing import Optional

import pytest

from logslice.parser import LogEntry
from logslice.throttle import Throttle, ThrottleState, throttle_entries


def make_entry(
    message: str = "test message",
    severity: str = "INFO",
    timestamp: Optional[datetime] = None,
    raw: str = "",
) -> LogEntry:
    return LogEntry(
        timestamp=timestamp or datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw=raw or f"{severity} {message}",
    )


class TestThrottle:
    def test_first_entry_always_allowed(self):
        t = Throttle(cooldown_seconds=60)
        entry = make_entry("hello")
        assert t.allow(entry) is True

    def test_duplicate_within_cooldown_blocked(self):
        t = Throttle(cooldown_seconds=60)
        e1 = make_entry("hello", timestamp=datetime(2024, 1, 1, 12, 0, 0))
        e2 = make_entry("hello", timestamp=datetime(2024, 1, 1, 12, 0, 30))
        t.allow(e1)
        assert t.allow(e2) is False

    def test_duplicate_after_cooldown_allowed(self):
        t = Throttle(cooldown_seconds=60)
        e1 = make_entry("hello", timestamp=datetime(2024, 1, 1, 12, 0, 0))
        e2 = make_entry("hello", timestamp=datetime(2024, 1, 1, 12, 1, 1))
        t.allow(e1)
        assert t.allow(e2) is True

    def test_different_messages_both_allowed(self):
        t = Throttle(cooldown_seconds=60)
        e1 = make_entry("hello", timestamp=datetime(2024, 1, 1, 12, 0, 0))
        e2 = make_entry("world", timestamp=datetime(2024, 1, 1, 12, 0, 5))
        assert t.allow(e1) is True
        assert t.allow(e2) is True

    def test_different_severity_treated_separately(self):
        t = Throttle(cooldown_seconds=60)
        e1 = make_entry("hello", severity="INFO", timestamp=datetime(2024, 1, 1, 12, 0, 0))
        e2 = make_entry("hello", severity="ERROR", timestamp=datetime(2024, 1, 1, 12, 0, 5))
        assert t.allow(e1) is True
        assert t.allow(e2) is True

    def test_suppressed_count_increments(self):
        t = Throttle(cooldown_seconds=60)
        base = datetime(2024, 1, 1, 12, 0, 0)
        e0 = make_entry("msg", timestamp=base)
        e1 = make_entry("msg", timestamp=base + timedelta(seconds=10))
        e2 = make_entry("msg", timestamp=base + timedelta(seconds=20))
        t.allow(e0)
        t.allow(e1)
        t.allow(e2)
        assert t.suppressed_count(e0) == 2

    def test_suppressed_count_resets_after_cooldown(self):
        t = Throttle(cooldown_seconds=60)
        base = datetime(2024, 1, 1, 12, 0, 0)
        e0 = make_entry("msg", timestamp=base)
        e1 = make_entry("msg", timestamp=base + timedelta(seconds=10))
        e2 = make_entry("msg", timestamp=base + timedelta(seconds=70))
        t.allow(e0)
        t.allow(e1)
        t.allow(e2)  # resets
        assert t.suppressed_count(e0) == 0

    def test_reset_clears_state(self):
        t = Throttle(cooldown_seconds=60)
        base = datetime(2024, 1, 1, 12, 0, 0)
        e1 = make_entry("msg", timestamp=base)
        e2 = make_entry("msg", timestamp=base + timedelta(seconds=5))
        t.allow(e1)
        t.reset()
        assert t.allow(e2) is True

    def test_no_timestamp_uses_utcnow(self):
        t = Throttle(cooldown_seconds=60)
        e = LogEntry(timestamp=None, severity="INFO", message="hi", raw="INFO hi")
        assert t.allow(e) is True


class TestThrottleEntries:
    def test_returns_list(self):
        entries = [make_entry("a"), make_entry("b")]
        result = throttle_entries(entries)
        assert isinstance(result, list)

    def test_no_duplicates_all_pass(self):
        base = datetime(2024, 1, 1, 12, 0, 0)
        entries = [
            make_entry("a", timestamp=base),
            make_entry("b", timestamp=base + timedelta(seconds=1)),
            make_entry("c", timestamp=base + timedelta(seconds=2)),
        ]
        assert throttle_entries(entries) == entries

    def test_duplicates_within_cooldown_dropped(self):
        base = datetime(2024, 1, 1, 12, 0, 0)
        entries = [
            make_entry("dup", timestamp=base),
            make_entry("dup", timestamp=base + timedelta(seconds=10)),
            make_entry("dup", timestamp=base + timedelta(seconds=20)),
        ]
        result = throttle_entries(entries, cooldown_seconds=60)
        assert len(result) == 1

    def test_accepts_external_throttle_instance(self):
        t = Throttle(cooldown_seconds=30)
        base = datetime(2024, 1, 1, 12, 0, 0)
        e1 = make_entry("x", timestamp=base)
        e2 = make_entry("x", timestamp=base + timedelta(seconds=5))
        throttle_entries([e1], throttle=t)
        result = throttle_entries([e2], throttle=t)
        assert result == []

    def test_empty_list_returns_empty(self):
        assert throttle_entries([]) == []
