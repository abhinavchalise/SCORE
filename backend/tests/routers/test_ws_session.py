import pytest

pytest.importorskip("fastapi")

from fastapi import WebSocketDisconnect
from sqlalchemy import func, select

from backend.models.orm import ExampleBankEntry, FeedbackEvent
from backend.nlp import example_bank
from backend.nlp.pipeline import PipelineResult
from backend.routers import sessions as sessions_module
from backend.routers.sessions import session_ws
from backend.session_state import SessionState

_SCHEDULE = {
    "intent": "deep_focus",
    "total_duration_sec": 1500,
    "steps": [
        {
            "timestamp_sec": 0,
            "target_bpm": 70,
            "binaural_freq": 10.0,
            "ramp_duration_sec": 60,
            "layer": "binaural",
        }
    ],
}


class FakeWebSocket:
    def __init__(self, incoming):
        self._incoming = list(incoming)
        self.sent = []
        self.accepted = False
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def receive_json(self):
        if not self._incoming:
            raise WebSocketDisconnect()
        return self._incoming.pop(0)

    async def send_json(self, data):
        self.sent.append(data)

    async def close(self):
        self.closed = True


@pytest.fixture
def stub_pipeline(monkeypatch):
    async def fake_run_pipeline(intent, db, duration_minutes=25):
        return PipelineResult(
            schedule=_SCHEDULE,
            intent="deep_focus",
            confidence=0.9,
            used_fallback=False,
            prompt_version_id=0,
            latency_breakdown_ms={},
        )

    monkeypatch.setattr(sessions_module, "run_pipeline", fake_run_pipeline)


async def _completion_row_count(db) -> int:
    result = await db.execute(
        select(func.count()).select_from(FeedbackEvent).where(FeedbackEvent.kind == "completion")
    )
    return result.scalar_one()


async def test_ws_runs_lifecycle_and_writes_completion(db, stub_pipeline):
    ws = FakeWebSocket(
        [
            {"type": "start", "intent": "deep_focus", "duration_minutes": 25},
            {"type": "control", "action": "stop"},
        ]
    )

    await session_ws(ws, db)

    types = [message["type"] for message in ws.sent]
    assert types[0] == "schedule"
    assert types[-1] == "ended"
    assert ws.closed is True
    assert await _completion_row_count(db) == 1


async def test_ws_disconnect_still_writes_completion(db, stub_pipeline):
    ws = FakeWebSocket([{"type": "start", "intent": "deep_focus", "duration_minutes": 25}])

    await session_ws(ws, db)

    assert ws.sent[0]["type"] == "schedule"
    assert all(message["type"] != "ended" for message in ws.sent)
    assert await _completion_row_count(db) == 1


async def _example_bank_count(db) -> int:
    result = await db.execute(select(func.count()).select_from(ExampleBankEntry))
    return result.scalar_one()


async def test_ws_qualifying_session_inserts_example(db, stub_pipeline, monkeypatch):
    monkeypatch.setattr(example_bank, "embed_text", lambda text: [0.1, 0.2, 0.3])
    monkeypatch.setattr(SessionState, "completion_pct", lambda self: 90.0)

    ws = FakeWebSocket(
        [
            {"intent": "deep focus please", "duration_minutes": 25},
            {"type": "control", "action": "stop"},
            {"type": "feedback", "kind": "rating", "payload": {"value": 5}},
        ]
    )

    await session_ws(ws, db)

    assert ws.sent[-1]["type"] == "ended"
    assert await _example_bank_count(db) == 1


async def test_ws_edited_session_skips_example(db, stub_pipeline, monkeypatch):
    monkeypatch.setattr(example_bank, "embed_text", lambda text: [0.1, 0.2, 0.3])
    monkeypatch.setattr(SessionState, "completion_pct", lambda self: 90.0)

    ws = FakeWebSocket(
        [
            {"intent": "deep focus please", "duration_minutes": 25},
            {"type": "feedback", "kind": "edit", "payload": {"field": "binaural_freq"}},
            {"type": "control", "action": "stop"},
            {"type": "feedback", "kind": "rating", "payload": {"value": 5}},
        ]
    )

    await session_ws(ws, db)

    assert await _example_bank_count(db) == 0
