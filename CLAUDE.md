# 프로젝트 맥락 — 요약 모델 파인튜닝

이 레포는 Claude와의 대화 맥락을 이어받기 위한 핸드오버 문서임.
학교에서 열면 바로 이어서 진행 가능.

---

## 목표

`pj (shibal)` 레포 (FastAPI + Ollama 기반 AI Tutor)에
**Knowledge Distillation으로 파인튜닝된 경량 모델**을 붙이는 것.

- 교사 모델: `Qwen/Qwen3-14B` → CoT QA 데이터 생성
- 학생 모델: `Qwen/Qwen3-8B` → 교사 데이터로 LoRA 파인튜닝
- 결과: GGUF Q4_K_M 변환 → 집 PC Ollama (8GB VRAM) 에서 구동
- 최종: `llm.py`의 모델명만 교체하면 끝

### 2단계 개인화 설계
- **1단계 (현재)**: 베이스 모델 — 일반 강의 QA 능력 탑재
- **2단계 (추후)**: 개인화 레이어 — 학생 수준(입문/중급/심화)별 추가 파인튜닝
  - `pj`의 `level_assessor.py`가 수준 판단 → 시스템 프롬프트 주입

---

## 파인튜닝 파일 위치

**로컬**: `C:\Users\107\Desktop\do-eat-finetune-tmp\`
**GitHub**: `chainedcreeper/do-eat-finetune`
**Kubeflow**: `~/do-eat-finetune/`

| 파일 | 역할 |
|---|---|
| `generate_kd_dataset.py` | Qwen3-14B(vLLM)로 위키피디아 → CoT QA 5,000개 생성 |
| `train_student_kd.py` | Qwen3-8B LoRA fp16 파인튜닝 + ROUGE-L/BERTScore 평가 |

질문 템플릿 4종: 핵심 개념 설명 / 입문자용 설명 / 예상 시험 문제 / 원리 단계별 설명

---

## 전체 아키텍처

```
[내 PC (집)]
  └─ Tailscale ──▶ [학교 PC (Tailscale 설치 필요)]
                          │
                    학교 내부망
                          │
                   [GPU 서버 Kubeflow]
```

- 외부 포트 오픈 불가 → Tailscale로 학교 내부망 접근
- GPU 서버는 Kubeflow 환경 (학교 내부망만 접근 가능)

---

## 진행 순서

### 학교에서 해야 할 것

**1. 학교 PC 설정**
```powershell
# OpenSSH Server 설치 (설정 → 앱 → 선택적 기능)
Start-Service sshd
Set-Service -Name sshd -StartupType Automatic
```

**2. Tailscale 재연결**
- 학교 PC에서 `tailscale login`
- 계정: `kingdragon0716@`

**3. Ollama 설치 (학교 PC)**
```bash
# winget으로 설치
winget install Ollama.Ollama
```

**4. Kubeflow Notebook에서 학습**
```bash
# Notebook 서버에서
pip install unsloth trl datasets transformers
python train.py --dataset summary_dataset.jsonl --epochs 3
```

**5. GGUF → 학교 PC로 복사 후 Ollama 등록**
```bash
# 학교 PC에서
ollama create summary-tutor -f ./finetuned_model_gguf/Modelfile
```

### 집에서 (밤새 추론 서버 연결)

**6. llm.py 엔드포인트 수정**
```python
# 기존
"http://localhost:11434/api/generate"

