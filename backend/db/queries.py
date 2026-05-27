from datetime import datetime, timezone
from typing import List, Optional

from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select

from backend.models.orm import Library, Session, User


class UserQueries:
    @staticmethod
    async def create_user(
        db: AsyncSession,
        email: str,
        username: str,
        hashed_password: str,
        neurotype: Optional[str] = None,
        volume_preference: Optional[float] = 0.5,
    ) -> User:
        user = User(
            email=email,
            username=username,
            hashed_password=hashed_password,
            neurotype=neurotype,
            user_preferences=None,
            created_at=datetime.now(timezone.utc),
            last_active=datetime.now(timezone.utc),
            activity=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)
        return user

    @staticmethod
    async def get_by_email(db: AsyncSession, email: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
        result = await db.execute(select(User).where(User.id == user_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_username(db: AsyncSession, username: str) -> Optional[User]:
        result = await db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_users(db: AsyncSession, skip: int = 0, limit: int = 100) -> List[User]:
        result = await db.execute(select(User).offset(skip).limit(limit))
        return result.scalars().all()

    @staticmethod
    async def update_last_active(db: AsyncSession, user_id: int) -> Optional[User]:
        user = await UserQueries.get_by_id(db, user_id)
        if user:
            user.last_active = datetime.now(timezone.utc)
            await db.commit()
            await db.refresh(user)
        return user


class SessionQueries:
    @staticmethod
    async def create_session(
        db: AsyncSession,
        intent: str,
        schedule: str,
        duration_sec: int,
        user_id: Optional[int] = None,
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

    @staticmethod
    async def get_by_id(db: AsyncSession, session_id: int) -> Optional[Session]:
        result = await db.execute(select(Session).where(Session.id == session_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_by_user(
        db: AsyncSession, user_id: int, limit: int = 20, offset: int = 0
    ) -> List[Session]:
        result = await db.execute(
            select(Session)
            .where(Session.user_id == user_id)
            .order_by(Session.started_at.desc())
            .limit(limit)
            .offset(offset)
        )
        return result.scalars().all()

    @staticmethod
    async def end_session(
        db: AsyncSession,
        session_id: int,
        rating: Optional[int] = None,
        feedback_note: Optional[str] = None,
    ) -> Optional[Session]:
        session = await SessionQueries.get_by_id(db, session_id)
        if not session:
            return None
        session.ended_at = datetime.now(timezone.utc)
        if session.started_at:
            delta = session.ended_at - session.started_at
            session.duration_sec = int(delta.total_seconds())
        session.rating = rating
        session.feedback_note = feedback_note
        await db.commit()
        await db.refresh(session)
        return session


class LibraryQueries:
    @staticmethod
    async def create_track(
        db: AsyncSession,
        file_path: str,
        filename: str,
        format: Optional[str] = None,
        duration_sec: Optional[float] = None,
        bpm: Optional[float] = None,
        key_signature: Optional[str] = None,
        tags: Optional[str] = None,
        analyzed_at: Optional[datetime] = None,
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

    @staticmethod
    async def get_by_id(db: AsyncSession, track_id: int) -> Optional[Library]:
        result = await db.execute(select(Library).where(Library.id == track_id))
        return result.scalar_one_or_none()

    @staticmethod
    async def get_by_path(db: AsyncSession, file_path: str) -> Optional[Library]:
        result = await db.execute(select(Library).where(Library.file_path == file_path))
        return result.scalar_one_or_none()

    @staticmethod
    async def list_tracks(
        db: AsyncSession,
        bpm_min: Optional[float] = None,
        bpm_max: Optional[float] = None,
        format: Optional[str] = None,
        limit: int = 50,
    ) -> List[Library]:
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
