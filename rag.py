import re
import numpy as np
import requests

from pdf_loader import extract_text
from text_chunker import split_text
from embedding import create_embeddings, model
from vector import build_index
from reranker import rerank
from llm import ask_qwen, ask_qwen_stream

parents = []
children = []
child_index = None


def process_pdf(pdf_path):
    global parents, children, child_index
    pages = extract_text(pdf_path)
    parents, children = split_text(pages)
    embeddings = create_embeddings([c["text"] for c in children])
    child_index = build_index(embeddings)


def _get_context(question, initial_k=20, final_k=3):
    if child_index is None:
        raise RuntimeError("PDF가 업로드되지 않았습니다.")

    q_emb = model.encode([question])
    _, I = child_index.search(np.array(q_emb), k=min(initial_k, len(children)))

    candidates = [children[idx] for idx in I[0]]

    # Reranker로 top-k 선별
    top_children = rerank(question, candidates, top_k=final_k)

    # Parent 청크로 컨텍스트 구성
    context = ""
    seen_parents = set()
    for child in top_children:
        pid = child["parent_id"]
        if pid not in seen_parents:
            seen_parents.add(pid)
            p = parents[pid]
            context += f"[p.{p['page']}] {p['text']}\n\n"

    return context


def ask(question, level_info=None):
    return ask_qwen(_get_context(question), question, level_info)


def ask_stream(question, level_info=None):
    yield from ask_qwen_stream(_get_context(question), question, level_info)


def ask_full(question, max_tokens=6000):
    """전체 문서 내용으로 질문 (요약/분석용)"""
    if not parents:
        raise RuntimeError("PDF가 업로드되지 않았습니다.")
    full_text = "\n\n".join(
        f"[p.{p['page']}] {p['text']}" for p in parents
    )
    context = full_text[:max_tokens]
    return ask_qwen(context, question)
