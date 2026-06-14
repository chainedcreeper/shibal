"""영상 합성 — 자막은 soft subtitle 트랙으로 (burn-in 폐기).

흐름:
    1. moviepy 로 슬라이드+음성만 합쳐서 영상 만듦 (자막 X, 매우 빠름)
    2. ffmpeg 로 SRT 자막을 mov_text 트랙으로 mp4 안에 박음
       → 브라우저 HTML5 video 가 CC 켜면 표시
"""
from __future__ import annotations

import os
import subprocess
import tempfile

import imageio_ffmpeg
from moviepy import AudioFileClip, ImageClip, concatenate_videoclips

from .subtitle import build_subtitles, to_srt

FPS = 24
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def _slide_clip(slide: dict):
    """슬라이드 PNG + 음성. 자막 overlay 없음 (가장 가벼움)."""
    duration = max(float(slide.get("duration", 0.0)), 1.0)
    clip = ImageClip(slide["png_path"]).with_duration(duration)

    audio_path = slide.get("audio_path")
    if audio_path and os.path.exists(audio_path) and os.path.getsize(audio_path) > 1024:
        try:
            audio = AudioFileClip(audio_path)
            if audio.duration and audio.duration > 0:
                clip = clip.with_audio(audio)
        except Exception:
            pass
    return clip


def _attach_subtitle(video_path: str, srt_text: str, out_path: str) -> None:
    """mov_text 트랙으로 자막을 mp4 안에 박음 (재인코딩 없이 copy)."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".srt", delete=False, encoding="utf-8") as f:
        f.write(srt_text)
        srt_path = f.name
    try:
        subprocess.run(
            [
                FFMPEG, "-y",
                "-i", video_path,
                "-i", srt_path,
                "-c", "copy",                              # 비디오/오디오 재인코딩 없음 (빠름)
                "-c:s", "mov_text",                        # mp4 컨테이너 호환 자막 코덱
                "-metadata:s:s:0", "language=kor",
                "-disposition:s:0", "default",             # 기본 자막 트랙 (브라우저 자동 표시)
                "-movflags", "+faststart",
                out_path,
            ],
            check=True,
            capture_output=True,
        )
    finally:
        try: os.remove(srt_path)
        except OSError: pass


def compose(slides: list[dict], out_path: str) -> str:
    """슬라이드 → mp4 (자막 트랙 포함)."""
    clips = [_slide_clip(s) for s in slides]
    video = concatenate_videoclips(clips, method="compose")

    # 1. 자막 없는 영상 (ultrafast 인코딩 — 자막 burn-in 빠진 만큼 매우 빠름)
    temp_path = out_path + ".tmp.mp4"
    video.write_videofile(
        temp_path,
        codec        = "libx264",
        preset       = "ultrafast",
        fps          = FPS,
        audio_codec  = "aac",
        threads      = 8,
        ffmpeg_params= ["-movflags", "+faststart"],
    )

    # 2. SRT 자막 만들어서 mp4 안에 mov_text 트랙으로 박기
    srt_text = to_srt(build_subtitles(slides))
    try:
        _attach_subtitle(temp_path, srt_text, out_path)
        try: os.remove(temp_path)
        except OSError: pass
    except subprocess.CalledProcessError:
        # 자막 합치기 실패 시 자막 없는 mp4 라도 살림
        os.rename(temp_path, out_path)

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
