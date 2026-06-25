import argparse
import asyncio
import datetime as dt
import json
from pathlib import Path

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from backend.config import settings
from backend.latency import durations, stage
from backend.llm_engine.client import llm_engine
from backend.models.orm import Base
from backend.models.schemas import INTENTS
from backend.nlp.example_bank import store_example
from backend.nlp.pipeline import run_pipeline

FIXTURES = Path(__file__).resolve().parents[1] / "tests" / "replay" / "fixtures" / "eval_50.jsonl"
SUMMARY = Path(__file__).resolve().parent / "perf_summary.json"

PROMPTS = {
    "deep_focus": "I need to lock in for deep focus work",
    "light_focus": "light background focus while reading",
    "creative_flow": "help me get into a creative flow state",
    "calm": "wind down and feel calm before bed",
    "sleep_aid": "help me fall asleep gently",
    "custom": "something for a long late-night study marathon",
}


def percentile(values: list[float], pct: float) -> float:
    ordered = sorted(values)
    rank = (len(ordered) - 1) * pct
    lower = int(rank)
    upper = min(lower + 1, len(ordered) - 1)
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def load_fixtures() -> list[dict]:
    return [json.loads(line) for line in FIXTURES.read_text().splitlines() if line.strip()]


async def build_session_factory() -> tuple:
    engine = create_async_engine(
        "sqlite+aiosqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    return engine, async_sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def seed_example_bank(db: AsyncSession, fixtures: list[dict]) -> None:
    seeded: set[str] = set()
    for case in fixtures:
        intent = case["intent"]
        if intent in seeded:
            continue
        seeded.add(intent)
        await store_example(
            db,
            intent=intent,
            schedule_json=case["schedule"],
            rating=5,
            completion_pct=90.0,
            text=case.get("intent_text", intent),
        )


async def run_sessions(session_factory, sessions: int) -> dict:
    async with session_factory() as db:
        await seed_example_bank(db, load_fixtures())

    end_to_end_ms: list[float] = []
    per_stage_ms: dict[str, list[float]] = {}
    fallback_count = 0
    for index in range(sessions):
        intent = INTENTS[index % len(INTENTS)]
        async with session_factory() as db:
            with stage("session.e2e"):
                result = await run_pipeline(PROMPTS[intent], db, duration_minutes=25)
        end_to_end_ms.append(durations("session.e2e")[-1])
        for name, value in result.latency_breakdown_ms.items():
            per_stage_ms.setdefault(name, []).append(value)
        if result.used_fallback:
            fallback_count += 1

    return {
        "sessions": sessions,
        "fallback_count": fallback_count,
        "fallback_rate": fallback_count / sessions if sessions else 0.0,
        "end_to_end_p50_ms": percentile(end_to_end_ms, 0.50),
        "end_to_end_p95_ms": percentile(end_to_end_ms, 0.95),
        "stages": per_stage_ms,
    }


async def run_load(sessions: int) -> dict:
    await llm_engine.load()
    engine, session_factory = await build_session_factory()
    try:
        return await run_sessions(session_factory, sessions)
    finally:
        await engine.dispose()


def write_summary(metrics: dict) -> None:
    SUMMARY.write_text(
        json.dumps(
            {
                "generated_at": dt.datetime.now(dt.timezone.utc).isoformat(),
                "model_id": settings.hf_model_id,
                "quantization": settings.quantization,
                "sessions": metrics["sessions"],
                "fallback_rate": metrics["fallback_rate"],
                "end_to_end_p50_ms": metrics["end_to_end_p50_ms"],
                "end_to_end_p95_ms": metrics["end_to_end_p95_ms"],
            },
            indent=2,
        )
    )


def main() -> None:
    parser = argparse.ArgumentParser(description="SCORE Step 10 latency load driver")
    parser.add_argument("--sessions", type=int, default=100)
    args = parser.parse_args()

    metrics = asyncio.run(run_load(args.sessions))
    write_summary(metrics)
    print(
        f"{metrics['sessions']} sessions | "
        f"end-to-end P50 {metrics['end_to_end_p50_ms']:.0f}ms "
        f"P95 {metrics['end_to_end_p95_ms']:.0f}ms | "
        f"fallback {metrics['fallback_rate'] * 100:.1f}%"
    )


if __name__ == "__main__":
    main()
