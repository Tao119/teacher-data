from __future__ import annotations

from pathlib import Path
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    openai_api_key: str = Field(..., alias="OPENAI_API_KEY")
    google_api_key: str = Field(..., alias="GOOGLE_API_KEY")

    whisper_model: str = Field("whisper-1", alias="WHISPER_MODEL")
    gemini_model: str = Field("gemini-2.0-flash", alias="GEMINI_MODEL")

    language: str = Field("ja", alias="LANGUAGE")
    concurrency: int = Field(4, alias="CONCURRENCY")

    output_dir: Path = Field(Path("output"), alias="OUTPUT_DIR")
    cache_dir: Path = Field(Path(".cache"), alias="CACHE_DIR")

    similarity_agree_threshold: float = Field(0.95, alias="SIMILARITY_AGREE_THRESHOLD")
    similarity_review_threshold: float = Field(0.80, alias="SIMILARITY_REVIEW_THRESHOLD")

    max_file_size_mb: float = Field(24.0, alias="MAX_FILE_SIZE_MB")
    chunk_duration_sec: int = Field(300, alias="CHUNK_DURATION_SEC")
