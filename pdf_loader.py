import fitz


def extract_text(pdf_path):
    doc = fitz.open(pdf_path)
    result = []
    for page in doc:
        text = page.get_text("text").strip()

        # 표 추출 후 텍스트 변환
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

    doc.close()
    return result
