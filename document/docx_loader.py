"""DOCX 로더 — python-docx 기반.

추출 대상:
    문단 (paragraphs) · 표 (tables) · 헤더/푸터.
페이지 분할:
    DOCX 는 명시적 페이지 끝이 없으므로 — 섹션 또는 페이지 브레이크,
    또는 누적 글자 수 1500 자 기준 split.
"""
from __future__ import annotations


def _iter_block_items(doc):
    """문단 + 표를 문서 순서대로 yield."""
    from docx.oxml.ns import qn
    body = doc.element.body
    for child in body.iterchildren():
        tag = child.tag
        if tag == qn("w:p"):
            yield ("p", child)
        elif tag == qn("w:tbl"):
            yield ("tbl", child)


def _para_text(p_element, doc) -> str:
    """<w:p> 요소에서 텍스트 추출."""
    from docx.text.paragraph import Paragraph
    return Paragraph(p_element, doc).text.strip()


def _table_text(t_element, doc) -> str:
    """<w:tbl> 요소에서 행/셀 텍스트 추출."""
    from docx.table import Table
    table = Table(t_element, doc)
    rows = []
    for row in table.rows:
        cells = [cell.text.strip() for cell in row.cells]
        rows.append(" | ".join(cells))
    return "\n".join(rows)


def _has_page_break(p_element) -> bool:
    from docx.oxml.ns import qn
    for br in p_element.iter(qn("w:br")):
        if br.get(qn("w:type")) == "page":
            return True
    return False


def extract_text(path: str) -> list[dict]:
    """DOCX → [{"text": ..., "page": N}, ...]."""
    from docx import Document
    doc = Document(path)

    pages: list[str] = []
    buf = ""

    # 헤더 텍스트 한 번에 (첫 페이지에 prefix 로 박음)
    headers = []
    for sec in doc.sections:
        if sec.header:
            for p in sec.header.paragraphs:
                t = p.text.strip()
                if t:
                    headers.append(t)
    if headers:
        buf = "[헤더] " + " · ".join(headers) + "\n\n"

    for kind, el in _iter_block_items(doc):
        if kind == "p":
            t = _para_text(el, doc)
            if t:
                buf = (buf + "\n" + t).strip() if buf else t
            # 명시적 페이지 브레이크
            if _has_page_break(el) and buf:
                pages.append(buf)
                buf = ""
        else:  # 표
            t = _table_text(el, doc)
            if t:
                buf = (buf + "\n\n[표]\n" + t).strip() if buf else "[표]\n" + t
        # 누적 글자 수 1500 자 넘으면 페이지 분할
        if len(buf) > 1500:
            pages.append(buf)
            buf = ""

    if buf:
        pages.append(buf)

    if not pages:
        return [{"text": "", "page": 1}]
    return [{"text": p, "page": i + 1} for i, p in enumerate(pages)]
