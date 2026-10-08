# -*- coding: utf-8 -*-
import os
import sys
import time
import socket
import subprocess
import urllib.request
import webbrowser
import threading
import uvicorn

import io

# GUI / No-Console 모드 스트림 보호 가드 (Windowed 모드 크래시 원천 차단)
class NullStream:
    def write(self, *args, **kwargs): pass
    def flush(self, *args, **kwargs): pass
    def isatty(self): return False

if sys.stdout is None:
    sys.stdout = NullStream()
if sys.stderr is None:
    sys.stderr = NullStream()
if sys.stdin is None:
    sys.stdin = io.StringIO()

try:
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding="utf-8")
    if hasattr(sys.stderr, 'reconfigure'):
        sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

CREATE_NO_WINDOW = 0x08000000

# from core.version import get_base_dir, get_resource_path
from core.version import get_base_dir, get_resource_path, VERSION_STRING, APP_TITLE
sys.path.insert(0, get_base_dir())

from server import app

def is_port_in_use(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.5)
        return s.connect_ex(('127.0.0.1', port)) == 0

def check_service_health(port: int) -> bool:
    """API 버전 및 정적 리소스(/static/style.css) 200 정상 응답 여부 철저 검증"""
    try:
        # 1. API 응답 확인
        api_url = f"http://127.0.0.1:{port}/api/version"
        req_api = urllib.request.Request(api_url, headers={'User-Agent': 'PicBoardChecker'})
        with urllib.request.urlopen(req_api, timeout=1.0) as resp:
            if resp.status != 200:
                return False

        # 2. 정적 CSS 서빙 상태 확인 (화면 깨짐 방어 핵심!)
        css_url = f"http://127.0.0.1:{port}/static/style.css"
        req_css = urllib.request.Request(css_url, headers={'User-Agent': 'PicBoardChecker'})
        with urllib.request.urlopen(req_css, timeout=1.0) as resp:
            return resp.status == 200
    except Exception:
        return False

def get_pids_using_port(port: int) -> list:
    """포트를 점유 중인 프로세스 PID 목록 조회"""
    pids = set()
    try:
        cmd = f'netstat -ano -p tcp | findstr /R /C:":{port} .*LISTENING"'
        # output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL).decode('cp949', errors='ignore')
        output = subprocess.check_output(cmd, shell=True, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW).decode('cp949', errors='ignore')
        for line in output.strip().splitlines():
            parts = line.split()
            if len(parts) >= 5 and parts[-1].isdigit():
                pids.add(int(parts[-1]))
    except Exception:
        pass
    return list(pids)

def kill_processes_on_port(port: int):
    """지정 포트를 점유 중인 비정상/구버전 프로세스 강제 종료"""
    pids = get_pids_using_port(port)
    current_pid = os.getpid()
    for pid in pids:
        if pid != current_pid and pid > 0:
            try:
                # subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                subprocess.run(f"taskkill /F /T /PID {pid}", shell=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=CREATE_NO_WINDOW)
                time.sleep(0.3)
            except Exception:
                pass

def find_available_port(start_port: int = 8000, max_tries: int = 20) -> int:
    for p in range(start_port, start_port + max_tries):
        if not is_port_in_use(p):
            return p
    return start_port

def open_browser_when_ready(target_url: str):
    time.sleep(1.2)
    webbrowser.open(target_url)

def main():
    target_port = 8000
    if is_port_in_use(target_port):
        if check_service_health(target_port):
            # 완전히 건강한 최신 인스턴스가 이미 정상 동작 중
            print("========================================================")
            print("  이미 사진대지 웹 스튜디오가 정상 실행 중입니다.")
            print(f"  브라우저를 엽니다: http://localhost:{target_port}")
            print("========================================================")
            webbrowser.open(f"http://localhost:{target_port}")
            time.sleep(1.5)
            return
        else:
            # 8000번 포트가 사용 중이지만 비정상(500 에러 or 구버전 좀비 프로세스)
            print("========================================================")
            print("  [주의] 8000번 포트에 비정상 구버전/좀비 프로세스 감지!")
            print("  자율 치유(Self-Healing): 기존 프로세스 자동 종료 및 새로 시작...")
            print("========================================================")
            kill_processes_on_port(target_port)
            time.sleep(0.8)

    # 8000번 포트가 비워지지 않은 경우를 대비한 가변 포트 배정 방어
    port = target_port if not is_port_in_use(target_port) else find_available_port(target_port)
    target_url = f"http://localhost:{port}"

    print("========================================================")
    # print(f"  [사진대지 웹 스튜디오 v2.0.0] 서버 시작 중...")
    print(f"  [{APP_TITLE}] 서버 시작 중...")
    print(f"  접속 주소: {target_url}")
    print("========================================================")

    threading.Thread(target=open_browser_when_ready, args=(target_url,), daemon=True).start()
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="info")

if __name__ == "__main__":
    main()
