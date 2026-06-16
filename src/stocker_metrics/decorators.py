from __future__ import annotations

import functools
import time
from types import TracebackType
from typing import Any, Callable

from .client import timing


class timer:
    """Dual-mode timer: use as a context manager or a decorator.

    As context manager:
        with timer("pipeline.duration_ms", tags={"pipeline": "nasdaq"}):
            run_job()

    As decorator:
        @timer("pipeline.duration_ms", tags={"pipeline": "nasdaq"})
        def run_job():
            ...
    """

    def __init__(self, name: str, tags: dict | None = None) -> None:
        self.name = name
        self.tags = tags
        self._start: float = 0.0

    # --- context manager ---

    def __enter__(self) -> "timer":
        self._start = time.perf_counter()
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        elapsed_ms = (time.perf_counter() - self._start) * 1000
        timing(self.name, elapsed_ms, self.tags)

    # --- decorator ---

    def __call__(self, func: Callable[..., Any]) -> Callable[..., Any]:
        @functools.wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            with timer(self.name, self.tags):
                return func(*args, **kwargs)

        return wrapper
