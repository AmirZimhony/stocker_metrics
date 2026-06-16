from __future__ import annotations

import socket
from typing import TYPE_CHECKING

from .config import MetricsConfig, from_env

if TYPE_CHECKING:
    pass

_default_client: "StatsDClient | None" = None


def _get_default_client() -> "StatsDClient":
    global _default_client
    if _default_client is None:
        _default_client = StatsDClient(from_env())
    return _default_client


class StatsDClient:
    def __init__(self, config: MetricsConfig) -> None:
        self.config = config

    def _format_tags(self, tags: dict | None) -> str:
        all_tags = {"env": self.config.env}
        if tags:
            all_tags.update(tags)
        return "#" + ",".join(f"{k}={v}" for k, v in all_tags.items())

    def _send(self, payload: str) -> None:
        if not self.config.enabled:
            return
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as sock:
                sock.sendto(payload.encode(), (self.config.host, self.config.port))
        except Exception:
            pass

    def _metric_name(self, name: str) -> str:
        return f"{self.config.prefix}.{name}"

    def incr(self, name: str, value: int = 1, tags: dict | None = None) -> None:
        payload = f"{self._metric_name(name)}:{value}|c|{self._format_tags(tags)}"
        self._send(payload)

    def gauge(self, name: str, value: int | float, tags: dict | None = None) -> None:
        payload = f"{self._metric_name(name)}:{value}|g|{self._format_tags(tags)}"
        self._send(payload)

    def timing(self, name: str, milliseconds: int | float, tags: dict | None = None) -> None:
        payload = f"{self._metric_name(name)}:{milliseconds}|ms|{self._format_tags(tags)}"
        self._send(payload)


def incr(name: str, value: int = 1, tags: dict | None = None) -> None:
    _get_default_client().incr(name, value, tags)


def gauge(name: str, value: int | float, tags: dict | None = None) -> None:
    _get_default_client().gauge(name, value, tags)


def timing(name: str, milliseconds: int | float, tags: dict | None = None) -> None:
    _get_default_client().timing(name, milliseconds, tags)
