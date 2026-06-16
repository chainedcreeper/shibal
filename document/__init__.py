"""문서 로더 통합 인터페이스.

지원: .pdf  .hwp  .hwpx  .pptx  .docx  .txt  .md
각 형식별로 여러 라이브러리를 병렬 실행 → 텍스트 가장 많은 결과 채택.
"""
from pathlib import Path

from . import hwp_loader, pdf_loader, pptx_loader, docx_loader, text_loader

SUPPORTED_EXTS = (".pdf", ".hwp", ".hwpx", ".pptx", ".docx", ".txt", ".md")


def extract_text(path: str) -> list[dict]:
    """파일 확장자로 적절한 로더 선택.

    반환: [{"text": str, "page": int}, ...]
    """
    ext = Path(path).suffix.lower()
    if ext == ".pdf":
        return pdf_loader.extract_text(path)
    if ext in (".hwp", ".hwpx"):
        return hwp_loader.extract_text(path)
    if ext == ".pptx":
        return pptx_loader.extract_text(path)
    if ext == ".docx":
        return docx_loader.extract_text(path)
    if ext in (".txt", ".md"):
        return text_loader.extract_text(path)
    raise ValueError(
        f"지원하지 않는 파일 형식: {ext} (지원: {', '.join(SUPPORTED_EXTS)})"
    )
