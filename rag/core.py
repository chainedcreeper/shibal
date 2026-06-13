"""RAG 코어 — 사용자별 인덱스 + 검색 + 답변.

모든 함수가 student_id 를 받음. 전역 상태 없음.
인덱스는 rag.state 가 메모리/디스크 자동 관리.
"""
from __future__ import annotations

import numpy as np

from document import extract_text
from llm      import ask_qwen, ask_qwen_stream

from .chunker   import split_text
from .embedding import create_embeddings, model
from .vector    import build_index
from .reranker  import rerank
from .state     import save_state, load_state, has_state


def process_document(doc_path: str, student_id: str, *, filename: str = "") -> dict:
    """문서 경로 → 추출 → 청킹 → 임베딩 → faiss → 디스크/메모리 저장."""
    pages = extract_text(doc_path)
    if not pages:
        raise ValueError("문서에서 텍스트를 추출할 수 없습니다. 이미지 전용이거나 손상된 파일일 수 있습니다.")

    parents, children = split_text(pages)
    if not children:
        raise ValueError("문서 내용이 너무 짧아 처리할 수 없습니다.")

    embeddings = create_embeddings([c["text"] for c in children])
    index      = build_index(embeddings)
    save_state(student_id, parents, children, index, filename=filename)

    return {
        "pages":    len(pages),
        "parents":  len(parents),
        "children": len(children),
    }


# 이전 이름 호환
process_pdf = process_document


def _require_state(student_id: str) -> dict:
    state = load_state(student_id)
    if state is None:
        raise RuntimeError("문서가 업로드되지 않았습니다.")
    return state


def _get_context(question: str, student_id: str, *, initial_k: int = 20, final_k: int = 3) -> str:
    state    = _require_state(student_id)
    parents  = state["parents"]
    children = state["children"]
    index    = state["index"]

    k     = min(initial_k, len(children))
    q_emb = model.encode([question], normalize_embeddings=True)
    _, I  = index.search(np.array(q_emb, dtype="float32"), k=k)

    candidates   = [children[idx] for idx in I[0] if idx < len(children)]
    top_children = rerank(question, candidates, top_k=min(final_k, len(candidates)))

    context, seen = "", set()
    for child in top_children:
        pid = child["parent_id"]
        if pid not in seen:
            seen.add(pid)
            p = parents[pid]
            context += f"[p.{p['page']}] {p['text']}\n\n"
    return context


def _full_context(student_id: str, max_chars: int = 6000) -> str:
    state   = _require_state(student_id)
    parents = state["parents"]
    return "\n\n".join(f"[p.{p['page']}] {p['text']}" for p in parents)[:max_chars]


def get_parents(student_id: str) -> list[dict]:
    """QA 생성 등에서 직접 parents 접근용."""
    return _require_state(student_id)["parents"]


# ── 답변 생성 ────────────────────────────────────────

def ask(question: str, student_id: str, level_info=None):
    return ask_qwen(_get_context(question, student_id), question, level_info)


def ask_stream(question: str, student_id: str, level_info=None):
    yield from ask_qwen_stream(_get_context(question, student_id), question, level_info)


def ask_full(question: str, student_id: str, max_tokens: int = 6000):
    return ask_qwen(_full_context(student_id, max_tokens), question)


def ask_full_stream(question: str, student_id: str, max_tokens: int = 6000):
    yield from ask_qwen_stream(_full_context(student_id, max_tokens), question)
