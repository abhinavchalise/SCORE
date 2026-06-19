SCHEDULE_PROMPT_TEMPLATE = """You are a binaural-beat schedule generator. Given a user's session intent, produce a modulation schedule as a JSON object.

The user's intent is: "{intent}"
Requested session duration: {duration_minutes} minutes.

You must output ONLY a valid JSON object (no markdown, no explanation outside the JSON) with this exact structure:

{{
  "intent": "{intent}",
  "total_duration_sec": {duration_sec},
  "steps": [
    {{
      "timestamp_sec": 0,
      "target_bpm": <int 40-200>,
      "binaural_freq": <float 0.5-40.0 Hz>,
      "ramp_duration_sec": <float>,
      "layer": "binaural"
    }}
  ]
}}

Rules for generating steps:
- Create 3-6 steps that form a natural progression for the intent
- For "focus" or "coding" intents: start with alpha (8-12 Hz), transition to beta (12-30 Hz), wind down
- For "relax" or "meditation" intents: transition from alpha (8-12 Hz) down to theta (4-8 Hz)
- For "sleep" intents: progress from theta (4-8 Hz) to delta (0.5-4 Hz)
- Each step's timestamp_sec must be greater than the previous
- The last step's timestamp_sec + ramp_duration_sec should approximately equal total_duration_sec
- target_bpm represents isochronic pulse rate; typical range 60-80 for calm, 80-120 for focus

Output ONLY the JSON object. No other text."""


def build_schedule_prompt(intent: str, duration_minutes: int = 25) -> str:
    duration_sec = duration_minutes * 60
    return SCHEDULE_PROMPT_TEMPLATE.format(
        intent=intent,
        duration_minutes=duration_minutes,
        duration_sec=duration_sec,
    )
