# Sampling

The `logslice.sample` module provides three strategies for reducing a large
list of `LogEntry` objects to a manageable subset.

## Functions

### `sample_entries(entries, n, seed=None)`

Choose **exactly** `n` entries at random without replacement.  
The original order of the selected entries is preserved.

```python
from logslice.sample import sample_entries

subset = sample_entries(entries, n=100, seed=42)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `entries` | `list[LogEntry]` | Source entries |
| `n` | `int` | Number of entries to return (clamped to list length) |
| `seed` | `int \| None` | Random seed for reproducibility |

---

### `sample_rate(entries, rate, seed=None)`

Keep each entry independently with probability `rate`.

```python
from logslice.sample import sample_rate

# Keep roughly 10 % of entries
subset = sample_rate(entries, rate=0.1, seed=0)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `entries` | `list[LogEntry]` | Source entries |
| `rate` | `float` | Probability in `[0.0, 1.0]` |
| `seed` | `int \| None` | Random seed for reproducibility |

---

### `every_nth(entries, n)`

Deterministic, uniform downsampling — returns entries at positions
`0, n, 2n, …`.

```python
from logslice.sample import every_nth

# Take every 10th entry
subset = every_nth(entries, 10)
```

| Parameter | Type | Description |
|-----------|------|-------------|
| `entries` | `list[LogEntry]` | Source entries |
| `n` | `int` | Step size; must be `>= 1` |

Raises `ValueError` if `n < 1`.

---

## CLI integration

Sampling is not yet exposed as a CLI flag but can be combined with
`slice_file` + `apply_filters` in a custom script:

```python
from logslice.slice import slice_file
from logslice.sample import sample_entries

entries = slice_file("app.log")
sampled = sample_entries(entries, n=200, seed=1)
```
