import pytest

try:
    from fastapi import WebSocketDisconnect
except ImportError:
    WebSocketDisconnect = None

_SCHEDULE = {
    "intent": "deep_focus",
    "total_duration_sec": 1500,
    "steps": [
        {
            "timestamp_sec": 0,
            "target_bpm": 70,
            "binaural_freq": 10.0,
            "ramp_duration_sec": 60,
            "layer": "binaural",
        },
        {
            "timestamp_sec": 300,
            "target_bpm": 78,
            "binaural_freq": 13.0,
            "ramp_duration_sec": 120,
            "layer": "binaural",
        },
    ],
}


class FakeWebSocket:
    TICK = object()

    def __init__(self, incoming):
        self._incoming = list(incoming)
        self.sent = []
        self.accepted = False
        self.closed = False

    async def accept(self):
        self.accepted = True

    async def receive_json(self):
        if not self._incoming:
            raise WebSocketDisconnect()
        item = self._incoming.pop(0)
        if item is FakeWebSocket.TICK:
            raise TimeoutError
        return item

    async def send_json(self, data):
        self.sent.append(data)

    async def close(self):
        self.closed = True


@pytest.fixture
def fake_ws():
    return FakeWebSocket


@pytest.fixture
def schedule():
    return _SCHEDULE


@pytest.fixture
def mocked_llm(monkeypatch):
    from backend.nlp.pipeline import PipelineResult
    from backend.routers import sessions as sessions_module

    async def fake_run_pipeline(intent, db, duration_minutes=25):
        return PipelineResult(
            schedule=_SCHEDULE,
            intent="deep_focus",
            confidence=0.9,
            used_fallback=False,
            prompt_version_id=0,
            latency_breakdown_ms={},
        )

    monkeypatch.setattr(sessions_module, "run_pipeline", fake_run_pipeline)
