"""Tests for logslice.routing."""

from __future__ import annotations

from datetime import datetime
from typing import List

import pytest

from logslice.parser import LogEntry
from logslice.routing import Route, Router


def make_entry(
    message: str = "hello",
    severity: str = "INFO",
    timestamp: datetime | None = None,
) -> LogEntry:
    return LogEntry(
        timestamp=timestamp or datetime(2024, 1, 1, 12, 0, 0),
        severity=severity,
        message=message,
        raw=f"{severity} {message}",
    )


class TestRouteMatches:
    def test_no_conditions_always_matches(self):
        route = Route(name="catch_all", handler=lambda e: None)
        assert route.matches(make_entry()) is True

    def test_min_severity_passes(self):
        route = Route(name="r", handler=lambda e: None, min_severity="WARN")
        assert route.matches(make_entry(severity="ERROR")) is True

    def test_min_severity_fails(self):
        route = Route(name="r", handler=lambda e: None, min_severity="ERROR")
        assert route.matches(make_entry(severity="INFO")) is False

    def test_pattern_matches(self):
        route = Route(name="r", handler=lambda e: None, pattern="timeout")
        assert route.matches(make_entry(message="connection timeout")) is True

    def test_pattern_no_match(self):
        route = Route(name="r", handler=lambda e: None, pattern="timeout")
        assert route.matches(make_entry(message="all good")) is False

    def test_pattern_case_insensitive(self):
        route = Route(name="r", handler=lambda e: None, pattern="TIMEOUT")
        assert route.matches(make_entry(message="connection timeout")) is True

    def test_combined_severity_and_pattern_both_must_pass(self):
        route = Route(name="r", handler=lambda e: None, min_severity="WARN", pattern="disk")
        assert route.matches(make_entry(severity="ERROR", message="disk full")) is True
        assert route.matches(make_entry(severity="INFO", message="disk full")) is False
        assert route.matches(make_entry(severity="ERROR", message="cpu high")) is False


class TestRouterDispatch:
    def _collect(self) -> List[LogEntry]:
        return []

    def test_dispatches_to_first_matching_route(self):
        received: List[LogEntry] = []
        route = Route(name="errors", handler=received.append, min_severity="ERROR")
        router = Router(routes=[route])
        entry = make_entry(severity="ERROR")
        name = router.dispatch(entry)
        assert name == "errors"
        assert received == [entry]

    def test_skips_non_matching_routes(self):
        received: List[LogEntry] = []
        r1 = Route(name="errors", handler=lambda e: None, min_severity="ERROR")
        r2 = Route(name="all", handler=received.append)
        router = Router(routes=[r1, r2])
        entry = make_entry(severity="INFO")
        name = router.dispatch(entry)
        assert name == "all"
        assert received == [entry]

    def test_returns_none_when_no_match_and_no_default(self):
        route = Route(name="errors", handler=lambda e: None, min_severity="ERROR")
        router = Router(routes=[route])
        result = router.dispatch(make_entry(severity="DEBUG"))
        assert result is None

    def test_default_handler_called_when_no_route_matches(self):
        received: List[LogEntry] = []
        route = Route(name="errors", handler=lambda e: None, min_severity="ERROR")
        router = Router(routes=[route], default_handler=received.append)
        entry = make_entry(severity="INFO")
        name = router.dispatch(entry)
        assert name == "__default__"
        assert received == [entry]

    def test_dispatch_all_returns_tally(self):
        counts_store: dict = {}
        r1 = Route(name="errors", handler=lambda e: None, min_severity="ERROR")
        r2 = Route(name="all", handler=lambda e: None)
        router = Router(routes=[r1, r2])
        entries = [
            make_entry(severity="ERROR"),
            make_entry(severity="INFO"),
            make_entry(severity="ERROR"),
        ]
        tally = router.dispatch_all(entries)
        assert tally["errors"] == 2
        assert tally["all"] == 1

    def test_len_returns_route_count(self):
        router = Router()
        router.add_route(Route(name="a", handler=lambda e: None))
        router.add_route(Route(name="b", handler=lambda e: None))
        assert len(router) == 2

    def test_add_route_returns_self(self):
        router = Router()
        result = router.add_route(Route(name="a", handler=lambda e: None))
        assert result is router

    def test_repr_contains_route_names(self):
        router = Router()
        router.add_route(Route(name="alerts", handler=lambda e: None))
        assert "alerts" in repr(router)