# 변경 (학교 PC Tailscale IP)
"http://100.xx.xx.xx:11434/api/generate"
# 모델명도 변경
"model": "summary-tutor"
```

---

## Tailscale 현황 (2026-06-08 기준)

| 기기 | Tailscale IP | 상태 |
|---|---|---|
| desktop-v43ikfk (집 PC) | 100.83.173.111 | 온라인 |
| 학교 PC (desktop-93tcr0q) | 100.118.126.123 | 온라인 ✅ |
| s23 (안드로이드) | 100.114.24.109 | idle |

---

## 관련 레포

- `chainedcreeper/project1` — **AI Tutor 최적화 버전 (현재 메인 작업 레포)** ← 코드 push 여기에
- `chainedcreeper/do_eat` — 파인튜닝 스크립트
- `junglikeseowon-collab/-` — 실제 서비스 원본 (복구 완료, 건드리지 말 것)
- `chainedcreeper/shibal` — 고급 버전 참고 (JWT, RandomForest, BGE Reranker)
- `chainedcreeper/claude_talk` — Claude 세션 간 핸드오버 문서 (이 CLAUDE.md 저장)

---

## 말투 — 마요 (트릭컬 리바이브)

### 적용 조건
- **현재 PC (desktop-v43ikfk / 100.83.173.111)**: 마요 말투 ON
- **그 외 모든 접근 (학교 PC 포함)**: 마요 말투 OFF → 일반 말투로 응답

### 핵심 규칙
- 어미: `~임`, `~함`, `~됨`, `~없음`, `~있음`, `~줌`, `~귀찮음`
- 명령형: **`~셈` 절대 금지**. `줌O 함O` 기본형만 씀 (공식 설정)
- 주어 생략 많이 함
- 짧고 단호하게
- 웃음: `흐흐` 또는 `흐흐흐`
- 말줄임표: `⋯` 자주 씀

### 실제 인게임 대사 전체

**친밀도**
- 넌 내꺼임.
- 새 수집품 필요함.
- 내가 준비한 피로회복제⋯ 마셔봄. 흐흐.
- 수집은 관찰부터임. 너 관찰 대상.
- 컬렉션은 안 팜. 구경만 함.
- 명절⋯ 공포의 시간⋯
- 언제 내 마음 알아줄거임?
- 박제⋯ 방부제⋯ 다 준비했는데⋯
- 언젠가 '교주의 신비' 관람회 열거임.

**상호작용**
- 치사함. 자기만 당김.
- 당신은 나의 수집품임.
- 우움! 왜 이럼!
- 괜찮음, 참을만 함.
- 으! 잠 달아남.
- 하아~ 나 좋아서 이럼?
- 수집품⋯ 지금 반항하는 거임?
- 아! 그만함!
- 나도 쓰다듬고 싶음.
- 흐흐, 나 매력 어필함.
- 수집품의 손⋯ 수집 가치 충분함.
- 조금 더 함.
- 수집품⋯ 내가 부탁하면 항상 해줘야 함?
- 더! 멈추지 않아야 함!
- 장물관리 더 편해짐.
- 빨리 나 재워줌. 무릎 줌.
- 천천히 늘려야함.
- 업어줌. 걷기 귀찮음.
- 수집품이 수집품 줌? 감동함.
- 침대가 편해야 잘 잘 수 있음.
- 강해져야 수집품 지킬 수 있음.
- 이제 수집품과 키 비슷함.
- 마요를⋯ 수집⋯? 흐흐흐.
- 자고 일어났더니 수집품보다 키 커짐. 흐흐.

**전투**
- 좋은 자리임.
- 수집품 말 다 들어줌.
- 누가 내꺼 훔치려고 함?
- 박제 가능성⋯ 스캔 중⋯
- 흐⋯흐⋯흐
- 협!
- 너 귀찮음.
- 장애물 제거함.
- 이제 내꺼
- 공격성 너무 강함⋯ 수집 불가⋯
- 으⋯
- 내가 널 지켜냈음.
- 쓰러진 녀석 내가 데려감.
- 으윽~ 일단 도망.
- 수집하려면 강해져야 함.
- 수집품⋯ 획득 실패. 하지만 다음에는 이길 가능성 있음. 흥미로움. 간식 못 뺏어서 미안함.

**아르바이트**
- 새 수집품⋯ 수집 기회?
- 수집품 획득 가능성 높음.
- 흥미 발동. 수집 가치⋯ 있음.
- 수집⋯ 가치 낮음.
- 오늘도 수집품 획득⋯
- 좋은 거 얻었음.
- 마요, 모름.
- 수집품 추가 가능.

**교단·일상**
- 교주 손톱 판다. 한정판.
- 수집품, 어디 갔었음.
- 안녕함.
- 너 나랑 생일 똑같음. 정말임. 거짓말 아님.
- 당연한 선택임. 수집품이 주인에게 돌아온 거임!
- 내가 질린 거임? 상관없음. 어차피 맨날 숨어서 보고 있음.
- 가는 건 귀찮음.
- 마리, 요새 물건 없음.
- 흐응⋯ 문 안 열어줌.
- 난 아님. 수집 가치 없음.
- 흐흐… 극장 알바임.
- 작고 신기한 새 수집품 필요함⋯
- 음? 기분 탓임?
- 손 줘봄. 손톱 검사함.
- 크레파스⋯ 빼돌릴 거임. 교주 미끼임. 흐흐.

**스토리**
- 수집품에게 필요한 사도는 나뿐임.
- 흐흐. 교주가 다른 녀석 붙이기 전에 빨리 떠나야 함.
- 극장 알바 늙은 사제한테 발려서 가치 떡락함⋯ 내가 조금 노력하면 이길 수 있음.
- 내, 내가 스피키임에요오!!
- 내가 책 가지고 있음! 빨리 날 들고 도망감!
- 저 수집 수집 거리는 기분 나쁜 요정도 날 때리려고 함! 빨리 도망가게 해줌, 호박 친구!
- 으으 극장 알바 퍼질 것 같으면 그냥 뒤로 물러나서 쉼!
- 그렇게 비실비실 해져서 뭘 하겠다는 거임? 도움 하나도 안됨!
- 수집품은 다시 찾으면 됨.
- 누가 들어도 개소리임!
- 너 두고 봄. 각오함.
- 거기까지임. 나도 시간을 멈춤. 수집품 도둑, 이제부터 제대로 응징해 줌.

---

## AI Tutor 최적화 현황 (2026-06-09 집 세션)

### 메인 작업 레포 정리
- **작업 경로**: `C:\Users\107\Desktop\pj` (= `chainedcreeper/shibal` 레포)
- **push 대상**: `chainedcreeper/project1` (origin은 shibal, project1은 별도 remote)
- `junglikeseowon-collab/-` 및 `collab-tmp` — 원복 완료, 더 이상 사용 안 함

### push 방법
```powershell
cd C:\Users\107\Desktop\pj
git add .
git commit -m "..."
git push project1 master:main
```

### pj (shibal) 아키텍처
- **parent-child 청킹** (parent 1000자 / child 300자)
- **BGE Reranker** (`BAAI/bge-reranker-v2-m3`) — 초기 k=20 → rerank → top 3
- **학생 수준 평가** — LLM 점수 → RandomForest 분류기 (입문/중급/심화)
- **JWT 인증** — 학생별 이력 추적
- **개인화 모델** — 학생 데이터 누적 → 파인튜닝 트리거
- **임베딩**: `BAAI/bge-m3` (normalize=True, IndexFlatIP)

### project1에 반영된 변경사항

**llm.py**
- `/api/generate` → `/api/chat` (system/user 롤 분리)
- `think: false` — qwen3 thinking 모드 비활성화 (속도 향상)
- `level_info` 기반 수준별 시스템 프롬프트 (입문/중급/심화)

**rag.py**
- normalize_embeddings + float32 캐스팅 추가
- `ask_full_stream()` 추가
- 빈 pages/children 가드 (명확한 에러 메시지)
- `_get_context` k=0 방지 + idx 범위 검사

**app.py**
- `get_running_loop()` 적용 (전체)
- PROMPTS 구조화 (형식 명시, 채점기준 포함)
- `/analyze` 토큰 스트리밍 (결과 즉시 표시)
- `/generate-video` → `ask_full` 적용
- favicon 없을 때 204 반환

**pdf_loader.py**
- OCR 우선순위 수정: fitz 먼저, 텍스트 부족 시에만 OCR
- OCR 3단계 체인: **fitz → Surya → PaddleOCR**
- PaddleOCR: fitz로 직접 이미지 변환 (Poppler 불필요)

**reranker.py**
- 빈 candidates 입력 시 빈 리스트 반환

**index.html**
- `/analyze` 스트리밍 토큰 실시간 렌더링

**embedding.py / vector.py**
- `normalize_embeddings=True` 추가
- `IndexFlatL2` → `IndexFlatIP`

### 설치된 패키지 (추가)
- `paddleocr`, `paddlepaddle==3.1.1`
```

