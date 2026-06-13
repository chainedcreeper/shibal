"""LLM 호출 통합 인터페이스.

ollama   — 로컬 ollama qwen3:8b (수준별 시스템 프롬프트)
personal — 학생별 개인화 모델 (ollama)
remote   — 외부 GPU 서버 (큰 모델 fallback)
"""
from .ollama import (
    ask_qwen, ask_qwen_stream,
    OLLAMA_HOST, OLLAMA_MODEL,
)
from .personal import (
    personal_model_exists, ask_personal, ask_personal_stream,
    register_personal_model, personal_model_name,
)
from .remote import (
    ask_server, ask_server_stream, is_server_available,
)

__all__ = [
    "ask_qwen", "ask_qwen_stream",
    "OLLAMA_HOST", "OLLAMA_MODEL",
    "personal_model_exists", "ask_personal", "ask_personal_stream",
    "register_personal_model", "personal_model_name",
    "ask_server", "ask_server_stream", "is_server_available",
]
