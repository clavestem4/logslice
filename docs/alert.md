# Alert Module

The `logslice.alert` module lets you define rules that fire callbacks when log
entries satisfy a severity threshold, a regex pattern, or both.

## Core Types

### `AlertRule`

```python
from logslice.alert import AlertRule

def on_alert(entry, rule):
    print(f"[{rule.name}] {entry.severity}: {entry.message}")

rule = AlertRule(
    name="disk-error",
    callback=on_alert,
    min_severity="ERROR",
    pattern=r"disk",
)
```

| Field | Type | Description |
|-------|------|-------------|
| `name` | `str` | Human-readable rule identifier |
| `callback` | `Callable[[LogEntry, AlertRule], None]` | Called when the rule fires |
| `min_severity` | `str \| None` | Minimum severity (uses `severity_rank`) |
| `pattern` | `str \| None` | Case-insensitive regex matched against `message` |

## Functions

### `evaluate_rules(entry, rules) -> List[AlertRule]`

Returns every rule in `rules` whose conditions are satisfied by `entry`.

### `dispatch(entry, rules) -> int`

Fires the callback of every matching rule and returns the number of alerts
triggered.

### `process_entries(entries, rules) -> int`

Convenience function that calls `dispatch` for every entry and returns the
cumulative alert count.

## CLI

```
logslice alert app.log --min-severity ERROR --pattern "timeout"
logslice alert app.log --min-severity WARN --count-only
logslice alert app.log --pattern "disk" --rule-name disk-alert --format json
```

### Options

| Flag | Default | Description |
|------|---------|-------------|
| `--min-severity` | _none_ | Minimum severity level |
| `--pattern` | _none_ | Regex pattern to match in message |
| `--rule-name` | `cli-rule` | Name shown in alert output |
| `--format` | `text` | Output format: `text`, `json`, `csv` |
| `--count-only` | off | Print only the total alert count |

## Example output

```
[ALERT:disk-alert] 2024-01-01T10:02:00 ERROR disk full
[ALERT:disk-alert] 2024-01-01T10:01:00 WARN  disk usage high
```
