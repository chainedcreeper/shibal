"""문서 로더 통합 인터페이스.

지원 형식: .pdf, .hwp, .hwpx
"""
from pathlib import Path

from .pdf_loader import extract_text as _extract_pdf
from .hwp_loader import extract_text as _extract_hwp

SUPPORTED_EXTS = (".pdf", ".hwp", ".hwpx")


def extract_text(path: str) -> list[dict]:
    """파일 확장자로 적절한 로더 선택.

    반환: [{"text": str, "page": int}, ...]
    """
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return _extract_pdf(path)
    if ext in (".hwp", ".hwpx"):
        return _extract_hwp(path)
    raise ValueError(f"지원하지 않는 파일 형식: {ext} (지원: {', '.join(SUPPORTED_EXTS)})")
