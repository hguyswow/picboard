@echo off
chcp 65001 > nul
cd /d "%~dp0dist\PicBoard_Desktop_v2.0"
echo ========================================================
echo   [사진대지 데스크톱 v2.0.0] 단독 실행 파일 구동 중...
echo ========================================================
start "" "PicBoard_Desktop_v2.0.exe"
