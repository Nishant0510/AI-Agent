"""Aggregate p50/p95 latency metrics from structured application JSON logs.

Default input: logs/app.jsonl

Example:
    venv\\Scripts\\python.exe scripts\\aggregate_log_latencies.py
    venv\\Scripts\\python.exe scripts\\aggregate_log_latencies.py --log-path logs\\app.jsonl
"""

from __future__ import annotations

import argparse
import json
import math
from collections import Counter, defaultdict
from pathlib import Path
from typing import Iterable


def percentile(values: list[float], percent: float) -> float | None:
    """Return a linearly interpolated percentile for a non-empty value list."""
    if not values:
        return None

    ordered = sorted(values)
    position = (len(ordered) - 1) * (percent / 100)
    lower = math.floor(position)
    upper = math.ceil(position)

    if lower == upper:
        return ordered[lower]

    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def numeric_values(records: Iterable[dict], field: str) -> list[float]:
    values: list[float] = []
    for record in records:
        value = record.get(field)
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            values.append(float(value))
    return values


def format_metrics(values: list[float]) -> str:
    if not values:
        return "count=0"
    return (
        f"count={len(values)}  "
        f"p50={percentile(values, 50):.2f} ms  "
        f"p95={percentile(values, 95):.2f} ms  "
        f"min={min(values):.2f} ms  "
        f"max={max(values):.2f} ms"
    )


def load_records(log_path: Path) -> tuple[list[dict], int]:
    records: list[dict] = []
    malformed = 0

    with log_path.open(encoding="utf-8") as log_file:
        for line in log_file:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                malformed += 1
                continue
            if isinstance(record, dict):
                records.append(record)
            else:
                malformed += 1

    return records, malformed


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log-path", type=Path, default=Path("logs/app.jsonl"))
    args = parser.parse_args()

    if not args.log_path.is_file():
        print(f"Log file not found: {args.log_path}")
        return 1

    all_records, malformed = load_records(args.log_path)
    requests = [
        record for record in all_records
        if record.get("message") == "request_completed"
    ]

    outcomes = Counter(record.get("outcome", "unknown") for record in requests)
    node_durations: dict[str, list[float]] = defaultdict(list)
    for request in requests:
        for node in request.get("node_trace") or []:
            if not isinstance(node, dict):
                continue
            name = node.get("node", "unknown_node")
            duration = node.get("duration_ms")
            if isinstance(duration, (int, float)) and not isinstance(duration, bool):
                node_durations[str(name)].append(float(duration))

    print(f"Log file: {args.log_path.resolve()}")
    print(f"Parsed records: {len(all_records)} | malformed/skipped: {malformed}")
    print(f"Completed requests: {len(requests)}")
    print(f"Outcomes: {dict(sorted(outcomes.items()))}")
    print()
    print("Request execution time")
    print(format_metrics(numeric_values(requests, "execution_time_ms")))
    print()
    print("LLM latency")
    print(format_metrics(numeric_values(requests, "llm_latency_ms")))
    print()
    print("Node duration")
    if not node_durations:
        print("count=0")
    else:
        for node_name in sorted(node_durations):
            print(f"{node_name}: {format_metrics(node_durations[node_name])}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
