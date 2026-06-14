"""영상 합성.

각 슬라이드 PNG + mp3 → ImageClip + AudioClip,
자막 TextClip 을 하단에 overlay 한 CompositeVideoClip 으로 concat.
"""
from __future__ import annotations

import os

from moviepy import (
    AudioFileClip,
    CompositeVideoClip,
    ImageClip,
    TextClip,
    concatenate_videoclips,
)

from .slide_render import _find_font
from .subtitle import _chunk_words

FPS              = 24
SUBTITLE_FONT_PX = 32
SUBTITLE_COLOR   = "white"
SUBTITLE_STROKE  = "black"
SUBTITLE_Y_REL   = 0.84  # 화면 높이의 84% 위치


def _slide_clip(slide: dict, font_path: str) -> CompositeVideoClip:
    duration = max(float(slide.get("duration", 0.0)), 1.0)
    bg = ImageClip(slide["png_path"]).with_duration(duration)

    # 오디오 첨부 (실패해도 영상은 살림)
    audio_path = slide.get("audio_path")
    if audio_path and os.path.exists(audio_path) and os.path.getsize(audio_path) > 1024:
        try:
            audio = AudioFileClip(audio_path)
            if audio.duration and audio.duration > 0:
                bg = bg.with_audio(audio)
        except Exception:
            pass

    overlays: list = []
    for chunk in _chunk_words(slide.get("word_times", [])):
        if chunk["end"] <= chunk["start"]:
            continue
        txt = TextClip(
            text=chunk["text"],
            font=font_path,
            font_size=SUBTITLE_FONT_PX,
            color=SUBTITLE_COLOR,
            stroke_color=SUBTITLE_STROKE,
            stroke_width=2,
            method="caption",
            size=(1100, None),
        )
        txt = txt.with_position(("center", SUBTITLE_Y_REL), relative=True)
        txt = txt.with_start(chunk["start"]).with_duration(chunk["end"] - chunk["start"])
        overlays.append(txt)

    if not overlays:
        return bg
    return CompositeVideoClip([bg, *overlays])


def compose(slides: list[dict], out_path: str) -> str:
    """슬라이드 리스트(audio_path, png_path, duration, word_times) → mp4 저장."""
    font_path = _find_font()
    clips = [_slide_clip(s, font_path) for s in slides]
    video = concatenate_videoclips(clips, method="compose")
    video.write_videofile(
        out_path,
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        threads=4,
        preset="medium",
        ffmpeg_params=["-movflags", "+faststart"],  # moov atom 을 앞에 → 브라우저 progressive 재생
    )
    return out_path


def cleanup(slides: list[dict]) -> None:
    """중간 산출물 정리 (PNG, mp3)."""
    for s in slides:
        for key in ("png_path", "audio_path"):
            p = s.get(key)
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
