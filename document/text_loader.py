"""순수 텍스트 로더 — .txt / .md.

인코딩 감지 fallback (UTF-8 → CP949 → Latin-1).
.md 의 마크다운 강조 (* _ # ` 등) 는 그대로 보존 (RAG 컨텍스트로 충분).
페이지 개념이 없으므로 빈 줄 2개 기준으로 page 분할.
"""
from __future__ import annotations

import re


_PAGE_BREAK = re.compile(r"\n{2,}")


def _read(path: str) -> str:
    """인코딩 자동 감지 — UTF-8 우선, CP949, Latin-1 fallback."""
    for enc in ("utf-8", "utf-8-sig", "cp949", "latin-1"):
        try:
            with open(path, encoding=enc) as f:
                return f.read()
        except UnicodeDecodeError:
            continue
    # 마지막 보루 — 에러 무시
    with open(path, encoding="utf-8", errors="ignore") as f:
        return f.read()


def extract_text(path: str) -> list[dict]:
    """텍스트 → [{"text": ..., "page": N}, ...] 형식.

    페이지 분할: 빈 줄 2개 이상 → 한 페이지.
    페이지 너무 짧으면 (50자 미만) 다음 페이지와 병합.
    """
    raw = _read(path).strip()
    if not raw:
        return [{"text": "", "page": 1}]

    chunks = [c.strip() for c in _PAGE_BREAK.split(raw) if c.strip()]
    if not chunks:
        return [{"text": raw, "page": 1}]

    # 너무 짧은 청크 병합
    pages: list[str] = []
    buf = ""
    for c in chunks:
        if len(buf) + len(c) < 500:
            buf = f"{buf}\n\n{c}".strip() if buf else c
        else:
            if buf:
                pages.append(buf)
            buf = c
    if buf:
        pages.append(buf)

    return [{"text": p, "page": i + 1} for i, p in enumerate(pages)]
