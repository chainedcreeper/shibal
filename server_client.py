import json
import requests

SERVER_URL = "http://학교서버IP:11434"
TEACHER_MODEL = "exaone3.5:32b"

_PROMPT_TMPL = """너는 대학 강의 AI Tutor다.

다음 문서를 참고해서 답변하라.

문서:
{context}

질문:
{question}

조건:
- 학생 수준에 맞게 쉽게 설명
- 핵심 개념 강조
- 구체적 예시 포함
- 모르면 모른다고 답변
"""

_OPTIONS = {"num_predict": 1024, "num_ctx": 4096}


def ask_server(context, question):
    resp = requests.post(
        f"{SERVER_URL}/api/generate",
        json={
            "model": TEACHER_MODEL,
            "prompt": _PROMPT_TMPL.format(context=context, question=question),
            "stream": False,
            "options": _OPTIONS,
        },
        timeout=120,
    )
    return resp.json()["response"]


def ask_server_stream(context, question):
    resp = requests.post(
        f"{SERVER_URL}/api/generate",
        json={
            "model": TEACHER_MODEL,
            "prompt": _PROMPT_TMPL.format(context=context, question=question),
            "stream": True,
            "options": _OPTIONS,
        },
        stream=True,
        timeout=120,
    )
    for line in resp.iter_lines():
        if line:
            token = json.loads(line).get("response", "")
            if token:
                yield token


def is_server_available():
    try:
        requests.get(f"{SERVER_URL}/api/tags", timeout=5)
        return True
    except Exception:
        return False
