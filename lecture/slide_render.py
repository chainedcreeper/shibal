"""슬라이드 이미지(PNG) 렌더링.

레이아웃 (1280x720):
    상단         : 제목 (큰 글씨)
    구분선
    헤드라인     : 그 슬라이드의 핵심 한 문장 (강조 색)
    본문         : bullets 목록 (긴 텍스트 wrap)
    하단 오른쪽  : 슬라이드 번호

한글 폰트: 시스템 후보 → 없으면 ~/.cache/pj/fonts 에 NanumGothic 자동 다운로드.
"""
from __future__ import annotations

import os
import textwrap
import urllib.request

from PIL import Image, ImageDraw, ImageFont

SIZE          = (1280, 720)
BG_COLOR      = (22, 27, 38)
TITLE_COLOR   = (240, 240, 240)
HEAD_COLOR    = (255, 215, 110)   # 노란 강조
BODY_COLOR    = (220, 220, 220)
ACCENT_COLOR  = (110, 130, 180)
PAGE_COLOR    = (120, 120, 120)
BULLET_COLOR  = (255, 215, 110)

_FONT_URL    = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
_FONT_CACHE  = os.path.expanduser("~/.cache/pj/fonts/NanumGothic-Regular.ttf")
_FONT_CANDIDATES = [
    "/usr/share/fonts/truetype/nanum/NanumGothic.ttf",
    "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
    "/usr/share/fonts/truetype/noto/NotoSansCJK-Regular.ttc",
    "/System/Library/Fonts/Supplemental/AppleSDGothicNeo.ttc",
    "C:/Windows/Fonts/malgun.ttf",
    _FONT_CACHE,
]


def _find_font() -> str:
    for p in _FONT_CANDIDATES:
        if os.path.exists(p):
            return p
    os.makedirs(os.path.dirname(_FONT_CACHE), exist_ok=True)
    urllib.request.urlretrieve(_FONT_URL, _FONT_CACHE)
    return _FONT_CACHE


def _wrap(text: str, width: int) -> str:
    if not text:
        return ""
    wrapped = "\n".join(textwrap.wrap(text, width=width)) or text
    return wrapped


def _line_height(font: ImageFont.FreeTypeFont) -> int:
    bbox = font.getbbox("가힣Hg")
    return (bbox[3] - bbox[1]) + 8


def render(slide: dict, out_path: str) -> str:
    """slide = {index, title, headline, bullets, ...}. PNG 저장 후 경로 반환."""
    img  = Image.new("RGB", SIZE, color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    font = _find_font()

    title_font = ImageFont.truetype(font, 52)
    head_font  = ImageFont.truetype(font, 34)
    body_font  = ImageFont.truetype(font, 28)
    page_font  = ImageFont.truetype(font, 22)

    # 1) 제목
    draw.text((70, 50), _wrap(slide["title"], 28), fill=TITLE_COLOR, font=title_font)

    # 2) 구분선
    draw.line([(70, 135), (SIZE[0] - 70, 135)], fill=ACCENT_COLOR, width=3)

    # 3) 헤드라인 (옵션, 핵심 한 문장 강조)
    y = 160
    headline = (slide.get("headline") or "").strip()
    if headline:
        head_wrapped = _wrap(headline, 36)
        draw.text((80, y), head_wrapped, fill=HEAD_COLOR, font=head_font, spacing=8)
        y += _line_height(head_font) * (head_wrapped.count("\n") + 1) + 16

    # 4) bullets
    body_lh = _line_height(body_font)
    for b in slide["bullets"]:
        # 불릿 마커
        draw.text((90, y), "•", fill=BULLET_COLOR, font=body_font)
        wrapped = _wrap(b, 42)
        draw.text((120, y), wrapped, fill=BODY_COLOR, font=body_font, spacing=6)
        y += body_lh * (wrapped.count("\n") + 1) + 12
        if y > SIZE[1] - 80:
            break  # 화면 넘으면 중단 (narration 에서 보완됨)

    # 5) 슬라이드 번호 (우하단)
    page = f"{slide.get('index', '?')}"
    bbox = draw.textbbox((0, 0), page, font=page_font)
    pw, ph = bbox[2] - bbox[0], bbox[3] - bbox[1]
    draw.text((SIZE[0] - pw - 50, SIZE[1] - ph - 30), page, fill=PAGE_COLOR, font=page_font)

    img.save(out_path)
    return out_path


def render_all(slides: list[dict], out_dir: str, on_progress=None) -> list[dict]:
    os.makedirs(out_dir, exist_ok=True)
    total = len(slides)
    for i, s in enumerate(slides, 1):
        path = os.path.join(out_dir, f"slide_{s['index']:02d}.png")
        s["png_path"] = render(s, path)
        if on_progress:
            try: on_progress(i, total)
            except Exception: pass
    return slides
