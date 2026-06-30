import asyncio
import json
import os
import subprocess
import time
from pathlib import Path

import torch
from pydantic import ValidationError

from backend.config import settings
from backend.llm_engine.client import llm_engine
from backend.models.schemas import ModulationSchedule
from backend.nlp.validators import clamp_schedule, validate_schedule

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


def _peak_gpu_mb() -> float | None:
    try:
        out = subprocess.check_output(
            [
                "nvidia-smi",
                "--query-compute-apps=pid,used_memory",
                "--format=csv,noheader,nounits",
            ],
            text=True,
        )
    except Exception:
        return None
    pid = str(os.getpid())
    for line in out.splitlines():
        parts = [part.strip() for part in line.split(",")]
        if len(parts) == 2 and parts[0] == pid:
            return float(parts[1])
    return None


async def _run() -> list[dict]:
    await llm_engine.load()
    runs = []
    for intent in _load_intents():
        prompt = f"{INSTRUCTION} {intent}"
        start = time.perf_counter()
        raw = await llm_engine.generate_constrained(prompt)
        latency_sec = time.perf_counter() - start
        raw_valid = _revalidates(raw)
        delivered_valid, _, _ = validate_schedule(clamp_schedule(raw))
        runs.append(
            {
                "intent": intent,
                "latency_sec": latency_sec,
                "raw_valid": raw_valid,
                "delivered_valid": delivered_valid,
            }
        )
    return runs


def main() -> None:
    runs = asyncio.run(_run())
    latencies = [run["latency_sec"] for run in runs]
    raw_rate = sum(run["raw_valid"] for run in runs) / len(runs)
    delivered_rate = sum(run["delivered_valid"] for run in runs) / len(runs)

    peak_mb = _peak_gpu_mb()
    if peak_mb is None and torch.cuda.is_available():
        peak_mb = torch.cuda.max_memory_allocated() / 1024 / 1024
    is_gguf = settings.llm_backend == "llamacpp"

    report = {
        "llm_backend": settings.llm_backend,
        "model": Path(settings.gguf_model_path).name if is_gguf else settings.hf_model_id,
        "quant": settings.gguf_quant if is_gguf else settings.quantization,
        "count": len(runs),
        "raw_schema_validity_rate": raw_rate,
        "delivered_schema_validity_rate": delivered_rate,
        "full_gen_p50_sec": _percentile(latencies, 0.50),
        "full_gen_p95_sec": _percentile(latencies, 0.95),
        "peak_gpu_mb": peak_mb,
        "ttft": "not measured; full-generation latency only",
        "runs": runs,
    }
    REPORT.write_text(json.dumps(report, indent=2))

    peak_str = f"{peak_mb:.0f}MB" if peak_mb is not None else "n/a (cpu)"
    print(
        f"{settings.llm_backend} | raw {raw_rate * 100:.1f}% | "
        f"delivered {delivered_rate * 100:.1f}% | "
        f"full-gen P50 {report['full_gen_p50_sec']:.2f}s | peak {peak_str}"
    )


if __name__ == "__main__":
    main()
