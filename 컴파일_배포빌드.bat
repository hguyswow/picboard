@echo off
chcp 65001 > nul
cd /d "%~dp0"
echo ========================================================
echo   [사진대지 v2.0.0] 컴파일 및 배포 빌드 파이프라인
echo ========================================================

echo.
echo [1/3] 소스코드 자동 백업 중...
python -c "import os, zipfile, datetime; b=r'e:\dev\picboard\_backups'; os.makedirs(b, exist_ok=True); ts=datetime.datetime.now().strftime('%Y%m%d_%H%M%S'); zp=os.path.join(b, f'picboard_backup_{ts}.zip'); zf=zipfile.ZipFile(zp,'w',zipfile.ZIP_DEFLATED); [zf.write(os.path.join(r,f), os.path.relpath(os.path.join(r,f),r'e:\dev\picboard')) for r,ds,fs in os.walk(r'e:\dev\picboard') if not any(x in r for x in ['_backups','build','dist','__pycache__','.git']) for f in fs if not f.endswith(('.pyc','.exe'))]; zf.close(); print(f'>> 백업 완료: {zp}')"

echo.
echo [2/3] 웹 스튜디오 (WebStudio) 컴파일 중...
python -m PyInstaller --noconfirm --clean --onedir --name "PicBoard_WebStudio_v2.0" --add-data "web;web" --add-data "pictureboard.pdf;." web_launcher.py

echo.
echo [3/3] 데스크톱 GUI (Desktop) 컴파일 중...
python -m PyInstaller --noconfirm --clean --onedir --windowed --name "PicBoard_Desktop_v2.0" --collect-all customtkinter --add-data "pictureboard.pdf;." main.py

echo.
echo ========================================================
echo   모든 컴파일 빌드가 완료되었습니다! (dist/ 폴더 확인)
echo ========================================================
pause
