from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class AudioMeta(BaseModel):
    path: str
    sha256: str
    duration_sec: float
    start_sec: float
    end_sec: float


class SourceMeta(BaseModel):
    strategy: str
    whisper: str
    gemini: str
    similarity: float
    chosen: str
    confidence: float


class QualityMeta(BaseModel):
    cer: float
    needs_review: bool


class DatasetRecord(BaseModel):
    id: str
    audio: AudioMeta
    text: str
    language: str
    source: SourceMeta
    quality: QualityMeta
    created_at: datetime
