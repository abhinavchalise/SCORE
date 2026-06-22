import json

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.db.queries import create_session
from backend.models.schemas import APIResponse, SessionStartRequest
from backend.nlp import run_pipeline

router = APIRouter(prefix="/sessions", tags=["sessions"])


@router.post("/start", response_model=APIResponse)
async def start_session(
    req: SessionStartRequest, db: AsyncSession = Depends(get_db)
) -> APIResponse:
    result = await run_pipeline(req.intent, db)

    session_record = await create_session(
        db,
        intent=result.intent,
        schedule=json.dumps(result.schedule),
        duration_sec=result.schedule["total_duration_sec"],
    )

    return APIResponse(
        success=True,
        message="Session started",
        data={
            "session_id": session_record.id,
            "schedule": result.schedule,
            "intent": result.intent,
            "used_fallback": result.used_fallback,
        },
    )
