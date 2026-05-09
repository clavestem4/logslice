"""Route log entries to different handlers based on rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, List, Optional

from logslice.parser import LogEntry
from logslice.filter import severity_rank


Handler = Callable[[LogEntry], None]


@dataclass
class Route:
    """A single routing rule that maps a predicate to a handler."""

    name: str
    handler: Handler
    min_severity: Optional[str] = None
    pattern: Optional[str] = None
    _compiled: object = field(default=None, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.pattern:
            import re
            self._compiled = re.compile(self.pattern, re.IGNORECASE)

    def matches(self, entry: LogEntry) -> bool:
        """Return True if the entry satisfies this route's conditions."""
        if self.min_severity:
            if severity_rank(entry.severity) < severity_rank(self.min_severity):
                return False
        if self._compiled:
            text = entry.message or ""
            if not self._compiled.search(text):
                return False
        return True


@dataclass
class Router:
    """Dispatch entries to the first matching route."""

    routes: List[Route] = field(default_factory=list)
    default_handler: Optional[Handler] = None

    def add_route(self, route: Route) -> "Router":
        self.routes.append(route)
        return self

    def dispatch(self, entry: LogEntry) -> Optional[str]:
        """Send entry to the first matching handler; return matched route name."""
        for route in self.routes:
            if route.matches(entry):
                route.handler(entry)
                return route.name
        if self.default_handler:
            self.default_handler(entry)
            return "__default__"
        return None

    def dispatch_all(self, entries: List[LogEntry]) -> dict:
        """Dispatch every entry and return a tally of route hits."""
        counts: dict = {}
        for entry in entries:
            name = self.dispatch(entry)
            if name:
                counts[name] = counts.get(name, 0) + 1
        return counts

    def __len__(self) -> int:
        return len(self.routes)

    def __repr__(self) -> str:
        names = [r.name for r in self.routes]
        return f"Router(routes={names})"
