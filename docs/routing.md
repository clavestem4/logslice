# Routing

The `routing` module dispatches log entries to different handlers based on
configurable rules. This is useful for fan-out pipelines where different
severity levels or message patterns require separate processing paths.

## Core types

### `Route`

A single rule combining an optional severity threshold, an optional regex
pattern, and a handler callable.

```python
from logslice.routing import Route

route = Route(
    name="critical_disk",
    handler=lambda entry: print("ALERT:", entry.message),
    min_severity="ERROR",
    pattern=r"disk",
)
```

| Parameter | Type | Description |
|---|---|---|
| `name` | `str` | Identifier for the route, used in tallies |
| `handler` | `Callable[[LogEntry], None]` | Called when the entry matches |
| `min_severity` | `str \| None` | Minimum severity level (inclusive) |
| `pattern` | `str \| None` | Case-insensitive regex applied to `message` |

### `Router`

Holds an ordered list of `Route` objects and dispatches each entry to the
**first** matching route.

```python
from logslice.routing import Router, Route

router = Router()
router.add_route(Route(name="errors", handler=error_sink, min_severity="ERROR"))
router.add_route(Route(name="default", handler=default_sink))
```

## Dispatching entries

```python
# Single entry — returns the matched route name or None
matched = router.dispatch(entry)

# Batch — returns a dict of route-name → hit count
tally = router.dispatch_all(entries)
print(tally)  # {'errors': 3, 'default': 17}
```

## Default handler

If no route matches and a `default_handler` is set, it is called and the
special key `"__default__"` is returned.

```python
router = Router(default_handler=fallback_sink)
```

## Chaining with Pipeline

`Router.dispatch` is a plain callable, so it integrates naturally with
`logslice.pipeline.Pipeline` as a step.

```python
from logslice.pipeline import Pipeline

pipeline = Pipeline()
pipeline.add_step(lambda entries: [e for e in entries if e.severity])
pipeline.add_step(lambda entries: (router.dispatch_all(entries), entries)[1])
```
