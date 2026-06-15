"""환경변수 중앙 명세.

모든 환경변수는 여기 한 곳에서 볼 수 있고, 기본값도 여기서 관리.
실제 코드는 여전히 os.getenv 직접 호출해도 되고 (현재 패턴), config.X 임포트해도 됨.
local.env 파일이 있으면 app.py 시작 시 자동 로드됨.
"""
import os

# ── 디렉토리 ──
BASE_DIR      = os.path.dirname(os.path.abspath(__file__))
RAG_INDEX_DIR = os.getenv("RAG_INDEX_DIR", os.path.join(BASE_DIR, "rag_indexes"))
DB_PATH       = os.getenv("DB_PATH",       os.path.join(BASE_DIR, "students.db"))

# ── 서버 ──
PJ_PORT       = int(os.getenv("PJ_PORT", "7860"))

# ── Ollama 추론 ──
OLLAMA_HOST   = os.getenv("OLLAMA_HOST",  "http://localhost:11434")
OLLAMA_MODEL  = os.getenv("OLLAMA_MODEL", "qwen3:32b")

# ── 원격 LLM 라우팅 (학교 GPU 서버 분리) ──
REMOTE_LLM_URL   = os.getenv("REMOTE_LLM_URL",   "")
REMOTE_LLM_MODEL = os.getenv("REMOTE_LLM_MODEL", "exaone3.5:32b")

# ── 인증 ──
SECRET_KEY         = os.environ.get("SECRET_KEY",        "woosong-ai-tutor-secret-change-me")
TOKEN_EXPIRE_HOURS = int(os.getenv("TOKEN_EXPIRE_HOURS", "24"))

# ── 모델/장치 ──
SURYA_DEVICE = os.getenv("SURYA_DEVICE", "cpu")


def summary():
    """현재 설정 요약 — 디버깅용."""
    return {
        "BASE_DIR":      BASE_DIR,
        "RAG_INDEX_DIR": RAG_INDEX_DIR,
        "DB_PATH":       DB_PATH,
        "PJ_PORT":       PJ_PORT,
        "OLLAMA_HOST":   OLLAMA_HOST,
        "OLLAMA_MODEL":  OLLAMA_MODEL,
        "REMOTE_LLM_URL":   REMOTE_LLM_URL or "(미설정)",
        "REMOTE_LLM_MODEL": REMOTE_LLM_MODEL,
        "SURYA_DEVICE":  SURYA_DEVICE,
        "SECRET_KEY":    "***" if SECRET_KEY != "woosong-ai-tutor-secret-change-me" else "(기본값 — 운영 시 변경 필수)",
    }
