from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class ProjectCreate(BaseModel):
    name: str
    description: str = ""
    language: str = "ja"
    agree_threshold: float = 0.95
    review_threshold: float = 0.80
    concurrency: int = 2


class ProjectUpdate(BaseModel):
    name: str | None = None
    description: str | None = None
    agree_threshold: float | None = None
    review_threshold: float | None = None
    concurrency: int | None = None


class ProjectStats(BaseModel):
    total_records: int
    train_count: int
    review_count: int
    avg_similarity: float
    total_audio_files: int


class ProjectOut(BaseModel):
    id: str
    name: str
    description: str
    language: str
    agree_threshold: float
    review_threshold: float
    concurrency: int
    created_at: datetime
    updated_at: datetime
    stats: ProjectStats | None = None

    model_config = {"from_attributes": True}
