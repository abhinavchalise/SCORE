from backend.models.schemas import INTENTS
from backend.nlp.fallback import fallback_for
from backend.nlp.validators import validate_schedule


def test_fallback_for_every_intent_is_valid():
    for intent in INTENTS:
        schedule = fallback_for(intent, 1500)
        ok, _, reason = validate_schedule(schedule.model_dump())
        assert ok, f"{intent} fallback invalid: {reason}"
        assert schedule.intent == intent
        assert schedule.total_duration_sec == 1500
