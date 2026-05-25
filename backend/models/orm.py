from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text, func
from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# A registered user and their neurodiversity preferences
class User(Base):
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


# A catalogued audio asset
class AudioTrack(Base):
    __tablename__ = "audio"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    audio_type = Column(String(50), nullable=False)

    duration = Column(Float, nullable=False)
    frequency = Column(Float, nullable=False)
    bpm = Column(Float, nullable=True)

    tags = Column(Text, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    activity = Column(Boolean, nullable=True)

    def __repr__(self):
        return f"<AudioTrack(name={self.name}, type={self.audio_type}, duration={self.duration}s)>"


# An LLM-generated audio session and its feedback
class Session(Base):
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


# Metadata for a user-uploaded audio file
class Library(Base):
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


# A versioned LLM prompt template
class Prompt(Base):
    __tablename__ = "prompts"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    template = Column(Text, nullable=False)
    model = Column(String(100), default="deepseek-ai/DeepSeek-R1-Distill-Llama-8B")
    version = Column(Integer, default=1)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now())

    def __repr__(self):
        return f"<Prompt(name={self.name}, version={self.version})>"
