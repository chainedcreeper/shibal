"""Edge-TTS 래퍼.

각 슬라이드 narration → mp3 + 단어 타임스탬프.
타임스탬프는 자막 SRT 생성에 사용.
"""
from __future__ import annotations

import asyncio
import os
import subprocess

import edge_tts

DEFAULT_VOICE = "ko-KR-SunHiNeural"  # 가장 자연스러운 여성 한국어
_HNS_TO_SEC = 1 / 10_000_000  # Edge-TTS 시간 단위는 100ns
_MIN_DURATION = 1.0  # 슬라이드 최소 노출 시간 (초)


async def _synthesize_async(text: str, mp3_path: str, voice: str) -> list[dict]:
    communicate = edge_tts.Communicate(text, voice)
    word_times: list[dict] = []
    with open(mp3_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "WordBoundary":
                word_times.append({
                    "text":  chunk["text"],
                    "start": chunk["offset"] * _HNS_TO_SEC,
                    "end":   (chunk["offset"] + chunk["duration"]) * _HNS_TO_SEC,
                })
    return word_times


def synthesize(text: str, mp3_path: str, voice: str = DEFAULT_VOICE) -> list[dict]:
    """텍스트 → mp3 저장. 반환: 단어별 [{text, start, end}]."""
    return asyncio.run(_synthesize_async(text, mp3_path, voice))


def _probe_duration(mp3_path: str) -> float:
    """ffprobe 로 mp3 실제 길이(초) 측정."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries", "format=duration",
             "-of", "default=noprint_wrappers=1:nokey=1", mp3_path],
            capture_output=True, text=True, timeout=15,
        )
        return float(out.stdout.strip() or 0.0)
    except Exception:
        return 0.0


def synthesize_slides(slides: list[dict], out_dir: str, voice: str = DEFAULT_VOICE) -> list[dict]:
    """슬라이드 리스트 → 각 slide.narration TTS.

    각 slide 에 {audio_path, word_times, duration} 채워 반환.
    빈 narration / 빈 word_times 인 슬라이드도 안전하게 처리:
    duration 은 ffprobe 실측 → 그래도 0 이면 _MIN_DURATION 으로 패딩.
    """
    os.makedirs(out_dir, exist_ok=True)
    for s in slides:
        path = os.path.join(out_dir, f"slide_{s['index']:02d}.mp3")
        narration = (s.get("narration") or "").strip()
        if not narration:
            # 빈 narration → 무음 패딩 (안 만들면 moviepy 가 죽음)
            narration = s.get("title", "")
        word_times = synthesize(narration, path, voice) if narration else []

        if word_times:
            duration = word_times[-1]["end"]
        else:
            duration = _probe_duration(path)
        if duration < _MIN_DURATION:
            duration = _MIN_DURATION

        s["audio_path"] = path
        s["word_times"] = word_times
        s["duration"]   = duration
    return slides
