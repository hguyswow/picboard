@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================
echo   [사진대지 웹 스튜디오] 개발 서버를 시작합니다.
echo   접속 주소: http://localhost:8000
echo ========================================================
timeout /t 2 > nul
start http://localhost:8000
python server.py
pause
