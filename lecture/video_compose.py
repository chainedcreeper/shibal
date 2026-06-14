"""영상 합성 — ffmpeg 직접 호출 (moviepy 폐기, 5~10배 빠름).

흐름:
    1. 슬라이드별 mp4 (PNG + mp3 → ffmpeg "stillimage" 튜닝). ThreadPoolExecutor 병렬.
    2. concat (재인코딩 X, "copy" 모드).
    3. mov_text 자막 트랙 박기 (실패해도 영상은 살림).
    4. faststart 보장 (브라우저 progressive 재생).

엣지케이스 모두 폴백:
    - 빈 narration → anullsrc 무음 + 이미지만 표시
    - 자막 합치기 실패 → 자막 없이 영상 살림
    - faststart 실패 → 그냥 concat 결과 copy
"""
from __future__ import annotations

import os
import shutil
import subprocess
import tempfile
from concurrent.futures import ThreadPoolExecutor

import imageio_ffmpeg

from .subtitle import build_subtitles, to_srt

FPS    = 24
WIDTH  = 1280
HEIGHT = 720
FFMPEG = imageio_ffmpeg.get_ffmpeg_exe()


def _run(cmd: list[str]) -> None:
    subprocess.run(cmd, check=True, capture_output=True)


def _slide_mp4(slide: dict, out_path: str) -> str:
    """슬라이드 한 장 → mp4 (이미지 + 음성). 1~2초/장."""
    audio_ok = (
        slide.get("audio_path")
        and os.path.exists(slide["audio_path"])
        and os.path.getsize(slide["audio_path"]) > 1024
    )
    duration = max(float(slide.get("duration", 1.0)), 1.0)

    base = [
        FFMPEG, "-y",
        "-loop", "1", "-i", slide["png_path"],
    ]
    if audio_ok:
        cmd = base + ["-i", slide["audio_path"]]
    else:
        cmd = base + [
            "-f", "lavfi",
            "-i", "anullsrc=channel_layout=stereo:sample_rate=44100",
            "-t", str(duration),
        ]
    cmd += [
        "-c:v", "libx264", "-tune", "stillimage", "-preset", "ultrafast",
        "-pix_fmt", "yuv420p", "-r", str(FPS),
        "-vf", f"scale={WIDTH}:{HEIGHT}",
        "-c:a", "aac", "-b:a", "128k",
        "-shortest",
        out_path,
    ]
    _run(cmd)
    return out_path


def _concat(slide_mp4s: list[str], list_path: str, out_path: str) -> None:
    """concat (재인코딩 X)."""
    with open(list_path, "w", encoding="utf-8") as f:
        for p in slide_mp4s:
            f.write(f"file '{p}'\n")
    _run([
        FFMPEG, "-y",
        "-f", "concat", "-safe", "0",
        "-i", list_path,
        "-c", "copy",
        out_path,
    ])


def _add_subtitle(in_mp4: str, srt_text: str, out_mp4: str) -> bool:
    """mov_text 자막 트랙 박기 + faststart. 성공 True / 실패 False."""
    srt_path = in_mp4 + ".srt"
    try:
        with open(srt_path, "w", encoding="utf-8") as f:
            f.write(srt_text)
        _run([
            FFMPEG, "-y",
            "-i", in_mp4,
            "-i", srt_path,
            "-c", "copy",
            "-c:s", "mov_text",
            "-metadata:s:s:0", "language=kor",
            "-disposition:s:0", "default",
            "-movflags", "+faststart",
            out_mp4,
        ])
        return True
    except subprocess.CalledProcessError:
        return False
    finally:
        try: os.remove(srt_path)
        except OSError: pass


def _faststart(in_mp4: str, out_mp4: str) -> None:
    """자막 없이 faststart 만 박음 (자막 실패 폴백)."""
    try:
        _run([
            FFMPEG, "-y",
            "-i", in_mp4,
            "-c", "copy",
            "-movflags", "+faststart",
            out_mp4,
        ])
    except subprocess.CalledProcessError:
        shutil.copy(in_mp4, out_mp4)


def compose(slides: list[dict], out_path: str) -> str:
    """슬라이드 리스트 → mp4 (자막 트랙 포함, ffmpeg 직접)."""
    work = tempfile.mkdtemp(prefix="lecture_compose_")
    try:
        # 1. 슬라이드별 mp4 (병렬, ThreadPoolExecutor)
        def make(s):
            p = os.path.join(work, f"slide_{s['index']:02d}.mp4")
            return _slide_mp4(s, p)

        with ThreadPoolExecutor(max_workers=4) as ex:
            slide_mp4s = list(ex.map(make, slides))

        # 2. concat (재인코딩 X)
        concat_path = os.path.join(work, "concat.mp4")
        list_path   = os.path.join(work, "concat.txt")
        _concat(slide_mp4s, list_path, concat_path)

        # 3. 자막 트랙 추가 → 실패하면 자막 없이 faststart
        try:
            srt = to_srt(build_subtitles(slides))
        except Exception:
            srt = ""

        if srt.strip() and _add_subtitle(concat_path, srt, out_path):
            return out_path
        _faststart(concat_path, out_path)
        return out_path
    finally:
        shutil.rmtree(work, ignore_errors=True)


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
