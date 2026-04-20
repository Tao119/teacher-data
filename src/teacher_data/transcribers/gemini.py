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
    model: str = "gemini-2.0-flash",
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
            return TranscriptResult(
                provider="gemini",
                model=model,
                text=text,
                language=language,
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
