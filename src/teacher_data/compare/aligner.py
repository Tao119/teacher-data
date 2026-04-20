from __future__ import annotations

import re
import unicodedata
import pykakasi

# 句読点・記号（比較時に無視）
_PUNCT = re.compile(r"[、。，．,.!！?？・…「」『』【】()（）\[\]〜~]")
# 空白系（全角スペース含む）
_SPACE = re.compile(r"[\s\u3000]+")

# カタカナ→ひらがな変換テーブル
_KATA_TO_HIRA = str.maketrans(
    "".join(chr(c) for c in range(0x30A1, 0x30F7)),
    "".join(chr(c) for c in range(0x3041, 0x3097)),
)

_kks = pykakasi.kakasi()


def _to_yomi(text: str) -> str:
    """漢字を含む日本語テキストをひらがな読みに変換する。"""
    result = _kks.convert(text)
    return "".join(item["hira"] for item in result)


def normalize(text: str) -> str:
    """表記ゆれ・漢字変換の違いを吸収して比較用文字列に変換する。"""
    text = unicodedata.normalize("NFKC", text)
    text = _to_yomi(text)
    text = text.translate(_KATA_TO_HIRA)
    text = _PUNCT.sub("", text)
    text = _SPACE.sub("", text)
    return text.lower()
