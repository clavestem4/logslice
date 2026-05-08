"""Pipeline: chain multiple log processing steps into a single pass."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable, Iterable, List, Optional

from logslice.parser import LogEntry


StepFn = Callable[[List[LogEntry]], List[LogEntry]]


@dataclass
class Pipeline:
    """An ordered sequence of transformation/filter steps."""

    steps: List[StepFn] = field(default_factory=list)
    name: str = "pipeline"

    def add_step(self, fn: StepFn, *, label: Optional[str] = None) -> "Pipeline":
        """Append a step and return self for chaining."""
        self.steps.append(fn)
        return self

    def run(self, entries: Iterable[LogEntry]) -> List[LogEntry]:
        """Execute all steps in order and return the final entry list."""
        result: List[LogEntry] = list(entries)
        for step in self.steps:
            result = step(result)
        return result

    def __len__(self) -> int:
        return len(self.steps)

    def __repr__(self) -> str:  # pragma: no cover
        return f"Pipeline(name={self.name!r}, steps={len(self.steps)})"


def build_pipeline(*steps: StepFn, name: str = "pipeline") -> Pipeline:
    """Convenience constructor — create a Pipeline from positional step functions."""
    p = Pipeline(name=name)
    for fn in steps:
        p.add_step(fn)
    return p


def run_pipeline(entries: Iterable[LogEntry], *steps: StepFn) -> List[LogEntry]:
    """One-shot helper: run *entries* through *steps* without creating a Pipeline object."""
    return build_pipeline(*steps).run(entries)
