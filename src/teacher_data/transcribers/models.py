from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class TranscriptSegment:
    text: str
    start_sec: float
    end_sec: float


@dataclass
class TranscriptResult:
    provider: str
    model: str
    text: str
    language: str
    segments: list[TranscriptSegment] = field(default_factory=list)
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None
