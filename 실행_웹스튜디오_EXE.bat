@echo off
cd /d "%~dp0"
if exist "PicBoard_WebStudio_v2.0.exe" (
    start "" "PicBoard_WebStudio_v2.0.exe"
    exit /b 0
)
if exist "dist\PicBoard_WebStudio_v2.0.exe" (
    start "" "dist\PicBoard_WebStudio_v2.0.exe"
    exit /b 0
)
if exist "dist\PicBoard_WebStudio_v2.0\PicBoard_WebStudio_v2.0.exe" (
    start "" "dist\PicBoard_WebStudio_v2.0\PicBoard_WebStudio_v2.0.exe"
    exit /b 0
)