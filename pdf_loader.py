import fitz
from PIL import Image

_det_model = None
_det_processor = None
_rec_model = None
_rec_processor = None

TEXT_MIN_LEN = 50


def _load_surya():
    global _det_model, _det_processor, _rec_model, _rec_processor
    if _det_model is not None:
        return
    from surya.model.detection.segformer import (
        load_model as load_det_model,
        load_processor as load_det_processor,
    )
    from surya.model.recognition.model import load_model as load_rec_model
    from surya.model.recognition.processor import load_processor as load_rec_processor
    _det_processor = load_det_processor()
    _det_model = load_det_model()
    _rec_model = load_rec_model()
    _rec_processor = load_rec_processor()


def _ocr_page(page) -> str:
    from surya.ocr import run_ocr
    _load_surya()
    mat = fitz.Matrix(2, 2)
    pix = page.get_pixmap(matrix=mat)
    img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
    results = run_ocr(
        [img], [["ko", "en"]],
        _det_model, _det_processor,
        _rec_model, _rec_processor,
    )
    return "
".join(line.text for line in results[0].text_lines)


def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    result = []
    for page in doc:
        text = page.get_text("text").strip()

        try:
            tables = page.find_tables()
            for table in tables:
                rows = table.extract()
                for row in rows:
                    text += "
" + " | ".join(str(c) for c in row if c)
        except Exception:
            pass

        if len(text) < TEXT_MIN_LEN:
            try:
                text = _ocr_page(page)
            except Exception:
                pass

        if text:
            result.append({"text": text, "page": page.number + 1})

    doc.close()
    return result
