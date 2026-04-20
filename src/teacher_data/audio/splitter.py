from __future__ import annotations

import tempfile
from pathlib import Path

from pydub import AudioSegment
from pydub.silence import detect_nonsilent


def split_audio(path: Path, max_mb: float = 24.0, chunk_sec: int = 300) -> list[tuple[Path, float, float]]:
    """Split audio into chunks. Returns list of (temp_path, start_sec, end_sec)."""
    size_mb = path.stat().st_size / (1024 * 1024)
    audio = AudioSegment.from_file(str(path))
    duration_sec = len(audio) / 1000.0

    if size_mb <= max_mb:
        return [(path, 0.0, duration_sec)]

    chunks = []
    chunk_ms = chunk_sec * 1000
    offset = 0

    while offset < len(audio):
        end = min(offset + chunk_ms, len(audio))
        segment = audio[offset:end]

        tmp = tempfile.NamedTemporaryFile(suffix=".wav", delete=False)
        tmp_path = Path(tmp.name)
        segment.export(str(tmp_path), format="wav")
        tmp.close()

        chunks.append((tmp_path, offset / 1000.0, end / 1000.0))
        offset = end

    return chunks
