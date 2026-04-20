from __future__ import annotations

import json
from pathlib import Path

from .schema import DatasetRecord


class DatasetWriter:
    def __init__(self, output_dir: Path) -> None:
        self._dir = output_dir
        self._dir.mkdir(parents=True, exist_ok=True)
        self._train = self._dir / "train.jsonl"
        self._review = self._dir / "review.jsonl"
        self._raw = self._dir / "raw.jsonl"

    def write(self, record: DatasetRecord) -> None:
        line = record.model_dump_json()
        self._raw.open("a", encoding="utf-8").write(line + "\n")

        if record.quality.needs_review:
            self._review.open("a", encoding="utf-8").write(line + "\n")
        else:
            self._train.open("a", encoding="utf-8").write(line + "\n")

    @property
    def train_path(self) -> Path:
        return self._train

    @property
    def review_path(self) -> Path:
        return self._review
