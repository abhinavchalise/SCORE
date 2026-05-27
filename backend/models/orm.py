from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    """A registered user and their neurodiversity preferences."""

    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    neurotype = Column(String(50), nullable=True)
    user_preferences = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    last_active = Column(DateTime, server_default=func.now())
    activity = Column(Boolean, nullable=True)

    def __repr__(self):
        return f"<User(username={self.username}, email={self.email}, neurotype={self.neurotype})>"


class Session(Base):
    """An LLM-generated audio session and its feedback."""

    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)  # nullable for MVP (no auth)
    intent = Column(String(100), nullable=False)
    schedule = Column(Text, nullable=False)  # JSON string
    duration_sec = Column(Integer, nullable=True)
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)
    rating = Column(Integer, nullable=True)
    feedback_note = Column(Text, nullable=True)

    def __repr__(self):
        return f"<Session(intent={self.intent}, duration={self.duration_sec}s)>"


class Library(Base):
    """Metadata for a user-uploaded audio file."""

    __tablename__ = "library"
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(512), unique=True, nullable=False)
    filename = Column(String(255), nullable=False)
    format = Column(String(10), nullable=True)
    duration_sec = Column(Float, nullable=True)
    bpm = Column(Float, nullable=True)
    key_signature = Column(String(10), nullable=True)
    tags = Column(Text, nullable=True)  # JSON string
    analyzed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Library(filename={self.filename}, bpm={self.bpm})>"
