from __future__ import annotations

import re
import unicodedata


# 句読点・記号（比較時に無視）
_PUNCT = re.compile(r"[、。，．,.!！?？・…「」『』【】()（）\[\]〜~]")
# 空白系（全角スペース含む）
_SPACE = re.compile(r"[\s\u3000]+")

# カタカナ→ひらがな変換テーブル
_KATA_TO_HIRA = str.maketrans(
    "".join(chr(c) for c in range(0x30A1, 0x30F7)),
    "".join(chr(c) for c in range(0x3041, 0x3097)),
)


def normalize(text: str) -> str:
    """表記ゆれを吸収して比較用文字列に変換する。"""
    # Unicode正規化（全角英数→半角、カナ統一など）
    text = unicodedata.normalize("NFKC", text)
    # カタカナ→ひらがな（「トン」と「とん」を同一視）
    text = text.translate(_KATA_TO_HIRA)
    # 句読点・記号を除去
    text = _PUNCT.sub("", text)
    # 空白・改行を完全除去（位置の違いを無視）
    text = _SPACE.sub("", text)
    return text.lower()
