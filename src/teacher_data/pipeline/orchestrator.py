from __future__ import annotations

import asyncio
from datetime import datetime, timezone
from pathlib import Path

from ..audio.splitter import split_audio
from ..compare.merger import merge
from ..config import Settings
from ..dataset.schema import AudioMeta, DatasetRecord, QualityMeta, SourceMeta
from ..dataset.writer import DatasetWriter
from ..transcribers.gemini import transcribe_gemini
from ..transcribers.whisper import transcribe_whisper
from ..utils.cache import Cache, file_sha256
from ..utils.logging import get_logger

log = get_logger(__name__)


async def process_file(
    path: Path,
    settings: Settings,
    writer: DatasetWriter,
    cache: Cache,
    file_index: int,
) -> int:
    sha256 = file_sha256(path)
    log.info("processing", file=path.name, sha256=sha256[:8])

    chunks = split_audio(path, max_mb=settings.max_file_size_mb, chunk_sec=settings.chunk_duration_sec)
    written = 0

    for chunk_idx, (chunk_path, start_sec, end_sec) in enumerate(chunks):
        w_key = cache.make_key(sha256, "openai", settings.whisper_model)
        g_key = cache.make_key(sha256, "gemini", settings.gemini_model)

        if len(chunks) > 1:
            w_key += f"_chunk{chunk_idx}"
            g_key += f"_chunk{chunk_idx}"

        whisper_cached = cache.get(w_key)
        gemini_cached = cache.get(g_key)

        from ..transcribers.models import TranscriptResult

        if whisper_cached:
            whisper = TranscriptResult(**whisper_cached)
        else:
            whisper = await transcribe_whisper(
                chunk_path, settings.openai_api_key, settings.whisper_model, settings.language
            )
            cache.set(w_key, {
                "provider": whisper.provider, "model": whisper.model,
                "text": whisper.text, "language": whisper.language,
                "segments": [], "error": whisper.error,
            })

        if gemini_cached:
            gemini = TranscriptResult(**gemini_cached)
        else:
            gemini = await transcribe_gemini(
                chunk_path, settings.google_api_key, settings.gemini_model, settings.language
            )
            cache.set(g_key, {
                "provider": gemini.provider, "model": gemini.model,
                "text": gemini.text, "language": gemini.language,
                "segments": [], "error": gemini.error,
            })

        merged = merge(
            whisper, gemini,
            agree_threshold=settings.similarity_agree_threshold,
            review_threshold=settings.similarity_review_threshold,
        )

        if merged.strategy == "both_failed":
            log.warning("both transcriptions failed", file=path.name, chunk=chunk_idx)
            continue

        record_id = f"{file_index:05d}_{chunk_idx:04d}"
        record = DatasetRecord(
            id=record_id,
            audio=AudioMeta(
                path=str(path),
                sha256=sha256,
                duration_sec=end_sec - start_sec,
                start_sec=start_sec,
                end_sec=end_sec,
            ),
            text=merged.text,
            language=settings.language,
            source=SourceMeta(
                strategy=merged.strategy,
                whisper=merged.whisper_text,
                gemini=merged.gemini_text,
                similarity=round(merged.sim, 4),
                chosen=merged.chosen,
                confidence=round(merged.confidence, 4),
            ),
            quality=QualityMeta(
                cer=round(merged.cer_score, 4),
                needs_review=merged.needs_review,
            ),
            created_at=datetime.now(timezone.utc),
        )
        writer.write(record)
        written += 1

        log.info(
            "chunk done",
            file=path.name,
            chunk=chunk_idx,
            strategy=merged.strategy,
            sim=f"{merged.sim:.2f}",
            needs_review=merged.needs_review,
        )

    return written
