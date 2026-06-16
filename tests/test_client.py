from __future__ import annotations

import socket
from unittest.mock import MagicMock, patch

import pytest

from stocker_metrics.client import StatsDClient
from stocker_metrics.config import MetricsConfig


def make_client(**overrides) -> StatsDClient:
    defaults = dict(host="localhost", port=9125, prefix="stocker", env="test", enabled=True)
    defaults.update(overrides)
    return StatsDClient(MetricsConfig(**defaults))


def capture_payload(client: StatsDClient, method: str, *args, **kwargs) -> str:
    """Call client.<method>(*args) and return the UDP payload sent."""
    sent: list[bytes] = []

    mock_sock = MagicMock()
    mock_sock.__enter__ = lambda s: s
    mock_sock.__exit__ = MagicMock(return_value=False)
    mock_sock.sendto.side_effect = lambda data, addr: sent.append(data)

    with patch("stocker_metrics.client.socket.socket", return_value=mock_sock):
        getattr(client, method)(*args, **kwargs)

    assert sent, "No payload was sent"
    return sent[0].decode()


class TestIncr:
    def test_basic(self):
        client = make_client()
        payload = capture_payload(client, "incr", "pipeline.run_started")
        assert payload == "stocker.pipeline.run_started:1|c|#env=test"

    def test_custom_value(self):
        client = make_client()
        payload = capture_payload(client, "incr", "jobs.count", 5)
        assert payload == "stocker.jobs.count:5|c|#env=test"

    def test_with_tags(self):
        client = make_client()
        payload = capture_payload(client, "incr", "pipeline.run_started", 1, {"pipeline": "nasdaq"})
        assert payload == "stocker.pipeline.run_started:1|c|#env=test,pipeline=nasdaq"


class TestGauge:
    def test_int(self):
        client = make_client()
        payload = capture_payload(client, "gauge", "pipeline.rows_fetched", 42)
        assert payload == "stocker.pipeline.rows_fetched:42|g|#env=test"

    def test_float(self):
        client = make_client()
        payload = capture_payload(client, "gauge", "mem.usage", 0.75)
        assert payload == "stocker.mem.usage:0.75|g|#env=test"

    def test_with_tags(self):
        client = make_client()
        payload = capture_payload(client, "gauge", "rows", 10, {"pipeline": "sp500"})
        assert payload == "stocker.rows:10|g|#env=test,pipeline=sp500"


class TestTiming:
    def test_basic(self):
        client = make_client()
        payload = capture_payload(client, "timing", "pipeline.duration_ms", 123.4)
        assert payload == "stocker.pipeline.duration_ms:123.4|ms|#env=test"

    def test_with_tags(self):
        client = make_client()
        payload = capture_payload(client, "timing", "job.duration_ms", 50, {"pipeline": "nasdaq"})
        assert payload == "stocker.job.duration_ms:50|ms|#env=test,pipeline=nasdaq"


class TestDisabled:
    def test_no_send_when_disabled(self):
        client = make_client(enabled=False)
        with patch("stocker_metrics.client.socket.socket") as mock_socket_cls:
            client.incr("some.metric")
            mock_socket_cls.assert_not_called()


class TestTagFormatting:
    def test_env_always_present(self):
        client = make_client(env="prod")
        payload = capture_payload(client, "incr", "x")
        assert "#env=prod" in payload

    def test_tags_merged_with_env(self):
        client = make_client(env="staging")
        payload = capture_payload(client, "incr", "x", 1, {"region": "us-east"})
        assert "env=staging" in payload
        assert "region=us-east" in payload

    def test_custom_prefix(self):
        client = make_client(prefix="myapp")
        payload = capture_payload(client, "incr", "events")
        assert payload.startswith("myapp.events:")


class TestSilentFailure:
    def test_socket_error_does_not_raise(self):
        client = make_client()
        mock_sock = MagicMock()
        mock_sock.__enter__ = lambda s: s
        mock_sock.__exit__ = MagicMock(return_value=False)
        mock_sock.sendto.side_effect = OSError("network unreachable")

        with patch("stocker_metrics.client.socket.socket", return_value=mock_sock):
            client.incr("something")  # should not raise
