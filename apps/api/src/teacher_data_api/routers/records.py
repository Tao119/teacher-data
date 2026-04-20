from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_db
from ..db.models import AudioFile, Record, RecordEdit
from ..schemas.record import RecordListOut, RecordOut, RecordUpdate

router = APIRouter(tags=["records"])


@router.get("/projects/{project_id}/records", response_model=RecordListOut)
async def list_records(
    project_id: str,
    bucket: str | None = None,
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
):
    q = select(Record).where(Record.project_id == project_id)
    if bucket:
        q = q.where(Record.bucket == bucket)
    total = await db.scalar(select(func.count()).select_from(q.subquery()))
    rows = (await db.execute(q.order_by(Record.similarity.asc()).offset((page - 1) * per_page).limit(per_page))).scalars().all()

    items = []
    for r in rows:
        af = await db.get(AudioFile, r.audio_file_id)
        out = RecordOut.model_validate(r)
        out.audio_file_name = af.original_name if af else None
        items.append(out)

    return RecordListOut(items=items, total=total or 0, page=page, per_page=per_page)


@router.get("/records/{record_id}", response_model=RecordOut)
async def get_record(record_id: str, db: AsyncSession = Depends(get_db)):
    r = await db.get(Record, record_id)
    if not r:
        raise HTTPException(404, "Record not found")
    af = await db.get(AudioFile, r.audio_file_id)
    out = RecordOut.model_validate(r)
    out.audio_file_name = af.original_name if af else None
    return out


@router.get("/records/{record_id}/audio")
async def stream_audio(record_id: str, db: AsyncSession = Depends(get_db)):
    r = await db.get(Record, record_id)
    if not r:
        raise HTTPException(404, "Record not found")
    af = await db.get(AudioFile, r.audio_file_id)
    if not af:
        raise HTTPException(404, "Audio file not found")

    path = Path(af.storage_path)
    if not path.exists():
        raise HTTPException(404, "Audio file missing on disk")

    suffix = path.suffix.lower()
    mime_map = {".mp3": "audio/mpeg", ".wav": "audio/wav", ".m4a": "audio/mp4", ".mp4": "audio/mp4", ".flac": "audio/flac", ".ogg": "audio/ogg"}
    media_type = mime_map.get(suffix, "audio/mpeg")

    def iterfile():
        with open(path, "rb") as f:
            yield from iter(lambda: f.read(65536), b"")

    return StreamingResponse(iterfile(), media_type=media_type, headers={
        "Content-Disposition": f'inline; filename="{path.name}"',
        "Accept-Ranges": "bytes",
    })


@router.patch("/records/{record_id}", response_model=RecordOut)
async def update_record(record_id: str, body: RecordUpdate, db: AsyncSession = Depends(get_db)):
    r = await db.get(Record, record_id)
    if not r:
        raise HTTPException(404, "Record not found")
    edit = RecordEdit(record_id=record_id, before_text=r.text, after_text=body.text, action="edit")
    r.text = body.text
    db.add(edit)
    await db.commit()
    await db.refresh(r)
    return RecordOut.model_validate(r)


@router.post("/records/{record_id}/approve", response_model=RecordOut)
async def approve_record(record_id: str, db: AsyncSession = Depends(get_db)):
    r = await db.get(Record, record_id)
    if not r:
        raise HTTPException(404, "Record not found")
    edit = RecordEdit(record_id=record_id, before_text=r.text, after_text=r.text, action="approve")
    r.bucket = "train"
    r.reviewed_at = datetime.now(timezone.utc)
    db.add(edit)
    await db.commit()
    await db.refresh(r)
    return RecordOut.model_validate(r)


@router.post("/records/{record_id}/reject", response_model=RecordOut)
async def reject_record(record_id: str, db: AsyncSession = Depends(get_db)):
    r = await db.get(Record, record_id)
    if not r:
        raise HTTPException(404, "Record not found")
    edit = RecordEdit(record_id=record_id, before_text=r.text, after_text=r.text, action="reject")
    r.reviewed_at = datetime.now(timezone.utc)
    db.add(edit)
    await db.commit()
    await db.refresh(r)
    return RecordOut.model_validate(r)


@router.post("/records/{record_id}/reset", response_model=RecordOut)
async def reset_record(record_id: str, db: AsyncSession = Depends(get_db)):
    r = await db.get(Record, record_id)
    if not r:
        raise HTTPException(404, "Record not found")
    edit = RecordEdit(record_id=record_id, before_text=r.text, after_text=r.original_text, action="reset")
    r.text = r.original_text
    db.add(edit)
    await db.commit()
    await db.refresh(r)
    return RecordOut.model_validate(r)
