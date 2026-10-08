@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================
echo   사진대지 데스크톱 프로그램 (PictureBoard Studio) 기동 중...
echo ========================================================
start "" pythonw main.py
if %ERRORLEVEL% NEQ 0 (
    echo [경고] pythonw 실행 실패, 콘솔 모드로 재시도합니다.
    python main.py
    pause
)
