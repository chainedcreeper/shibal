from gtts import gTTS

def create_tts(text):

    tts = gTTS(
        text=text,
        lang="ko"
    )

    tts.save("lecture_audio.mp3")

    return "lecture_audio.mp3"