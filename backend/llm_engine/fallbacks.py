from backend.models.schemas import ModulationSchedule, ModulationStep

FALLBACK_SCHEDULES = {
    "focus": ModulationSchedule(
        intent="focus",
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
    "relax": ModulationSchedule(
        intent="relax",
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
    "sleep": ModulationSchedule(
        intent="sleep",
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


def get_fallback_schedule(intent: str, duration_minutes: int = 25) -> ModulationSchedule:
    # Return a safe hardcoded schedule, maps intent keywords to known schedules
    intent_lower = intent.lower()
    for key in FALLBACK_SCHEDULES:
        if key in intent_lower:
            return FALLBACK_SCHEDULES[key]
    return FALLBACK_SCHEDULES["focus"]
