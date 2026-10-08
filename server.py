# -*- coding: utf-8 -*-
import os
import sys
import json
import shutil
import uuid
import zipfile
from typing import List, Optional
from datetime import datetime

import uvicorn
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import FileResponse, HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)))

from core.version import VERSION, VERSION_STRING, APP_NAME, APP_TITLE, get_resource_path, sanitize_filename
from core.models import PictureItem, StampConfig, CropMode, StampPosition
from core.image_processor import extract_metadata, format_date, process_picture
from core.preset_manager import PresetManager
from core.pdf_exporter import PDFExporter
from core.excel_exporter import ExcelExporter

app = FastAPI(title=APP_TITLE, version=VERSION)

UPLOAD_DIR = os.path.abspath("uploads")
EXPORT_DIR = os.path.abspath("exports")
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(EXPORT_DIR, exist_ok=True)

def cleanup_old_temp_files(max_age_hours: int = 24):
    """24시간 이상 지난 임시 업로드/내보내기 파일 자동 정리 (디스크 고갈 원천 차단)"""
    try:
        now = datetime.now().timestamp()
        for d in (UPLOAD_DIR, EXPORT_DIR):
            if os.path.exists(d):
                for fname in os.listdir(d):
                    fpath = os.path.join(d, fname)
                    if os.path.isfile(fpath):
                        if now - os.path.getmtime(fpath) > (max_age_hours * 3600):
                            try:
                                os.remove(fpath)
                            except Exception:
                                pass
    except Exception:
        pass

# 서버 기동 시 1회 백그라운드 청소 실행
import threading
threading.Thread(target=cleanup_old_temp_files, daemon=True).start()

preset_mgr = PresetManager()

web_dir = get_resource_path("web")

@app.get("/static/{file_path:path}")
async def serve_static_direct(file_path: str):
    """정적 리소스(CSS, JS 등) 500 방어 전용 고속 FileResponse 서빙"""
    target = os.path.normpath(os.path.join(web_dir, file_path))
    abs_web = os.path.abspath(web_dir)
    if not os.path.abspath(target).startswith(abs_web):
        raise HTTPException(status_code=403, detail="Forbidden")
    if os.path.exists(target) and os.path.isfile(target):
        media_type = None
        if target.endswith(".css"): media_type = "text/css; charset=utf-8"
        elif target.endswith(".js"): media_type = "application/javascript; charset=utf-8"
        elif target.endswith(".png"): media_type = "image/png"
        elif target.endswith(".jpg") or target.endswith(".jpeg"): media_type = "image/jpeg"
        elif target.endswith(".svg"): media_type = "image/svg+xml"
        return FileResponse(target, media_type=media_type)
    raise HTTPException(status_code=404, detail="Static file not found")

app.mount("/static", StaticFiles(directory=web_dir), name="static")
app.mount("/uploads", StaticFiles(directory=UPLOAD_DIR), name="uploads")

@app.get("/api/version")
async def get_version():
    return {
        "version": VERSION,
        "version_string": VERSION_STRING,
        "app_name": APP_NAME,
        "app_title": APP_TITLE
    }

@app.post("/api/shutdown")
async def shutdown_server():
    """웹 브라우저에서 안전하게 백엔드 프로그램을 종료"""
    import threading
    import time
    def kill_self():
        time.sleep(0.5)
        os._exit(0)
    threading.Thread(target=kill_self, daemon=True).start()
    return {"status": "ok", "message": "프로그램이 안전하게 종료됩니다."}

# ================= 사용자 환경설정 (UI 모드 등) 디스크 영구 저장 =================
def get_settings_file_path() -> str:
    """실행 환경(PyInstaller/개발)에 구애받지 않는 안전한 user_settings.json 절대 경로"""
    if getattr(sys, 'frozen', False):
        exe_dir = os.path.dirname(sys.executable)
        return os.path.join(exe_dir, "user_settings.json")
    return os.path.abspath(os.path.join(os.path.dirname(__file__), "user_settings.json"))

