import pytest

pytest.importorskip("torch")
pytest.importorskip("transformers")

from backend.llm_engine.client import LLMEngine
from backend.models.schemas import ModulationSchedule, ModulationStep

_VALID_SCHEDULE = ModulationSchedule(
    intent="deep_focus",
    total_duration_sec=1500,
    steps=[
        ModulationStep(
            timestamp_sec=0,
            target_bpm=70,
            binaural_freq=10.0,
            ramp_duration_sec=60,
            layer="binaural",
        )
    ],
)


async def test_generate_constrained_returns_validatable_dict():
    engine = LLMEngine()
    engine._constrained_generator = lambda prompt, max_tokens=None: _VALID_SCHEDULE.model_dump_json()

    result = await engine.generate_constrained("help me focus deeply")

    assert isinstance(result, dict)
    ModulationSchedule(**result)