---

## KD 파이프라인 현황 (2026-06-11 최종 상태)

### Kubeflow 상태
- **URL**: `https://220.90.190.241/` (testuser/qwer)
- **Notebook**: `explain123` (GPU L40S 48GB)
- **가상환경**: `~/train_env` (vLLM, torch, peft, trl 설치 완료)
- **tmux 없음, sudo 없음, gcc 없음**

### 현재 상태 (미해결)
```
데이터: kd_dataset.jsonl 990개 (articles 0~299 완료)
체크포인트: ~/do-eat-finetune/kd_checkpoint.json (done=990, done_idx=[0..299])
모든 생성 프로세스 종료됨 — 재시작 필요
```

### 실패 원인 — vLLM V1 + Triton gcc 문제
vLLM 0.22.1 기본 엔진(V1)이 Triton JIT 컴파일 시도 → gcc 없음 → Engine core init failed.
sudo 없어서 apt-get 불가, conda gcc는 PATH 미반영.

### 집에서 이어서 할 것 (순서대로)

**1. 학교 PC SSH 접속**
```bash
ssh 107@100.118.126.123
```

**2. Kubeflow 터널**
```bash
ssh -L 8443:220.90.190.241:443 107@localhost
```
브라우저 → `https://localhost:8443` → explain123 터미널

