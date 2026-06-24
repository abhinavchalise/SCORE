import asyncio
import json
from dataclasses import dataclass

from fastapi import APIRouter, Depends, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.ext.asyncio import AsyncSession

from backend.db.database import get_db
from backend.db.queries import (
    EXAMPLE_MIN_COMPLETION_PCT,
    EXAMPLE_MIN_RATING,
    append_feedback,
    create_session,
    end_session,
    recent_sessions,
)
from backend.models.schemas import APIResponse, SessionStartRequest
from backend.nlp import run_pipeline
from backend.nlp.example_bank import store_example
from backend.nlp.pipeline import PipelineResult
from backend.session_state import SessionPhase, SessionState

router = APIRouter(prefix="/sessions", tags=["sessions"])

TICK_INTERVAL_SEC = 1.0
RATING_WAIT_SEC = 30.0


@dataclass
class _FeedbackTally:
    edit_count: int = 0
    rating: int | None = None


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


@router.get("/history", response_model=APIResponse)
async def session_history(
    limit: int = Query(20, ge=1, le=100), db: AsyncSession = Depends(get_db)
) -> APIResponse:
    sessions = await recent_sessions(db, limit)
    return APIResponse(
        success=True,
        message=f"Found {len(sessions)} sessions",
        data={"sessions": sessions},
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

    tally = _FeedbackTally()
    ended_cleanly = True
    try:
        await _run_playback(websocket, state, db, session.id, tally)
    except WebSocketDisconnect:
        ended_cleanly = False
        if state.phase != SessionPhase.ENDED:
            state.stop()

    completion_pct = state.completion_pct()
    await end_session(db, session.id, completion_pct)
    if not ended_cleanly:
        return

    await websocket.send_json(
        {"type": "ended", "session_id": session.id, "completion_pct": completion_pct}
    )
    await _collect_final_rating(websocket, db, session.id, tally)
    await _maybe_store_example(db, result, req.intent, completion_pct, tally)
    await websocket.close()


async def _run_playback(
    websocket: WebSocket,
    state: SessionState,
    db: AsyncSession,
    session_id: int,
    tally: _FeedbackTally,
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
            _record_feedback(tally, message)
            await append_feedback(db, session_id, message["kind"], message.get("payload", {}))


async def _collect_final_rating(
    websocket: WebSocket, db: AsyncSession, session_id: int, tally: _FeedbackTally
) -> None:
    try:
        message = await asyncio.wait_for(websocket.receive_json(), RATING_WAIT_SEC)
    except (TimeoutError, WebSocketDisconnect):
        return
    if message.get("type") == "feedback" and message.get("kind") == "rating":
        _record_feedback(tally, message)
        await append_feedback(db, session_id, "rating", message.get("payload", {}))


async def _maybe_store_example(
    db: AsyncSession,
    result: PipelineResult,
    raw_intent: str,
    completion_pct: float,
    tally: _FeedbackTally,
) -> None:
    rating = tally.rating
    if rating is None or rating < EXAMPLE_MIN_RATING:
        return
    if completion_pct < EXAMPLE_MIN_COMPLETION_PCT or tally.edit_count != 0:
        return
    await store_example(
        db,
        intent=result.intent,
        schedule_json=result.schedule,
        rating=rating,
        completion_pct=completion_pct,
        text=raw_intent,
    )


def _record_feedback(tally: _FeedbackTally, message: dict) -> None:
    kind = message.get("kind")
    payload = message.get("payload", {})
    if kind == "edit":
        tally.edit_count += 1
    elif kind == "rating":
        value = payload.get("value")
        if isinstance(value, int):
            tally.rating = value


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
