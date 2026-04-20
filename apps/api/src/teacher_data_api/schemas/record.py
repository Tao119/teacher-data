from __future__ import annotations
from datetime import datetime
from pydantic import BaseModel


class RecordOut(BaseModel):
    id: str
    project_id: str
    audio_file_id: str
    start_sec: float
    end_sec: float
    text: str
    original_text: str
    whisper_text: str
    gemini_text: str
    strategy: str
    similarity: float
    confidence: float
    cer: float
    bucket: str
    reviewed_at: datetime | None
    created_at: datetime
    audio_file_name: str | None = None

    model_config = {"from_attributes": True}


class RecordUpdate(BaseModel):
    text: str


class RecordListOut(BaseModel):
    items: list[RecordOut]
    total: int
    page: int
    per_page: int
