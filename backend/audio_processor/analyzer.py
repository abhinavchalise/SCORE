import logging
from typing import Optional

import librosa
import numpy as np

logger = logging.getLogger(__name__)

PITCH_CLASSES = ["C", "C#", "D", "D#", "E", "F", "F#", "G", "G#", "A", "A#", "B"]


def analyze_track(file_path: str) -> dict:
    try:
        audio_samples, sample_rate = librosa.load(file_path, sr=22050)
    except Exception:
        logger.warning("librosa failed to load %s", file_path, exc_info=True)
        return {"duration_sec": None, "bpm": None, "key_signature": None}

    duration_sec = float(librosa.get_duration(y=audio_samples, sr=sample_rate))
    bpm = _extract_bpm(audio_samples, sample_rate)
    key_signature = _extract_key(audio_samples, sample_rate)

    return {
        "duration_sec": duration_sec,
        "bpm": bpm,
        "key_signature": key_signature,
    }


def _extract_bpm(audio_samples: np.ndarray, sample_rate: int) -> Optional[float]:
    try:
        tempo, _ = librosa.beat.beat_track(y=audio_samples, sr=sample_rate)
        # librosa >= 0.10 returns an array
        if hasattr(tempo, "__len__"):
            return float(tempo[0])
        return float(tempo)
    except Exception:
        logger.warning("BPM extraction failed", exc_info=True)
        return None


def _extract_key(audio_samples: np.ndarray, sample_rate: int) -> Optional[str]:
    try:
        chroma = librosa.feature.chroma_cqt(y=audio_samples, sr=sample_rate)
        chroma_mean = np.mean(chroma, axis=1)
        key_index = int(np.argmax(chroma_mean))
        return PITCH_CLASSES[key_index]
    except Exception:
        logger.warning("Key extraction failed", exc_info=True)
        return None
