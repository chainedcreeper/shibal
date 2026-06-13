"""인강 자동 생성 전체 파이프라인.

generate_lecture(context, level_info, out_path) 한 줄로
강의 자료 텍스트 → mp4 영상까지 끝냄.
"""
from __future__ import annotations

import os
import shutil
import tempfile

from .script_gen import generate_script
from .tts_engine import synthesize_slides
from .slide_render import render_all
from .video_compose import compose, cleanup

DEFAULT_OUT = "lecture_video.mp4"


def generate_lecture(
    context: str,
    level_info: dict | None = None,
    out_path: str = DEFAULT_OUT,
    keep_intermediate: bool = False,
) -> str:
    """강의 자료 텍스트 → mp4.

    1. qwen3:8b 가 슬라이드 스크립트 JSON 생성
    2. 슬라이드별 Edge-TTS 나레이션
    3. 슬라이드 PNG 렌더
    4. moviepy 로 영상 합성 (자막 burn-in)
    """
    work_dir = tempfile.mkdtemp(prefix="lecture_")
    try:
        slides = generate_script(context, level_info)
        synthesize_slides(slides, os.path.join(work_dir, "audio"))
        render_all(slides, os.path.join(work_dir, "slides"))
        compose(slides, out_path)
        if not keep_intermediate:
            cleanup(slides)
        return out_path
    finally:
        if not keep_intermediate:
            shutil.rmtree(work_dir, ignore_errors=True)
