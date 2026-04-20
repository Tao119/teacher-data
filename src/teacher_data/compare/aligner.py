from __future__ import annotations

import re
import unicodedata


def normalize(text: str) -> str:
    text = unicodedata.normalize("NFKC", text)
    text = re.sub(r"[\s\u3000]+", " ", text)
    text = re.sub(r"[、。，．,\.]", "", text)
    return text.strip().lower()
