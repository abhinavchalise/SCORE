import json
import re

from backend.models.schemas import ModulationSchedule


def strip_think_tags(text: str) -> str:
    """Remove <think>...</think> reasoning blocks from R1-style output."""
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def extract_json(text: str) -> str:
    depth = 0
    start_idx = None
    for i, ch in enumerate(text):
        if ch == "{":
            if depth == 0:
                start_idx = i
            depth += 1
        elif ch == "}":
            depth -= 1
            if depth == 0 and start_idx is not None:
                return text[start_idx : i + 1]
    # Fallback: return text as-is and let JSON parser handle the error
    return text


def parse_llm_response(raw_output: str) -> ModulationSchedule:
    """Clean, extract, and validate raw output into a ModulationSchedule."""
    cleaned = strip_think_tags(raw_output)
    json_str = extract_json(cleaned)
    data = json.loads(json_str)
    return ModulationSchedule(**data)
