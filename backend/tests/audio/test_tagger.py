import math
import struct
import wave

import pytest

from backend.audio_processor import tagger as tagger_module
from backend.db.queries import list_tracks

SAMPLE_RATE = 22050


def _write_wav(path, seconds: float = 0.2) -> None:
    frame_count = int(SAMPLE_RATE * seconds)
    with wave.open(str(path), "w") as handle:
        handle.setnchannels(1)
        handle.setsampwidth(2)
        handle.setframerate(SAMPLE_RATE)
        frames = b"".join(
            struct.pack("<h", int(32767 * 0.3 * math.sin(2 * math.pi * 220 * n / SAMPLE_RATE)))
            for n in range(frame_count)
        )
        handle.writeframes(frames)


@pytest.fixture
def corpus(tmp_path) -> str:
    for name in ("alpha.wav", "beta.wav", "gamma.wav"):
        _write_wav(tmp_path / name)
    return str(tmp_path)


@pytest.fixture(autouse=True)
def stub_analyzer(monkeypatch):
    def fake_analyze(file_path: str) -> dict:
        return {"duration_sec": 12.0, "bpm": 120.0, "key_signature": "C"}

    monkeypatch.setattr(tagger_module, "_analyze", fake_analyze)


async def test_tag_directory_populates_features(db, corpus):
    tracks = await tagger_module.tag_directory(db, corpus)

    assert len(tracks) == 3
    for track in tracks:
        assert track.duration_sec == 12.0
        assert track.bpm == 120.0
        assert track.key_signature == "C"
        assert track.analyzed_at is not None
    assert len(await list_tracks(db)) == 3


async def test_tag_directory_is_idempotent(db, corpus):
    await tagger_module.tag_directory(db, corpus)
    rescanned = await tagger_module.tag_directory(db, corpus)

    assert rescanned == []
    assert len(await list_tracks(db)) == 3
