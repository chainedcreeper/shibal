@echo off
chcp 65001 > nul
echo ========================================
echo  AI Tutor 환경 세팅
echo ========================================

:: Python 확인
python --version > nul 2>&1
if errorlevel 1 (
    echo [오류] Python이 설치되어 있지 않습니다.
    echo https://www.python.org/downloads/ 에서 설치 후 다시 실행하세요.
    pause
    exit /b 1
)

:: Ollama 확인
ollama --version > nul 2>&1
if errorlevel 1 (
    echo [경고] Ollama가 설치되어 있지 않습니다.
    echo https://ollama.com 에서 설치 후 ollama pull qwen3:8b 실행하세요.
)

:: 가상환경 생성
if not exist "venv" (
    echo [1/3] 가상환경 생성 중...
    python -m venv venv
)

:: 가상환경 활성화 및 패키지 설치
echo [2/3] 패키지 설치 중... (시간이 걸릴 수 있습니다)
call venv\Scripts\activate.bat

pip install --upgrade pip -q
pip install ^
    fastapi uvicorn ^
    pymupdf pillow ^
    sentence-transformers faiss-cpu numpy ^
    requests python-jose[cryptography] passlib[bcrypt] python-multipart ^
    scikit-learn ^
    gtts moviepy ^
    python-pptx ^
    surya-ocr ^
    langchain langchain-text-splitters ^
    -q

:: local.env 없으면 기본값 생성
if not exist "local.env" (
    echo [3/3] local.env 기본값 생성 중...
    (
        echo OLLAMA_HOST=http://localhost:11434
        echo OLLAMA_MODEL=qwen3:8b
        echo SECRET_KEY=change-this-secret-key
    ) > local.env
    echo local.env 생성 완료. 필요 시 수정하세요.
)

echo.
echo ========================================
echo  세팅 완료!
echo  실행: run.bat
echo ========================================
pause
