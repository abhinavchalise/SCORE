from dataclasses import dataclass

from sqlalchemy.ext.asyncio import AsyncSession

from backend.latency import counter, durations, stage
from backend.nlp.example_bank import fetch_examples
from backend.nlp.fallback import fallback_for
from backend.nlp.intent_classifier import classify
from backend.nlp.prompt_templates import render_prompt
from backend.nlp.sanitize import sanitize
from backend.nlp.validators import validate_schedule

_STAGES = (
    "nlp.sanitize",
    "nlp.classify",
    "nlp.retrieve",
    "nlp.render",
    "nlp.llm",
    "nlp.validate",
)


@dataclass
class PipelineResult:
    schedule: dict
    intent: str
    confidence: float
    used_fallback: bool
    prompt_version_id: int
    latency_breakdown_ms: dict[str, float]


async def _call_llm(prompt: str) -> dict:
    # Lazy import so the pipeline loads without the LLM stack.
    from backend.llm_engine.client import llm_engine

    return await llm_engine.generate_constrained(prompt)


async def run_pipeline(
    raw_input: str, db: AsyncSession, duration_minutes: int = 25
) -> PipelineResult:
    duration_sec = duration_minutes * 60
    with stage("nlp.sanitize"):
        text = sanitize(raw_input)
    with stage("nlp.classify"):
        intent, confidence = classify(text)

    schedule = None
    version_id = 0
    used_fallback = False
    try:
        with stage("nlp.retrieve"):
            examples = await fetch_examples(db, intent, k=3)
        with stage("nlp.render"):
            prompt, version = await render_prompt(
                intent, text, examples, db, duration_sec=duration_sec
            )
            version_id = version.id
        with stage("nlp.llm"):
            raw = await _call_llm(prompt)
        with stage("nlp.validate"):
            valid, schedule, _reason = validate_schedule(raw)
        used_fallback = not valid
    except Exception:
        used_fallback = True

    if used_fallback:
        counter("nlp.fallback")
        schedule = fallback_for(intent, duration_sec).model_dump()

    return PipelineResult(
        schedule=schedule,
        intent=intent,
        confidence=confidence,
        used_fallback=used_fallback,
        prompt_version_id=version_id,
        latency_breakdown_ms={name: durations(name)[-1] for name in _STAGES if durations(name)},
    )
