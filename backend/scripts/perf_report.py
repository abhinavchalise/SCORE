import argparse
import json
import os
import sys
from pathlib import Path

from backend.scripts.perf_run import percentile

SUMMARY = Path(__file__).resolve().parent / "perf_summary.json"
BASELINE = Path(__file__).resolve().parent / "perf_baseline.json"
REGRESSION_RATIO = 1.2

TARGETS_MS = {
    "nlp.classify": 50.0,
    "nlp.retrieve": 30.0,
    "nlp.render": 30.0,
    "nlp.validate": 20.0,
}
ORDER = [
    "nlp.sanitize",
    "nlp.classify",
    "nlp.retrieve",
    "nlp.render",
    "nlp.llm",
    "nlp.validate",
    "session.e2e",
]


def read_stage_durations(log_path: Path) -> dict[str, list[float]]:
    durations: dict[str, list[float]] = {}
    for line in log_path.read_text().splitlines():
        if not line.strip():
            continue
        entry = json.loads(line)
        durations.setdefault(entry["stage"], []).append(entry["ms"])
    return durations


def print_table(durations: dict[str, list[float]]) -> None:
    print(f"{'stage':<16}{'P50 (ms)':>12}{'P95 (ms)':>12}{'target (ms)':>14}")
    for stage in ORDER:
        values = durations.get(stage)
        if not values:
            continue
        target = TARGETS_MS.get(stage)
        target_text = f"< {target:.0f}" if target else "measured"
        print(
            f"{stage:<16}"
            f"{percentile(values, 0.50):>12.1f}"
            f"{percentile(values, 0.95):>12.1f}"
            f"{target_text:>14}"
        )


def main() -> None:
    parser = argparse.ArgumentParser(description="Summarize logs/latency.jsonl per stage")
    parser.add_argument("--log", default=os.getenv("LATENCY_LOG_PATH", "logs/latency.jsonl"))
    parser.add_argument("--write-baseline", action="store_true")
    args = parser.parse_args()

    log_path = Path(args.log)
    if not log_path.exists():
        sys.exit(f"no latency log at {log_path}; run perf_run.py first")

    durations = read_stage_durations(log_path)
    print_table(durations)

    if SUMMARY.exists():
        summary = json.loads(SUMMARY.read_text())
        print(f"\nfallback rate: {summary['fallback_rate'] * 100:.1f}%")

    end_to_end = durations.get("session.e2e")
    if not end_to_end:
        return
    current_p95 = percentile(end_to_end, 0.95)

    if args.write_baseline:
        BASELINE.write_text(json.dumps({"end_to_end_p95_ms": current_p95}, indent=2))
        print(f"\nbaseline written: end-to-end P95 {current_p95:.0f}ms")
        return

    if BASELINE.exists():
        baseline_p95 = json.loads(BASELINE.read_text())["end_to_end_p95_ms"]
        ceiling = baseline_p95 * REGRESSION_RATIO
        status = "OK" if current_p95 <= ceiling else "REGRESSED"
        print(f"\nend-to-end P95 {current_p95:.0f}ms vs baseline {baseline_p95:.0f}ms [{status}]")
        if current_p95 > ceiling:
            sys.exit(1)


if __name__ == "__main__":
    main()
