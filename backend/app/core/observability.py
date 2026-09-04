"""Tracing seam (ADR-0006): one trace per Query, spans for its phases.

The interface is tiny — a `Tracer` opens a `Trace`, a `Trace` opens named spans.
Adapters: `NullTracer` (no-op default so /chat works with zero config),
`RecordingTracer` (captures traces/spans for tests), and `LangfuseTracer` (real,
lazy — needs the `tracing` extra + Langfuse keys, else it no-ops).
"""

from collections.abc import Iterator
from contextlib import AbstractContextManager, contextmanager
from typing import Any, Protocol

from app.core.config import Settings


class Trace(Protocol):
    def span(self, name: str) -> AbstractContextManager[None]: ...


class Tracer(Protocol):
    def trace(self, name: str, *, query: str) -> AbstractContextManager[Trace]: ...


class _NullTrace:
    @contextmanager
    def span(self, name: str) -> Iterator[None]:
        yield


class NullTracer:
    @contextmanager
    def trace(self, name: str, *, query: str) -> Iterator[Trace]:
        yield _NullTrace()


class _RecordingTrace:
    def __init__(self, record: dict[str, Any]) -> None:
        self._record = record

    @contextmanager
    def span(self, name: str) -> Iterator[None]:
        self._record["spans"].append(name)
        yield


class RecordingTracer:
    """In-memory tracer for tests. `traces` is a list of {name, query, spans}."""

    def __init__(self) -> None:
        self.traces: list[dict[str, Any]] = []

    @contextmanager
    def trace(self, name: str, *, query: str) -> Iterator[Trace]:
        record: dict[str, Any] = {"name": name, "query": query, "spans": []}
        self.traces.append(record)
        yield _RecordingTrace(record)


class _LangfuseTrace:
    def __init__(self, handle: Any) -> None:
        self._handle = handle

    @contextmanager
    def span(self, name: str) -> Iterator[None]:
        span = self._handle.span(name=name)
        try:
            yield
        finally:
            span.end()


class LangfuseTracer:
    def __init__(self, settings: Settings) -> None:
        self._settings = settings

    @contextmanager
    def trace(self, name: str, *, query: str) -> Iterator[Trace]:
        try:
            from langfuse import Langfuse  # type: ignore[import-not-found]
        except ImportError:  # pragma: no cover - no-ops without the `tracing` extra
            yield _NullTrace()
            return
        client = Langfuse()
        handle = client.trace(name=name, input={"query": query})
        try:
            yield _LangfuseTrace(handle)
        finally:
            client.flush()
