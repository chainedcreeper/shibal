"""인강 자동 생성 전체 파이프라인 — 진행 상황 콜백 지원.

generate_lecture(context, level_info, out_path, on_progress=callable) 한 줄로
강의 자료 텍스트 → mp4 영상까지. on_progress(stage, current, total, msg) 호출됨.
"""
from __future__ import annotations

import os
import shutil
import tempfile
from typing import Callable, Optional

from .script_gen import generate_script
from .tts_engine import synthesize_slides
from .slide_render import render_all
from .video_compose import compose, cleanup

DEFAULT_OUT = "lecture_video.mp4"

ProgressCB = Optional[Callable[[str, int, int, str], None]]


def _emit(cb: ProgressCB, stage: str, current: int, total: int, msg: str = ""):
    if cb:
        try:
            cb(stage, current, total, msg)
        except Exception:
            pass


def generate_lecture(
    context: str,
    level_info: dict | None = None,
    out_path: str = DEFAULT_OUT,
    keep_intermediate: bool = False,
    on_progress: ProgressCB = None,
) -> str:
    """강의 자료 → mp4.

    on_progress 가 받는 stage 종류:
      "script"    스크립트 생성 (current=0, total=1)
      "tts"       슬라이드별 TTS (current=i, total=N)
      "render"    슬라이드 PNG 렌더 (current=i, total=N)
      "compose"   영상 합성 (current=0, total=1)
      "done"      완료 (msg=out_path)
    """
    work_dir = tempfile.mkdtemp(prefix="lecture_")
    try:
        # 1. 스크립트
        _emit(on_progress, "script", 0, 1, "강의 스크립트 생성 중")
        slides = generate_script(context, level_info)
        n = len(slides)
        _emit(on_progress, "script", 1, 1, f"{n}장 슬라이드 스크립트 완성")

        # 2. TTS (슬라이드별)
        audio_dir = os.path.join(work_dir, "audio")
        synthesize_slides(
            slides, audio_dir,
            on_progress=lambda i, t: _emit(on_progress, "tts", i, t, f"슬라이드 {i}/{t} 나레이션"),
        )

        # 3. 슬라이드 렌더 (슬라이드별)
        slides_dir = os.path.join(work_dir, "slides")
        render_all(
            slides, slides_dir,
            on_progress=lambda i, t: _emit(on_progress, "render", i, t, f"슬라이드 {i}/{t} 이미지"),
        )

        # 4. 영상 합성 (한 덩어리, 가장 오래 걸림)
        _emit(on_progress, "compose", 0, 1, "영상 합성 + 자막 burn-in 중")
        compose(slides, out_path)
        _emit(on_progress, "compose", 1, 1, "영상 합성 완료")

        if not keep_intermediate:
            cleanup(slides)

        _emit(on_progress, "done", 1, 1, out_path)
        return out_path
    finally:
        if not keep_intermediate:
            shutil.rmtree(work_dir, ignore_errors=True)
