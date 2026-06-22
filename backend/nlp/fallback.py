from backend.llm_engine.fallbacks import get_fallback_schedule
from backend.models.schemas import ModulationSchedule


def fallback_for(intent: str) -> ModulationSchedule:
    return get_fallback_schedule(intent)
