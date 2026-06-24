from backend.nlp import example_bank
from backend.nlp.example_bank import fetch_examples, store_example

SCHEDULE = {
    "intent": "deep_focus",
    "total_duration_sec": 1500,
    "steps": [
        {
            "timestamp_sec": 0,
            "target_bpm": 70,
            "binaural_freq": 10.0,
            "ramp_duration_sec": 60,
            "layer": "binaural",
        }
    ],
}


async def test_store_and_fetch_round_trip(db, monkeypatch):
    monkeypatch.setattr(example_bank, "embed_text", lambda text: [0.1, 0.2, 0.3])

    await store_example(db, "deep_focus", SCHEDULE, rating=5, completion_pct=90.0, text="focus")

    assert await fetch_examples(db, "deep_focus") == [SCHEDULE]


async def test_fetch_filters_low_quality(db, monkeypatch):
    monkeypatch.setattr(example_bank, "embed_text", lambda text: [0.1, 0.2, 0.3])

    await store_example(
        db, "deep_focus", SCHEDULE, rating=3, completion_pct=90.0, text="low rating"
    )
    await store_example(db, "calm", SCHEDULE, rating=5, completion_pct=50.0, text="low completion")

    assert await fetch_examples(db, "deep_focus") == []
    assert await fetch_examples(db, "calm") == []


def test_embed_text_delegates_to_encoder(monkeypatch):
    class FakeVector:
        def tolist(self):
            return [1.0, 2.0]

    class FakeEncoder:
        def encode(self, text):
            return FakeVector()

    monkeypatch.setattr(example_bank, "get_encoder", lambda: FakeEncoder())

    assert example_bank.embed_text("hello") == [1.0, 2.0]
