from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, EmailStr, Field


# Response schema
class APIResponse(BaseModel):
    success: bool
    message: str
    data: Optional[Dict[str, Any]] = None


# User schemas
class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)


class UserCreate(UserBase):
    password: str = Field(..., min_length=8)


# Intent taxonomy
INTENTS = [
    "deep_focus",
    "light_focus",
    "creative_flow",
    "calm",
    "sleep_aid",
    "custom",
]


# LLM schemas
class ModulationStep(BaseModel):
    timestamp_sec: float = Field(..., ge=0, description="Seconds from session start")
    target_bpm: int = Field(..., ge=40, le=200)
    binaural_freq: float = Field(..., ge=0.5, le=40.0, description="Beat frequency in Hz")
    ramp_duration_sec: float = Field(..., ge=0, le=300, description="Seconds to transition")
    layer: Literal["binaural"] = "binaural"


class ModulationSchedule(BaseModel):
    intent: str
    total_duration_sec: int = Field(..., ge=60, le=7200)
    steps: List[ModulationStep] = Field(..., min_length=1, max_length=20)


# Session request schemas
class SessionStartRequest(BaseModel):
    intent: str = Field(..., min_length=1, max_length=100)
    duration_minutes: int = Field(25, ge=1, le=120)


# Auth schemas
class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)


# Library schemas
class LibraryScanRequest(BaseModel):
    directory_path: str = Field(..., min_length=1)
