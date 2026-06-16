from __future__ import annotations

import os
from dataclasses import dataclass


@dataclass
class MetricsConfig:
    host: str
    port: int
    prefix: str
    env: str
    enabled: bool


def from_env() -> MetricsConfig:
    return MetricsConfig(
        host=os.getenv("STATSD_HOST", "localhost"),
        port=int(os.getenv("STATSD_PORT", "9125")),
        prefix=os.getenv("METRICS_PREFIX", "stocker"),
        env=os.getenv("METRICS_ENV", "dev"),
        enabled=os.getenv("METRICS_ENABLED", "true").lower() not in ("false", "0", "no"),
    )
