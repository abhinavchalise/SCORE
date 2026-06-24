import pytest

pytest.importorskip("fastapi")

from backend.models.orm import FeedbackEvent, Session
from backend.nlp.pipeline import PipelineResult
from backend.routers import sessions as sessions_module
from backend.routers.sessions import session_ws
from sqlalchemy import func, select


async def _count(db, model, *where):
    result = await db.execute(select(func.count()).select_from(model).where(*where))
    return result.scalar_one()


async def test_full_lifecycle_writes_session_and_completion(db, fake_ws, mocked_llm):
    ws = fake_ws(
        [
            {"intent": "deep_focus", "duration_minutes": 25},
            fake_ws.TICK,
            {"type": "control", "action": "stop"},
        ]
    )

    await session_ws(ws, db)

    types = [message["type"] for message in ws.sent]
    assert types[0] == "schedule"
    assert "tick" in types
    assert types[-1] == "ended"
    assert ws.closed is True

    session = (await db.execute(select(Session))).scalars().one()
    assert session.intent == "deep_focus"
    assert session.ended_at is not None
    assert await _count(db, FeedbackEvent, FeedbackEvent.kind == "completion") == 1


async def test_fallback_path_emits_fallback(db, fake_ws, schedule, monkeypatch):
    async def fallback_pipeline(intent, db, duration_minutes=25):
        return PipelineResult(
            schedule=schedule,
            intent="deep_focus",
            confidence=0.4,
            used_fallback=True,
            prompt_version_id=0,
            latency_breakdown_ms={},
        )

    monkeypatch.setattr(sessions_module, "run_pipeline", fallback_pipeline)
    ws = fake_ws(
        [
            {"intent": "deep_focus", "duration_minutes": 25},
            {"type": "control", "action": "stop"},
        ]
    )

    await session_ws(ws, db)

    assert ws.sent[0]["type"] == "fallback"
    assert ws.sent[-1]["type"] == "ended"
