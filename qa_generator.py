import json
import re
import requests

_OPTIONS = {"num_predict": 512, "num_ctx": 2048}


def _call_llm(prompt):
    resp = requests.post(
        "http://localhost:11434/api/generate",
        json={"model": "qwen3:8b", "prompt": prompt, "stream": False, "options": _OPTIONS},
    )
    return resp.json()["response"]


def _strip_think(text):
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


def _generate_questions(chunk_text, n=3):
    prompt = f"""다음 텍스트를 읽고 핵심 내용에 대한 질문 {n}개를 생성하라.

텍스트:
{chunk_text}

규칙:
- 질문만 출력, 번호 포함
- 예시: 1. 질문내용
- 답변 출력 금지"""

    raw = _strip_think(_call_llm(prompt))
    questions = []
    for line in raw.splitlines():
        line = re.sub(r"^\d+[\.\)]\s*", "", line.strip())
        if line:
            questions.append(line)
    return questions[:n]


def _generate_answer(chunk_text, question):
    prompt = f"""다음 텍스트를 참고해서 질문에 답하라.

텍스트:
{chunk_text}

질문: {question}

조건:
- 텍스트 기반으로만 답변
- 핵심 개념 강조
- 예시 포함"""

    return _strip_think(_call_llm(prompt))


def generate_qa_pairs(parents, questions_per_chunk=3):
    pairs = []
    for i, parent in enumerate(parents):
        chunk_text = parent["text"]
        page = parent["page"]

        questions = _generate_questions(chunk_text, n=questions_per_chunk)
        for q in questions:
            if not q:
                continue
            answer = _generate_answer(chunk_text, q)
            pairs.append({
                "question": q,
                "answer": answer,
                "source_page": page,
                "source_text": chunk_text,
            })

        yield i + 1, len(parents), pairs[-len(questions):]


def save_qa_pairs(pairs, output_path="qa_dataset.jsonl"):
    with open(output_path, "w", encoding="utf-8") as f:
        for pair in pairs:
            f.write(json.dumps(pair, ensure_ascii=False) + "\n")
    return output_path
