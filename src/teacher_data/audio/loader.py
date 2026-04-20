from __future__ import annotations

from pathlib import Path

SUPPORTED_EXTENSIONS = {".wav", ".mp3", ".m4a", ".mp4", ".flac", ".ogg", ".webm"}


def find_audio_files(path: Path) -> list[Path]:
    if path.is_file():
        if path.suffix.lower() in SUPPORTED_EXTENSIONS:
            return [path]
        raise ValueError(f"Unsupported file type: {path.suffix}")

    files = [p for p in sorted(path.rglob("*")) if p.suffix.lower() in SUPPORTED_EXTENSIONS]
    if not files:
        raise ValueError(f"No audio files found in: {path}")
    return files
