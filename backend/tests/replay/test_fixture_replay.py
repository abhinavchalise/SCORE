import json
from pathlib import Path

from backend.nlp.validators import validate_schedule

FIXTURES = Path(__file__).parent / "fixtures" / "eval_50.jsonl"


def _load() -> list[dict]:
    with FIXTURES.open() as handle:
        return [json.loads(line) for line in handle if line.strip()]


def test_replay_meets_quality_gate():
    fixtures = _load()
    assert len(fixtures) == 50

    valid = 0
    reasons: dict[str, int] = {}
    for case in fixtures:
        ok, _, reason = validate_schedule(case["schedule"])
        if ok:
            valid += 1
        else:
            reasons[reason] = reasons.get(reason, 0) + 1

    validity_rate = valid / len(fixtures)
    fallback_rate = (len(fixtures) - valid) / len(fixtures)
    detail = f"failures={reasons}"
    assert validity_rate >= 0.995, f"validity {validity_rate:.3f} < 0.995 {detail}"
    assert fallback_rate <= 0.05, f"fallback {fallback_rate:.3f} > 0.05 {detail}"
