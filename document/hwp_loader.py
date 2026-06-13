"""HWP / HWPX 텍스트 추출 — 모든 라이브러리 병렬.

HWPX (신형, ZIP+OWPML XML):
    - python-hwpx (공식 API)
    - zipfile + lxml 로 Contents/section*.xml 직접 파싱 (폴백)

HWP5 (구형, OLE Compound Document):
    - pyhwp 의 hwp5txt CLI (subprocess)
    - olefile 로 PrvText 미리보기 스트림 직접 추출 (폴백)
"""
from __future__ import annotations

import subprocess
import zipfile
from pathlib import Path

from ._parallel import paginate, run_parallel


# ── HWPX ──────────────────────────────────────────────

def _python_hwpx(path: str) -> list[dict]:
    from hwpx import HwpxDocument

    doc = HwpxDocument.open(path)
    return paginate(doc.export_text())


def _xml_raw_hwpx(path: str) -> list[dict]:
    from lxml import etree

    chunks: list[str] = []
    with zipfile.ZipFile(path) as zf:
        names = sorted(
            n for n in zf.namelist()
            if n.startswith("Contents/section") and n.endswith(".xml")
        )
        for name in names:
            with zf.open(name) as f:
                tree = etree.parse(f)
            # OWPML 의 <hp:t> 텍스트 노드 (namespace 무시하고 local name 매칭)
            texts = [
                (t.text or "").strip()
                for t in tree.iter()
                if isinstance(t.tag, str) and t.tag.rsplit("}", 1)[-1] == "t"
            ]
            joined = "\n".join(t for t in texts if t)
            if joined:
                chunks.append(joined)
    return paginate("\n".join(chunks))


# ── HWP5 ──────────────────────────────────────────────

def _pyhwp_cli(path: str) -> list[dict]:
    result = subprocess.run(
        ["hwp5txt", path],
        capture_output=True, text=True, encoding="utf-8", timeout=120,
    )
    if result.returncode != 0:
        raise RuntimeError(f"hwp5txt: {result.stderr.strip()}")
    return paginate(result.stdout)


def _olefile_prvtext(path: str) -> list[dict]:
    """HWP5 의 PrvText 스트림 = 미리보기 텍스트 (utf-16-le)."""
    import olefile

    ole = olefile.OleFileIO(path)
    try:
        if not ole.exists("PrvText"):
            return []
        data = ole.openstream("PrvText").read()
        return paginate(data.decode("utf-16-le", errors="ignore"))
    finally:
        ole.close()


_HWPX_EXTRACTORS = {
    "python-hwpx": _python_hwpx,
    "xml-raw":     _xml_raw_hwpx,
}

_HWP5_EXTRACTORS = {
    "pyhwp":   _pyhwp_cli,
    "olefile": _olefile_prvtext,
}


def extract_text(path: str) -> list[dict]:
    ext = Path(path).suffix.lower()
    if ext == ".hwpx":
        return run_parallel(_HWPX_EXTRACTORS, path, min_chars=30)
    if ext == ".hwp":
        return run_parallel(_HWP5_EXTRACTORS, path, min_chars=30)
    raise ValueError(f"지원하지 않는 확장자: {ext}")
