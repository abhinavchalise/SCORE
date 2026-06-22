import asyncio
import os
from datetime import datetime, timezone
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from backend.audio_processor.analyzer import analyze_track
from backend.audio_processor.scanner import scan_directory
from backend.db.database import get_db
from backend.db.queries import create_track, get_track_by_id, get_track_by_path, list_tracks
from backend.models.schemas import APIResponse, LibraryScanRequest

router = APIRouter(prefix="/library", tags=["library"])

MEDIA_TYPES = {
    "wav": "audio/wav",
    "flac": "audio/flac",
    "mp3": "audio/mpeg",
}


@router.post("/scan", response_model=APIResponse)
async def scan_library(req: LibraryScanRequest, db: AsyncSession = Depends(get_db)) -> APIResponse:
    loop = asyncio.get_running_loop()

    try:
        found = await loop.run_in_executor(None, scan_directory, req.directory_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    tracks_analyzed = 0
    for entry in found:
        existing = await get_track_by_path(db, entry["file_path"])
        if existing:
            continue

        analysis = await loop.run_in_executor(None, analyze_track, entry["file_path"])

        await create_track(
            db,
            file_path=entry["file_path"],
            filename=entry["filename"],
            format=entry["format"],
            duration_sec=analysis.get("duration_sec"),
            bpm=analysis.get("bpm"),
            key_signature=analysis.get("key_signature"),
            analyzed_at=datetime.now(timezone.utc) if analysis.get("duration_sec") else None,
        )
        tracks_analyzed += 1

    return APIResponse(
        success=True,
        message="Library scan complete",
        data={
            "tracks_found": len(found),
            "tracks_analyzed": tracks_analyzed,
        },
    )


@router.get("/", response_model=APIResponse)
async def list_library(
    bpm_min: Optional[float] = Query(None, ge=20, le=300),
    bpm_max: Optional[float] = Query(None, ge=20, le=300),
    format: Optional[str] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    db: AsyncSession = Depends(get_db),
) -> APIResponse:
    tracks = await list_tracks(db, bpm_min=bpm_min, bpm_max=bpm_max, format=format, limit=limit)
    return APIResponse(
        success=True,
        message=f"Found {len(tracks)} tracks",
        data={
            "tracks": [
                {
                    "id": track.id,
                    "file_path": track.file_path,
                    "filename": track.filename,
                    "format": track.format,
                    "duration_sec": track.duration_sec,
                    "bpm": track.bpm,
                    "key_signature": track.key_signature,
                    "analyzed_at": track.analyzed_at.isoformat() if track.analyzed_at else None,
                }
                for track in tracks
            ],
        },
    )


@router.get("/{track_id}/stream")
async def stream_track(track_id: int, db: AsyncSession = Depends(get_db)) -> FileResponse:
    track = await get_track_by_id(db, track_id)
    if not track:
        raise HTTPException(status_code=404, detail="Track not found")

    if not os.path.isfile(track.file_path):
        raise HTTPException(status_code=404, detail="Audio file not found on disk")

    media_type = MEDIA_TYPES.get(track.format, "application/octet-stream")
    return FileResponse(track.file_path, media_type=media_type, filename=track.filename)