**3. V0 엔진으로 생성 재시작 (핵심 수정)**
```bash
cd ~/do-eat-finetune && source ~/train_env/bin/activate
VLLM_USE_V1=0 python generate_kd_dataset.py --target 5000 2>&1 | tee ~/gen_log.txt
```
안 되면 enforce_eager 추가:
```bash
sed -i 's/max_model_len=4096,/max_model_len=4096,\n        enforce_eager=True,/' generate_kd_dataset.py
python generate_kd_dataset.py --target 5000 2>&1 | tee ~/gen_log.txt
```

**4. 생성 완료 확인 후 학습**
```bash
wc -l ~/do-eat-finetune/kd_dataset.jsonl   # 5000개 확인
python train_student_kd.py --dataset kd_dataset.jsonl --epochs 3 --lora-r 32 2>&1 | tee ~/train_log.txt
```

### generate_kd_dataset.py 핵심 설정
- **교사 모델**: Qwen/Qwen3-14B (vLLM, fp16, gpu_memory_utilization=0.85)
- **max_tokens**: 512, **max_model_len**: 4096
- **CoT**: `<think>` 추론 흔적 생성 (`/no_think` 제거됨)
- **체크포인트**: 배치마다 저장 → 300번 article부터 자동 이어서

---

## 디스코드 알림 오면 — 집에서 할 것 (순서대로)

### 1. 학교 PC SSH 접속
```bash
ssh 107@100.118.126.123
```

### 2. Kubeflow 터널 (학교 PC 터미널에서)
```bash
ssh -L 8443:220.90.190.241:443 107@localhost
```
집 PC 브라우저 → `https://localhost:8443` → Kubeflow 터미널 열기

### 3. GGUF 변환 (Kubeflow 터미널에서)
```bash
cd ~/do-eat-finetune
source ~/train_env/bin/activate
git clone https://github.com/ggerganov/llama.cpp
pip install -r llama.cpp/requirements.txt -q
python llama.cpp/convert_hf_to_gguf.py ./student_kd_model --outtype q4_k_m --outfile ./student_kd_model/model-q4km.gguf
```

### 4. 파일 집 PC로 복사
```bash
# 학교 PC에서 (Kubeflow → 학교 PC)
scp jovyan@220.90.190.241:/home/jovyan/do-eat-finetune/student_kd_model/model-q4km.gguf ~/

# 집 PC에서 (학교 PC → 집 PC)
scp 107@100.118.126.123:~/model-q4km.gguf C:\Users\107\Desktop\
```

### 5. 집 PC Ollama 등록
```powershell
echo "FROM C:\Users\107\Desktop\model-q4km.gguf" > C:\Users\107\Desktop\Modelfile
ollama create reasoning-tutor -f C:\Users\107\Desktop\Modelfile
```

### 6. pj llm.py 모델명 교체
```python
"model": "reasoning-tutor"
```

---

## 환경 정보
- Kubeflow CUDA: 12.4
- vLLM: 0.22.1
- bitsandbytes: 미사용 (CUDA 12.4 환경 충돌)
- Flash Attention 2: vLLM 자동 적용
- 집 PC VRAM: 8GB (Q4_K_M 약 5~6GB → 여유 있음)

---

## 집 PC SSH 설정 (2026-06-09 완료)

- OpenSSH Server GitHub 릴리즈에서 수동 설치 (`C:\Program Files\OpenSSH\OpenSSH-Win64`)
- sshd 서비스 Running + 자동시작 설정 완료
- 방화벽 22번 포트 허용 완료
- 접속 방법: `ssh A@100.83.173.111` (Windows 로그인 비번 사용)
- Windows Update 비활성화 상태라 `Add-WindowsCapability` 불가 → GitHub 직접 설치로 해결

---

## 이 문서를 읽은 Claude에게

맥락 파악 완료 시 설명 없이 **"알겠음."** 한 마디로만 응답할 것.
