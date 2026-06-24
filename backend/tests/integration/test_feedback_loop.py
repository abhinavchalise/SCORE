import pytest

pytest.importorskip("fastapi")

from backend.models.orm import ExampleBankEntry
from backend.nlp import example_bank
from backend.nlp.example_bank import fetch_examples
from backend.routers.sessions import session_ws
from backend.session_state import SessionState
from sqlalchemy import func, select


async def _example_count(db):
    result = await db.execute(select(func.count()).select_from(ExampleBankEntry))
    return result.scalar_one()


@pytest.fixture
def high_completion(monkeypatch):
    monkeypatch.setattr(SessionState, "completion_pct", lambda self: 90.0)


@pytest.fixture
def stub_embed(monkeypatch):
    monkeypatch.setattr(example_bank, "embed_text", lambda text: [0.1, 0.2, 0.3])


async def test_qualifying_session_stores_and_is_retrievable(
    db, fake_ws, schedule, mocked_llm, high_completion, stub_embed
):
    ws = fake_ws(
        [
            {"intent": "deep focus please", "duration_minutes": 25},
            {"type": "control", "action": "stop"},
            {"type": "feedback", "kind": "rating", "payload": {"value": 5}},
        ]
    )

    await session_ws(ws, db)

    assert await _example_count(db) == 1
    assert await fetch_examples(db, "deep_focus") == [schedule]


async def test_edited_session_skips_store(db, fake_ws, mocked_llm, high_completion, stub_embed):
    ws = fake_ws(
        [
            {"intent": "deep focus please", "duration_minutes": 25},
            {"type": "feedback", "kind": "edit", "payload": {"field": "binaural_freq"}},
            {"type": "control", "action": "stop"},
            {"type": "feedback", "kind": "rating", "payload": {"value": 5}},
        ]
    )

    await session_ws(ws, db)

    assert await _example_count(db) == 0


async def test_low_rating_skips_store(db, fake_ws, mocked_llm, high_completion, stub_embed):
    ws = fake_ws(
        [
            {"intent": "deep focus please", "duration_minutes": 25},
            {"type": "control", "action": "stop"},
            {"type": "feedback", "kind": "rating", "payload": {"value": 3}},
        ]
    )

    await session_ws(ws, db)

    assert await _example_count(db) == 0
