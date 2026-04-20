from __future__ import annotations

import io
import json
import zipfile

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_db
from ..db.models import AudioFile, Project, Record

router = APIRouter(tags=["exports"])


def _record_to_dict(r: Record, af: AudioFile | None) -> dict:
    return {
        "id": r.id,
        "audio": {
            "path": af.original_name if af else "",
            "sha256": af.sha256 if af else "",
            "duration_sec": round(r.end_sec - r.start_sec, 3),
            "start_sec": r.start_sec,
            "end_sec": r.end_sec,
        },
        "text": r.text,
        "language": r.project_id,
        "source": {
            "strategy": r.strategy,
            "whisper": r.whisper_text,
            "gemini": r.gemini_text,
            "similarity": r.similarity,
            "chosen": r.strategy,
            "confidence": r.confidence,
        },
        "quality": {"cer": r.cer, "needs_review": r.bucket == "review"},
    }


@router.get("/projects/{project_id}/export/train.jsonl")
async def export_train(project_id: str, db: AsyncSession = Depends(get_db)):
    return await _export_jsonl(project_id, "train", db)


@router.get("/projects/{project_id}/export/review.jsonl")
async def export_review(project_id: str, db: AsyncSession = Depends(get_db)):
    return await _export_jsonl(project_id, "review", db)


async def _export_jsonl(project_id: str, bucket: str, db: AsyncSession):
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")

    rows = (await db.execute(
        select(Record).where(Record.project_id == project_id, Record.bucket == bucket).order_by(Record.created_at)
    )).scalars().all()

    async def generate():
        for r in rows:
            af = await db.get(AudioFile, r.audio_file_id)
            yield json.dumps(_record_to_dict(r, af), ensure_ascii=False) + "\n"

    filename = f"{p.name}_{bucket}.jsonl"
    return StreamingResponse(generate(), media_type="application/x-ndjson", headers={
        "Content-Disposition": f'attachment; filename="{filename}"'
    })


@router.get("/projects/{project_id}/export.zip")
async def export_zip(project_id: str, db: AsyncSession = Depends(get_db)):
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")

    rows = (await db.execute(
        select(Record).where(Record.project_id == project_id).order_by(Record.bucket, Record.created_at)
    )).scalars().all()

    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as zf:
        for bucket in ("train", "review"):
            lines = []
            for r in rows:
                if r.bucket == bucket:
                    af = await db.get(AudioFile, r.audio_file_id)
                    lines.append(json.dumps(_record_to_dict(r, af), ensure_ascii=False))
            zf.writestr(f"{bucket}.jsonl", "\n".join(lines) + "\n" if lines else "")

    buf.seek(0)
    return StreamingResponse(iter([buf.read()]), media_type="application/zip", headers={
        "Content-Disposition": f'attachment; filename="{p.name}_dataset.zip"'
    })
