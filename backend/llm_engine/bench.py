import asyncio
import json
import time
from pathlib import Path

import torch
from pydantic import ValidationError

from backend.llm_engine.client import llm_engine
from backend.models.schemas import ModulationSchedule

FIXTURE = Path(__file__).resolve().parents[1] / "tests" / "nlp" / "fixtures" / "intent_seed.jsonl"
REPORT = Path(__file__).resolve().parent / "bench_report.json"
BENCH_SIZE = 50
INSTRUCTION = "Generate a binaural-beat modulation schedule for this focus session intent:"


def _percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    rank = (len(ordered) - 1) * pct
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def _load_intents() -> list[str]:
    lines = FIXTURE.read_text().splitlines()[:BENCH_SIZE]
    return [json.loads(line)["text"] for line in lines]


def _revalidates(schedule: dict) -> bool:
    try:
        ModulationSchedule(**schedule)
        return True
    except ValidationError:
        return False


async def _run() -> list[dict]:
    await llm_engine.load()
    runs = []
    for intent in _load_intents():
        prompt = f"{INSTRUCTION} {intent}"
        start = time.perf_counter()
        schedule = await llm_engine.generate_constrained(prompt)
        latency_sec = time.perf_counter() - start
        runs.append({"intent": intent, "latency_sec": latency_sec, "valid": _revalidates(schedule)})
    return runs


def main() -> None:
    runs = asyncio.run(_run())
    latencies = [run["latency_sec"] for run in runs]
    validity_rate = sum(run["valid"] for run in runs) / len(runs)
    peak_mb = torch.cuda.max_memory_allocated() / 1024 / 1024 if torch.cuda.is_available() else None

    report = {
        "count": len(runs),
        "schema_validity_rate": validity_rate,
        "full_gen_p50_sec": _percentile(latencies, 0.50),
        "full_gen_p95_sec": _percentile(latencies, 0.95),
        "peak_gpu_mb": peak_mb,
        "ttft": "not measured; full-generation latency only",
        "runs": runs,
    }
    REPORT.write_text(json.dumps(report, indent=2))

    peak_str = f"{peak_mb:.0f}MB" if peak_mb is not None else "n/a (cpu)"
    print(
        f"validity {validity_rate * 100:.1f}% | "
        f"full-gen P50 {report['full_gen_p50_sec']:.2f}s | "
        f"peak {peak_str}"
    )


if __name__ == "__main__":
    main()
