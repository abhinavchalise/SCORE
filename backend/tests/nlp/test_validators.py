from backend.nlp.validators import clamp_schedule, validate_schedule


def _step(timestamp_sec, target_bpm, binaural_freq, ramp_duration_sec):
    return {
        "timestamp_sec": timestamp_sec,
        "target_bpm": target_bpm,
        "binaural_freq": binaural_freq,
        "ramp_duration_sec": ramp_duration_sec,
        "layer": "binaural",
    }


def _schedule(steps):
    return {"intent": "deep_focus", "total_duration_sec": 1500, "steps": steps}


def test_valid_schedule_passes():
    raw = _schedule([_step(0, 70, 10.0, 60), _step(300, 75, 12.0, 120)])
    ok, schedule, reason = validate_schedule(raw)
    assert ok is True
    assert reason is None
    assert schedule["intent"] == "deep_focus"


def test_range_violation_is_flagged():
    raw = _schedule([_step(0, 400, 10.0, 60)])
    ok, schedule, reason = validate_schedule(raw)
    assert ok is False
    assert schedule is None
    assert reason == "range_invalid"


def test_schema_violation_is_flagged():
    ok, schedule, reason = validate_schedule({"intent": "deep_focus", "total_duration_sec": 1500})
    assert ok is False
    assert reason == "schema_invalid"


def test_smoothness_violation_is_flagged():
    raw = _schedule([_step(0, 70, 10.0, 60), _step(300, 130, 12.0, 1)])
    ok, schedule, reason = validate_schedule(raw)
    assert ok is False
    assert reason == "smoothness_invalid"


def test_clamp_repairs_range_and_smoothness():
    steps = [_step(0, 70, 50.0, 0), _step(300, 400, 5.0, 0)]
    assert validate_schedule(_schedule(steps))[0] is False

    ok, schedule, reason = validate_schedule(clamp_schedule(_schedule(steps)))
    assert ok is True
    assert reason is None
    assert schedule["steps"][0]["binaural_freq"] == 40.0
    assert schedule["steps"][1]["target_bpm"] == 200
    assert schedule["steps"][1]["ramp_duration_sec"] > 0
