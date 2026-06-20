from backend.models.schemas import ModulationSchedule, ModulationStep

FALLBACK_SCHEDULES = {
    "deep_focus": ModulationSchedule(
        intent="deep_focus",
        total_duration_sec=1500,
        steps=[
            ModulationStep(
                timestamp_sec=0,
                target_bpm=70,
                binaural_freq=10.0,
                ramp_duration_sec=60,
                layer="binaural",
            ),
            ModulationStep(
                timestamp_sec=300,
                target_bpm=80,
                binaural_freq=14.0,
                ramp_duration_sec=120,
                layer="binaural",
            ),
            ModulationStep(
                timestamp_sec=900,
                target_bpm=75,
                binaural_freq=12.0,
                ramp_duration_sec=180,
                layer="binaural",
            ),
            ModulationStep(
                timestamp_sec=1350,
                target_bpm=65,
                binaural_freq=8.0,
                ramp_duration_sec=150,
                layer="binaural",
            ),
        ],
    ),
    "calm": ModulationSchedule(
        intent="calm",
        total_duration_sec=1500,
        steps=[
            ModulationStep(
                timestamp_sec=0,
                target_bpm=70,
                binaural_freq=10.0,
                ramp_duration_sec=60,
                layer="binaural",
            ),
            ModulationStep(
                timestamp_sec=300,
                target_bpm=60,
                binaural_freq=7.0,
                ramp_duration_sec=180,
                layer="binaural",
            ),
            ModulationStep(
                timestamp_sec=900,
                target_bpm=55,
                binaural_freq=5.0,
                ramp_duration_sec=300,
                layer="binaural",
            ),
            ModulationStep(
                timestamp_sec=1350,
                target_bpm=50,
                binaural_freq=4.0,
                ramp_duration_sec=150,
                layer="binaural",
            ),
        ],
    ),
    "sleep_aid": ModulationSchedule(
        intent="sleep_aid",
        total_duration_sec=1500,
        steps=[
            ModulationStep(
                timestamp_sec=0,
                target_bpm=60,
                binaural_freq=6.0,
                ramp_duration_sec=60,
                layer="binaural",
            ),
            ModulationStep(
                timestamp_sec=300,
                target_bpm=55,
                binaural_freq=4.0,
                ramp_duration_sec=180,
                layer="binaural",
            ),
            ModulationStep(
                timestamp_sec=900,
                target_bpm=50,
                binaural_freq=2.0,
                ramp_duration_sec=300,
                layer="binaural",
            ),
            ModulationStep(
                timestamp_sec=1350,
                target_bpm=45,
                binaural_freq=1.0,
                ramp_duration_sec=150,
                layer="binaural",
            ),
        ],
    ),
}

INTENT_FALLBACKS = {
    "deep_focus": "deep_focus",
    "light_focus": "deep_focus",
    "creative_flow": "deep_focus",
    "calm": "calm",
    "sleep_aid": "sleep_aid",
    "custom": "deep_focus",
}


def get_fallback_schedule(intent: str, duration_minutes: int = 25) -> ModulationSchedule:
    key = INTENT_FALLBACKS.get(intent, "deep_focus")
    return FALLBACK_SCHEDULES[key].model_copy(update={"intent": intent})
