import asyncio

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.config import settings
from backend.db.database import get_db
from backend.db.queries import SessionQueries
from backend.llm_engine.client import llm_engine
from backend.models.schemas import APIResponse, SessionStartRequest

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/start", response_model=APIResponse)
async def start_session(
    req: SessionStartRequest, db: AsyncSession = Depends(get_db)
) -> APIResponse:
    """Generate a modulation schedule for the intent and persist the session."""
    # Run LLM inference in a thread executor to avoid blocking the event loop
    loop = asyncio.get_running_loop()
    schedule = await asyncio.wait_for(
        loop.run_in_executor(
            None,
            llm_engine.generate_schedule,
            req.intent,
            req.duration_minutes,
        ),
        timeout=settings.llm_timeout_seconds,
    )

    session_record = await SessionQueries.create_session(
        db,
        intent=req.intent,
        schedule=schedule.model_dump_json(),
        duration_sec=schedule.total_duration_sec,
    )

    return APIResponse(
        success=True,
        message="Session started",
        data={
            "session_id": session_record.id,
            "schedule": schedule.model_dump(),
        },
    )
