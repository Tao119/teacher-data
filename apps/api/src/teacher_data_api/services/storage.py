from __future__ import annotations

from pathlib import Path


STORAGE_ROOT = Path(__file__).parents[5] / "storage"


def project_dir(project_id: str) -> Path:
    d = STORAGE_ROOT / "projects" / project_id / "audio"
    d.mkdir(parents=True, exist_ok=True)
    return d


def audio_path(project_id: str, sha256: str, suffix: str) -> Path:
    return project_dir(project_id) / f"{sha256}{suffix}"