SETTINGS_FILE = get_settings_file_path()

def load_user_settings() -> dict:
    if os.path.exists(SETTINGS_FILE):
        try:
            with open(SETTINGS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            pass
    return {"ui_mode": "easy", "custom_ui": {}}

def save_user_settings(data: dict):
    try:
        with open(SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        print(f"[Settings Save Error] {e}")

@app.get("/api/ui_settings")
async def get_ui_settings():
    """사용자가 마지막으로 선택한 UI 모드 및 커스텀 설정 디스크 조회"""
    return load_user_settings()

class UiSettingsReq(BaseModel):
    ui_mode: Optional[str] = "easy"
    custom_ui: Optional[dict] = None

@app.post("/api/ui_settings")
async def set_ui_settings(req: UiSettingsReq):
    """사용자가 선택한 UI 모드 및 설정을 디스크에 실시간 영구 저장"""
    settings = load_user_settings()
    if req.ui_mode:
        settings["ui_mode"] = req.ui_mode
    if req.custom_ui is not None:
        settings["custom_ui"] = req.custom_ui
    save_user_settings(settings)
    return {"status": "ok", "ui_mode": settings["ui_mode"]}

@app.get("/", response_class=HTMLResponse)
async def index():
    html_path = os.path.join(web_dir, "index.html")
    if os.path.exists(html_path):
        with open(html_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>PictureBoard Studio</h1>"

@app.get("/api/presets")
async def get_presets():
    return {
        "work_types": preset_mgr.get_work_types(),
        "locations": preset_mgr.get_locations(),
        "contents": preset_mgr.get_contents(),
        "combos": preset_mgr.get_combos()
    }

class AddPresetReq(BaseModel):
    category: str
    value: str

@app.post("/api/presets/add")
async def add_preset(req: AddPresetReq):
    if req.category == "work_types":
        preset_mgr.add_work_type(req.value)
    elif req.category == "locations":
        preset_mgr.add_location(req.value)
    elif req.category == "contents":
        preset_mgr.add_content(req.value)
    return {"status": "ok"}

class AddComboReq(BaseModel):
    title: str
    work_type: str
    location: str
    content: str

@app.post("/api/presets/combo")
async def add_combo(req: AddComboReq):
    preset_mgr.add_combo(req.title, req.work_type, req.location, req.content)
    return {"status": "ok"}

@app.delete("/api/presets/combo/{index}")
async def delete_combo(index: int):
    preset_mgr.delete_combo(index)
    return {"status": "ok"}

@app.post("/api/upload")
async def upload_images(files: List[UploadFile] = File(...), folder_name: Optional[str] = Form("")):
    results = []
    now_str = datetime.now().strftime("%Y.%m.%d")

    for file in files:
        raw_filename = file.filename or "image.jpg"
        # 1. 윈도우/유닉스 경로 구분자 슬래시(/)로 통일
        normalized_path = raw_filename.replace("\\", "/")
        # 2. 경로로부터 순수 파일명 분리 (하위 디렉토리 완벽 탈락)
        pure_filename = os.path.basename(normalized_path)
        if not pure_filename:
            pure_filename = "image.jpg"

        ext = os.path.splitext(pure_filename)[1].lower()
        if ext not in [".jpg", ".jpeg", ".png", ".bmp", ".heic", ".webp"]:
            continue

        # 3. 폴더명 결정: 폼 파라미터 우선, 없으면 상대경로의 최상위 폴더명 자동 추출
        item_folder = (folder_name or "").strip()
        if not item_folder:
            parts = [p for p in normalized_path.split("/") if p]
            if len(parts) > 1:
                item_folder = parts[0]
            else:
                item_folder = "기본폴더"

        # 4. 파일명 금지 문자 정제 및 UPLOAD_DIR 직속 평탄화 저장
        safe_name = sanitize_filename(pure_filename)
        unique_name = f"{uuid.uuid4().hex[:8]}_{safe_name}"
        save_path = os.path.join(UPLOAD_DIR, unique_name)

        try:
            os.makedirs(os.path.dirname(save_path), exist_ok=True)
            with open(save_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
        except Exception as e:
            print(f"[Upload Error] 파일 저장 실패: {save_path}, error={e}")
            continue

        try:
            exif_dt, mtime_dt, ctime_dt = extract_metadata(save_path)
            dt_use = exif_dt or mtime_dt or ctime_dt
            d_str = format_date(dt_use, "YYYY.MM.DD") if dt_use else now_str
        except Exception:
            exif_dt, mtime_dt, ctime_dt = None, None, None
            d_str = now_str

        results.append({
            "id": uuid.uuid4().hex,
            "filename": pure_filename,
            "server_path": save_path,
            "url": f"/uploads/{unique_name}",
            "folder_name": item_folder,
            "work_type": "공통공사",
            "location": "현장사무실",
            "content": "",
            "stamp_content": "",
            "date_str": d_str,
            "date_source": "exif" if exif_dt else ("mtime" if mtime_dt else "now"),
            "exif_date_iso": exif_dt.strftime("%Y-%m-%d %H:%M:%S") if exif_dt else "",
            "mtime_date_iso": mtime_dt.strftime("%Y-%m-%d %H:%M:%S") if mtime_dt else "",
            "ctime_date_iso": ctime_dt.strftime("%Y-%m-%d %H:%M:%S") if ctime_dt else "",
            "rotation": 0,
            "padding": 0,
            "crop_mode": "cover",
            "stamp_enabled": True
        })

    return results

class ExportItem(BaseModel):
    server_path: str
    folder_name: str = ""
    file_name: str = ""
    work_type: str = ""
    location: str = ""
    content: str = ""
    stamp_content: str = ""
    date_str: str = ""
    custom1: str = ""
    custom2: str = ""
    crop_mode: str = "cover"
    rotation: int = 0
    padding: int = 0
    stamp_enabled: bool = True

class ExportRequest(BaseModel):
    project_name: str
    items: List[ExportItem]
    stamp_config: dict
    table_config: Optional[dict] = None

def _build_picture_items(req: ExportRequest) -> List[PictureItem]:
    st_cfg = req.stamp_config
    pos_val = st_cfg.get("position", "bottom_right")
    pos_enum = StampPosition(pos_val) if pos_val in [p.value for p in StampPosition] else StampPosition.BOTTOM_RIGHT

    stamp_cfg = StampConfig(
        enabled=st_cfg.get("enabled", True),
        position=pos_enum,
        show_project=st_cfg.get("show_project", False),
        show_work_type=st_cfg.get("show_work_type", True),
        show_location=st_cfg.get("show_location", True),
        show_content=st_cfg.get("show_content", True),
        show_date=st_cfg.get("show_date", True),
        custom_text=st_cfg.get("custom_text", ""),
        font_size=st_cfg.get("font_size", 18),
        text_color=st_cfg.get("text_color", "#FFFFFF"),
        bg_color=st_cfg.get("bg_color", "#000000"),
        bg_alpha=float(st_cfg.get("bg_alpha", 0.65)),
        border=st_cfg.get("border", True),
        hide_labels=bool(st_cfg.get("hide_labels", False))
    )

    pic_items = []
    for it in req.items:
        c_mode = CropMode.COVER
        if it.crop_mode == "fit": c_mode = CropMode.FIT
        elif it.crop_mode == "stretch": c_mode = CropMode.STRETCH

        p_it = PictureItem(
            image_path=it.server_path,
            folder_name=it.folder_name,
            file_name=it.file_name,
            project_name=req.project_name,
            work_type=it.work_type,
            location=it.location,
            content=it.content,
            stamp_content=it.stamp_content,
            date_str=it.date_str,
            custom1=it.custom1,
            custom2=it.custom2,
            crop_mode=c_mode,
            rotation=it.rotation,
            padding=it.padding,
            stamp_enabled=it.stamp_enabled,
            stamp_config=stamp_cfg
        )
        pic_items.append(p_it)
    return pic_items

@app.post("/api/export/pdf")
async def export_pdf(req: ExportRequest):
    if not req.items:
        raise HTTPException(status_code=400, detail="내보낼 사진이 없습니다.")

    items = _build_picture_items(req)
    safe_proj = sanitize_filename(req.project_name, default="사진대지")
    filename = f"사진대지_{safe_proj}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf"
    output_path = os.path.join(EXPORT_DIR, filename)

    exporter = PDFExporter()
    success = exporter.export(items, output_path, project_name=req.project_name, table_config=req.table_config)
    if not success:
        raise HTTPException(status_code=500, detail="PDF 생성 실패")

    return FileResponse(output_path, filename=filename, media_type="application/pdf")

@app.post("/api/export/excel")
async def export_excel(req: ExportRequest):
    if not req.items:
        raise HTTPException(status_code=400, detail="내보낼 사진이 없습니다.")

    items = _build_picture_items(req)
    safe_proj = sanitize_filename(req.project_name, default="사진대지")
    filename = f"사진대지_{safe_proj}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    output_path = os.path.join(EXPORT_DIR, filename)

    exporter = ExcelExporter()
    success = exporter.export(items, output_path, project_name=req.project_name, table_config=req.table_config)
    if not success:
        raise HTTPException(status_code=500, detail="Excel 생성 실패")

    return FileResponse(output_path, filename=filename, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

@app.get("/api/table_settings")
async def get_table_settings():
    """사용자가 저장한 사진대지 표 커스텀 설정 조회"""
    settings = load_user_settings()
    return settings.get("table_config", None)

@app.post("/api/table_settings")
async def set_table_settings(req: dict):
    """사용자가 설정한 사진대지 표 커스텀 설정을 디스크에 영구 저장"""
    settings = load_user_settings()
    settings["table_config"] = req
    save_user_settings(settings)
    return {"status": "ok"}

@app.post("/api/export/images-zip")
async def export_images_zip(req: ExportRequest):
    """스탬프와 크롭/회전이 반영된 실제 이미지 파일들을 ZIP 압축 파일로 다운로드"""
    if not req.items:
        raise HTTPException(status_code=400, detail="내보낼 사진이 없습니다.")

    items = _build_picture_items(req)
    safe_proj = sanitize_filename(req.project_name, default="스탬프사진")
    zip_filename = f"스탬프사진_{safe_proj}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.zip"
    zip_path = os.path.join(EXPORT_DIR, zip_filename)

    temp_img_dir = os.path.join(EXPORT_DIR, f"_temp_zip_{uuid.uuid4().hex[:8]}")
    os.makedirs(temp_img_dir, exist_ok=True)

    try:
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zf:
            for idx, item in enumerate(items):
                # 고해상도 (1600x1000) 스탬프 사진 렌더링
                processed = process_picture(item, 1600, 1000)
                disp_cnt = sanitize_filename(item.stamp_content or item.content or '사진', default='사진')
                disp_work = sanitize_filename(item.work_type or '공종', default='공종')
                disp_date = sanitize_filename(item.date_str or '', default='')
                safe_name = f"{idx+1:03d}_{disp_work}_{disp_cnt}_{disp_date}.jpg"
                temp_file = os.path.join(temp_img_dir, safe_name)
                processed.save(temp_file, "JPEG", quality=95)
                zf.write(temp_file, arcname=safe_name)

        return FileResponse(zip_path, filename=zip_filename, media_type="application/zip")
    finally:
        shutil.rmtree(temp_img_dir, ignore_errors=True)

if __name__ == "__main__":
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=False)
