from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field


# Enums
class NeurotypeEnum(str, Enum):
    ADHD = "ADHD"
    AUTISM = "Autism"
    ANXIETY = "Anxiety"
    DEPRESSION = "Depression"
    NEUROTYPICAL = "Neurotypical"
    OTHER = "Other"


# Response Schema
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


# Error Schema
class ErrorResponse(BaseModel):
    success: bool = False
    error: str
    details: Optional[str] = None


# User Schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    neurotype: Optional[NeurotypeEnum] = None
    volume_preference: float = Field(0.5, ge=0.0, le=1.0)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


class UserResponse(UserBase):
    id: int
    created_at: datetime
    last_active: datetime
    activity: bool

    class Config:
        from_attributes = True


class UserPreferencesUpdate(BaseModel):
    neurotype: Optional[NeurotypeEnum] = None
    volume_preference: Optional[float] = Field(None, ge=0.0, le=1.0)
    sensory_preferences: Optional[List[str]] = None


# LLM schemas
class ModulationStep(BaseModel):
    timestamp_sec: float = Field(..., ge=0, description="Seconds from session start")
    target_bpm: int = Field(..., ge=40, le=200)
    binaural_freq: float = Field(..., ge=0.5, le=40.0, description="Beat frequency in Hz")
    ramp_duration_sec: float = Field(..., ge=0, le=300, description="Seconds to transition")
    layer: Literal["binaural", "isochronic", "ambient"] = "binaural"


class ModulationSchedule(BaseModel):
    intent: str
    total_duration_sec: int = Field(..., ge=60, le=7200)
    steps: List[ModulationStep] = Field(..., min_length=1, max_length=20)


# Session request/response schemas
class SessionStartRequest(BaseModel):
    intent: str = Field(..., min_length=1, max_length=100)
    duration_minutes: int = Field(25, ge=1, le=120)


class SessionEndRequest(BaseModel):
    rating: Optional[int] = Field(None, ge=1, le=5)
    feedback_note: Optional[str] = Field(None, max_length=1000)


class SessionEndResponse(BaseModel):
    session_id: int
    duration_sec: int


class SessionResponse(BaseModel):
    id: int
    user_id: Optional[int] = None
    intent: str
    schedule: str
    duration_sec: Optional[int] = None
    started_at: datetime
    ended_at: Optional[datetime] = None
    rating: Optional[int] = None
    feedback_note: Optional[str] = None

    class Config:
        from_attributes = True


# Auth schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class TokenResponse(BaseModel):
    token: str
    expires_in: int
    user_id: int


# Library schemas
class LibraryScanRequest(BaseModel):
    directory_path: str = Field(..., min_length=1)


class LibraryTrackResponse(BaseModel):
    id: int
    file_path: str
    filename: str
    format: Optional[str] = None
    duration_sec: Optional[float] = None
    bpm: Optional[float] = None
    key_signature: Optional[str] = None
    tags: Optional[List[str]] = None
    analyzed_at: Optional[datetime] = None
    created_at: datetime

    class Config:
        from_attributes = True


class LibraryQueryParams(BaseModel):
    bpm_min: Optional[float] = Field(None, ge=20, le=300)
    bpm_max: Optional[float] = Field(None, ge=20, le=300)
    format: Optional[str] = None
    limit: int = Field(50, ge=1, le=200)


# Standalone LLM request schema
class GenerateScheduleRequest(BaseModel):
    intent: str = Field(..., min_length=1, max_length=100)
    current_bpm: Optional[int] = Field(None, ge=40, le=200)
    duration_min: int = Field(25, ge=1, le=120)
