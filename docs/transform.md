# logslice.transform

The `transform` module provides utilities for modifying log entries in a non-destructive way. All functions return new `LogEntry` instances, leaving the originals unchanged.

## Functions

### `redact_message(entry, pattern, replacement="[REDACTED]") -> LogEntry`

Replaces all occurrences of a regex `pattern` in `entry.message` with `replacement`.

```python
from logslice.transform import redact_message

redacted = redact_message(entry, r"token=\S+")
# entry.message: "user=alice token=secret123"
# result.message: "user=alice [REDACTED]"
```

### `normalize_severity(entry) -> LogEntry`

Returns a new entry with the severity field uppercased and whitespace stripped. Useful when ingesting logs from sources with inconsistent casing.

```python
from logslice.transform import normalize_severity

normalized = normalize_severity(entry)  # "info" -> "INFO"
```

### `truncate_message(entry, max_length) -> LogEntry`

Returns a new entry with the message truncated to at most `max_length` characters. Raises `ValueError` if `max_length` is negative.

```python
from logslice.transform import truncate_message

short = truncate_message(entry, 80)
```

### `apply_transform(entries, transform) -> List[LogEntry]`

Applies a callable `transform` to every entry in `entries`. If the transform returns `None` for an entry, that entry is excluded from the result. Useful for building transformation pipelines.

```python
from logslice.transform import apply_transform, normalize_severity

cleaned = apply_transform(entries, normalize_severity)
```

You can chain multiple transforms using `functools.reduce` or nested calls:

```python
import functools
from logslice.transform import apply_transform, normalize_severity, truncate_message

transforms = [
    normalize_severity,
    lambda e: truncate_message(e, 120),
]
cleaned = functools.reduce(apply_transform, transforms, entries)
```
