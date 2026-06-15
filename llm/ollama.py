"""로컬 ollama qwen3:8b 호출. 수준별 시스템 프롬프트 분기."""
import os
import json

import requests

OLLAMA_HOST  = os.getenv("OLLAMA_HOST",  "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "qwen3:8b")

_LEVEL_GUIDE = {
    "입문": "학생은 이 분야가 처음이다. 전문 용어를 최대한 피하고, 일상적인 비유와 쉬운 예시로 설명해라.",
    "중급": "학생은 기본 개념을 알고 있다. 원리와 이유를 중심으로 설명하고 적절한 예시를 포함해라.",
    "심화": "학생은 개념을 깊이 이해하고 있다. 세부 메커니즘, 예외 사항, 다른 개념과의 연관성까지 다뤄라.",
}

_BASE_SYSTEM = (
    "너는 대학 강의 전문 AI 튜터다. "
    "반드시 주어진 강의 문서를 근거로만 답변하고, 문서에 없는 내용은 추측하지 마라. "
    "답변은 체계적이고 명확하게 작성해라."
)


def _system_prompt(level_info=None):
    if level_info and level_info.get("label"):
        guide = _LEVEL_GUIDE.get(level_info["label"], "")
        if guide:
            return f"{_BASE_SYSTEM}\n\n[학생 수준: {level_info['label']}] {guide}"
    return _BASE_SYSTEM


def _messages(context, question, level_info=None):
    return [
        {"role": "system", "content": _system_prompt(level_info)},
        {"role": "user",   "content": f"[강의 문서]\n{context}\n\n[요청]\n{question}"},
    ]


def _call_ollama(context, question, level_info=None, stream=False):
    resp = requests.post(
        f"{OLLAMA_HOST}/api/chat",
        json={
            "model":    OLLAMA_MODEL,
            "messages": _messages(context, question, level_info),
            "stream":   stream,
            "think":    False,
            "options": {
                "num_predict": 16384,   # 영상 스크립트 등 긴 JSON 응답도 잘리지 않게
                "num_ctx":     16384,   # 강의 자료 + 응답 공간 여유
            },
        },
        timeout=600,    # 32B 등 느린 모델 대비
        stream=stream,
    )
    resp.raise_for_status()
    return resp


def ask_qwen(context, question, level_info=None):
    return _call_ollama(context, question, level_info, stream=False).json()["message"]["content"]


def ask_qwen_stream(context, question, level_info=None):
    for line in _call_ollama(context, question, level_info, stream=True).iter_lines():
        if line:
            token = json.loads(line).get("message", {}).get("content", "")
            if token:
                yield token
