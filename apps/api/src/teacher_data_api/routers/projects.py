from __future__ import annotations

from ulid import ULID
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.base import get_db
from ..db.models import Project, Record
from ..schemas.project import ProjectCreate, ProjectOut, ProjectStats, ProjectUpdate

router = APIRouter(prefix="/projects", tags=["projects"])


async def _stats(db: AsyncSession, project_id: str) -> ProjectStats:
    total = await db.scalar(select(func.count()).where(Record.project_id == project_id))
    train = await db.scalar(select(func.count()).where(Record.project_id == project_id, Record.bucket == "train"))
    review = await db.scalar(select(func.count()).where(Record.project_id == project_id, Record.bucket == "review"))
    avg_sim = await db.scalar(select(func.avg(Record.similarity)).where(Record.project_id == project_id, Record.strategy != "fallback")) or 0.0
    total_cost = await db.scalar(select(func.sum(Record.cost_usd)).where(Record.project_id == project_id)) or 0.0
    from ..db.models import AudioFile
    total_af = await db.scalar(select(func.count()).where(AudioFile.project_id == project_id))
    return ProjectStats(total_records=total or 0, train_count=train or 0, review_count=review or 0, avg_similarity=round(avg_sim, 3), total_audio_files=total_af or 0, total_cost_usd=round(total_cost, 4))


@router.get("", response_model=list[ProjectOut])
async def list_projects(db: AsyncSession = Depends(get_db)):
    rows = (await db.execute(select(Project).order_by(Project.created_at.desc()))).scalars().all()
    result = []
    for p in rows:
        out = ProjectOut.model_validate(p)
        out.stats = await _stats(db, p.id)
        result.append(out)
    return result


@router.post("", response_model=ProjectOut, status_code=201)
async def create_project(body: ProjectCreate, db: AsyncSession = Depends(get_db)):
    p = Project(id=str(ULID()), **body.model_dump())
    db.add(p)
    await db.commit()
    await db.refresh(p)
    out = ProjectOut.model_validate(p)
    out.stats = await _stats(db, p.id)
    return out


@router.get("/{project_id}", response_model=ProjectOut)
async def get_project(project_id: str, db: AsyncSession = Depends(get_db)):
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    out = ProjectOut.model_validate(p)
    out.stats = await _stats(db, p.id)
    return out


@router.patch("/{project_id}", response_model=ProjectOut)
async def update_project(project_id: str, body: ProjectUpdate, db: AsyncSession = Depends(get_db)):
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    for k, v in body.model_dump(exclude_none=True).items():
        setattr(p, k, v)
    await db.commit()
    await db.refresh(p)
    out = ProjectOut.model_validate(p)
    out.stats = await _stats(db, p.id)
    return out


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: str, db: AsyncSession = Depends(get_db)):
    p = await db.get(Project, project_id)
    if not p:
        raise HTTPException(404, "Project not found")
    await db.delete(p)
    await db.commit()
