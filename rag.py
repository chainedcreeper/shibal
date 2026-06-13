import re
import numpy as np
import requests

from document import extract_text
from text_chunker import split_text
from embedding import create_embeddings, model
from vector import build_index
from reranker import rerank
from llm import ask_qwen, ask_qwen_stream

parents = []
children = []
child_index = None


def process_document(doc_path):
    global parents, children, child_index
    pages = extract_text(doc_path)
    if not pages:
        raise ValueError("문서에서 텍스트를 추출할 수 없습니다. 이미지 전용이거나 손상된 파일일 수 있습니다.")
    parents, children = split_text(pages)
    if not children:
        raise ValueError("문서 내용이 너무 짧아 처리할 수 없습니다.")
    embeddings = create_embeddings([c["text"] for c in children])
    child_index = build_index(embeddings)


# 이전 이름 호환
process_pdf = process_document


def _get_context(question, initial_k=20, final_k=3):
    if child_index is None or not children:
        raise RuntimeError("문서가 업로드되지 않았습니다.")

    k = min(initial_k, len(children))
    q_emb = model.encode([question], normalize_embeddings=True)
    _, I = child_index.search(np.array(q_emb, dtype="float32"), k=k)

    candidates = [children[idx] for idx in I[0] if idx < len(children)]
    top_children = rerank(question, candidates, top_k=min(final_k, len(candidates)))

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


def _full_context(max_chars=6000):
    if not parents:
        raise RuntimeError("문서가 업로드되지 않았습니다.")
    return "\n\n".join(f"[p.{p['page']}] {p['text']}" for p in parents)[:max_chars]

def ask_full(question, max_tokens=6000):
    return ask_qwen(_full_context(max_tokens), question)

def ask_full_stream(question, max_tokens=6000):
    yield from ask_qwen_stream(_full_context(max_tokens), question)
