"""자막 생성.

각 슬라이드의 word_times → 5단어 단위 청크 → 슬라이드 누적 offset 적용.
moviepy CompositeVideoClip 에서 TextClip 으로 overlay 할 때 사용.
"""
from __future__ import annotations

WORDS_PER_CHUNK = 5
MIN_CHUNK_SEC   = 0.6   # 너무 짧은 청크는 가독성 떨어짐


def _chunk_words(words: list[dict], per_chunk: int = WORDS_PER_CHUNK) -> list[dict]:
    chunks: list[dict] = []
    i = 0
    while i < len(words):
        group = words[i:i + per_chunk]
        if not group:
            break
        chunk = {
            "text":  " ".join(w["text"] for w in group),
            "start": group[0]["start"],
            "end":   group[-1]["end"],
        }
        if chunk["end"] - chunk["start"] < MIN_CHUNK_SEC and chunks:
            chunks[-1]["text"] += " " + chunk["text"]
            chunks[-1]["end"]   = chunk["end"]
        else:
            chunks.append(chunk)
        i += per_chunk
    return chunks


def build_subtitles(slides: list[dict]) -> list[dict]:
    """슬라이드 리스트 → 전체 자막 청크.

    반환: [{text, start, end}, ...]  (전체 영상 기준 절대 시간)
    각 슬라이드의 word_times 가 그 슬라이드 시작점(0초) 기준이라는 가정.
    """
    out: list[dict] = []
    offset = 0.0
    for s in slides:
        for chunk in _chunk_words(s.get("word_times", [])):
            out.append({
                "text":  chunk["text"],
                "start": offset + chunk["start"],
                "end":   offset + chunk["end"],
            })
        offset += s.get("duration", 0.0)
    return out


def _fmt_srt_time(sec: float) -> str:
    ms = int(round((sec - int(sec)) * 1000))
    s  = int(sec) % 60
    m  = (int(sec) // 60) % 60
    h  = int(sec) // 3600
    return f"{h:02d}:{m:02d}:{s:02d},{ms:03d}"


def to_srt(subtitles: list[dict]) -> str:
    lines: list[str] = []
    for i, c in enumerate(subtitles, 1):
        lines.append(str(i))
        lines.append(f"{_fmt_srt_time(c['start'])} --> {_fmt_srt_time(c['end'])}")
        lines.append(c["text"])
        lines.append("")
    return "\n".join(lines)
