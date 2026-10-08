# -*- coding: utf-8 -*-
import os
import sys

# VERSION = "2.0.0"
# VERSION = "2.1.0"
# VERSION = "2.2.0"
# VERSION = "2.3.0"
# VERSION = "2.3.1"
VERSION = "2.4.0"
VERSION_STRING = f"v{VERSION}"
APP_NAME = "Minos 사진대지 Studio"
APP_TITLE = f"{APP_NAME} {VERSION_STRING}"
AUTHOR = "부장님을 위한 맞춤형 제작"
CONTACT_EMAIL = "hguyswow@gmail.com"

def get_base_dir():
    """PyInstaller 번들 실행 환경 또는 일반 파이썬 실행 환경의 기준 디렉토리 반환"""
    if getattr(sys, 'frozen', False):
        if hasattr(sys, '_MEIPASS'):
            return sys._MEIPASS
        exe_dir = os.path.dirname(sys.executable)
        internal_dir = os.path.join(exe_dir, "_internal")
        if os.path.exists(internal_dir):
            return internal_dir
        return exe_dir
    return os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))

def get_resource_path(relative_path):
    """실행 환경에 구애받지 않는 절대 리소스 경로 획득 헬퍼 (다중 fallback 방어)"""
    # 1. base_dir 기준 우선 확인
    p1 = os.path.normpath(os.path.join(get_base_dir(), relative_path))
    if os.path.exists(p1):
        return p1

    # 2. 현재 작업 디렉토리(CWD) 기준 확인
    p2 = os.path.normpath(os.path.join(os.getcwd(), relative_path))
    if os.path.exists(p2):
        return p2

    # 3. 실행 파일 디렉토리(exe_dir) 기준 확인
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        p3 = os.path.normpath(os.path.join(exe_dir, relative_path))
        if os.path.exists(p3):
            return p3
        p4 = os.path.normpath(os.path.join(exe_dir, "_internal", relative_path))
        if os.path.exists(p4):
            return p4

    return p1

def sanitize_filename(name: str, default: str = "사진대지") -> str:
    r"""Windows 파일명 금지 문자(\ / : * ? " < > |)를 안전하게 치환"""
    import re
    if not name or not str(name).strip():
        return default
    # 윈도우 파일명 금지 문자 치환
    cleaned = re.sub(r'[\/:*?"<>|\r\n\t]', '_', str(name)).strip()
    cleaned = re.sub(r'_+', '_', cleaned).strip('_')
    return cleaned or default

