"""인강 자동 생성 파이프라인.

강의 자료 → 슬라이드 스크립트 → TTS → 슬라이드 이미지 → 영상.

주요 함수:
    generate_lecture(context, level_info) -> str
        강의 자료 텍스트를 받아 mp4 영상 경로를 반환.
"""
from .pipeline import generate_lecture

__all__ = ["generate_lecture"]
