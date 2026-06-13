"""공통 병렬 추출 헬퍼.

여러 추출기를 ThreadPoolExecutor 로 동시에 돌리고
텍스트가 가장 많이 뽑힌 결과를 채택.
실패한 추출기는 무시하고 계속 진행.
"""
from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Callable

Extractor = Callable[[str], list[dict]]


def run_parallel(
    extractors: dict[str, Extractor],
    path: str,
    min_chars: int = 100,
) -> list[dict]:
    """모든 추출기 병렬 실행 → 최장 텍스트 채택.

    실패는 무시. 모두 실패하거나 min_chars 미달이면 ValueError.
    """
    results: list[tuple[str, int, list[dict]]] = []
    workers = max(2, len(extractors))
    with ThreadPoolExecutor(max_workers=workers) as ex:
        futures = {ex.submit(fn, path): name for name, fn in extractors.items()}
        for f in as_completed(futures):
            name = futures[f]
            try:
                pages = f.result()
                if not pages:
                    continue
                total = sum(len(p.get("text", "")) for p in pages)
                if total >= min_chars:
                    results.append((name, total, pages))
            except Exception:
                continue

    if not results:
        raise ValueError(f"모든 추출기 실패 또는 텍스트 부족 ({list(extractors)})")

    best_name, best_total, best_pages = max(results, key=lambda r: r[1])
    return best_pages


def paginate(text: str, page_char_limit: int = 1000) -> list[dict]:
    """긴 평문을 가상 page 단위로 분할."""
    pages: list[dict] = []
    buffer = ""
    page_num = 1
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            continue
        if buffer and len(buffer) + len(line) > page_char_limit:
            pages.append({"text": buffer.strip(), "page": page_num})
            page_num += 1
            buffer = ""
        buffer = f"{buffer}\n{line}" if buffer else line
    if buffer.strip():
        pages.append({"text": buffer.strip(), "page": page_num})
    return pages
