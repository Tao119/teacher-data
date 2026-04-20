from __future__ import annotations

import asyncio
import os
from datetime import datetime, timezone
from pathlib import Path

from ..db.base import SessionLocal
from ..db.models import AudioFile, Job, Project, Record
from ..services import progress_bus
from teacher_data.config import Settings as CLISettings
from teacher_data.audio.splitter import split_audio
from teacher_data.compare.merger import merge
from teacher_data.transcribers.models import TranscriptResult
from teacher_data.transcribers.whisper import transcribe_whisper
from teacher_data.transcribers.gemini import transcribe_gemini
from teacher_data.utils.cache import Cache, file_sha256


_CACHE = Cache(Path(".cache"))
_running: dict[str, asyncio.Task] = {}


async def start_job(job_id: str, project_id: str, audio_file_ids: list[str]) -> None:
    task = asyncio.create_task(_run(job_id, project_id, audio_file_ids))
    _running[job_id] = task
    task.add_done_callback(lambda _: _running.pop(job_id, None))


async def _run(job_id: str, project_id: str, audio_file_ids: list[str]) -> None:
    try:
        async with SessionLocal() as db:
            job = await db.get(Job, job_id)
            if not job:
                return
            project = await db.get(Project, project_id)
            if not project:
                return

            job.status = "running"
            job.started_at = datetime.now(timezone.utc)
            job.total_files = len(audio_file_ids)
            await db.commit()

            settings = CLISettings(
                OPENAI_API_KEY=os.environ["OPENAI_API_KEY"],
                GOOGLE_API_KEY=os.environ["GOOGLE_API_KEY"],
                LANGUAGE=project.language,
                CONCURRENCY=project.concurrency,
                SIMILARITY_AGREE_THRESHOLD=project.agree_threshold,
                SIMILARITY_REVIEW_THRESHOLD=project.review_threshold,
            )

        sem = asyncio.Semaphore(settings.concurrency)
        tasks = [
            _process_one(job_id, project_id, af_id, settings, sem)
            for af_id in audio_file_ids
        ]
        results = await asyncio.gather(*tasks, return_exceptions=True)

        failed = sum(1 for r in results if isinstance(r, Exception))
        written = sum(r for r in results if isinstance(r, int))

        async with SessionLocal() as db:
            job = await db.get(Job, job_id)
            job.status = "failed" if failed == len(audio_file_ids) else "completed"
            job.completed_at = datetime.now(timezone.utc)
            job.failed = failed
            job.written = written
            await db.commit()

        await progress_bus.publish(job_id, "completed", {
            "job_id": job_id, "written": written, "failed": failed
        })

    except Exception as e:
        async with SessionLocal() as db:
            job = await db.get(Job, job_id)
            if job:
                job.status = "failed"
                job.error_message = str(e)
                job.completed_at = datetime.now(timezone.utc)
                await db.commit()
        await progress_bus.publish(job_id, "failed", {"job_id": job_id, "error": str(e)})


async def _process_one(
    job_id: str,
    project_id: str,
    audio_file_id: str,
    settings: CLISettings,
    sem: asyncio.Semaphore,
) -> int:
    async with sem:
        async with SessionLocal() as db:
            af = await db.get(AudioFile, audio_file_id)
            if not af:
                return 0
            af.status = "processing"
            await db.commit()

        try:
            path = Path(af.storage_path)
            sha256 = file_sha256(path)
            chunks = split_audio(path, max_mb=settings.max_file_size_mb, chunk_sec=settings.chunk_duration_sec)
            written = 0

            for chunk_idx, (chunk_path, start_sec, end_sec) in enumerate(chunks):
                w_key = _CACHE.make_key(sha256, "openai", settings.whisper_model) + f"_c{chunk_idx}"
                g_key = _CACHE.make_key(sha256, "gemini", settings.gemini_model) + f"_c{chunk_idx}"

                cached_w = _CACHE.get(w_key)
                cached_g = _CACHE.get(g_key)

                if cached_w:
                    whisper = TranscriptResult(**cached_w)
                else:
                    whisper = await transcribe_whisper(chunk_path, settings.openai_api_key, settings.whisper_model, settings.language)
                    _CACHE.set(w_key, {"provider": whisper.provider, "model": whisper.model, "text": whisper.text, "language": whisper.language, "segments": [], "error": whisper.error})

                if cached_g:
                    gemini = TranscriptResult(**cached_g)
                else:
                    gemini = await transcribe_gemini(chunk_path, settings.google_api_key, settings.gemini_model, settings.language)
                    _CACHE.set(g_key, {"provider": gemini.provider, "model": gemini.model, "text": gemini.text, "language": gemini.language, "segments": [], "error": gemini.error})

                merged = merge(whisper, gemini, settings.similarity_agree_threshold, settings.similarity_review_threshold)
                if merged.strategy == "both_failed":
                    continue

                from ulid import ULID
                async with SessionLocal() as db:
                    record = Record(
                        id=str(ULID()),
                        project_id=project_id,
                        audio_file_id=audio_file_id,
                        start_sec=start_sec,
                        end_sec=end_sec,
                        text=merged.text,
                        original_text=merged.text,
                        whisper_text=merged.whisper_text,
                        gemini_text=merged.gemini_text,
                        strategy=merged.strategy,
                        similarity=round(merged.sim, 4),
                        confidence=round(merged.confidence, 4),
                        cer=round(merged.cer_score, 4),
                        bucket="review" if merged.needs_review else "train",
                    )
                    db.add(record)
                    await db.commit()
                written += 1

            processed = 0
            total = 0
            file_name = audio_file_id
            async with SessionLocal() as db:
                af = await db.get(AudioFile, audio_file_id)
                if af:
                    af.status = "done"
                    af.error_message = None
                    file_name = af.original_name
                job = await db.get(Job, job_id)
                if job:
                    job.processed += 1
                    job.written += written
                    processed = job.processed
                    total = job.total_files
                await db.commit()

            await progress_bus.publish(job_id, "file_done", {
                "job_id": job_id,
                "file": file_name,
                "written": written,
                "processed": processed,
                "total": total,
            })
            return written

        except Exception as e:
            async with SessionLocal() as db:
                af_err = await db.get(AudioFile, audio_file_id)
                if af_err:
                    af_err.status = "failed"
                    af_err.error_message = str(e)
                    await db.commit()
            await progress_bus.publish(job_id, "file_error", {
                "job_id": job_id, "file": audio_file_id, "error": str(e)
            })
            raise
