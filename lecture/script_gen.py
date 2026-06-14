"""슬라이드 스크립트 생성 — 풍부한 본문 + 자세한 나레이션.

흐름:
    강의 자료 → qwen3:8b → 도입 / 본문(섹션별) / 정리 구조의 슬라이드 N장.

각 슬라이드 필드:
    title     — 슬라이드 제목 (20자)
    headline  — 핵심 한 문장 (한 줄 강조, 50자)
    bullets   — 세부 항목 3~5개 (각 40~70자)
    narration — 강사가 자세히 풀어 설명 (400~600자)
"""
from __future__ import annotations

import json
import re

from llm import ask_qwen


SCRIPT_PROMPT = """\
업로드된 강의 자료를 풍부하게 풀어 설명하는 강의 슬라이드를 만들어라.

분량 규칙:
- 강의 자료가 짧아도 최소 6장 만들어라
- 강의 자료가 길면 최대 12장까지 늘려라
- 짧은 자료여도 비유와 예시를 추가해서 깊이있게 설명해라

구조:
- 1장:   도입 (강의 주제 + 학습 목표 3~5개)
- 본문: 핵심 개념을 섹션별로 분해해서 자세히 설명 (4~10장)
- 마지막: 정리 (배운 것 요약 + 시험 대비 포인트)

각 슬라이드는 반드시 다음 4개 필드:

  title     — 슬라이드 제목 (한 줄, 20자 이내)
  headline  — 그 슬라이드의 핵심을 한 문장으로 (40~60자, 코랄색으로 강조 표시됨)
  bullets   — 세부 항목 3~5개. 각 항목은 반드시 50~90자의 실제 설명
              · "X는 Y이다" 정의 X — "X는 Y이고 그 이유는 Z이다" 정도로 풀어라
              · 한 단어/구절 금지. 완성된 문장으로
  narration — 강사가 학생 앞에서 칠판 설명하듯 500~700자
              · 비유 1~2개, 일상 예시 1~2개 포함
              · 슬라이드 화면에 없는 깊은 디테일을 narration 에서 보충
              · 슬라이드 텍스트를 그대로 읽지 말고 더 자세히 풀어 설명
              · 다음 슬라이드로 자연스럽게 연결되는 한 문장 마무리

반드시 아래 JSON 배열 형식으로만 출력하라 (다른 텍스트 절대 금지):

[
  {"title": "...", "headline": "...", "bullets": ["...", "...", "..."], "narration": "..."},
  ...
]
"""

_FENCE_RE = re.compile(r"```(?:json)?\s*|\s*```", re.IGNORECASE)
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL)
_ARRAY_RE = re.compile(r"\[.*\]", re.DOTALL)

_REQUIRED = ("title", "bullets", "narration")  # headline 은 optional 폴백 가능


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
        missing = [k for k in _REQUIRED if k not in s]
        if missing:
            raise ValueError(f"슬라이드 {idx} 필드 누락: {missing}")
        if not isinstance(s["bullets"], list) or not s["bullets"]:
            raise ValueError(f"슬라이드 {idx}: bullets 형식 오류")
        cleaned.append({
            "index":     idx,
            "title":     str(s["title"]).strip(),
            "headline":  str(s.get("headline") or "").strip(),
            "bullets":   [str(b).strip() for b in s["bullets"] if str(b).strip()],
            "narration": str(s["narration"]).strip(),
        })
    return cleaned


def generate_script(context: str, level_info: dict | None = None) -> list[dict]:
    """강의 자료 텍스트 → 슬라이드 스크립트 리스트.

    각 원소: {index, title, headline, bullets, narration}
    """
    raw = ask_qwen(context, SCRIPT_PROMPT, level_info)
    try:
        slides = _extract_json_array(raw)
        return _validate(slides)
    except Exception as e:
        snippet = raw[:300].replace("\n", " ")
        raise RuntimeError(f"슬라이드 스크립트 생성 실패: {e} | 응답 앞부분: {snippet!r}") from e
