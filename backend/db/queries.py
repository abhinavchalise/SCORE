import hashlib
from datetime import datetime, timezone

from sqlalchemy import func, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.orm import (
    ExampleBankEntry,
    FeedbackEvent,
    Library,
    PromptVersion,
    Session,
    User,
)
from backend.models.schemas import ExampleBankEntryCreate, PromptVersionCreate

EXAMPLE_MIN_RATING = 4
EXAMPLE_MIN_COMPLETION_PCT = 80.0
COMPLETION_PCT_KEY = "pct"


async def create_user(
    db: AsyncSession,
    email: str,
    username: str,
    hashed_password: str,
) -> User:
    user = User(
        email=email,
        username=username,
        hashed_password=hashed_password,
        created_at=datetime.now(timezone.utc),
        last_active=datetime.now(timezone.utc),
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


async def get_user_by_email(db: AsyncSession, email: str) -> User | None:
    result = await db.execute(select(User).where(User.email == email))
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> User | None:
    result = await db.execute(select(User).where(User.id == user_id))
    return result.scalar_one_or_none()


async def get_user_by_username(db: AsyncSession, username: str) -> User | None:
    result = await db.execute(select(User).where(User.username == username))
    return result.scalar_one_or_none()


async def update_user_last_active(db: AsyncSession, user_id: int) -> User | None:
    user = await get_user_by_id(db, user_id)
    if user:
        user.last_active = datetime.now(timezone.utc)
        await db.commit()
        await db.refresh(user)
    return user


async def create_session(
    db: AsyncSession,
    intent: str,
    schedule: str,
    duration_sec: int,
    user_id: int | None = None,
) -> Session:
    session = Session(
        user_id=user_id,
        intent=intent,
        schedule=schedule,
        duration_sec=duration_sec,
    )
    db.add(session)
    await db.commit()
    await db.refresh(session)
    return session


async def end_session(
    db: AsyncSession,
    session_id: int,
    completion_pct: float,
) -> Session | None:
    session = await db.get(Session, session_id)
    if session is None:
        return None
    session.ended_at = datetime.now(timezone.utc)
    db.add(
        FeedbackEvent(
            session_id=session_id,
            kind="completion",
            payload={COMPLETION_PCT_KEY: completion_pct},
        )
    )
    await db.commit()
    await db.refresh(session)
    return session


async def create_track(
    db: AsyncSession,
    file_path: str,
    filename: str,
    format: str | None = None,
    duration_sec: float | None = None,
    bpm: float | None = None,
    key_signature: str | None = None,
    tags: str | None = None,
    analyzed_at: datetime | None = None,
) -> Library:
    track = Library(
        file_path=file_path,
        filename=filename,
        format=format,
        duration_sec=duration_sec,
        bpm=bpm,
        key_signature=key_signature,
        tags=tags,
        analyzed_at=analyzed_at,
    )
    db.add(track)
    await db.commit()
    await db.refresh(track)
    return track


async def get_track_by_id(db: AsyncSession, track_id: int) -> Library | None:
    result = await db.execute(select(Library).where(Library.id == track_id))
    return result.scalar_one_or_none()


async def get_track_by_path(db: AsyncSession, file_path: str) -> Library | None:
    result = await db.execute(select(Library).where(Library.file_path == file_path))
    return result.scalar_one_or_none()


async def list_tracks(
    db: AsyncSession,
    bpm_min: float | None = None,
    bpm_max: float | None = None,
    format: str | None = None,
    limit: int = 50,
) -> list[Library]:
    query = select(Library)
    if bpm_min is not None:
        query = query.where(Library.bpm >= bpm_min)
    if bpm_max is not None:
        query = query.where(Library.bpm <= bpm_max)
    if format is not None:
        query = query.where(Library.format == format)
    query = query.limit(limit)
    result = await db.execute(query)
    return result.scalars().all()


async def append_feedback(
    db: AsyncSession,
    session_id: int,
    kind: str,
    payload: dict,
) -> FeedbackEvent:
    event = FeedbackEvent(session_id=session_id, kind=kind, payload=payload)
    db.add(event)
    await db.commit()
    await db.refresh(event)
    return event


async def insert_example(db: AsyncSession, entry: ExampleBankEntryCreate) -> ExampleBankEntry:
    row = ExampleBankEntry(
        intent=entry.intent,
        schedule_json=entry.schedule_json,
        rating=entry.rating,
        completion_pct=entry.completion_pct,
        embedding=entry.embedding,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def fetch_example_bank(db: AsyncSession, intent: str, k: int = 3) -> list[ExampleBankEntry]:
    result = await db.execute(
        select(ExampleBankEntry)
        .where(
            ExampleBankEntry.intent == intent,
            ExampleBankEntry.rating >= EXAMPLE_MIN_RATING,
            ExampleBankEntry.completion_pct >= EXAMPLE_MIN_COMPLETION_PCT,
        )
        .order_by(
            ExampleBankEntry.rating.desc(),
            ExampleBankEntry.completion_pct.desc(),
            ExampleBankEntry.added_at.desc(),
        )
        .limit(k)
    )
    return result.scalars().all()


async def insert_prompt_version(db: AsyncSession, version: PromptVersionCreate) -> PromptVersion:
    row = PromptVersion(
        intent=version.intent,
        template=version.template,
        hash=hashlib.sha256(version.template.encode()).hexdigest(),
        active=version.active,
    )
    db.add(row)
    await db.commit()
    await db.refresh(row)
    return row


async def active_prompt_version(db: AsyncSession, intent: str) -> PromptVersion | None:
    result = await db.execute(
        select(PromptVersion)
        .where(PromptVersion.intent == intent, PromptVersion.active.is_(True))
        .order_by(PromptVersion.created_at.desc())
    )
    return result.scalars().first()


async def activate_prompt_version(db: AsyncSession, version_id: int) -> PromptVersion | None:
    version = await db.get(PromptVersion, version_id)
    if version is None:
        return None
    await db.execute(
        update(PromptVersion)
        .where(PromptVersion.intent == version.intent, PromptVersion.id != version_id)
        .values(active=False)
    )
    version.active = True
    await db.commit()
    await db.refresh(version)
    return version


async def session_completion_rate(
    db: AsyncSession,
    intent: str,
    since: datetime | None = None,
) -> float:
    query = (
        select(FeedbackEvent.payload)
        .join(Session, FeedbackEvent.session_id == Session.id)
        .where(FeedbackEvent.kind == "completion", Session.intent == intent)
    )
    if since is not None:
        query = query.where(FeedbackEvent.at >= since)

    result = await db.execute(query)
    values = [
        payload[COMPLETION_PCT_KEY]
        for payload in result.scalars().all()
        if isinstance(payload, dict) and payload.get(COMPLETION_PCT_KEY) is not None
    ]
    return sum(values) / len(values) if values else 0.0


async def fallback_rate(db: AsyncSession, since: datetime | None = None) -> float:
    total_query = select(func.count()).select_from(Session)
    fallback_query = (
        select(func.count()).select_from(Session).where(Session.used_fallback.is_(True))
    )
    if since is not None:
        total_query = total_query.where(Session.started_at >= since)
        fallback_query = fallback_query.where(Session.started_at >= since)

    total = (await db.execute(total_query)).scalar_one()
    fallbacks = (await db.execute(fallback_query)).scalar_one()
    return fallbacks / total if total else 0.0
