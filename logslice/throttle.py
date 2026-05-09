"""Entry throttling: suppress repeated log entries within a cooldown window."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from logslice.parser import LogEntry
from logslice.dedupe import entry_fingerprint


@dataclass
class ThrottleState:
    """Tracks the last-seen time and suppression count for a fingerprint."""

    last_seen: datetime
    suppressed: int = 0


@dataclass
class Throttle:
    """Suppress duplicate-ish entries that arrive within *cooldown* seconds."""

    cooldown_seconds: float = 60.0
    _state: Dict[str, ThrottleState] = field(default_factory=dict, init=False, repr=False)

    def _is_expired(self, ts: datetime, last: datetime) -> bool:
        return (ts - last) >= timedelta(seconds=self.cooldown_seconds)

    def allow(self, entry: LogEntry) -> bool:
        """Return True if the entry should pass through, False if throttled."""
        fp = entry_fingerprint(entry)
        ts = entry.timestamp or datetime.utcnow()

        if fp not in self._state:
            self._state[fp] = ThrottleState(last_seen=ts)
            return True

        state = self._state[fp]
        if self._is_expired(ts, state.last_seen):
            state.last_seen = ts
            state.suppressed = 0
            return True

        state.suppressed += 1
        return False

    def suppressed_count(self, entry: LogEntry) -> int:
        """Return how many times *entry* has been suppressed since last pass."""
        fp = entry_fingerprint(entry)
        return self._state[fp].suppressed if fp in self._state else 0

    def reset(self) -> None:
        """Clear all throttle state."""
        self._state.clear()


def throttle_entries(
    entries: List[LogEntry],
    cooldown_seconds: float = 60.0,
    throttle: Optional[Throttle] = None,
) -> List[LogEntry]:
    """Filter *entries*, dropping those within the cooldown window of an identical entry."""
    t = throttle if throttle is not None else Throttle(cooldown_seconds=cooldown_seconds)
    return [e for e in entries if t.allow(e)]
