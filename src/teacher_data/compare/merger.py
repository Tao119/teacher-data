from __future__ import annotations

from dataclasses import dataclass

from ..transcribers.models import TranscriptResult
from .scorer import similarity, cer


@dataclass
class MergeResult:
    text: str
    strategy: str
    chosen: str
    whisper_text: str
    gemini_text: str
    sim: float
    confidence: float
    needs_review: bool
    cer_score: float


def merge(
    whisper: TranscriptResult,
    gemini: TranscriptResult,
    agree_threshold: float = 0.95,
    review_threshold: float = 0.80,
) -> MergeResult:
    w_text = whisper.text if whisper.success else ""
    g_text = gemini.text if gemini.success else ""

    if not whisper.success and not gemini.success:
        return MergeResult(
            text="", strategy="both_failed", chosen="none",
            whisper_text=w_text, gemini_text=g_text,
            sim=0.0, confidence=0.0, needs_review=True, cer_score=1.0,
        )

    if not whisper.success:
        return MergeResult(
            text=g_text, strategy="fallback", chosen="gemini",
            whisper_text=w_text, gemini_text=g_text,
            sim=0.0, confidence=0.7, needs_review=False, cer_score=0.0,
        )

    if not gemini.success:
        return MergeResult(
            text=w_text, strategy="fallback", chosen="whisper",
            whisper_text=w_text, gemini_text=g_text,
            sim=0.0, confidence=0.7, needs_review=False, cer_score=0.0,
        )

    sim = similarity(w_text, g_text)
    cer_score = cer(w_text, g_text)

    if sim >= agree_threshold:
        return MergeResult(
            text=w_text, strategy="agree", chosen="whisper",
            whisper_text=w_text, gemini_text=g_text,
            sim=sim, confidence=min(0.95 + (sim - agree_threshold) * 2, 1.0),
            needs_review=False, cer_score=cer_score,
        )

    if sim >= review_threshold:
        chosen = _pick_better(w_text, g_text)
        text = w_text if chosen == "whisper" else g_text
        return MergeResult(
            text=text, strategy="prefer", chosen=chosen,
            whisper_text=w_text, gemini_text=g_text,
            sim=sim, confidence=0.75, needs_review=False, cer_score=cer_score,
        )

    return MergeResult(
        text=w_text, strategy="diverged", chosen="whisper",
        whisper_text=w_text, gemini_text=g_text,
        sim=sim, confidence=0.5, needs_review=True, cer_score=cer_score,
    )


def _pick_better(w_text: str, g_text: str) -> str:
    """Simple heuristic: prefer the longer (more complete) transcription."""
    return "whisper" if len(w_text) >= len(g_text) else "gemini"
