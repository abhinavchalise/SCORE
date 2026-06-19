from typing import Literal

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env", env_file_encoding="utf-8", protected_namespaces=("model_",)
    )

    api_title: str = "SCORE API"
    api_version: str = "1.0.0"
    api_description: str = "Local LLM backend that generates validated binaural-beat audio schedules from typed intent"

    host: str = "127.0.0.1"
    port: int = 8000
    debug: bool = True
    allowed_origins: list[str] = ["http://localhost:3000", "http://127.0.0.1:3000"]

    secret_key: str
    algorithm: str = "HS256"
    access_token_expire_minutes: int = 30
    database_url: str = "sqlite+aiosqlite:///./score.db"

    hf_model_id: str = "Qwen/Qwen3.5-9B-Instruct"
    quantization: Literal["8bit", "4bit", "none"] = "8bit"
    llm_max_new_tokens: int = 2048
    llm_temperature: float = 0.6
    llm_top_p: float = 0.95
    llm_timeout_seconds: int = 15


settings = Settings()
