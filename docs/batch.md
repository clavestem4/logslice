# Batch Processing

The `logslice.batch` module groups log entries into fixed-size or time-based
chunks, making it easy to process large log streams in manageable pieces.

## Data Model

```python
@dataclass
class Batch:
    entries: List[LogEntry]
    index: int  # zero-based position in the sequence of batches
```

`Batch.size` returns `len(entries)`.  
`Batch.as_dict()` serialises the batch to a plain dictionary.

## Functions

### `batch_by_size(entries, n) -> Iterator[Batch]`

Split *entries* into successive batches of at most *n* items.

```python
from logslice.batch import batch_by_size

for batch in batch_by_size(entries, n=500):
    process(batch.entries)
```

Yields nothing when `n <= 0` or *entries* is empty.

### `batch_by_time(entries, window, *, anchor=None) -> Iterator[Batch]`

Group entries so that every batch spans at most one *window* of time.  The
window is anchored to the timestamp of the first entry seen (or *anchor* if
provided).  Entries without a timestamp are appended to the current open batch.

```python
from datetime import timedelta
from logslice.batch import batch_by_time

for batch in batch_by_time(entries, window=timedelta(minutes=5)):
    print(batch.index, batch.size)
```

Yields nothing when `window <= 0` or *entries* is empty.

### `count_batches(entries, n) -> int`

Return the number of size-based batches that `batch_by_size` would produce
without actually iterating.

```python
from logslice.batch import count_batches

total = count_batches(entries, 100)
print(f"Will produce {total} batches")
```

## Example

```python
from logslice.slice import slice_file
from logslice.batch import batch_by_size, batch_by_time
from datetime import timedelta

entries = slice_file("app.log")

# Fixed-size batches
for batch in batch_by_size(entries, 1000):
    print(f"Batch {batch.index}: {batch.size} entries")

# Time-windowed batches
for batch in batch_by_time(entries, timedelta(minutes=15)):
    print(f"Window {batch.index}: {batch.size} entries")
```
