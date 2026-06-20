import logging
from typing import Optional

import librosa
import numpy as np

logger = logging.getLogger(__name__)

PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def analyze_track(file_path: str) -> dict:
    try:
        y, sr = librosa.load(file_path, sr=22050)
    except Exception:
        logger.warning("librosa failed to load %s", file_path, exc_info=True)
        return {"duration_sec": None, "bpm": None, "key_signature": None}

    duration_sec = float(librosa.get_duration(y=y, sr=sr))
    bpm = _extract_bpm(y, sr)
    key_signature = _extract_key(y, sr)

    return {
        "duration_sec": duration_sec,
        "bpm": bpm,
        "key_signature": key_signature,
    }


def _extract_bpm(y: np.ndarray, sr: int) -> Optional[float]:
    try:
        tempo, _ = librosa.beat.beat_track(y=y, sr=sr)
        # librosa >= 0.10 returns an array
        if hasattr(tempo, "__len__"):
            return float(tempo[0])
        return float(tempo)
    except Exception:
        logger.warning("BPM extraction failed", exc_info=True)
        return None


def _extract_key(y: np.ndarray, sr: int) -> Optional[str]:
    try:
        chroma = librosa.feature.chroma_cqt(y=y, sr=sr)
        chroma_mean = np.mean(chroma, axis=1)
        key_index = int(np.argmax(chroma_mean))
        return PITCH_CLASSES[key_index]
    except Exception:
        logger.warning("Key extraction failed", exc_info=True)
        return None
