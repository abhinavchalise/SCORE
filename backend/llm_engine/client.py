import asyncio
import json
import time
import torch
from pydantic import ValidationError
from transformers import AutoTokenizer, AutoModelForCausalLM, BitsAndBytesConfig

from backend.config import settings
from backend.models.schemas import ModulationSchedule
from backend.llm_engine.prompts import build_schedule_prompt
from backend.llm_engine.fallbacks import get_fallback_schedule
from backend.llm_engine.validator import parse_llm_response

MAX_RETRIES = 2


class LLMEngine:
    def __init__(self):
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    # initially loading in async to avoid blocking startup
    async def load(self):
        print(f"Loading {settings.hf_model_id} on {self.device}...")
        start = time.time()

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._load_model)

        elapsed = time.time() - start
        print(f"Model loaded in {elapsed:.1f}s on {self.device}")

    # models loaded in synchronous threads 
    def _load_model(self):
        self.tokenizer = AutoTokenizer.from_pretrained(settings.hf_model_id)

        model_kwargs = {"device_map": "auto"}
        if settings.quantization == "8bit":
            model_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
        elif settings.quantization == "4bit":
            model_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)
        else:
            model_kwargs["torch_dtype"] = torch.float16

        self.model = AutoModelForCausalLM.from_pretrained(settings.hf_model_id, **model_kwargs)

# Quen Schedule
    def generate_schedule(self, intent: str, duration_minutes: int = 25) -> ModulationSchedule:
        prompt = build_schedule_prompt(intent, duration_minutes)

        messages = [{"role": "user", "content": prompt}]
        input_text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(input_text, return_tensors="pt").to(self.device)

        last_error = None
        for attempt in range(MAX_RETRIES + 1):
            start = time.time()
            with torch.no_grad():
                outputs = self.model.generate(
                    **inputs,
                    max_new_tokens=settings.llm_max_new_tokens,
                    temperature=settings.llm_temperature,
                    top_p=0.95,
                    do_sample=True,
                )
            inference_time = time.time() - start
            print(f"LLM inference took {inference_time:.2f}s (attempt {attempt + 1})")

            # skipping input tokens to get only the new output tokens
            new_tokens = outputs[0][inputs["input_ids"].shape[1]:]
            raw_output = self.tokenizer.decode(new_tokens, skip_special_tokens=True)

            try:
                return parse_llm_response(raw_output)
            except json.JSONDecodeError as e:
                last_error = e
                print(f"LLM JSON parse failed (attempt {attempt + 1}): {e}")
            except ValidationError as e:
                last_error = e
                print(f"LLM validation failed (attempt {attempt + 1}): {e}")

        print(f"All retries exhausted, using fallback. Last error: {last_error}")
        print(f"Raw output (first 500 chars): {raw_output[:500]}")
        return get_fallback_schedule(intent, duration_minutes)


llm_engine = LLMEngine()
