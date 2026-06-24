import asyncio
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
        return outlines.generate.json(constrained_model, ModulationSchedule)

    async def generate_constrained(self, prompt: str) -> dict:
        if self._constrained_generator is None:
            self._constrained_generator = self._build_constrained_generator()

        loop = asyncio.get_running_loop()
        schedule = await loop.run_in_executor(None, self._constrained_generator, prompt)
        return schedule.model_dump()


llm_engine = LLMEngine()
