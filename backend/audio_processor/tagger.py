import asyncio
from datetime import datetime, timezone

from sqlalchemy.ext.asyncio import AsyncSession

from backend.audio_processor.scanner import scan_directory
from backend.db.queries import create_track, get_track_by_path
from backend.models.orm import Library


def _analyze(file_path: str) -> dict:
    from backend.audio_processor.analyzer import analyze_track

    return analyze_track(file_path)


async def tag_track(
    db: AsyncSession,
    file_path: str,
    filename: str,
    format: str | None = None,
) -> Library:
    loop = asyncio.get_running_loop()
    analysis = await loop.run_in_executor(None, _analyze, file_path)
    return await create_track(
        db,
        file_path=file_path,
        filename=filename,
        format=format,
        duration_sec=analysis.get("duration_sec"),
        bpm=analysis.get("bpm"),
        key_signature=analysis.get("key_signature"),
        analyzed_at=datetime.now(timezone.utc) if analysis.get("duration_sec") else None,
    )


async def tag_directory(db: AsyncSession, directory_path: str) -> list[Library]:
    loop = asyncio.get_running_loop()
    found = await loop.run_in_executor(None, scan_directory, directory_path)

    tagged: list[Library] = []
    for entry in found:
        if await get_track_by_path(db, entry["file_path"]):
            continue
        tagged.append(await tag_track(db, entry["file_path"], entry["filename"], entry["format"]))
    return tagged
