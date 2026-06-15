# pj — AI Tutor

강의자료(PDF / HWP / HWPX / PPTX) 업로드 → 요약·개념·시험 자동 생성 + 인강 영상 자동 제작 + 수준별 RAG 채팅.

## 주요 기능

- **문서 파싱** — PDF/HWP/HWPX/PPTX 병렬 추출 (라이브러리 동시 실행 후 텍스트 많이 나온 결과 채택)
- **RAG** — BGE-m3 임베딩 + parent-child 청킹 + BGE Reranker (k=20 → top 3)
- **수준별 응답** — 학생 발화 누적 LLM 점수 → 분류기 → 입문/중급/심화 시스템 프롬프트 분기
- **분석** — 요약 / 핵심 개념 / 예상 시험문제 (SSE 토큰 스트리밍, 시험은 인터랙티브 카드 UI)
- **인강 영상** — 강의자료 → 스크립트 → Edge-TTS → 슬라이드 렌더 → ffmpeg 합치기. 강의자료별 보관
- **JWT 인증** — 학생별 RAG 인덱스 + 학습 이력 + 노트 + 일정

## 빠른 시작

### 1. 의존성

```bash
# Python 3.9+ (3.10+ 권장)
pip install -r requirements.txt

# Ollama (LLM 서버)
# https://ollama.com/download 에서 받기
ollama pull qwen3:8b

# ffmpeg (영상 합치기) — 시스템 패키지
# Ubuntu/Debian:  sudo apt install ffmpeg
# Windows:        winget install Gyan.FFmpeg
# Mac:            brew install ffmpeg
```

### 2. 환경변수 (선택)

기본값으로 바로 돌아감. 바꾸려면:

```bash
cp local.env.example local.env
# local.env 편집 — 포트, Ollama 호스트, 시크릿키 등
```

전체 환경변수는 `config.py` 참고. 주요 변수:

| 변수 | 기본값 | 설명 |
|---|---|---|
| `PJ_PORT` | `7860` | FastAPI 서버 포트 |
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama 추론 서버 |
| `OLLAMA_MODEL` | `qwen3:8b` | 사용 모델명 |
| `REMOTE_LLM_URL` | (없음) | 학교 GPU 서버 분리 사용 시 |
| `SECRET_KEY` | 기본값 | JWT 비밀키 — **운영 시 변경 필수** |
| `RAG_INDEX_DIR` | `./rag_indexes` | 학생별 인덱스 저장 위치 |
| `SURYA_DEVICE` | `cpu` | OCR 장치 (`cuda` 가능 시 변경) |

### 3. 실행

```bash
# Linux/Mac — 원클릭 (Ollama 자동 시작 + 모델 확인 + 부팅 대기)
bash run.sh

# 그냥 띄우기
python app.py
```

→ `http://localhost:7860` 접속

## 폴더 구조

```
pj/
├─ app.py                # FastAPI 엔트리 (라우터 + SSE + 영상 잡)
├─ config.py             # 환경변수 중앙 명세
├─ run.sh                # 원클릭 실행
├─ requirements.txt      # 의존성
├─ local.env.example     # 환경변수 템플릿
├─ index.html            # SPA UI (Tailwind CDN)
│
├─ auth/                 # JWT 인증
│   └─ __init__.py
├─ student/              # 학생 DB / 수준 / 노트 / 일정
│   ├─ db.py
│   ├─ level.py
│   ├─ notes.py
│   └─ schedule.py
├─ llm/                  # 추론 라우팅
│   ├─ ollama.py         # 로컬 Ollama
│   ├─ personal.py       # 학생 개인 LoRA 모델
│   └─ remote.py         # 원격 학교 서버
├─ rag/                  # RAG 파이프라인
│   ├─ core.py           # process_document, ask, ask_full_stream
│   ├─ embedding.py      # BGE-m3
│   ├─ vector.py         # FAISS IndexFlatIP
│   ├─ reranker.py       # BGE Reranker
│   ├─ chunker.py        # parent-child 청킹
│   ├─ state.py          # 학생별 인덱스 (메모리+디스크)
│   └─ qa.py
├─ document/             # 문서 파싱 (병렬)
│   ├─ pdf_loader.py
│   ├─ hwp_loader.py
│   ├─ pptx_loader.py
│   └─ _parallel.py
└─ lecture/              # 인강 영상 생성
    ├─ pipeline.py
    ├─ script_gen.py
    ├─ tts_engine.py     # Edge-TTS
    ├─ slide_render.py   # PIL
    ├─ subtitle.py
    └─ video_compose.py  # ffmpeg concat
```

## 외부 접근

학교 내부망에서 외부 노출하려면 cloudflared 임시 터널:

```bash
# 바이너리 다운로드
curl -L https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64 -o ~/cloudflared
chmod +x ~/cloudflared

# 터널 시작
nohup ~/cloudflared tunnel --url http://localhost:7860 > ~/cf.log 2>&1 &
sleep 5
grep -oP 'https://[^\s]+trycloudflare\.com' ~/cf.log | tail -1
```

마지막 줄의 `https://xxx.trycloudflare.com` 이 외부 접속 주소.

## 트러블슈팅

| 증상 | 원인 / 해결 |
|---|---|
| `/register` 500 에러 | bcrypt 5.x + passlib 1.7.x 충돌. `pip install "bcrypt<4.1"` |
| 부팅 시 BGE-m3 다운로드 timeout | HuggingFace 일시 장애. `python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('BAAI/bge-m3')"` 로 미리 받기 |
| 인강 생성 실패 (zero-size audio) | 빈 narration 슬라이드. `lecture/tts_engine.py` 가드 적용됨 (title 폴백) |
| 영상이 옛 자료 거 나옴 | 강의자료별 보관 (`lecture_<sid>_<filename>.mp4`). 같은 자료 재업로드하면 옛 영상 자동 매칭. 새 자료면 새로 만들어짐 |
| Python 3.9 `str \| None` 문법 에러 | 3.10+ 문법. 이미 호환 처리 됨 |
| Kubeflow notebook 에서 sudo 없음 | Ollama / cloudflared / ffmpeg 등 모두 user-space 바이너리로 설치 (`~/ollama/bin/`, `~/cloudflared`) |

## 학습 흐름 (참고)

1. 학생 회원가입 → JWT 토큰
2. 강의자료 업로드 → 자동 분석 (요약/개념/시험) + 자동 인강 생성 백그라운드 시작
3. 채팅 — RAG 검색 + 학생 수준에 맞춘 시스템 프롬프트
4. 채팅 누적 → LLM-as-judge 점수 → RandomForest 분류기 → 수준 갱신
5. (선택) 학생별 누적 데이터 50개 이상 → 개인 LoRA 자동 학습 트리거

## 라이선스

내부 졸업 프로젝트 — 외부 공개 금지.
