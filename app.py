import os as _os
_env_path = _os.path.join(_os.path.dirname(__file__), "local.env")
if _os.path.exists(_env_path):
    with open(_env_path, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                _os.environ.setdefault(_k.strip(), _v.strip())

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import uvicorn
import tempfile
import os
import asyncio
import json
import re
from concurrent.futures import ThreadPoolExecutor

import rag as rag_module
from rag import process_pdf, ask, ask_stream, ask_full
from qa_generator import generate_qa_pairs, save_qa_pairs
from student_db import init_db, log_interaction, should_train, export_student_data, get_student
from model_manager import personal_model_exists, ask_personal_stream
from server_client import ask_server_stream, is_server_available
from auth import init_auth_db, register_user, authenticate_user, create_token, get_current_user
from level_assessor import init_level_db, assess_and_update, get_student_level

init_db()
init_auth_db()
init_level_db()
from tts import create_tts
from video import create_video

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=2)
pdf_ready = False


def strip_thinking(text: str) -> str:
    return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()


class RegisterRequest(BaseModel):
    student_id: str
    name: str
    password: str


class ChatMessage(BaseModel):
    message: str


@app.post("/register")
async def register(req: RegisterRequest):
    register_user(req.student_id, req.name, req.password)
    return {"status": "ok", "message": f"{req.name}님 등록 완료"}


@app.post("/login")
async def login(form: OAuth2PasswordRequestForm = Depends()):
    user = authenticate_user(form.username, form.password)
    token = create_token(user["student_id"], user["name"])
    return {"access_token": token, "token_type": "bearer", "name": user["name"]}


@app.get("/", response_class=HTMLResponse)
async def root():
    with open(os.path.join(BASE_DIR, "index.html"), encoding="utf-8") as f:
        return f.read()


@app.post("/upload")
async def upload_pdf(file: UploadFile = File(...)):
    global pdf_ready
    pdf_ready = False

    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    loop = asyncio.get_event_loop()
    try:
        await loop.run_in_executor(executor, process_pdf, tmp_path)
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        try:
            os.unlink(tmp_path)
        except Exception:
            pass

    pdf_ready = True
    return {"status": "ok"}


PROMPTS = [
    ("summary", """업로드된 강의자료를 요약해줘.
규칙:
- 핵심 내용 위주
- 학생이 이해하기 쉽게 설명
- 10줄 이내"""),
    ("concepts", """업로드된 강의자료의 핵심 개념을 정리해줘.
형식:
개념명
설명

개념명
설명"""),
    ("exam", """업로드된 강의자료를 기반으로
객관식 5문제
주관식 5문제
생성해줘.
정답과 해설 포함."""),
]


async def _stream():
    loop = asyncio.get_event_loop()
    for type_key, prompt in PROMPTS:
        try:
            result = await loop.run_in_executor(executor, ask_full, prompt)
            result = strip_thinking(result)
            yield f"data: {json.dumps({'type': type_key, 'content': result}, ensure_ascii=False)}\n\n"
        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'content': str(e)}, ensure_ascii=False)}\n\n"
    yield 'data: {"type":"done"}\n\n'


@app.get("/analyze")
async def analyze():
    if not pdf_ready:
        raise HTTPException(status_code=400, detail="PDF 업로드 필요")
    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/chat")
