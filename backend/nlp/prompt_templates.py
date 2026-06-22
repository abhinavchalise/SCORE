import hashlib
import json
from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.queries import active_prompt_version, insert_prompt_version
from backend.models.schemas import INTENTS, PromptVersionCreate

_INTENT_GUIDANCE = {
    "deep_focus": "Sustained beta (12-30 Hz) for intense concentration.",
    "light_focus": "Gentle beta with alpha rests for lighter, sustainable focus.",
    "creative_flow": "Alpha-theta blend (6-12 Hz) to encourage associative thinking.",
    "calm": "Descend from alpha to theta (4-8 Hz) to settle arousal.",
    "sleep_aid": "Progress from theta down to delta (0.5-4 Hz) for sleep onset.",
    "custom": "Infer a safe, smooth progression; default to gentle alpha if unclear.",
}

_TEMPLATE = """You are a binaural-beat schedule generator. Produce a modulation schedule as JSON.

Intent: {intent}
Guidance: {guidance}
{duration_hint}

Reference schedules that worked well for this intent:
{examples_block}

User request: "{user_input}"

Output ONLY a JSON object with this shape (no prose, no markdown):
{
  "intent": "{intent}",
  "total_duration_sec": <int 60-7200>,
  "steps": [
    {
      "timestamp_sec": <float>,
      "target_bpm": <int 40-200>,
      "binaural_freq": <float 0.5-40.0>,
      "ramp_duration_sec": <float 0-300>,
      "layer": "binaural"
    }
  ]
}

Rules:
- 1 to 20 steps, timestamps strictly increasing.
- No parameter may change by more than 20% of its range per second.
- Output only the JSON object."""


@dataclass(frozen=True)
class PromptTemplate:
    intent: str
    template: str
    hash: str


def _build(intent: str) -> PromptTemplate:
    template = _TEMPLATE.replace("{guidance}", _INTENT_GUIDANCE[intent])
    return PromptTemplate(
        intent=intent,
        template=template,
        hash=hashlib.sha256(template.encode()).hexdigest(),
    )


TEMPLATES: dict[str, PromptTemplate] = {intent: _build(intent) for intent in INTENTS}


def get_template(intent: str) -> PromptTemplate:
    return TEMPLATES.get(intent, TEMPLATES["custom"])


def _format_examples(examples: list[dict]) -> str:
    if not examples:
        return "(no prior examples available)"
    return "\n".join(
        f"[EXAMPLE {position}]: {json.dumps(example)}"
        for position, example in enumerate(examples, start=1)
    )


async def render_prompt(
    intent: str,
    user_input: str,
    examples: list[dict],
    db: AsyncSession,
    duration_sec: int = 1800,
):
    template = get_template(intent)
    prompt = (
        template.template.replace("{intent}", intent)
        .replace("{duration_hint}", f"Target total duration: {duration_sec} seconds.")
        .replace("{examples_block}", _format_examples(examples))
        .replace("{user_input}", user_input)
    )

    version = await active_prompt_version(db, intent)
    if version is None:
        version = await insert_prompt_version(
            db,
            PromptVersionCreate(intent=intent, template=template.template, active=True),
        )
    return prompt, version
