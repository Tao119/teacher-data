from __future__ import annotations

from pathlib import Path

import openai

from .models import TranscriptResult, TranscriptSegment


async def transcribe_whisper(
    path: Path,
    api_key: str,
    model: str = "whisper-1",
    language: str = "ja",
) -> TranscriptResult:
    client = openai.AsyncOpenAI(api_key=api_key)
    try:
        with open(path, "rb") as f:
            response = await client.audio.transcriptions.create(
                model=model,
                file=f,
                language=language,
                response_format="verbose_json",
                timestamp_granularities=["segment"],
            )

        segments = []
        if hasattr(response, "segments") and response.segments:
            for seg in response.segments:
                segments.append(TranscriptSegment(
                    text=seg.text.strip(),
                    start_sec=seg.start,
                    end_sec=seg.end,
                ))

        duration = getattr(response, "duration", None)
        cost = round((duration / 60.0) * 0.006, 6) if duration else 0.0

        return TranscriptResult(
            provider="openai",
            model=model,
            text=response.text.strip(),
            language=response.language or language,
            segments=segments,
            cost_usd=cost,
        )
    except Exception as e:
        return TranscriptResult(
            provider="openai",
            model=model,
            text="",
            language=language,
            error=str(e),
        )