async def chat(msg: ChatMessage, user=Depends(get_current_user)):
    if not pdf_ready:
        raise HTTPException(status_code=400, detail="PDF 업로드 필요")

    student_id = user["student_id"]

    async def sse_gen():
        import queue as q_mod
        token_queue = q_mod.Queue()

        def produce():
            buf = ""
            in_think = False
            collected = []
            # 수준평가 백그라운드 실행 (답변 속도에 영향 없음)
            import threading
            threading.Thread(
                target=assess_and_update, args=(student_id, msg.message), daemon=True
            ).start()
            try:
                level_info = None

                # 라우팅: 개인 모델 → 서버 → 로컬 순으로 시도
                if personal_model_exists(student_id):
                    from rag import _get_context
                    ctx = _get_context(msg.message)
                    stream = ask_personal_stream(student_id, ctx, msg.message)
                    source = "personal"
                elif is_server_available():
                    from rag import _get_context
                    ctx = _get_context(msg.message)
                    stream = ask_server_stream(ctx, msg.message)
                    source = "server"
                else:
                    stream = ask_stream(msg.message, level_info)
                    source = "local"

                for token in stream:
                    buf += token
                    while True:
                        if in_think:
                            end = buf.find("</think>")
                            if end != -1:
                                buf = buf[end + 8:]
                                in_think = False
                            else:
                                buf = ""
                                break
                        else:
                            start = buf.find("<think>")
                            if start != -1:
                                if buf[:start]:
                                    token_queue.put(buf[:start])
                                buf = buf[start + 7:]
                                in_think = True
                            else:
                                safe = max(0, len(buf) - 7)
                                if buf[:safe]:
                                    token_queue.put(buf[:safe])
                                buf = buf[safe:]
                                break
                if buf and not in_think:
                    token_queue.put(buf)
                    collected.append(buf)
            finally:
                token_queue.put(None)
                # 상호작용 로그 저장
                full_answer = "".join(collected)
                if full_answer:
                    log_interaction(student_id, msg.message, full_answer, source)
                # 학습 트리거 알림
                if should_train(student_id):
                    token_queue.put("__TRAIN_READY__")

        loop = asyncio.get_event_loop()
        loop.run_in_executor(executor, produce)

        train_ready = False
        while True:
            token = await loop.run_in_executor(None, token_queue.get)
            if token is None:
                break
            if token == "__TRAIN_READY__":
                train_ready = True
                continue
            yield f"data: {json.dumps({'token': token}, ensure_ascii=False)}\n\n"
        yield f"data: {json.dumps({'done': True, 'train_ready': train_ready}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        sse_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


VIDEO_PROMPT = """너는 업로드된 강의자료 전담 AI 튜터다.
반드시 아래 형식을 지켜:

## 슬라이드 제목
- 핵심 내용
- 핵심 내용
- 핵심 내용

규칙:
- 모든 슬라이드는 반드시 ## 로 시작
- 최소 5개 이상의 슬라이드 생성
- 각 슬라이드 내용은 3~5개의 핵심 항목
- 긴 문단 금지
- 발표용 슬라이드 형식"""


@app.post("/generate-video")
async def generate_video():
    if not pdf_ready:
        raise HTTPException(status_code=400, detail="PDF 업로드 필요")
    loop = asyncio.get_event_loop()
    summary = await loop.run_in_executor(executor, ask, VIDEO_PROMPT)
    summary = strip_thinking(summary)
    await loop.run_in_executor(executor, create_tts, summary)
    video_path = await loop.run_in_executor(executor, create_video, summary)
    return FileResponse(video_path, media_type="video/mp4", filename="lecture_video.mp4")

@app.get("/my-level")
async def my_level(user=Depends(get_current_user)):
    return get_student_level(user["student_id"])


@app.get("/export-student/{student_id}")
async def export_student(student_id: str, user=Depends(get_current_user)):
    path = export_student_data(student_id, f"qa_{student_id}.jsonl")
    info = get_student(student_id)
    return {
        "student_id": student_id,
        "interactions": info["interaction_count"],
        "model_trained": info["model_trained"],
        "exported_to": path,
    }


@app.get("/generate-qa")
async def generate_qa():
    if not pdf_ready:
        raise HTTPException(status_code=400, detail="PDF 업로드 필요")

    async def sse_gen():
        import queue as q_mod
        progress_queue = q_mod.Queue()
        all_pairs = []

        def produce():
            try:
                for current, total, new_pairs in generate_qa_pairs(rag_module.parents):
                    all_pairs.extend(new_pairs)
                    progress_queue.put((current, total, False))
            finally:
                progress_queue.put((0, 0, True))

        loop = asyncio.get_event_loop()
        loop.run_in_executor(executor, produce)

        while True:
            current, total, done = await loop.run_in_executor(None, progress_queue.get)
            if done:
                path = save_qa_pairs(all_pairs)
                yield f"data: {json.dumps({'done': True, 'total': len(all_pairs), 'path': path}, ensure_ascii=False)}\n\n"
                break
            yield f"data: {json.dumps({'current': current, 'total': total}, ensure_ascii=False)}\n\n"

    return StreamingResponse(
        sse_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.get("/favicon.ico")
async def favicon():
    return FileResponse("favicon.ico")

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
