from __future__ import annotations

import asyncio
from pathlib import Path

from google import genai
from google.genai import types

from .models import TranscriptResult


TRANSCRIPTION_PROMPT = (
    "この音声ファイルを正確に文字起こしをしてください。"
    "句読点や段落を適切に入れてください。"
    "テキストのみを出力し、説明や補足は一切加えないでください。"
)


async def transcribe_gemini(
    path: Path,
    api_key: str,
    model: str = "gemini-2.5-flash",
    language: str = "ja",
) -> TranscriptResult:
    def _sync_transcribe() -> TranscriptResult:
        try:
            client = genai.Client(api_key=api_key)

            with open(path, "rb") as f:
                audio_bytes = f.read()

            suffix = path.suffix.lower()
            mime_map = {
                ".wav": "audio/wav",
                ".mp3": "audio/mp3",
                ".m4a": "audio/mp4",
                ".mp4": "audio/mp4",
                ".flac": "audio/flac",
                ".ogg": "audio/ogg",
                ".webm": "audio/webm",
            }
            mime_type = mime_map.get(suffix, "audio/wav")

            response = client.models.generate_content(
                model=model,
                contents=[
                    TRANSCRIPTION_PROMPT,
                    types.Part.from_bytes(data=audio_bytes, mime_type=mime_type),
                ],
            )

            text = response.text.strip() if response.text else ""

            cost = 0.0
            if hasattr(response, "usage_metadata") and response.usage_metadata:
                u = response.usage_metadata
                input_tokens = getattr(u, "prompt_token_count", 0) or 0
                output_tokens = getattr(u, "candidates_token_count", 0) or 0
                # gemini-2.5-flash: $0.15/1M input, $0.60/1M output
                cost = round(input_tokens * 0.15 / 1_000_000 + output_tokens * 0.60 / 1_000_000, 6)

            return TranscriptResult(
                provider="gemini",
                model=model,
                text=text,
                language=language,
                cost_usd=cost,
            )
        except Exception as e:
            return TranscriptResult(
                provider="gemini",
                model=model,
                text="",
                language=language,
                error=str(e),
            )

    return await asyncio.get_event_loop().run_in_executor(None, _sync_transcribe)
