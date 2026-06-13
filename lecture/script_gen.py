"""슬라이드 스크립트 생성.

강의 자료 → qwen3:8b → 슬라이드별 {title, bullets, narration} JSON.
"""
from __future__ import annotations

import json
import re

from llm import ask_qwen


SCRIPT_PROMPT = """\
업로드된 강의 자료를 바탕으로 5~10장의 강의 슬라이드 스크립트를 만들어라.

각 슬라이드는 다음 정보를 포함:
- title:     슬라이드 제목 (한 줄, 20자 이내)
- bullets:   핵심 항목 3~5개 (각 항목 30자 이내)
- narration: 강사가 학생에게 말하듯 자연스러운 설명 (200~400자)

반드시 아래 JSON 배열 형식으로만 출력하고, 그 외 텍스트는 절대 출력하지 마라.

[
  {"title": "...", "bullets": ["...", "..."], "narration": "..."},
  ...
]

규칙:
- 슬라이드 5~10장
- 강의 흐름이 자연스럽게 이어지도록 (첫 장은 주제 소개, 마지막은 정리/요약)
- narration 은 실제 강사가 학생에게 말하는 톤 ("~입니다", "~하죠")
- bullets 는 narration 의 요약이 아닌 시각적 핵심 키워드
"""

_FENCE_RE = re.compile(r"```(?:json)?\s*|\s*```", re.IGNORECASE)
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)

_REQUIRED_FIELDS = ("title", "bullets", "narration")


def _extract_json_array(raw: str) -> list[dict]:
    text = _THINK_RE.sub("", raw)
    text = _FENCE_RE.sub("", text)
    m = _ARRAY_RE.search(text)
    if not m:
        raise ValueError("응답에서 JSON 배열을 찾을 수 없음")
    return json.loads(m.group(0))


def _validate(slides: list[dict]) -> list[dict]:
    if not isinstance(slides, list) or not slides:
        raise ValueError("슬라이드 리스트가 비어있음")
    cleaned: list[dict] = []
    for idx, s in enumerate(slides, 1):
        missing = [k for k in _REQUIRED_FIELDS if k not in s]
        if missing:
            raise ValueError(f"슬라이드 {idx} 필드 누락: {missing}")
        if not isinstance(s["bullets"], list) or not s["bullets"]:
            raise ValueError(f"슬라이드 {idx}: bullets 형식 오류")
        cleaned.append({
            "index":     idx,
            "title":     str(s["title"]).strip(),
            "bullets":   [str(b).strip() for b in s["bullets"] if str(b).strip()],
            "narration": str(s["narration"]).strip(),
        })
    return cleaned


def generate_script(context: str, level_info: dict | None = None) -> list[dict]:
    """강의 자료 텍스트 → 슬라이드 스크립트 리스트.

    각 원소: {index, title, bullets, narration}
    """
    raw = ask_qwen(context, SCRIPT_PROMPT, level_info)
    try:
        slides = _extract_json_array(raw)
        return _validate(slides)
    except Exception as e:
        snippet = raw[:300].replace("\n", " ")
        raise RuntimeError(f"슬라이드 스크립트 생성 실패: {e} | 응답 앞부분: {snippet!r}") from e
