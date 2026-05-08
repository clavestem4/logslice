# Pipeline

The `pipeline` module lets you chain multiple processing steps — filters,
transforms, deduplication, and more — into a single reusable object.

## Core API

```python
from logslice.pipeline import Pipeline, build_pipeline, run_pipeline
```

### `Pipeline`

```python
p = Pipeline(name="my-pipeline")
p.add_step(step_fn)   # returns self for chaining
result = p.run(entries)
```

Each *step* is a callable `(List[LogEntry]) -> List[LogEntry]`.
Steps are applied in the order they were added.

### `build_pipeline(*steps, name="pipeline")`

Convenience constructor:

```python
from logslice.filter import filter_by_severity
from logslice.dedupe import deduplicate

p = build_pipeline(
    lambda e: filter_by_severity(e, min_level="WARNING"),
    deduplicate,
    name="warn-dedup",
)
result = p.run(entries)
```

### `run_pipeline(entries, *steps)`

One-shot helper when you don't need to keep the Pipeline object:

```python
result = run_pipeline(entries, step1, step2, step3)
```

## CLI usage

```
logslice pipeline app.log \
    --min-severity WARNING \
    --step dedup \
    --format json
```

### Options

| Flag | Description |
|------|-------------|
| `--min-severity LEVEL` | Keep only entries at or above *LEVEL* |
| `--start DATETIME` | Earliest timestamp |
| `--end DATETIME` | Latest timestamp |
| `--step NAME` | Add a named built-in step (`dedup`, `errors-only`) |
| `--format` | Output format: `text` (default), `json`, `csv` |

Multiple `--step` flags are applied left-to-right.

## Built-in steps

| Name | Effect |
|------|--------|
| `dedup` | Remove duplicate entries (same message + severity) |
| `errors-only` | Keep only `ERROR`, `CRITICAL`, and `FATAL` entries |
