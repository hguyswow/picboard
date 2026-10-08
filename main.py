# -*- coding: utf-8 -*-
import os
import sys
import ctypes

# 1. 인코딩 및 스트림 방어 (Rule 3)
try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

# 2. Windows High DPI 선명화 설정
try:
    ctypes.windll.shcore.SetProcessDpiAwareness(1)
except Exception:
    pass

# 3. 프로젝트 루트 경로 보장
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from ui.main_window import MainWindow

def main():
    try:
        app = MainWindow()
        app.mainloop()
    except Exception as e:
        import traceback
        err_msg = traceback.format_exc()
        print(f"치명적 오류 발생:\n{err_msg}")
        try:
            from tkinter import messagebox
            messagebox.showerror("프로그램 오류", f"프로그램 실행 중 오류가 발생했습니다:\n{e}\n\n상세:\n{err_msg}")
        except Exception:
            pass

if __name__ == "__main__":
    main()
