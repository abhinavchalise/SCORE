import asyncio
import functools
import json
import logging
import time

from backend.config import settings
from backend.models.schemas import ModulationSchedule

logger = logging.getLogger(__name__)

_CUDA_LIBS = ("libcudart.so.12", "libcublasLt.so.12", "libcublas.so.12")


def _preload_cuda_libs() -> None:
    import ctypes
    import site
    from pathlib import Path

    lib_dirs = []
    for site_dir in site.getsitepackages():
        nvidia = Path(site_dir) / "nvidia"
        lib_dirs += [nvidia / "cuda_runtime" / "lib", nvidia / "cublas" / "lib"]
    for lib_name in _CUDA_LIBS:
        for lib_dir in lib_dirs:
            candidate = lib_dir / lib_name
            if candidate.exists():
                ctypes.CDLL(str(candidate), mode=ctypes.RTLD_GLOBAL)
                break


class LlamaCppEngine:
    def __init__(self) -> None:
        self.model = None
        self._grammar = None

    async def load(self) -> None:
        logger.info("Loading GGUF %s on llama.cpp", settings.gguf_model_path)
        start = time.time()

        loop = asyncio.get_running_loop()
        await loop.run_in_executor(None, self._load_model)

        elapsed = time.time() - start
        logger.info("GGUF model loaded in %.1fs", elapsed)

    def _load_model(self) -> None:
        _preload_cuda_libs()
        from llama_cpp import Llama, LlamaGrammar

        self.model = Llama(
            model_path=settings.gguf_model_path,
            n_gpu_layers=settings.n_gpu_layers,
            n_ctx=settings.n_ctx,
            verbose=False,
        )
        schema = json.dumps(ModulationSchedule.model_json_schema())
        self._grammar = LlamaGrammar.from_json_schema(schema)

    def _generate(self, prompt: str) -> str:
        result = self.model.create_completion(
            prompt,
            grammar=self._grammar,
            max_tokens=settings.llm_max_new_tokens,
            temperature=settings.llm_temperature,
            top_p=settings.llm_top_p,
        )
        return result["choices"][0]["text"]

    async def generate_constrained(self, prompt: str) -> dict:
        loop = asyncio.get_running_loop()
        generate = functools.partial(self._generate, prompt)
        raw = await loop.run_in_executor(None, generate)
        return json.loads(raw)
