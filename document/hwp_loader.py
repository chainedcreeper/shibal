"""HWP / HWPX 텍스트 추출.

rhwp-python (Rust + PyO3) 사용. HWP5 + HWPX 동일 API.
HWP는 페이지 개념이 약하므로 문단을 묶어 가상 page 번호를 매김.
"""
from __future__ import annotations

_PAGE_CHAR_LIMIT = 1000


def extract_text(path: str) -> list[dict]:
    import rhwp  # type: ignore

    doc = rhwp.parse(path)
    paragraphs = doc.paragraphs()

    pages: list[dict] = []
    buffer = ""
    page_num = 1

    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if buffer and len(buffer) + len(p) > _PAGE_CHAR_LIMIT:
            pages.append({"text": buffer.strip(), "page": page_num})
            page_num += 1
            buffer = ""
        buffer = f"{buffer}\n{p}" if buffer else p

    if buffer.strip():
        pages.append({"text": buffer.strip(), "page": page_num})

    if not pages:
        raise ValueError("HWP에서 텍스트를 추출할 수 없습니다. (빈 문서 또는 이미지만 포함)")

    return pages
