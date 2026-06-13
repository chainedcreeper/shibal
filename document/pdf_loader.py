"""PDF 텍스트 추출.

1단계 — 텍스트 추출기 병렬: fitz, pdfplumber, pypdf
        → 가장 텍스트 많이 뽑힌 결과 채택

2단계 (폴백) — OCR 병렬: Surya, PaddleOCR
        → 1단계가 텍스트 부족할 때만 실행
"""
from __future__ import annotations

import os
import re
import tempfile
from concurrent.futures import ThreadPoolExecutor

from PIL import Image

from ._parallel import run_parallel

_DPI = 192
_TEXT_MIN_PER_PAGE = 80


def _fitz(path: str) -> list[dict]:
    import fitz

    doc = fitz.open(path)
    try:
        pages: list[dict] = []
        for page in doc:
            text = page.get_text("text").strip()
            try:
                for table in page.find_tables():
                    for row in table.extract():
                        text += "\n" + " | ".join(str(c) for c in row if c)
            except Exception:
                pass
            if text:
                pages.append({"text": text, "page": page.number + 1})
        return pages
    finally:
        doc.close()


def _pdfplumber(path: str) -> list[dict]:
    import pdfplumber

    pages: list[dict] = []
    with pdfplumber.open(path) as pdf:
        for i, page in enumerate(pdf.pages, 1):
            text = (page.extract_text() or "").strip()
            if text:
                pages.append({"text": text, "page": i})
    return pages


def _pypdf(path: str) -> list[dict]:
    from pypdf import PdfReader

    reader = PdfReader(path)
    pages: list[dict] = []
    for i, page in enumerate(reader.pages, 1):
        text = (page.extract_text() or "").strip()
        if text:
            pages.append({"text": text, "page": i})
    return pages


# ── OCR ───────────────────────────────────────────────

def _page_to_image(page) -> Image.Image:
    pix = page.get_pixmap(dpi=_DPI)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


def _html_to_text(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;|&amp;|&lt;|&gt;", " ", text)
    return re.sub(r" +", " ", text).strip()


def _surya(path: str) -> list[dict]:
    import fitz
    from surya.inference import SuryaInferenceManager
    from surya.recognition import RecognitionPredictor

    mgr = SuryaInferenceManager(lazy=True)
    predictor = RecognitionPredictor(mgr)
    doc = fitz.open(path)
    try:
        with ThreadPoolExecutor() as ex:
            images = list(ex.map(_page_to_image, list(doc)))
        page_results = predictor(images, full_page=True)
        out: list[dict] = []
        for i, ocr in enumerate(page_results, 1):
            blocks = sorted(
                (b for b in ocr.blocks if not b.skipped and not b.error),
                key=lambda b: b.reading_order if b.reading_order is not None else 9999,
            )
            text = "\n".join(_html_to_text(b.html) for b in blocks if b.html).strip()
            if text:
                out.append({"text": text, "page": i})
        return out
    finally:
        doc.close()


def _paddle(path: str) -> list[dict]:
    import fitz
    from paddleocr import PaddleOCR

    ocr = PaddleOCR(lang="korean", show_log=False)
    doc = fitz.open(path)
    try:
        out: list[dict] = []
        for page in doc:
            img = _page_to_image(page)
            with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                tmp_path = tmp.name
            try:
                img.save(tmp_path)
                try:
                    paddle_result = ocr.predict(tmp_path)
                    text = "\n".join(
                        line
                        for pg in (paddle_result or [])
                        for line in (pg.get("rec_texts") or [])
                    )
                except (AttributeError, TypeError):
                    paddle_result = ocr.ocr(tmp_path, cls=True)
                    text = "\n".join(
                        line[1][0]
                        for pg in (paddle_result or [])
                        for line in (pg or [])
                        if line and len(line) >= 2
                    )
                if text.strip():
                    out.append({"text": text.strip(), "page": page.number + 1})
            except Exception:
                pass
            finally:
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
        return out
    finally:
        doc.close()


_TEXT_EXTRACTORS = {
    "fitz":       _fitz,
    "pdfplumber": _pdfplumber,
    "pypdf":      _pypdf,
}

_OCR_EXTRACTORS = {
    "surya":  _surya,
    "paddle": _paddle,
}


def extract_text(path: str) -> list[dict]:
    """텍스트 추출기 3개 병렬 → 부족하면 OCR 2개 병렬."""
    try:
        return run_parallel(_TEXT_EXTRACTORS, path, min_chars=_TEXT_MIN_PER_PAGE)
    except ValueError:
        pass
    return run_parallel(_OCR_EXTRACTORS, path, min_chars=20)
