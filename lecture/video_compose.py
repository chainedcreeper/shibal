"""영상 합성 — ffmpeg concat demuxer 한 방식 (단일 파이프).

흐름:
    [1] audio concat   (12개 mp3 → 1개)         copy 모드,    ~5초
    [2] video concat   (PNG seq + duration)     stillimage,   ~30~60초
    [3] mux + 자막     (mov_text + faststart)   copy 모드,    ~5초

총 40~70초 (이전 8~14분 → 7~12배 단축).

엣지케이스 폴백:
    - audio 깨진/빈 슬라이드   → 무음 mp3 자동 생성
    - 자막 mov_text 실패       → 자막 없이 mp4 살림
    - 어느 단계든 ffmpeg 실패  → FfmpegError 에 stderr 마지막 500자 포함 (디버그)
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile

import imageio_ffmpeg

from .subtitle import build_subtitles, to_srt

FPS    = 24
WIDTH  = 1280
HEIGHT = 720
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


class FfmpegError(RuntimeError):
    """ffmpeg 실패. stderr 마지막 500자 포함."""


def _run(cmd: list[str], step: str) -> None:
    r = subprocess.run(cmd, capture_output=True)
    if r.returncode != 0:
        tail = r.stderr.decode("utf-8", errors="replace")[-500:]
        raise FfmpegError(f"[{step}] ffmpeg exit {r.returncode}\n{tail}")


# ── 1. audio ─────────────────────────────────────────

def _silence_mp3(path: str, duration: float) -> None:
    _run(
        [
            FFMPEG, "-y",
            "-f", "lavfi",
            "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t", f"{max(duration, 1.0):.3f}",
            "-c:a", "libmp3lame", "-b:a", "128k",
            path,
        ],
        step="silence",
    )


def _audio_concat(slides: list[dict], work: str) -> str:
    """모든 slide.audio_path 를 concat → merged_audio.mp3 (copy 모드)."""
    paths: list[str] = []
    for s in slides:
        ap = s.get("audio_path")
        if ap and os.path.exists(ap) and os.path.getsize(ap) > 1024:
            paths.append(ap)
        else:
            sil = os.path.join(work, f"silence_{s['index']:02d}.mp3")
            _silence_mp3(sil, float(s.get("duration", 1.0)))
            paths.append(sil)

    list_path = os.path.join(work, "audio.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for p in paths:
            f.write(f"file '{p}'\n")

    out = os.path.join(work, "audio.mp3")
    _run(
        [
            FFMPEG, "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_path,
            "-c", "copy",
            out,
        ],
        step="audio_concat",
    )
    return out


# ── 2. video ─────────────────────────────────────────

def _video_concat(slides: list[dict], work: str) -> str:
    """PNG 시퀀스 + 슬라이드별 duration → video-only mp4."""
    list_path = os.path.join(work, "video.txt")
    with open(list_path, "w", encoding="utf-8") as f:
        for s in slides:
            d = max(float(s.get("duration", 1.0)), 1.0)
            f.write(f"file '{s['png_path']}'\n")
            f.write(f"duration {d:.3f}\n")
        # concat demuxer 끝 처리: 마지막 파일 한 번 더 (duration 무관)
        f.write(f"file '{slides[-1]['png_path']}'\n")

    out = os.path.join(work, "video.mp4")
    _run(
        [
            FFMPEG, "-y",
            "-f", "concat", "-safe", "0",
            "-i", list_path,
            "-vsync", "vfr",                # 정적 이미지 → 가변 프레임 (빠름)
            "-pix_fmt", "yuv420p",
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-tune", "stillimage",
            "-r", str(FPS),
            out,
        ],
        step="video_concat",
    )
    return out


# ── 3. mux ───────────────────────────────────────────

def _mux_with_subtitle(video: str, audio: str, srt_text: str, out_path: str) -> bool:
    """video + audio + 자막 mov_text + faststart. 자막 실패 시 False."""
    srt_path = video + ".srt"
    try:
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_text)
        _run(
            [
                FFMPEG, "-y",
                "-i", video,
                "-i", audio,
                "-i", srt_path,
                "-map", "0:v",
                "-map", "1:a",
                "-map", "2:s",
                "-c:v", "copy",
                "-c:a", "aac", "-b:a", "128k",
                "-c:s", "mov_text",
                "-metadata:s:s:0", "language=kor",
                "-disposition:s:0", "default",
                "-shortest",
                "-movflags", "+faststart",
                out_path,
            ],
            step="mux_with_subtitle",
        )
        return True
    except FfmpegError:
        return False
    finally:
        try: os.remove(srt_path)
        except OSError: pass


def _mux_plain(video: str, audio: str, out_path: str) -> None:
    """자막 없이 video + audio + faststart."""
    _run(
        [
            FFMPEG, "-y",
            "-i", video,
            "-i", audio,
            "-c:v", "copy",
            "-c:a", "aac", "-b:a", "128k",
            "-shortest",
            "-movflags", "+faststart",
            out_path,
        ],
        step="mux_plain",
    )


# ── 통합 진입점 ──────────────────────────────────────

def compose(slides: list[dict], out_path: str) -> str:
    """슬라이드 리스트 → mp4. 자막 mov_text 트랙 포함 (실패 시 자막 없이)."""
    if not slides:
        raise ValueError("슬라이드가 비어있음")

    work = tempfile.mkdtemp(prefix="lecture_compose_")
    try:
        audio_path = _audio_concat(slides, work)
        video_path = _video_concat(slides, work)

        try:
            srt_text = to_srt(build_subtitles(slides))
        except Exception:
            srt_text = ""

        if not (srt_text.strip() and _mux_with_subtitle(video_path, audio_path, srt_text, out_path)):
            _mux_plain(video_path, audio_path, out_path)

        return out_path
    finally:
        shutil.rmtree(work, ignore_errors=True)


def cleanup(slides: list[dict]) -> None:
    """중간 산출물 (PNG, mp3) 정리."""
    for s in slides:
        for key in ("png_path", "audio_path"):
            p = s.get(key)
            if p and os.path.exists(p):
                try:
                    os.remove(p)
                except OSError:
                    pass
