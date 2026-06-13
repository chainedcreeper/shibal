"""Edge-TTS 래퍼.

각 슬라이드 narration → mp3 + 단어 타임스탬프.
타임스탬프는 자막 SRT 생성에 사용.
"""
from __future__ import annotations

import asyncio

import edge_tts

DEFAULT_VOICE = "ko-KR-SunHiNeural"  # 가장 자연스러운 여성 한국어
_HNS_TO_SEC = 1 / 10_000_000  # Edge-TTS 시간 단위는 100ns


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


def synthesize_slides(slides: list[dict], out_dir: str, voice: str = DEFAULT_VOICE) -> list[dict]:
    """슬라이드 리스트 → 각 slide.narration TTS.

    각 slide 에 {audio_path, word_times, duration} 채워 반환.
    """
    import os

    os.makedirs(out_dir, exist_ok=True)
    for s in slides:
        path = os.path.join(out_dir, f"slide_{s['index']:02d}.mp3")
        word_times = synthesize(s["narration"], path, voice)
        s["audio_path"] = path
        s["word_times"] = word_times
        s["duration"]   = word_times[-1]["end"] if word_times else 0.0
    return slides
