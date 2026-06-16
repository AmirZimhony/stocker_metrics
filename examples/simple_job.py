"""
Example: using stocker-metrics in a data pipeline job.

Run with:
    METRICS_ENV=prod STATSD_HOST=statsd-exporter python examples/simple_job.py
"""

import time

from stocker_metrics import gauge, incr, timer


def scrape_nasdaq() -> list[dict]:
    time.sleep(0.05)  # simulate network I/O
    return [{"ticker": "AAPL"}, {"ticker": "MSFT"}]


def main() -> None:
    pipeline = "nasdaq"

    incr("pipeline.run_started", tags={"pipeline": pipeline})

    try:
        with timer("pipeline.duration_ms", tags={"pipeline": pipeline}):
            rows = scrape_nasdaq()
            gauge("pipeline.rows_fetched", len(rows), tags={"pipeline": pipeline})

        incr("pipeline.run_success", tags={"pipeline": pipeline})

    except Exception as exc:
        incr("pipeline.run_failed", tags={"pipeline": pipeline})
        raise


if __name__ == "__main__":
    main()
    print("Done.")
