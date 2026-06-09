@echo off
chcp 65001 > nul
call venv\Scripts\activate.bat
echo AI Tutor 시작 중... http://localhost:7860
python app.py
pause
