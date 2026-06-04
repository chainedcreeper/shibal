import json
import requests

_LEVEL_GUIDE = {
    "입문": "매우 쉽게 설명. 전문 용어 최소화. 일상적 비유 사용. 단계별로 천천히.",
    "중급": "핵심 개념 위주로 설명. 적절한 전문 용어 사용. 구체적 예시 포함.",
    "심화": "심층 분석 제공. 전문 용어 적극 사용. 원리와 응용까지 설명. 관련 개념 연결.",
}

_PROMPT_TMPL = """너는 대학 강의 AI Tutor다.

다음 문서를 참고해서 답변하라.

문서:
{context}

질문:
{question}

학생 수준: {label} (점수 {level}/10)
설명 방식: {guide}
"""

_OPTIONS = {"num_predict": 1024, "num_ctx": 8192}


def _build_prompt(context, question, level_info=None):
    label = level_info.get("label", "중급") if level_info else "중급"
    level = level_info.get("level", 5.0) if level_info else 5.0
    guide = _LEVEL_GUIDE.get(label, _LEVEL_GUIDE["중급"])
    return _PROMPT_TMPL.format(context=context, question=question, label=label, level=level, guide=guide)


def ask_qwen(context, question, level_info=None):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen3:8b",
            "prompt": _build_prompt(context, question, level_info),
            "stream": False,
            "options": _OPTIONS,
        },
    )
    return response.json()["response"]


def ask_qwen_stream(context, question, level_info=None):
    response = requests.post(
        "http://localhost:11434/api/generate",
        json={
            "model": "qwen3:8b",
            "prompt": _build_prompt(context, question, level_info),
            "stream": True,
            "options": _OPTIONS,
        },
        stream=True,
    )
    for line in response.iter_lines():
        if line:
            token = json.loads(line).get("response", "")
            if token:
                yield token