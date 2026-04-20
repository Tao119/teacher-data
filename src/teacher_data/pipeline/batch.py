from __future__ import annotations

import asyncio
from pathlib import Path

from ..audio.loader import find_audio_files
from ..config import Settings
from ..dataset.writer import DatasetWriter
from ..pipeline.orchestrator import process_file
from ..utils.cache import Cache
from ..utils.logging import get_logger

log = get_logger(__name__)


async def run_batch(
    input_path: Path,
    settings: Settings,
    writer: DatasetWriter,
    cache: Cache,
) -> dict[str, int]:
    files = find_audio_files(input_path)
    log.info("batch start", total_files=len(files))

    sem = asyncio.Semaphore(settings.concurrency)
    total_written = 0
    total_failed = 0

    async def _process_one(path: Path, idx: int) -> None:
        nonlocal total_written, total_failed
        async with sem:
            try:
                n = await process_file(path, settings, writer, cache, idx)
                total_written += n
            except Exception as e:
                log.error("file failed", file=path.name, error=str(e))
                total_failed += 1

    tasks = [_process_one(p, i) for i, p in enumerate(files)]
    await asyncio.gather(*tasks)

    return {"written": total_written, "failed": total_failed, "total": len(files)}
