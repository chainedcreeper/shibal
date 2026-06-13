"""RAG 통합 인터페이스.

문서 처리 → 청킹 → 임베딩 → faiss → reranker → LLM.
"""
from . import core
from .core import (
    process_document, process_pdf,
    ask, ask_stream, ask_full, ask_full_stream,
)
from .qa import generate_qa_pairs, save_qa_pairs

__all__ = [
    "core",
    "process_document", "process_pdf",
    "ask", "ask_stream", "ask_full", "ask_full_stream",
    "generate_qa_pairs", "save_qa_pairs",
]
