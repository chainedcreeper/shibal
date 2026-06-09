import re
import fitz
from PIL import Image
from concurrent.futures import ThreadPoolExecutor

DPI = 192

_manager = None
_predictor = None
_surya_available = None


def _init_surya():
    global _manager, _predictor, _surya_available
    if _surya_available is not None:
        return _surya_available
    try:
        from surya.inference import SuryaInferenceManager
        from surya.recognition import RecognitionPredictor
        _manager = SuryaInferenceManager(lazy=True)
        _predictor = RecognitionPredictor(_manager)
        _surya_available = True
    except Exception:
        _surya_available = False
    return _surya_available


def _html_to_text(html: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html)
    text = re.sub(r"&nbsp;", " ", text)
    text = re.sub(r"&lt;", "<", text)
    text = re.sub(r"&gt;", ">", text)
    text = re.sub(r"&amp;", "&", text)
    return re.sub(r" +", " ", text).strip()


def _page_to_image(page) -> Image.Image:
    pix = page.get_pixmap(dpi=DPI)
    return Image.frombytes("RGB", [pix.width, pix.height], pix.samples)


def _extract_with_surya(doc) -> list:
    with ThreadPoolExecutor() as executor:
        images = list(executor.map(_page_to_image, list(doc)))

    page_results = _predictor(images, full_page=True)

    result = []
    for page_num, ocr_result in enumerate(page_results, start=1):
        blocks = sorted(
            (b for b in ocr_result.blocks if not b.skipped and not b.error),
            key=lambda b: b.reading_order if b.reading_order is not None else 9999,
        )
        text = "\n".join(_html_to_text(b.html) for b in blocks if b.html).strip()
        if text:
            result.append({"text": text, "page": page_num})
    return result


def _extract_with_fitz(doc) -> list:
    result = []
    for page in doc:
        text = page.get_text("text").strip()
        try:
            tables = page.find_tables()
            for table in tables:
                rows = table.extract()
                for row in rows:
                    text += "\n" + " | ".join(str(c) for c in row if c)
        except Exception:
            pass
        if text:
            result.append({"text": text, "page": page.number + 1})
    return result


_TEXT_MIN_PER_PAGE = 80

def extract_text(pdf_path: str) -> list:
    doc = fitz.open(pdf_path)
    try:
        pages = _extract_with_fitz(doc)
        total = sum(len(p["text"]) for p in pages)
        if total >= _TEXT_MIN_PER_PAGE * max(1, doc.page_count):
            return pages
        if _init_surya():
            try:
                return _extract_with_surya(doc)
            except Exception:
                pass
        return pages
    finally:
        doc.close()
