import pytest

from backend.session_state import SessionPhase, SessionState


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0

    def __call__(self) -> float:
        return self.now

    def advance(self, seconds: float) -> None:
        self.now += seconds


def test_begin_playing_picks_phase():
    playing = SessionState(1500)
    playing.begin_playing(used_fallback=False)
    assert playing.phase is SessionPhase.PLAYING

    fallback = SessionState(1500)
    fallback.begin_playing(used_fallback=True)
    assert fallback.phase is SessionPhase.FALLBACK_PLAY


def test_pause_does_not_count_toward_elapsed():
    clock = FakeClock()
    state = SessionState(1500, clock=clock)
    state.begin_playing(used_fallback=False)

    clock.advance(100)
    state.pause()
    clock.advance(500)  # paused time is not counted
    state.resume()
    assert state.phase is SessionPhase.PLAYING
    clock.advance(50)

    assert state.elapsed_sec() == 150


def test_completion_pct_caps_at_100():
    clock = FakeClock()
    state = SessionState(100, clock=clock)
    state.begin_playing(used_fallback=False)
    clock.advance(250)
    assert state.completion_pct() == 100.0


def test_stop_ends_and_banks_final_segment():
    clock = FakeClock()
    state = SessionState(1000, clock=clock)
    state.begin_playing(used_fallback=False)
    clock.advance(400)
    state.stop()

    assert state.phase is SessionPhase.ENDED
    clock.advance(999)  # clock keeps moving but a stopped session has no open segment
    assert state.elapsed_sec() == 400
    assert state.completion_pct() == 40.0


def test_illegal_transitions_raise():
    state = SessionState(1500)
    with pytest.raises(ValueError):
        state.pause()  # cannot pause while generating

    state.begin_playing(used_fallback=False)
    with pytest.raises(ValueError):
        state.resume()  # cannot resume while playing
    with pytest.raises(ValueError):
        state.begin_playing(used_fallback=False)  # cannot begin twice

    state.stop()
    with pytest.raises(ValueError):
        state.stop()  # cannot stop after ended
