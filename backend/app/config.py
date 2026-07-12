from typing import Literal, Optional
from pathlib import Path

from pydantic import model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parents[1]


def _resolve_path(value: str) -> str:
    path = Path(value)
    if path.is_absolute():
        return str(path)
    return str((BASE_DIR / path).resolve())


def _resolve_sqlite_url(value: str) -> str:
    prefix = "sqlite:///"
    if not value.startswith(prefix):
        return value
    raw_path = value[len(prefix) :]
    if not raw_path.startswith("."):
        return value
    resolved = Path(_resolve_path(raw_path))
    return f"sqlite:///{resolved.as_posix()}"


class Settings(BaseSettings):
    """Application settings from environment variables."""

    model_config = SettingsConfigDict(env_file=".env", case_sensitive=False)

    # Environment
    environment: Literal["development", "staging", "production"] = "development"
    debug: bool = False
    log_level: str = "INFO"

    # Server
    api_host: str = "0.0.0.0"
    api_port: int = 8000

    # Database
    database_url: str = "sqlite:///./agrisense.db"
    sql_echo: bool = False

    # Gemini Vision
    gemini_api_key: Optional[str] = None
    gemini_base_url: str = "https://generativelanguage.googleapis.com/v1beta"
    gemini_model: str = "gemini-2.0-flash-exp"
    gemini_timeout_seconds: float = 45.0
    gemini_max_retries: int = 3
    gemini_retry_backoff_seconds: float = 1.5
    gemini_max_image_side: int = 1024
    gemini_image_jpeg_quality: int = 82
    gemini_max_upload_bytes: int = 8_388_608

    # OpenRouter
    openrouter_api_key: Optional[str] = ""
    openrouter_base_url: str = "https://openrouter.ai/api/v1"
    openrouter_model: str = "meta-llama/llama-3.3-70b-instruct"
    openrouter_timeout_seconds: float = 60.0
    openrouter_max_retries: int = 3
    openrouter_retry_backoff_seconds: float = 1.5
    openrouter_temperature: float = 0.2
    openrouter_max_tokens: int = 2048
    openrouter_reasoning_effort: Literal["none", "low", "medium", "high", "xhigh", "max"] = "high"
    openrouter_site_url: str = "http://localhost:8000"
    openrouter_app_name: str = "AgriSense AI"
    openrouter_rate_limit_rpm: int = 10

    # OpenRouter Vision
    openrouter_vision_model: str = "openai/gpt-4o-mini"
    openrouter_vision_timeout_seconds: float = 60.0
    openrouter_vision_max_retries: int = 3
    openrouter_vision_retry_backoff_seconds: float = 1.5
    openrouter_vision_max_image_side: int = 1024
    openrouter_vision_image_jpeg_quality: int = 82
    openrouter_vision_max_upload_bytes: int = 8_388_608

    # RAG
    faiss_index_path: str = "./data/faiss_index"
    documents_path: str = "./data/documents"
    rag_embedding_model: str = "all-MiniLM-L6-v2"

    @model_validator(mode="after")
    def _normalize_paths(self) -> "Settings":
        self.database_url = _resolve_sqlite_url(self.database_url)
        self.faiss_index_path = _resolve_path(self.faiss_index_path)
        self.documents_path = _resolve_path(self.documents_path)
        return self


settings = Settings()
