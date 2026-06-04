import os
from moviepy import ImageClip, AudioFileClip, concatenate_videoclips
from PIL import Image, ImageDraw, ImageFont
import textwrap

def create_video(summary):

    font = ImageFont.truetype(
        r"C:\Windows\Fonts\malgun.ttf",
        30
    )

    # ## 기준으로 슬라이드 분리
    slides_text = summary.split("##")

    slides = []

    # 슬라이드 이미지 생성
    for idx, slide_text in enumerate(slides_text):

        slide_text = slide_text.strip()

        if not slide_text:
            continue

        img = Image.new(
            "RGB",
            (1280, 720),
            color=(30, 30, 30)
        )

        draw = ImageDraw.Draw(img)

        wrapped_text = ""

        for line in slide_text.split("\n"):
            wrapped_text += "\n".join(
            textwrap.wrap(line, width=20)
        )
        wrapped_text += "\n"

        draw.text(
            (80, 80),
            wrapped_text,
            fill=(255, 255, 255),
            font=font
        )

        filename = f"slide_{idx}.png"

        img.save(filename)

        slides.append(filename)

    audio = AudioFileClip(
        "lecture_audio.mp3"
    )

    slide_count = len(slides)

    if slide_count == 0:
        raise ValueError("생성된 슬라이드가 없습니다.")

    duration_per_slide = (
        audio.duration / slide_count
    )

    clips = []

    for slide in slides:

        clip = ImageClip(
            slide,
            duration=duration_per_slide
        )

        clips.append(clip)

    video = concatenate_videoclips(
        clips,
        method="compose"
    )

    video = video.with_audio(audio)

    video.write_videofile(
        "lecture_video.mp4",
        fps=24,
        codec="libx264",
        audio_codec="aac"
    )

    for slide in slides:
        try:
            os.remove(slide)
        except Exception:
            pass

    return "lecture_video.mp4"
