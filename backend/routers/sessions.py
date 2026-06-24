import asyncio
import json

from fastapi import APIRouter, Depends, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.db.queries import append_feedback, create_session, end_session
from backend.models.schemas import APIResponse, SessionStartRequest
from backend.nlp import run_pipeline
from backend.session_state import SessionPhase, SessionState

router = APIRouter(prefix="/sessions", tags=["sessions"])

TICK_INTERVAL_SEC = 1.0


@router.post("/start", response_model=APIResponse)
async def start_session(
    req: SessionStartRequest, db: AsyncSession = Depends(get_db)
) -> APIResponse:
    result = await run_pipeline(req.intent, db, req.duration_minutes)

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


@router.websocket("/ws")
async def session_ws(websocket: WebSocket, db: AsyncSession = Depends(get_db)) -> None:
    await websocket.accept()

    first = await websocket.receive_json()
    req = SessionStartRequest(**first)

    result = await run_pipeline(req.intent, db, req.duration_minutes)
    session = await create_session(
        db,
        intent=result.intent,
        schedule=json.dumps(result.schedule),
        duration_sec=result.schedule["total_duration_sec"],
    )

    state = SessionState(result.schedule["total_duration_sec"])
    state.begin_playing(result.used_fallback)
    if result.used_fallback:
        await websocket.send_json(
            {
                "type": "fallback",
                "session_id": session.id,
                "reason": "pipeline_fallback",
                "schedule": result.schedule,
            }
        )
    else:
        await websocket.send_json(
            {"type": "schedule", "session_id": session.id, "schedule": result.schedule}
        )

    ended_cleanly = True
    try:
        await _run_playback(websocket, state, db, session.id)
    except WebSocketDisconnect:
        ended_cleanly = False
        if state.phase != SessionPhase.ENDED:
            state.stop()

    await end_session(db, session.id, state.completion_pct())
    if ended_cleanly:
        await websocket.send_json(
            {
                "type": "ended",
                "session_id": session.id,
                "completion_pct": state.completion_pct(),
            }
        )
        await websocket.close()


async def _run_playback(
    websocket: WebSocket, state: SessionState, db: AsyncSession, session_id: int
) -> None:
    while state.phase != SessionPhase.ENDED:
        if state.phase == SessionPhase.PAUSED:
            message = await websocket.receive_json()
        else:
            try:
                message = await asyncio.wait_for(websocket.receive_json(), TICK_INTERVAL_SEC)
            except TimeoutError:
                if state.completion_pct() >= 100:
                    state.stop()
                else:
                    await websocket.send_json(
                        {
                            "type": "tick",
                            "session_id": session_id,
                            "elapsed_sec": state.elapsed_sec(),
                        }
                    )
                continue

        if message.get("type") == "control":
            _apply_control(state, message.get("action"))
        elif message.get("type") == "feedback":
            await append_feedback(db, session_id, message["kind"], message.get("payload", {}))


def _apply_control(state: SessionState, action: str) -> None:
    try:
        if action == "pause":
            state.pause()
        elif action == "resume":
            state.resume()
        elif action == "stop":
            state.stop()
    except ValueError:
        pass
