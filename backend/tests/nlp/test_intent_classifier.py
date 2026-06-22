import json
from pathlib import Path

import pytest

torch = pytest.importorskip("torch")
pytest.importorskip("sentence_transformers")

from backend.nlp.intent_classifier import IntentClassifier  # noqa: E402

FIXTURE = Path(__file__).parent / "fixtures" / "intent_seed.jsonl"


def _load():
    return [json.loads(line) for line in FIXTURE.read_text().splitlines() if line.strip()]


def _stratified_split(examples, train_fraction=0.8):
    by_intent: dict[str, list] = {}
    for example in examples:
        by_intent.setdefault(example["intent"], []).append(example)
    train, evaluate = [], []
    for rows in by_intent.values():
        cut = int(len(rows) * train_fraction)
        train.extend(rows[:cut])
        evaluate.extend(rows[cut:])
    return train, evaluate


def test_macro_f1_meets_threshold():
    train, evaluate = _stratified_split(_load())
    classifier = IntentClassifier()
    classifier.train(train)
    assert classifier.evaluate(evaluate) >= 0.85


def test_low_confidence_routes_to_custom(monkeypatch):
    from torch import nn

    classifier = IntentClassifier()
    nn.init.zeros_(classifier.head.weight)
    nn.init.zeros_(classifier.head.bias)
    monkeypatch.setattr(classifier, "_embed", lambda texts: torch.zeros(1, 384))

    intent, confidence = classifier.classify("anything")
    assert confidence < 0.55
    assert intent == "custom"
