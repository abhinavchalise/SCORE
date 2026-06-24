from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


class APIResponse(BaseModel):
    success: bool
    message: str
    data: dict[str, Any] | None = None


class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


INTENTS = [
    "deep_focus",
    "light_focus",
    "creative_flow",
    "calm",
    "sleep_aid",
    "custom",
]


class ModulationStep(BaseModel):
    timestamp_sec: float = Field(..., ge=0, description="Seconds from session start")
    target_bpm: int = Field(..., ge=40, le=200)
    binaural_freq: float = Field(..., ge=0.5, le=40.0, description="Beat frequency in Hz")
    ramp_duration_sec: float = Field(..., ge=0, le=300, description="Seconds to transition")
    layer: Literal["binaural"] = "binaural"


class ModulationSchedule(BaseModel):
    intent: str
    total_duration_sec: int = Field(..., ge=60, le=7200)
    steps: list[ModulationStep] = Field(..., min_length=1, max_length=20)


class SessionStartRequest(BaseModel):
    intent: str = Field(..., min_length=1, max_length=100)
    duration_minutes: int = Field(25, ge=1, le=120)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


class LibraryScanRequest(BaseModel):
    directory_path: str = Field(..., min_length=1)


FeedbackKind = Literal["skip", "edit", "rating", "completion"]


class FeedbackEventCreate(BaseModel):
    session_id: int
    kind: FeedbackKind
    payload: dict[str, Any] = Field(default_factory=dict)


class FeedbackEventRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    session_id: int
    kind: str
    payload: dict[str, Any]
    at: datetime


class ExampleBankEntryCreate(BaseModel):
    intent: str
    schedule_json: dict[str, Any]
    rating: int = Field(..., ge=1, le=5)
    completion_pct: float = Field(..., ge=0, le=100)
    embedding: list[float]


class ExampleBankEntryRead(ExampleBankEntryCreate):
    model_config = ConfigDict(from_attributes=True)

    id: int
    added_at: datetime


class PromptVersionCreate(BaseModel):
    intent: str
    template: str
    active: bool = False


class PromptVersionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    intent: str
    template: str
    hash: str
    active: bool
    created_at: datetime
