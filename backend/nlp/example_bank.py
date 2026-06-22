from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.queries import fetch_example_bank, insert_example
from backend.models.schemas import ExampleBankEntryCreate
from backend.nlp.intent_classifier import get_encoder


def embed_text(text: str) -> list[float]:
    return get_encoder().encode(text).tolist()


async def fetch_examples(db: AsyncSession, intent: str, k: int = 3) -> list[dict]:
    rows = await fetch_example_bank(db, intent, k)
    return [row.schedule_json for row in rows]


async def store_example(
    db: AsyncSession,
    intent: str,
    schedule_json: dict,
    rating: int,
    completion_pct: float,
    text: str,
) -> None:
    entry = ExampleBankEntryCreate(
        intent=intent,
        schedule_json=schedule_json,
        rating=rating,
        completion_pct=completion_pct,
        embedding=embed_text(text),
    )
    await insert_example(db, entry)
