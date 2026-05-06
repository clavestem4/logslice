# Deduplication (`logslice.dedupe`)

The `dedupe` module removes repeated log entries so that noisy logs with
burst-repeated messages are easier to analyse.

## Concepts

Two entries are considered **duplicates** when they share the same
*severity* and *message* text.  The timestamp is intentionally ignored so
that the same error message emitted multiple times within a time window is
still collapsed.

A stable MD5 **fingerprint** is computed for each entry and used as the
deduplication key.

## API

### `entry_fingerprint(entry) -> str`

Return a 32-character hex fingerprint for *entry*.

```python
fp = entry_fingerprint(log_entry)
```

### `deduplicate(entries, *, keep="first", max_seen=None) -> Iterator[LogEntry]`

Yield unique entries from *entries*.

| Parameter  | Default   | Description |
|------------|-----------|-------------|
| `keep`     | `"first"` | `"first"` keeps the earliest occurrence; `"last"` keeps the latest. |
| `max_seen` | `None`    | Bound memory by evicting old fingerprints after this many unique entries. |

```python
from logslice.dedupe import deduplicate

unique = list(deduplicate(entries, keep="first"))
```

### `count_duplicates(entries) -> dict[str, int]`

Return a mapping of *fingerprint → occurrence count* without filtering.
Useful for reporting how many times each unique message appeared.

```python
from logslice.dedupe import count_duplicates

counts = count_duplicates(entries)
for fp, n in counts.items():
    if n > 1:
        print(f"{fp}: {n} occurrences")
```

## CLI integration

Pass `--dedupe` (or `-D`) to the `logslice` command to enable deduplication
before output is rendered:

```bash
logslice app.log --level ERROR --dedupe
```

Combine with `--keep last` to retain the most-recent occurrence of each
repeated message:

```bash
logslice app.log --dedupe --keep last
```
