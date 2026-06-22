import asyncio
import json
import logging
import time

import torch
from pydantic import ValidationError
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from backend.config import settings
from backend.llm_engine.fallbacks import get_fallback_schedule
from backend.llm_engine.prompts import build_schedule_prompt
from backend.llm_engine.validator import parse_llm_response
from backend.models.schemas import ModulationSchedule

logger = logging.getLogger(__name__)

MAX_RETRIES = 2


class LLMEngine:
    def __init__(self) -> None:
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"

    async def load(self) -> None:
        logger.info("Loading %s on %s", settings.hf_model_id, self.device)
        start = time.time()

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._load_model)

        elapsed = time.time() - start
        logger.info("Model loaded in %.1fs on %s", elapsed, self.device)

    def _load_model(self) -> None:
        self.tokenizer = AutoTokenizer.from_pretrained(settings.hf_model_id)

        model_kwargs = {"device_map": "auto"}
        if settings.quantization == "8bit":
            model_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_8bit=True)
        elif settings.quantization == "4bit":
            model_kwargs["quantization_config"] = BitsAndBytesConfig(load_in_4bit=True)
        else:
            model_kwargs["torch_dtype"] = torch.float16

        self.model = AutoModelForCausalLM.from_pretrained(settings.hf_model_id, **model_kwargs)

    def generate_schedule(self, intent: str, duration_minutes: int = 25) -> ModulationSchedule:
        prompt = build_schedule_prompt(intent, duration_minutes)

        last_error = None
        raw_output = ""
        for attempt in range(MAX_RETRIES + 1):
            start = time.time()
            raw_output = self._generate_text(prompt)
            inference_time = time.time() - start
            logger.info("LLM inference took %.2fs (attempt %d)", inference_time, attempt + 1)

            try:
                return parse_llm_response(raw_output)
            except json.JSONDecodeError as e:
                last_error = e
                logger.warning("LLM JSON parse failed (attempt %d): %s", attempt + 1, e)
            except ValidationError as e:
                last_error = e
                logger.warning("LLM validation failed (attempt %d): %s", attempt + 1, e)

        logger.warning("All retries exhausted, using fallback. Last error: %s", last_error)
        logger.debug("Raw LLM output (first 500 chars): %s", raw_output[:500])
        return get_fallback_schedule(intent, duration_minutes)

    def _generate_text(self, prompt: str) -> str:
        messages = [{"role": "user", "content": prompt}]
        input_text = self.tokenizer.apply_chat_template(
            messages, tokenize=False, add_generation_prompt=True
        )
        inputs = self.tokenizer(input_text, return_tensors="pt").to(self.device)
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=settings.llm_max_new_tokens,
                temperature=settings.llm_temperature,
                top_p=settings.llm_top_p,
                do_sample=True,
            )
        new_tokens = outputs[0][inputs["input_ids"].shape[1] :]
        return self.tokenizer.decode(new_tokens, skip_special_tokens=True)

    async def generate_constrained(self, prompt: str, schema: type = ModulationSchedule) -> dict:
        # schema reserved for constrained decoding
        loop = asyncio.get_running_loop()
        raw_output = await loop.run_in_executor(None, self._generate_text, prompt)
        return parse_llm_response(raw_output).model_dump()


llm_engine = LLMEngine()
