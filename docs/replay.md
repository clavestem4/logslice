# Replay

The `logslice.replay` module lets you stream log entries back at a pace that
mirrors the original timing — useful for feeding entries into dashboards,
alert pipelines, or integration tests that depend on realistic cadence.

## Core API

### `ReplayOptions`

```python
@dataclass
class ReplayOptions:
    speed: float = 1.0        # 2.0 = twice as fast
    max_delay: float = 5.0    # seconds; caps long idle gaps
    real_time: bool = True    # False → emit instantly
    on_emit: Callable | None = None
```

### `replay_entries(entries, options)`

Yields each `LogEntry` after an appropriate `time.sleep()` based on the
timestamp gap to the previous entry.

```python
from logslice.replay import ReplayOptions, replay_entries
from logslice.slice import slice_file

opts = ReplayOptions(speed=4.0, max_delay=2.0)
for entry in replay_entries(slice_file("app.log"), opts):
    print(entry.message)
```

### `replay_count(entries, options)`

Convenience wrapper that replays and returns the total entry count.

## CLI

```
logslice replay app.log [--speed X] [--max-delay SEC] [--no-real-time] [--severity LEVEL]
```

| Flag | Default | Description |
|------|---------|-------------|
| `--speed` | `1.0` | Replay speed multiplier |
| `--max-delay` | `5.0` | Cap on inter-entry pause (seconds) |
| `--no-real-time` | off | Disable timing; emit as fast as possible |
| `--severity` | none | Minimum severity filter |

## Notes

- Entries with missing timestamps are emitted without delay.
- When consecutive timestamps are equal or decrease, no sleep occurs.
- The `on_emit` callback fires **before** the entry is yielded, making it
  suitable for side-effects such as metrics or alerting.
