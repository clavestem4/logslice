# logslice.cluster

The `cluster` module groups similar log entries together by normalising
variable tokens in their messages (numbers, IP addresses, UUIDs, hex
literals, and timestamps) into a common placeholder `<VAR>`.  Entries
that share the same normalised signature are placed in the same
`Cluster`.

This is useful for identifying the most frequent *types* of log event
without being misled by ever-changing values like retry counts, request
IDs, or IP addresses.

---

## API

### `message_signature(message: str) -> str`

Normalise *message* by replacing variable tokens with `<VAR>` and
collapsing whitespace.  Two messages that differ only in their variable
parts will produce the same signature.

```python
from logslice.cluster import message_signature

message_signature("retry 3 times")   # "retry <VAR> times"
message_signature("retry 99 times")  # "retry <VAR> times"
```

---

### `cluster_entries(entries, *, min_count=1, top_n=None) -> List[Cluster]`

Group *entries* into clusters and return them sorted by count
(descending).

| Parameter   | Type            | Description |
|-------------|-----------------|-------------|
| `entries`   | `List[LogEntry]`| Entries to cluster. |
| `min_count` | `int`           | Discard clusters smaller than this. |
| `top_n`     | `int \| None`   | Return at most this many clusters. |

```python
from logslice.cluster import cluster_entries
from logslice.slice import slice_file

entries = slice_file("app.log")
clusters = cluster_entries(entries, min_count=5, top_n=10)

for c in clusters:
    print(c.count, c.signature)
```

---

### `Cluster`

| Attribute    | Type                  | Description |
|--------------|-----------------------|-------------|
| `signature`  | `str`                 | Normalised message pattern. |
| `entries`    | `List[LogEntry]`      | All matching entries. |
| `count`      | `int` (property)      | Number of entries. |
| `severities` | `Dict[str, int]`      | Breakdown by severity level. |

```python
cluster.as_dict()
# {
#   "signature": "retry <VAR> times",
#   "count": 42,
#   "severities": {"WARN": 30, "ERROR": 12}
# }
```
