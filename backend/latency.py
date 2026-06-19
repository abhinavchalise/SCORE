import json
import os
import time
from collections import defaultdict
from contextlib import contextmanager
from pathlib import Path

_durations = defaultdict(list)
_counts = defaultdict(int)
_log_path = Path(os.getenv("LATENCY_LOG_PATH", "./logs/latency.jsonl"))
_log_path.parent.mkdir(parents=True, exist_ok=True)


@contextmanager
def stage(name: str, **labels):
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        _durations[name].append(elapsed_ms)
        with _log_path.open("a") as f:
            f.write(json.dumps({"stage": name, "ms": elapsed_ms, **labels}) + "\n")


def counter(name: str, by: int = 1):
    _counts[name] += by


def durations(name: str) -> list[float]:
    return list(_durations[name])
