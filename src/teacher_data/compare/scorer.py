from __future__ import annotations

from rapidfuzz.distance import Levenshtein
from rapidfuzz import fuzz

from .aligner import normalize


def similarity(text_a: str, text_b: str) -> float:
    """Character-level similarity ratio between 0 and 1."""
    na, nb = normalize(text_a), normalize(text_b)
    if not na and not nb:
        return 1.0
    if not na or not nb:
        return 0.0
    return fuzz.ratio(na, nb) / 100.0


def cer(reference: str, hypothesis: str) -> float:
    """Character Error Rate."""
    ref = list(normalize(reference))
    hyp = list(normalize(hypothesis))
    if not ref:
        return 0.0 if not hyp else 1.0
    dist = Levenshtein.distance(ref, hyp)
    return dist / len(ref)
