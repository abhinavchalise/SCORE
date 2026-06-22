from pydantic import ValidationError

from backend.latency import counter
from backend.models.schemas import ModulationSchedule

SMOOTHNESS_LIMIT_FRACTION = 0.20

_RANGE_ERROR_TYPES = {"greater_than", "greater_than_equal", "less_than", "less_than_equal"}
_FIELD_RANGE_WIDTHS = {
    "target_bpm": 200 - 40,
    "binaural_freq": 40.0 - 0.5,
    "ramp_duration_sec": 300 - 0,
}


def validate_schedule(raw: dict) -> tuple[bool, dict | None, str | None]:
    try:
        schedule = ModulationSchedule(**raw)
    except ValidationError as error:
        reason = (
            "range_invalid"
            if any(item["type"] in _RANGE_ERROR_TYPES for item in error.errors())
            else "schema_invalid"
        )
        counter(f"nlp.{reason}")
        return False, None, reason

    if _check_smoothness(schedule) is not None:
        counter("nlp.smoothness_invalid")
        return False, None, "smoothness_invalid"

    return True, schedule.model_dump(), None


def _check_smoothness(schedule: ModulationSchedule) -> str | None:
    for previous, current in zip(schedule.steps, schedule.steps[1:]):
        # ramp_duration_sec of the destination step is the window the cap is measured over.
        seconds = current.ramp_duration_sec
        for field, width in _FIELD_RANGE_WIDTHS.items():
            delta = abs(getattr(current, field) - getattr(previous, field))
            if seconds <= 0:
                if delta > 0:
                    return field
            elif delta / seconds > SMOOTHNESS_LIMIT_FRACTION * width:
                return field
    return None
