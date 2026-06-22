import re

from backend.latency import counter

MAX_LENGTH = 500

_CONTROL_CHARS = re.compile(r"[\x00-\x08\x0b-\x1f]")
_INJECTION_PATTERNS = (
    re.compile(r"(?im)^\s*ignore\s+previous.*$"),
    re.compile(r"(?im)^\s*system\s*:.*$"),
    re.compile(r"(?im)^\s*assistant\s*:.*$"),
    re.compile(r"\n\n#"),
    re.compile(r"<\|"),
)


def sanitize(text: str) -> str:
    cleaned = _CONTROL_CHARS.sub("", text)[:MAX_LENGTH]

    injected = False
    for pattern in _INJECTION_PATTERNS:
        cleaned, hits = pattern.subn("", cleaned)
        injected = injected or bool(hits)
    if injected:
        counter("nlp.injection_detected")

    return cleaned.strip() or "calm"
