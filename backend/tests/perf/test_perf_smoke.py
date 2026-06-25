import pytest

pytest.importorskip("torch")
pytest.importorskip("sentence_transformers")


async def test_non_llm_stage_budgets_hold(monkeypatch):
    from backend.nlp import pipeline
    from backend.scripts.perf_run import (
        build_session_factory,
        load_fixtures,
        percentile,
        run_sessions,
    )

    schedule = load_fixtures()[0]["schedule"]

    async def fake_call_llm(_prompt):
        return schedule

    monkeypatch.setattr(pipeline, "_call_llm", fake_call_llm)

    engine, session_factory = await build_session_factory()
    try:
        metrics = await run_sessions(session_factory, 10)
    finally:
        await engine.dispose()

    assert metrics["sessions"] == 10
    assert metrics["fallback_rate"] == 0.0

    stages = metrics["stages"]
    for name in ("nlp.sanitize", "nlp.classify", "nlp.retrieve", "nlp.render", "nlp.validate"):
        assert stages[name], f"stage {name} not recorded"

    assert percentile(stages["nlp.classify"], 0.50) < 50.0
    assert percentile(stages["nlp.retrieve"], 0.50) + percentile(stages["nlp.render"], 0.50) < 30.0
    assert percentile(stages["nlp.validate"], 0.50) < 20.0
