from __future__ import annotations

from unittest.mock import patch

from stocker_metrics.decorators import timer


def test_timer_context_manager_calls_timing():
    calls: list[tuple] = []

    with patch("stocker_metrics.decorators.timing", side_effect=lambda *a, **kw: calls.append((a, kw))):
        with timer("pipeline.duration_ms", tags={"pipeline": "nasdaq"}):
            pass

    assert len(calls) == 1
    name, ms, _tags = calls[0][0]
    assert name == "pipeline.duration_ms"
    assert ms > 0


def test_timer_context_manager_elapsed_is_positive():
    import time

    calls: list[tuple] = []

    with patch("stocker_metrics.decorators.timing", side_effect=lambda *a, **kw: calls.append((a, kw))):
        with timer("sleep.duration_ms"):
            time.sleep(0.01)

    _name, ms, _tags = calls[0][0]
    assert ms >= 10  # at least 10ms


def test_timer_decorator_calls_timing():
    calls: list[tuple] = []

    @timer("job.duration_ms", tags={"step": "fetch"})
    def fake_job():
        return 42

    with patch("stocker_metrics.decorators.timing", side_effect=lambda *a, **kw: calls.append((a, kw))):
        result = fake_job()

    assert result == 42
    assert len(calls) == 1
    name, ms, _tags = calls[0][0]
    assert name == "job.duration_ms"
    assert ms > 0


def test_timer_decorator_passes_tags():
    calls: list[tuple] = []

    @timer("job.duration_ms", tags={"pipeline": "sp500"})
    def fake_job():
        pass

    with patch("stocker_metrics.decorators.timing", side_effect=lambda *a, **kw: calls.append((a, kw))):
        fake_job()

    _, kwargs = calls[0]
    # tags passed as positional arg
    assert calls[0][0][2] == {"pipeline": "sp500"}


def test_timer_decorator_preserves_function_name():
    @timer("irrelevant")
    def my_named_function():
        pass

    assert my_named_function.__name__ == "my_named_function"
