import asyncio
import functools
import json
import logging
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer, BitsAndBytesConfig

from backend.config import settings
from backend.models.schemas import ModulationSchedule

logger = logging.getLogger(__name__)


class LLMEngine:
    def __init__(self) -> None:
        self.model = None
        self.tokenizer = None
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self._constrained_generator = None

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

    def _build_constrained_generator(self):
        import outlines

        constrained_model = outlines.models.Transformers(self.model, self.tokenizer)
        sampler = outlines.samplers.multinomial(
            temperature=settings.llm_temperature, top_p=settings.llm_top_p
        )
        return outlines.generate.json(
            constrained_model, ModulationSchedule, sampler=sampler, whitespace_pattern=""
        )

    async def generate_constrained(self, prompt: str) -> dict:
        if self._constrained_generator is None:
            self._constrained_generator = self._build_constrained_generator()
            self._constrained_generator.format_sequence = lambda text: text

        loop = asyncio.get_running_loop()
        generate = functools.partial(
            self._constrained_generator, prompt, max_tokens=settings.llm_max_new_tokens
        )
        raw = await loop.run_in_executor(None, generate)
        return json.loads(raw)


llm_engine = LLMEngine()
