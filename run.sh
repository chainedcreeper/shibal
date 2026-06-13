#!/bin/bash
# pj 원클릭 실행 — Ollama serve + qwen3:8b 확인 + pj FastAPI 서버.
# 사용:  bash run.sh   또는   ./run.sh
set -e

PJ_DIR="$(cd "$(dirname "$0")" && pwd)"
HOME_DIR="$HOME"
OLLAMA_BIN="${OLLAMA_BIN:-$HOME_DIR/ollama/bin/ollama}"
PORT="${PJ_PORT:-7860}"
MODEL="${OLLAMA_MODEL:-qwen3:8b}"

echo "==========================================="
echo "  pj 서버 시작"
echo "  PJ_DIR  : $PJ_DIR"
echo "  OLLAMA  : $OLLAMA_BIN"
echo "  PORT    : $PORT"
echo "  MODEL   : $MODEL"
echo "==========================================="

# [1/4] Ollama serve
echo "[1/4] Ollama serve 확인"
if pgrep -f "ollama serve" > /dev/null 2>&1; then
    echo "    이미 실행 중"
else
    if [ ! -x "$OLLAMA_BIN" ]; then
        echo "ERROR: Ollama 바이너리 없음: $OLLAMA_BIN"
        echo "  설치: https://github.com/ollama/ollama/releases 에서 받아"
        echo "        $HOME_DIR/ollama/ 에 풀기"
        exit 1
    fi
    nohup "$OLLAMA_BIN" serve > "$HOME_DIR/ollama.log" 2>&1 &
    sleep 5
    if pgrep -f "ollama serve" > /dev/null 2>&1; then
        echo "    시작됨 (로그: $HOME_DIR/ollama.log)"
    else
        echo "ERROR: Ollama 시작 실패. tail -30 $HOME_DIR/ollama.log"
        exit 1
    fi
fi

# [2/4] 모델 확인
echo "[2/4] $MODEL 모델 확인"
if "$OLLAMA_BIN" list 2>/dev/null | grep -q "$MODEL"; then
    echo "    이미 받음"
else
    echo "    pull 시작 (5GB 정도, 4~5분)..."
    "$OLLAMA_BIN" pull "$MODEL"
fi

# [3/4] pj 서버
echo "[3/4] pj 서버 시작"
if pgrep -f "python.*app.py" > /dev/null 2>&1; then
    echo "    기존 서버 중지"
    pkill -f "python.*app.py" || true
    sleep 2
fi
cd "$PJ_DIR"
nohup python app.py > "$HOME_DIR/pj.log" 2>&1 &
PJ_PID=$!
echo "    PID=$PJ_PID  (로그: $HOME_DIR/pj.log)"

# [4/4] 부팅 대기 (BGE-m3 + reranker 로드 시간 포함)
echo "[4/4] 부팅 대기 (최대 120초)"
for i in $(seq 1 40); do
    sleep 3
    CODE=$(curl -s -o /dev/null -w "%{http_code}" "http://localhost:$PORT/docs" --max-time 2 || echo "000")
    if [ "$CODE" = "200" ]; then
        echo ""
        echo "==========================================="
        echo "OK  pj 서버 떴음: http://localhost:$PORT"
        echo "    로그 보기:  tail -f $HOME_DIR/pj.log"
        echo "    중지:       pkill -f 'python.*app.py'"
        echo "==========================================="
        exit 0
    fi
    printf "."
done

echo ""
echo "ERROR: 120초 안에 부팅 실패. 로그 확인:"
echo "  tail -80 $HOME_DIR/pj.log"
exit 1
