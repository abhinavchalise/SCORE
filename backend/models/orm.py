from sqlalchemy import (
    JSON,
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True, nullable=False)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    created_at = Column(DateTime, server_default=func.now())
    last_active = Column(DateTime, server_default=func.now())


class Session(Base):
    __tablename__ = "sessions"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=True)
    intent = Column(String(100), nullable=False)
    schedule = Column(Text, nullable=False)
    duration_sec = Column(Integer, nullable=True)
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)
    rating = Column(Integer, nullable=True)
    feedback_note = Column(Text, nullable=True)
    used_fallback = Column(Boolean, nullable=False, server_default=text("0"))
    prompt_version_id = Column(Integer, ForeignKey("prompt_versions.id"), nullable=True)


class Library(Base):
    __tablename__ = "library"
    id = Column(Integer, primary_key=True, index=True)
    file_path = Column(String(512), unique=True, nullable=False)
    filename = Column(String(255), nullable=False)
    format = Column(String(10), nullable=True)
    duration_sec = Column(Float, nullable=True)
    bpm = Column(Float, nullable=True)
    key_signature = Column(String(10), nullable=True)
    tags = Column(Text, nullable=True)
    analyzed_at = Column(DateTime, nullable=True)
    created_at = Column(DateTime, server_default=func.now())


class FeedbackEvent(Base):
    __tablename__ = "feedback_events"
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(Integer, ForeignKey("sessions.id"), index=True, nullable=False)
    kind = Column(String(20), nullable=False)
    payload = Column(JSON, nullable=False)
    at = Column(DateTime, server_default=func.now())


class ExampleBankEntry(Base):
    __tablename__ = "example_bank"
    id = Column(Integer, primary_key=True, index=True)
    intent = Column(String(100), index=True, nullable=False)
    schedule_json = Column(JSON, nullable=False)
    rating = Column(Integer, nullable=False)
    completion_pct = Column(Float, nullable=False)
    embedding = Column(JSON, nullable=False)
    added_at = Column(DateTime, server_default=func.now())


class PromptVersion(Base):
    __tablename__ = "prompt_versions"
    id = Column(Integer, primary_key=True, index=True)
    intent = Column(String(100), index=True, nullable=False)
    template = Column(Text, nullable=False)
    hash = Column(String(64), nullable=False)
    active = Column(Boolean, nullable=False, server_default=text("0"))
    created_at = Column(DateTime, server_default=func.now())
