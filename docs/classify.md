# classify

The `classify` module assigns category labels to `LogEntry` objects based on
configurable rules. Each rule can match on a regex pattern, a minimum severity,
a maximum severity, or any combination of those conditions.

## ClassifyRule

```python
from logslice.classify import ClassifyRule

rule = ClassifyRule(
    category="database",
    pattern=r"db|database|sql",
    min_severity="WARNING",
)
```

| Field | Type | Description |
|---|---|---|
| `category` | `str` | Label assigned when this rule matches |
| `pattern` | `str \| None` | Case-insensitive regex applied to `entry.message` |
| `min_severity` | `str \| None` | Entry severity must be ≥ this level |
| `max_severity` | `str \| None` | Entry severity must be ≤ this level |

## Functions

### `classify_entry(entry, rules, default="unclassified") -> str`

Returns the category of the **first** rule that matches *entry*. If no rule
matches, `default` is returned.

### `classify_entries(entries, rules, default="unclassified") -> list[tuple]`

Returns a list of `(LogEntry, category)` pairs.

### `group_by_category(entries, rules, default="unclassified") -> dict`

Returns a `dict` mapping each category to the list of entries that belong to it.

## CLI usage

```
logslice classify app.log \
    --rule db:database \
    --rule net:network \
    --summary
```

Flags:

| Flag | Description |
|---|---|
| `--rule CATEGORY:PATTERN` | Add a classification rule (repeatable) |
| `--min-severity LEVEL` | Pre-filter entries below this severity |
| `--summary` | Print category counts instead of entries |
| `--json` | Output the summary as a JSON object |

## Example

```python
from logslice.classify import ClassifyRule, group_by_category
from logslice.slice import slice_file

entries = slice_file("app.log")
rules = [
    ClassifyRule("db_error", pattern=r"database", min_severity="ERROR"),
    ClassifyRule("slow_query", pattern=r"slow query"),
]
groups = group_by_category(entries, rules)
for cat, ents in groups.items():
    print(f"{cat}: {len(ents)} entries")
```
