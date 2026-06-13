import os as _os
_env_path = _os.path.join(_os.path.dirname(__file__), "local.env")
if _os.path.exists(_env_path):
    with open(_env_path, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _k, _v = _line.split("=", 1)
                _os.environ.setdefault(_k.strip(), _v.strip())
_os.environ.setdefault("SURYA_DEVICE", "cpu")

import queue

from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.responses import HTMLResponse, StreamingResponse, FileResponse
from fastapi.security import OAuth2PasswordRequestForm
from pydantic import BaseModel
import uvicorn
import tempfile
import os
import asyncio
import json
from concurrent.futures import ThreadPoolExecutor

import rag as rag_module
from rag import process_document, ask_stream, ask_full_stream
from document import SUPPORTED_EXTS
from qa_generator import generate_qa_pairs, save_qa_pairs
from student_db import init_db, log_interaction, should_train, export_student_data, get_student
from model_manager import personal_model_exists, ask_personal_stream
from server_client import ask_server_stream, is_server_available
from auth import init_auth_db, register_user, authenticate_user, create_token, get_current_user
from level_assessor import init_level_db, assess_and_update, get_student_level

init_db()
init_auth_db()
init_level_db()
from lecture import generate_lecture

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

app = FastAPI()
executor = ThreadPoolExecutor(max_workers=2)
pdf_ready = False


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
async def upload_document(file: UploadFile = File(...)):
    global pdf_ready
    pdf_ready = False

    filename = file.filename or "uploaded"
    ext = os.path.splitext(filename)[1].lower()
    if ext not in SUPPORTED_EXTS:
        raise HTTPException(
            status_code=400,
            detail=f"지원하지 않는 형식: {ext or '없음'} (지원: {', '.join(SUPPORTED_EXTS)})",
        )

    content = await file.read()
    with tempfile.NamedTemporaryFile(delete=False, suffix=ext) as tmp:
        tmp.write(content)
        tmp_path = tmp.name

    loop = asyncio.get_running_loop()
    try:
        await loop.run_in_executor(executor, process_document, tmp_path)
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
    ("summary", """업로드된 강의자료 전체를 분석해서 아래 형식으로 요약해줘.

1. 강의 주제 (한 줄)
2. 학습 목표 (3~5개, 번호 목록)
3. 섹션별 핵심 내용 (강의 흐름 순서대로)
4. 중요 포인트 (반드시 기억해야 할 것 5개 이내)

조건:
- 강의 흐름을 유지하며 요약
- 전문 용어는 괄호 안에 간단히 설명
- 학생이 시험 전 복습에 바로 쓸 수 있는 수준"""),

    ("concepts", """업로드된 강의자료에서 핵심 개념을 모두 추출해서 아래 형식으로 정리해줘.

각 개념마다:
▶ 개념명
  - 정의: 한 문장으로
  - 핵심 특징: 2~3가지
  - 관련 개념: (있으면 명시)

조건:
- 중요도 높은 순서로 정렬
- 전문 용어는 쉬운 설명 병기
- 강의에서 강조된 내용 위주로 선별"""),

    ("exam", """업로드된 강의자료를 기반으로 실제 시험에 나올 법한 문제를 만들어줘.

[객관식 5문제]
각 문제 형식:
번호. 문제 내용
① 보기1 ② 보기2 ③ 보기3 ④ 보기4 ⑤ 보기5
정답: 번호
해설: 정답 근거 (강의 내용 기반)

[주관식 5문제]
각 문제 형식:
번호. 문제 내용
모범답안: (핵심 키워드 포함)
채점 기준: 주요 포인트 2~3개

조건:
- 강의 핵심 내용에서 골고루 출제
- 객관식: 명확한 정답, 그럴듯한 오답 포함
- 주관식: 단순 암기보다 개념 이해를 측정"""),
]


async def _stream():
    loop = asyncio.get_running_loop()
    for type_key, prompt in PROMPTS:
        yield f"data: {json.dumps({'type': type_key, 'event': 'start'}, ensure_ascii=False)}\n\n"
        token_queue: queue.Queue = queue.Queue()

        def produce(p=prompt):
            try:
                for token in ask_full_stream(p):
                    token_queue.put(token)
            except Exception as e:
                token_queue.put(('__error__', str(e)))
            finally:
                token_queue.put(None)

        loop.run_in_executor(executor, produce)
        while True:
            item = await loop.run_in_executor(None, token_queue.get)
            if item is None:
                break
            if isinstance(item, tuple):
                yield f"data: {json.dumps({'type': 'error', 'content': item[1]}, ensure_ascii=False)}\n\n"
                break
            yield f"data: {json.dumps({'type': type_key, 'event': 'token', 'token': item}, ensure_ascii=False)}\n\n"

        yield f"data: {json.dumps({'type': type_key, 'event': 'done'}, ensure_ascii=False)}\n\n"
    yield 'data: {"type":"done"}\n\n'


@app.get("/analyze")
async def analyze():
    if not pdf_ready:
        raise HTTPException(status_code=400, detail="문서 업로드 필요")
    return StreamingResponse(
        _stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


@app.post("/chat")
async def chat(msg: ChatMessage, user=Depends(get_current_user)):
    if not pdf_ready:
        raise HTTPException(status_code=400, detail="문서 업로드 필요")

    student_id = user["student_id"]

    async def sse_gen():
        import queue as q_mod
        token_queue = q_mod.Queue()

        def produce():
            buf = ""
            in_think = False
            collected = []
            import threading
            threading.Thread(
                target=assess_and_update, args=(student_id, msg.message), daemon=True
            ).start()
            try:
                level_info = get_student_level(student_id)

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
                                    collected.append(buf[:start])
                                buf = buf[start + 7:]
                                in_think = True
                            else:
                                safe = max(0, len(buf) - 7)
                                if buf[:safe]:
                                    token_queue.put(buf[:safe])
                                    collected.append(buf[:safe])
                                buf = buf[safe:]
                                break
                if buf and not in_think:
                    token_queue.put(buf)
                    collected.append(buf)
            finally:
                full_answer = "".join(collected)
                if full_answer:
                    log_interaction(student_id, msg.message, full_answer, source)
                if should_train(student_id):
                    token_queue.put("__TRAIN_READY__")
                token_queue.put(None)

        loop = asyncio.get_running_loop()
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


@app.post("/generate-video")
async def generate_video(user=Depends(get_current_user)):
    if not pdf_ready:
        raise HTTPException(status_code=400, detail="문서 업로드 필요")
    loop = asyncio.get_running_loop()

    level_info = get_student_level(user["student_id"])
    context = await loop.run_in_executor(executor, rag_module._full_context)

    out_path = os.path.join(BASE_DIR, "lecture_video.mp4")
    video_path = await loop.run_in_executor(
        executor, generate_lecture, context, level_info, out_path
    )
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
        raise HTTPException(status_code=400, detail="문서 업로드 필요")

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

        loop = asyncio.get_running_loop()
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
    path = os.path.join(BASE_DIR, "favicon.ico")
    if os.path.exists(path):
        return FileResponse(path)
    from fastapi.responses import Response
    return Response(status_code=204)

if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=7860)
