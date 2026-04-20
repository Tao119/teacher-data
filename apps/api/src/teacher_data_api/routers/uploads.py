from __future__ import annotations

import hashlib
from pathlib import Path

from ulid import ULID
from fastapi import APIRouter, Depends, HTTPException, UploadFile
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_db
from ..db.models import AudioFile, Project, Record
from ..services.storage import audio_path

router = APIRouter(tags=["uploads"])

SUPPORTED = {".wav", ".mp3", ".m4a", ".mp4", ".flac", ".ogg", ".webm"}


@router.get("/projects/{project_id}/audio-files")
async def list_audio_files(project_id: str, db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(
        select(AudioFile).where(AudioFile.project_id == project_id).order_by(AudioFile.uploaded_at)
    )).scalars().all()
    return [{"id": r.id, "name": r.original_name, "status": r.status, "size_bytes": r.size_bytes, "error": r.error_message} for r in rows]


@router.post("/projects/{project_id}/uploads")
async def upload_audio(
    project_id: str,
    files: list[UploadFile],
    db: AsyncSession = Depends(get_db),
):
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")

    created = []
    for file in files:
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in SUPPORTED:
            continue

        data = await file.read()
        sha256 = hashlib.sha256(data).hexdigest()

        existing = (await db.execute(
            select(AudioFile).where(AudioFile.project_id == project_id, AudioFile.sha256 == sha256)
        )).scalar_one_or_none()
        if existing:
            existing.status = "pending"
            existing.error_message = None
            created.append({"id": existing.id, "name": file.filename, "duplicate": True})
            continue

        dest = audio_path(project_id, sha256, suffix)
        dest.write_bytes(data)

        af = AudioFile(
            id=str(ULID()),
            project_id=project_id,
            original_name=file.filename or "unknown",
            sha256=sha256,
            storage_path=str(dest),
            size_bytes=len(data),
            status="pending",
        )
        db.add(af)
        created.append({"id": af.id, "name": file.filename, "duplicate": False})

    await db.commit()
    return {"uploaded": len(created), "files": created}


@router.delete("/audio-files/{audio_file_id}", status_code=204)
async def delete_audio_file(audio_file_id: str, db: AsyncSession = Depends(get_db)):
    af = await db.get(AudioFile, audio_file_id)
    if not af:
        raise HTTPException(404, "AudioFile not found")

    await db.execute(delete(Record).where(Record.audio_file_id == audio_file_id))

    storage = Path(af.storage_path)
    if storage.exists():
        storage.unlink()

    await db.delete(af)
    await db.commit()
