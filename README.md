# stocker-metrics

A tiny, dependency-free Python package that emits custom metrics over UDP to a StatsD exporter, which Prometheus/Grafana then scrapes.

## Installation

```bash
pip install git+https://github.com/<user>/stocker-metrics.git@v0.1.0
```

## Configuration

All config is read from environment variables at import time (or when the first metric is emitted).

| Variable          | Default       | Description                              |
|-------------------|---------------|------------------------------------------|
| `STATSD_HOST`     | `localhost`   | StatsD exporter host                     |
| `STATSD_PORT`     | `9125`        | StatsD exporter UDP port                 |
| `METRICS_PREFIX`  | `stocker`     | Prefix prepended to every metric name    |
| `METRICS_ENV`     | `dev`         | Value for the automatic `env` tag        |
| `METRICS_ENABLED` | `true`        | Set to `false`/`0`/`no` to disable all metrics |

## Usage

```python
from stocker_metrics import incr, gauge, timer

def main():
    incr("pipeline.run_started", tags={"pipeline": "nasdaq"})

    with timer("pipeline.duration_ms", tags={"pipeline": "nasdaq"}):
        rows = scrape()
        gauge("pipeline.rows_fetched", len(rows), tags={"pipeline": "nasdaq"})

    incr("pipeline.run_success", tags={"pipeline": "nasdaq"})
```

`timer` also works as a decorator:

```python
from stocker_metrics import timer

@timer("pipeline.duration_ms", tags={"pipeline": "nasdaq"})
def run_job():
    ...
```

## Wire format

Metrics are emitted in DogStatsD format over UDP:

```
stocker.pipeline.run_started:1|c|#env=prod,pipeline=nasdaq
stocker.pipeline.rows_fetched:42|g|#env=prod,pipeline=nasdaq
stocker.pipeline.duration_ms:123.4|ms|#env=prod,pipeline=nasdaq
```

The `env` tag is always injected automatically from `METRICS_ENV`.

## Fail-silent behaviour

Metrics will **never** crash your job. If the StatsD host is unreachable or any socket error occurs, the error is silently swallowed. Set `METRICS_ENABLED=false` to disable all metric emission entirely (useful in unit tests).

## Docker networking note

Inside a Docker container, `localhost` refers to the container itself — not the host or a sidecar. When running jobs in a Docker network alongside a `statsd-exporter` container, set `STATSD_HOST` to the service/container name:

```yaml
# docker-compose.yml excerpt
services:
  my-job:
    environment:
      STATSD_HOST: statsd-exporter
  statsd-exporter:
    image: prom/statsd-exporter
```

## Development

```bash
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
pytest
```
