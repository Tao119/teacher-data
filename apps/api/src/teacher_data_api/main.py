from __future__ import annotations

from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parents[4] / ".env")

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .db.base import init_db
from .routers import exports, jobs, projects, records, uploads

app = FastAPI(title="Teacher Data API", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def startup():
    await init_db()


app.include_router(projects.router, prefix="/api/v1")
app.include_router(uploads.router, prefix="/api/v1")
app.include_router(jobs.router, prefix="/api/v1")
app.include_router(records.router, prefix="/api/v1")
app.include_router(exports.router, prefix="/api/v1")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}
