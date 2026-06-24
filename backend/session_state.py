import time
from enum import Enum
from typing import Callable


class SessionPhase(str, Enum):
    GENERATING = "generating"
    PLAYING = "playing"
    FALLBACK_PLAY = "fallback_play"
    PAUSED = "paused"
    ENDED = "ended"


_PLAYING_PHASES = (SessionPhase.PLAYING, SessionPhase.FALLBACK_PLAY)


class SessionState:
    def __init__(
        self, total_duration_sec: int, clock: Callable[[], float] = time.monotonic
    ) -> None:
        self.total_duration_sec = total_duration_sec
        self.phase = SessionPhase.GENERATING
        self._clock = clock
        self._accumulated_active = 0.0
        self._segment_start: float | None = None
        self._active_phase = SessionPhase.PLAYING

    def begin_playing(self, used_fallback: bool) -> None:
        if self.phase != SessionPhase.GENERATING:
            raise ValueError(f"cannot begin playing from {self.phase.value}")
        self._active_phase = SessionPhase.FALLBACK_PLAY if used_fallback else SessionPhase.PLAYING
        self.phase = self._active_phase
        self._segment_start = self._clock()

    def pause(self) -> None:
        if self.phase not in _PLAYING_PHASES:
            raise ValueError(f"cannot pause from {self.phase.value}")
        self._bank_segment()
        self.phase = SessionPhase.PAUSED

    def resume(self) -> None:
        if self.phase != SessionPhase.PAUSED:
            raise ValueError(f"cannot resume from {self.phase.value}")
        self.phase = self._active_phase
        self._segment_start = self._clock()

    def stop(self) -> None:
        if self.phase == SessionPhase.ENDED:
            raise ValueError("session already ended")
        self._bank_segment()
        self.phase = SessionPhase.ENDED

    def elapsed_sec(self) -> float:
        open_segment = 0.0 if self._segment_start is None else self._clock() - self._segment_start
        return self._accumulated_active + open_segment

    def completion_pct(self) -> float:
        if self.total_duration_sec <= 0:
            return 0.0
        return min(100.0, self.elapsed_sec() / self.total_duration_sec * 100)

    def _bank_segment(self) -> None:
        if self._segment_start is not None:
            self._accumulated_active += self._clock() - self._segment_start
            self._segment_start = None
