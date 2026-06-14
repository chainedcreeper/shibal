"""슬라이드 이미지(PNG) 생성.

PIL 로 1280x720 슬라이드를 그림. 한글 폰트는 시스템 후보 → 없으면
~/.cache/pj/fonts/ 에 NanumGothic 자동 다운로드.
"""
from __future__ import annotations

import os
import textwrap
import urllib.request

from PIL import Image, ImageDraw, ImageFont

SIZE          = (1280, 720)
BG_COLOR      = (22, 27, 38)
TITLE_COLOR   = (240, 240, 240)
BODY_COLOR    = (215, 215, 215)
ACCENT_COLOR  = (110, 130, 180)
PAGE_COLOR    = (120, 120, 120)

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
    return "\n".join(textwrap.wrap(text, width=width)) or text


def render(slide: dict, out_path: str) -> str:
    """slide = {index, title, bullets, ...}.  PNG 저장하고 경로 반환."""
    img  = Image.new("RGB", SIZE, color=BG_COLOR)
    draw = ImageDraw.Draw(img)
    font = _find_font()

    title_font = ImageFont.truetype(font, 56)
    body_font  = ImageFont.truetype(font, 34)
    page_font  = ImageFont.truetype(font, 22)

    draw.text((80, 70), _wrap(slide["title"], 28), fill=TITLE_COLOR, font=title_font)
    draw.line([(80, 170), (SIZE[0] - 80, 170)], fill=ACCENT_COLOR, width=3)

    y = 220
    for b in slide["bullets"]:
        wrapped = _wrap(f"• {b}", 38)
        draw.text((100, y), wrapped, fill=BODY_COLOR, font=body_font, spacing=10)
        y += 50 * (wrapped.count("\n") + 1)
        if y > SIZE[1] - 100:
            break

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
