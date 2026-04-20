from __future__ import annotations

from ulid import ULID
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_db
from ..db.models import AudioFile, Job
from ..services import progress_bus
from ..services.job_runner import start_job

router = APIRouter(tags=["jobs"])


class JobCreate(BaseModel):
    audio_file_ids: list[str] | None = None


@router.post("/projects/{project_id}/jobs", status_code=201)
async def create_job(project_id: str, body: JobCreate, db: AsyncSession = Depends(get_db)):
    if body.audio_file_ids:
        file_ids = body.audio_file_ids
    else:
        rows = (await db.execute(
            select(AudioFile.id).where(AudioFile.project_id == project_id, AudioFile.status == "pending")
        )).scalars().all()
        file_ids = list(rows)

    if not file_ids:
        raise HTTPException(400, "No pending files to process")

    job = Job(id=str(ULID()), project_id=project_id, total_files=len(file_ids))
    db.add(job)
    await db.commit()

    await start_job(job.id, project_id, file_ids)
    return {"job_id": job.id, "total_files": len(file_ids)}


@router.get("/jobs/{job_id}")
async def get_job(job_id: str, db: AsyncSession = Depends(get_db)):
    job = await db.get(Job, job_id)
    if not job:
        raise HTTPException(404, "Job not found")
    return {
        "id": job.id,
        "project_id": job.project_id,
        "status": job.status,
        "total_files": job.total_files,
        "processed": job.processed,
        "failed": job.failed,
        "written": job.written,
        "started_at": job.started_at,
        "completed_at": job.completed_at,
    }


@router.get("/jobs/{job_id}/events")
async def job_events(job_id: str):
    return StreamingResponse(
        progress_bus.stream(job_id),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
