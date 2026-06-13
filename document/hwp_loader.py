"""HWP / HWPX 텍스트 추출.

- HWPX: python-hwpx (순수 파이썬, XML 파싱)
- HWP5: pyhwp 의 hwp5txt CLI (subprocess 호출이 Python API 보다 안정)

둘 다 FreeType 의존 없음 — 가벼운 환경에서도 동작.
"""
from __future__ import annotations

import subprocess
from pathlib import Path

_PAGE_CHAR_LIMIT = 1000


def _paginate(text: str) -> list[dict]:
    pages: list[dict] = []
    buffer = ""
    page_num = 1
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if buffer and len(buffer) + len(line) > _PAGE_CHAR_LIMIT:
            pages.append({"text": buffer.strip(), "page": page_num})
            page_num += 1
            buffer = ""
        buffer = f"{buffer}\n{line}" if buffer else line
    if buffer.strip():
        pages.append({"text": buffer.strip(), "page": page_num})
    return pages


def _extract_hwpx(path: str) -> str:
    from hwpx import HwpxDocument  # type: ignore

    doc = HwpxDocument.open(path)
    return doc.export_text()


def _extract_hwp5(path: str) -> str:
    try:
        result = subprocess.run(
            ["hwp5txt", path],
            capture_output=True, text=True, encoding="utf-8", timeout=120,
        )
    except FileNotFoundError as e:
        raise RuntimeError(
            "hwp5txt 명령을 찾을 수 없음. `pip install pyhwp` 필요."
        ) from e
    if result.returncode != 0:
        raise RuntimeError(f"hwp5txt 실패: {result.stderr.strip()}")
    return result.stdout


def extract_text(path: str) -> list[dict]:
    ext = Path(path).suffix.lower()
    if ext == ".hwpx":
        text = _extract_hwpx(path)
    elif ext == ".hwp":
        text = _extract_hwp5(path)
    else:
        raise ValueError(f"지원하지 않는 확장자: {ext}")

    if not text.strip():
        raise ValueError("HWP 에서 텍스트를 추출할 수 없습니다. (빈 문서 또는 이미지만 포함)")

    pages = _paginate(text)
    if not pages:
        raise ValueError("HWP 텍스트가 너무 짧아 처리할 수 없습니다.")
    return pages
