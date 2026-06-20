import time

from backend.db.queries import (
    activate_prompt_version,
    active_prompt_version,
    append_feedback,
    create_session,
    create_user,
    fallback_rate,
    fetch_example_bank,
    get_user_by_email,
    insert_example,
    insert_prompt_version,
    session_completion_rate,
)
from backend.models.orm import ExampleBankEntry
from backend.models.schemas import ExampleBankEntryCreate, PromptVersionCreate


async def test_create_user(db):
    user = await create_user(db, "a@b.com", "alice", "hashed")
    assert user.id is not None
    assert await get_user_by_email(db, "a@b.com") is not None


async def test_create_session_defaults_fallback_false(db):
    session = await create_session(db, intent="deep_focus", schedule="{}", duration_sec=1500)
    assert session.id is not None
    assert session.used_fallback is False


async def test_append_feedback(db):
    session = await create_session(db, intent="deep_focus", schedule="{}", duration_sec=1500)
    event = await append_feedback(db, session.id, "rating", {"value": 5})
    assert event.id is not None
    assert event.kind == "rating"
    assert event.payload == {"value": 5}


async def test_insert_and_fetch_example_bank_filters_by_quality(db):
    await insert_example(
        db,
        ExampleBankEntryCreate(
            intent="deep_focus",
            schedule_json={"steps": []},
            rating=5,
            completion_pct=95.0,
            embedding=[0.1, 0.2],
        ),
    )
    await insert_example(
        db,
        ExampleBankEntryCreate(
            intent="deep_focus",
            schedule_json={"steps": []},
            rating=2,
            completion_pct=95.0,
            embedding=[0.1, 0.2],
        ),
    )
    await insert_example(
        db,
        ExampleBankEntryCreate(
            intent="calm",
            schedule_json={"steps": []},
            rating=5,
            completion_pct=95.0,
            embedding=[0.1, 0.2],
        ),
    )

    results = await fetch_example_bank(db, "deep_focus", k=5)
    assert len(results) == 1
    assert results[0].rating == 5


async def test_fetch_example_bank_respects_k(db):
    for i in range(5):
        await insert_example(
            db,
            ExampleBankEntryCreate(
                intent="calm",
                schedule_json={"i": i},
                rating=5,
                completion_pct=90.0,
                embedding=[float(i)],
            ),
        )
    results = await fetch_example_bank(db, "calm", k=3)
    assert len(results) == 3


async def test_prompt_version_active_returns_active(db):
    version = await insert_prompt_version(
        db, PromptVersionCreate(intent="deep_focus", template="v1", active=True)
    )
    assert version.hash
    active = await active_prompt_version(db, "deep_focus")
    assert active is not None
    assert active.id == version.id


async def test_prompt_version_activate_switches_active(db):
    v1 = await insert_prompt_version(
        db, PromptVersionCreate(intent="calm", template="v1", active=True)
    )
    v2 = await insert_prompt_version(
        db, PromptVersionCreate(intent="calm", template="v2", active=False)
    )
    await activate_prompt_version(db, v2.id)

    active = await active_prompt_version(db, "calm")
    assert active.id == v2.id
    refreshed_v1 = await db.get(type(v1), v1.id)
    assert refreshed_v1.active is False


async def test_session_completion_rate_averages_completion_events(db):
    s1 = await create_session(db, intent="deep_focus", schedule="{}", duration_sec=1500)
    s2 = await create_session(db, intent="deep_focus", schedule="{}", duration_sec=1500)
    await append_feedback(db, s1.id, "completion", {"pct": 80.0})
    await append_feedback(db, s2.id, "completion", {"pct": 100.0})

    rate = await session_completion_rate(db, "deep_focus")
    assert rate == 90.0


async def test_fallback_rate_counts_fallback_sessions(db):
    await create_session(db, intent="calm", schedule="{}", duration_sec=600)
    fallback_session = await create_session(db, intent="calm", schedule="{}", duration_sec=600)
    fallback_session.used_fallback = True
    await db.commit()

    rate = await fallback_rate(db)
    assert rate == 0.5


async def test_example_bank_fetch_under_50ms_at_10k_rows(db):
    db.add_all(
        ExampleBankEntry(
            intent="deep_focus",
            schedule_json={"i": i},
            rating=5,
            completion_pct=90.0,
            embedding=[float(i)],
        )
        for i in range(10_000)
    )
    await db.commit()

    start = time.perf_counter()
    results = await fetch_example_bank(db, "deep_focus", k=3)
    elapsed_ms = (time.perf_counter() - start) * 1000

    assert len(results) == 3
    assert elapsed_ms < 50
