@echo off
cd /d "%~dp0"
if exist "%LOCALAPPDATA%\Programs\PicBoard\PicBoard_WebStudio_v2.2.exe" (
    start "" "%LOCALAPPDATA%\Programs\PicBoard\PicBoard_WebStudio_v2.2.exe"
    exit /b 0
)
if exist "dist\PicBoard_WebStudio_v2.2\PicBoard_WebStudio_v2.2.exe" (
    start "" "dist\PicBoard_WebStudio_v2.2\PicBoard_WebStudio_v2.2.exe"
    exit /b 0
)
if exist "%LOCALAPPDATA%\Programs\PicBoard\PicBoard_WebStudio_v2.1.exe" (
    start "" "%LOCALAPPDATA%\Programs\PicBoard\PicBoard_WebStudio_v2.1.exe"
    exit /b 0
)
if exist "dist\PicBoard_WebStudio_v2.1\PicBoard_WebStudio_v2.1.exe" (
    start "" "dist\PicBoard_WebStudio_v2.1\PicBoard_WebStudio_v2.1.exe"
    exit /b 0
)
if exist "PicBoard_WebStudio_v2.0.exe" (
    start "" "PicBoard_WebStudio_v2.0.exe"
    exit /b 0
)
python web_launcher.py
exit /b 0