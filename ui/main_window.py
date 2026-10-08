# -*- coding: utf-8 -*-
import os
import tempfile
from datetime import datetime
from typing import List, Optional

import customtkinter as ctk
from tkinter import filedialog, messagebox
from PIL import Image, ImageGrab

from core.models import PictureItem, StampConfig, CropMode, StampPosition
from core.image_processor import extract_metadata, format_date
from core.preset_manager import PresetManager
from core.pdf_exporter import PDFExporter
from core.excel_exporter import ExcelExporter
from ui.dialogs import StampSettingsDialog, PresetManagerDialog
from ui.left_panel import LeftPanel
from ui.preview_canvas import A4PreviewCanvas

from core.version import VERSION_STRING, APP_TITLE, CONTACT_EMAIL

ctk.set_appearance_mode("Light")
ctk.set_default_color_theme("blue")

class MainWindow(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_TITLE} (문의: {CONTACT_EMAIL})")
        self.geometry("1420x880")
        self.minsize(1220, 760)

        # 데이터 모델
        self.items: List[PictureItem] = []
        self.current_index: int = -1
        self.current_page: int = 0
        self.default_stamp_config = StampConfig()
        self.preset_mgr = PresetManager()
        self.temp_clipboard_files = []

        self._build_top_bar()
        self._build_body()
        self._bind_shortcuts()
        self._refresh_presets_dropdown()
        self._sync_view()

    def _bind_shortcuts(self):
        self.bind("<Control-v>", lambda e: self.on_clipboard_paste())
        self.bind("<Control-V>", lambda e: self.on_clipboard_paste())

    def _build_top_bar(self):
        top_bar = ctk.CTkFrame(self, height=55, corner_radius=0)
        top_bar.pack(fill="x", side="top")

        ctk.CTkLabel(top_bar, text="공사명 :", font=("맑은 고딕", 13, "bold")).pack(side="left", padx=(15, 5))
        self.ent_project = ctk.CTkEntry(top_bar, width=320, placeholder_text="공사명을 입력하세요")
        self.ent_project.insert(0, "검암역세권 공공주택지구 도시시설물 건설공사")
        self.ent_project.pack(side="left", padx=5)
        self.ent_project.bind("<KeyRelease>", lambda e: self._sync_view())

        btn_add_files = ctk.CTkButton(top_bar, text="➕ 파일 추가", width=95, command=self.on_add_files)
        btn_add_files.pack(side="left", padx=4)

        btn_add_folder = ctk.CTkButton(top_bar, text="📁 폴더 추가", width=95, command=self.on_add_folder)
        btn_add_folder.pack(side="left", padx=4)

        btn_paste = ctk.CTkButton(
            top_bar, text="📋 붙여넣기 (Ctrl+V)", width=135,
            fg_color="#17a2b8", hover_color="#138496", command=self.on_clipboard_paste
        )
        btn_paste.pack(side="left", padx=4)

        btn_pdf = ctk.CTkButton(
            top_bar, text="📄 PDF 저장 (A4 인쇄)", width=150,
            fg_color="#dc3545", hover_color="#bb2d3b", command=self.on_export_pdf
        )
        btn_pdf.pack(side="right", padx=(4, 15))

        btn_excel = ctk.CTkButton(
            top_bar, text="📊 엑셀 내보내기 (.xlsx)", width=155,
            fg_color="#198754", hover_color="#157347", command=self.on_export_excel
        )
        btn_excel.pack(side="right", padx=4)

        btn_presets = ctk.CTkButton(
            top_bar, text="⚙️ 프리셋 관리", width=100,
            fg_color="#6c757d", hover_color="#5a6268", command=self.open_preset_dialog
        )
        btn_presets.pack(side="right", padx=4)

    def _build_body(self):
        body = ctk.CTkFrame(self, fg_color="transparent")
        body.pack(fill="both", expand=True, padx=10, pady=10)

        self.left_panel = LeftPanel(
            body, width=540,
            on_select_callback=self.on_item_selected,
            on_refresh_callback=self._sync_view
        )
        self.left_panel.pack(side="left", fill="both", padx=(0, 5))

        right_panel = ctk.CTkFrame(body)
        right_panel.pack(side="right", fill="both", expand=True, padx=(5, 0))

        form_card = ctk.CTkFrame(right_panel)
        form_card.pack(fill="x", padx=10, pady=(10, 5))
        self._build_editor_form(form_card)

        preview_card = ctk.CTkFrame(right_panel)
        preview_card.pack(fill="both", expand=True, padx=10, pady=(5, 10))
        self._build_preview_card(preview_card)

    def _build_editor_form(self, parent):
        # 1행: 프리셋, 크롭모드, 스탬프 제어
        row1 = ctk.CTkFrame(parent, fg_color="transparent")
        row1.pack(fill="x", padx=10, pady=(8, 4))

        ctk.CTkLabel(row1, text="✨ 프리셋:", font=("맑은 고딕", 11, "bold")).pack(side="left", padx=(0, 4))
        self.combo_preset_menu = ctk.CTkOptionMenu(row1, width=190, values=["프리셋 선택..."], command=self.on_preset_selected)
        self.combo_preset_menu.pack(side="left", padx=4)

        ctk.CTkLabel(row1, text="크롭 모드:", font=("맑은 고딕", 11, "bold")).pack(side="left", padx=(12, 4))
        self.crop_menu = ctk.CTkOptionMenu(
            row1, width=130,
            values=["비율유지 꽉채움(기본)", "비율유지 여백(전체)", "늘임"],
            command=self.on_crop_mode_changed
        )
        self.crop_menu.pack(side="left", padx=4)

        # 스탬프 버튼과 체크박스 사이 여백 확보
        btn_stamp_cfg = ctk.CTkButton(
            row1, text="스탬프 세부설정", width=110, height=26,
            fg_color="#495057", command=self.open_stamp_settings_dialog
        )
        btn_stamp_cfg.pack(side="right", padx=(8, 5))

        self.chk_stamp = ctk.CTkCheckBox(row1, text="스탬프 켜기", command=self.on_stamp_toggled)
        self.chk_stamp.select()
        self.chk_stamp.pack(side="right", padx=(5, 8))

        # 2행: 공종 & 위치
        row2 = ctk.CTkFrame(parent, fg_color="transparent")
        row2.pack(fill="x", padx=10, pady=3)

        ctk.CTkLabel(row2, text="공    종:", width=55, anchor="w").pack(side="left")
        self.ent_work = ctk.CTkEntry(row2, width=180)
        self.ent_work.pack(side="left", padx=(0, 15))
        self.ent_work.bind("<KeyRelease>", lambda e: self.on_field_edited())

        ctk.CTkLabel(row2, text="위    치:", width=55, anchor="w").pack(side="left")
        self.ent_loc = ctk.CTkEntry(row2, width=220)
        self.ent_loc.pack(side="left", padx=(0, 10))
        self.ent_loc.bind("<KeyRelease>", lambda e: self.on_field_edited())

        # 3행: 내용 & 촬영일자 및 날짜 추출 버튼들
        row3 = ctk.CTkFrame(parent, fg_color="transparent")
        row3.pack(fill="x", padx=10, pady=(3, 8))

        ctk.CTkLabel(row3, text="내    용:", width=55, anchor="w").pack(side="left")
        self.ent_content = ctk.CTkEntry(row3, width=180)
        self.ent_content.pack(side="left", padx=(0, 15))
        self.ent_content.bind("<KeyRelease>", lambda e: self.on_field_edited())

        ctk.CTkLabel(row3, text="촬영일자:", width=55, anchor="w").pack(side="left")
        self.ent_date = ctk.CTkEntry(row3, width=105)
        self.ent_date.pack(side="left", padx=(0, 5))
        self.ent_date.bind("<KeyRelease>", lambda e: self.on_field_edited())

        # 날짜 추출 버튼군 (EXIF 촬영일, 파일 수정일)
        btn_exif = ctk.CTkButton(row3, text="📷 EXIF 촬영일", width=95, height=26, fg_color="#0d6efd", command=self.on_re_extract_exif)
        btn_exif.pack(side="left", padx=2)

        btn_mtime = ctk.CTkButton(row3, text="📁 파일 수정일", width=95, height=26, fg_color="#6c757d", command=self.on_extract_mtime)
        btn_mtime.pack(side="left", padx=2)

    def _build_preview_card(self, parent):
        nav_bar = ctk.CTkFrame(parent, fg_color="transparent")
        nav_bar.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(nav_bar, text="📄 A4 2단 실시간 인쇄 미리보기 (pictureboard.pdf 규격)", font=("맑은 고딕", 12, "bold")).pack(side="left")

        btn_next = ctk.CTkButton(nav_bar, text="다음 ▶", width=60, height=26, command=self.on_next_page)
        btn_next.pack(side="right", padx=5)

        self.lbl_page_info = ctk.CTkLabel(nav_bar, text="페이지: 0 / 0", font=("맑은 고딕", 11))
        self.lbl_page_info.pack(side="right", padx=10)

        btn_prev = ctk.CTkButton(nav_bar, text="◀ 이전", width=60, height=26, command=self.on_prev_page)
        btn_prev.pack(side="right", padx=5)

        cv_frame = ctk.CTkFrame(parent, fg_color="#555555")
        cv_frame.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        self.preview_canvas = A4PreviewCanvas(cv_frame)
        self.preview_canvas.pack(fill="both", expand=True, padx=6, pady=6)

    def on_add_files(self):
        paths = filedialog.askopenfilenames(
            title="사진 파일 선택 (다중 선택 가능)",
            filetypes=[("이미지 파일", "*.jpg *.jpeg *.png *.bmp *.heic *.HEIC"), ("모든 파일", "*.*")]
        )
        if paths:
            self._add_paths(paths)

    def on_add_folder(self):
        folder = filedialog.askdirectory(title="사진이 들어있는 폴더 선택")
        if folder:
            valid_exts = {".jpg", ".jpeg", ".png", ".bmp", ".heic"}
            collected = []
            for root, _, files in os.walk(folder):
                for f in sorted(files):
                    ext = os.path.splitext(f)[1].lower()
                    if ext in valid_exts:
                        collected.append(os.path.join(root, f))
            if collected:
                self._add_paths(collected, default_folder=os.path.basename(folder))
            else:
                messagebox.showinfo("안내", "해당 폴더 내에 이미지 파일이 없습니다.")

    def on_clipboard_paste(self):
        try:
            img = ImageGrab.grabclipboard()
            if isinstance(img, Image.Image):
                temp_dir = tempfile.gettempdir()
                filename = f"clip_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{len(self.items)+1}.png"
                temp_path = os.path.join(temp_dir, filename)
                img.save(temp_path, "PNG")
                self.temp_clipboard_files.append(temp_path)
                self._add_paths([temp_path], default_folder="클립보드")
                messagebox.showinfo("완료", "클립보드 이미지가 추가되었습니다!")
            elif isinstance(img, list):
                self._add_paths(img)
            else:
                messagebox.showinfo("안내", "클립보드에 이미지 데이터가 없습니다.\n(캡처 도구 등으로 복사 후 시도하세요)")
        except Exception as e:
            messagebox.showerror("오류", f"붙여넣기 실패: {e}")

    def _add_paths(self, paths: List[str], default_folder: str = ""):
        now_str = datetime.now().strftime("%Y.%m")
        proj = self.ent_project.get().strip()

        for p in paths:
            if not os.path.exists(p): continue
            fname = os.path.basename(p)
            fol = default_folder or os.path.basename(os.path.dirname(p))
            exif_dt, mtime_dt, ctime_dt = extract_metadata(p)
            dt_use = exif_dt or mtime_dt or ctime_dt
            d_str = format_date(dt_use, "YYYY.MM") if dt_use else now_str

            item = PictureItem(
                image_path=p, folder_name=fol, file_name=fname,
                project_name=proj, work_type="공통공사", location="현장사무실",
                content="", date_str=d_str, exif_date=exif_dt, file_date=mtime_dt,
                crop_mode=CropMode.COVER, stamp_enabled=True,
                stamp_config=StampConfig(
                    enabled=True, position=self.default_stamp_config.position,
                    show_project=self.default_stamp_config.show_project,
                    show_work_type=self.default_stamp_config.show_work_type,
                    show_location=self.default_stamp_config.show_location,
                    show_content=self.default_stamp_config.show_content,
                    show_date=self.default_stamp_config.show_date,
                    font_size=self.default_stamp_config.font_size,
                    bg_alpha=self.default_stamp_config.bg_alpha,
                    border=self.default_stamp_config.border
                )
            )
            self.items.append(item)

        self.left_panel.set_items(self.items)
        if self.items and self.current_index == -1:
            self.on_item_selected(0)
            self.left_panel.select_row(0)
        self._sync_view()

    def on_item_selected(self, idx: int):
        if 0 <= idx < len(self.items):
            self.current_index = idx
            item = self.items[idx]

            self.ent_work.delete(0, "end")
            self.ent_work.insert(0, item.work_type)
            self.ent_loc.delete(0, "end")
            self.ent_loc.insert(0, item.location)
            self.ent_content.delete(0, "end")
            self.ent_content.insert(0, item.content)
            self.ent_date.delete(0, "end")
            self.ent_date.insert(0, item.date_str)

            crop_map = {
                CropMode.COVER: "비율유지 꽉채움(기본)",
                CropMode.FIT: "비율유지 여백(전체)",
                CropMode.STRETCH: "늘임"
            }
            self.crop_menu.set(crop_map.get(item.crop_mode, "비율유지 꽉채움(기본)"))

            if item.stamp_enabled: self.chk_stamp.select()
            else: self.chk_stamp.deselect()

            self.current_page = idx // 2
            self._sync_view()

    def on_field_edited(self):
        if 0 <= self.current_index < len(self.items):
            it = self.items[self.current_index]
            it.work_type = self.ent_work.get()
            it.location = self.ent_loc.get()
            it.content = self.ent_content.get()
            it.date_str = self.ent_date.get()
            it.project_name = self.ent_project.get()

            self.left_panel.refresh_tree()
            self._sync_view()

    def on_crop_mode_changed(self, choice):
        if 0 <= self.current_index < len(self.items):
            cmap = {
                "비율유지 꽉채움(기본)": CropMode.COVER,
                "비율유지 여백(전체)": CropMode.FIT,
                "늘임": CropMode.STRETCH
            }
            self.items[self.current_index].crop_mode = cmap.get(choice, CropMode.COVER)
            self._sync_view()

    def on_stamp_toggled(self):
        if 0 <= self.current_index < len(self.items):
            self.items[self.current_index].stamp_enabled = bool(self.chk_stamp.get())
            self.left_panel.refresh_tree()
            self._sync_view()

    def on_re_extract_exif(self):
        if 0 <= self.current_index < len(self.items):
            it = self.items[self.current_index]
            exif_dt, _, _ = extract_metadata(it.image_path)
            if exif_dt:
                it.date_str = format_date(exif_dt, "YYYY.MM")
                self.ent_date.delete(0, "end")
                self.ent_date.insert(0, it.date_str)
                self.on_field_edited()
                messagebox.showinfo("완료", f"사진 EXIF 촬영일자({it.date_str})를 추출했습니다.")
            else:
                messagebox.showwarning("경고", "해당 사진에는 EXIF 원본 촬영일자 정보가 없습니다.")

    def on_extract_mtime(self):
        if 0 <= self.current_index < len(self.items):
            it = self.items[self.current_index]
            _, mtime_dt, _ = extract_metadata(it.image_path)
            if mtime_dt:
                it.date_str = format_date(mtime_dt, "YYYY.MM")
                self.ent_date.delete(0, "end")
                self.ent_date.insert(0, it.date_str)
                self.on_field_edited()
                messagebox.showinfo("완료", f"파일 수정일자({it.date_str})를 적용했습니다.")
            else:
                messagebox.showwarning("경고", "파일 수정일자를 읽어올 수 없습니다.")

    def on_preset_selected(self, choice):
        for cb in self.preset_mgr.get_combos():
            chk = f"[{cb.get('title')}] {cb.get('work_type')} / {cb.get('content')}"
            if chk == choice:
                self.ent_work.delete(0, "end")
                self.ent_work.insert(0, cb.get("work_type", ""))
                self.ent_loc.delete(0, "end")
                self.ent_loc.insert(0, cb.get("location", ""))
                self.ent_content.delete(0, "end")
                self.ent_content.insert(0, cb.get("content", ""))
                self.on_field_edited()
                break

    def _refresh_presets_dropdown(self):
        combos = self.preset_mgr.get_combos()
        vals = [f"[{cb.get('title')}] {cb.get('work_type')} / {cb.get('content')}" for cb in combos]
        if not vals: vals = ["등록된 프리셋 없음"]
        self.combo_preset_menu.configure(values=vals)
        self.combo_preset_menu.set("✨ 프리셋 선택...")

    def open_preset_dialog(self):
        PresetManagerDialog(self, self.preset_mgr, self._refresh_presets_dropdown)

    def open_stamp_settings_dialog(self):
        cur_cfg = self.items[self.current_index].stamp_config if (0 <= self.current_index < len(self.items)) else self.default_stamp_config
        def on_save(new_cfg: StampConfig):
            self.default_stamp_config = new_cfg
            if 0 <= self.current_index < len(self.items):
                self.items[self.current_index].stamp_config = new_cfg
            self._sync_view()
        StampSettingsDialog(self, cur_cfg, on_save)

    def on_prev_page(self):
        if self.current_page > 0:
            self.current_page -= 1
            self._sync_view()

    def on_next_page(self):
        tot = max(1, (len(self.items) + 1) // 2)
        if self.current_page < tot - 1:
            self.current_page += 1
            self._sync_view()

    def _sync_view(self):
        tot_pages = max(1, (len(self.items) + 1) // 2)
        if self.current_page >= tot_pages:
            self.current_page = max(0, tot_pages - 1)
        self.lbl_page_info.configure(text=f"페이지: {self.current_page + 1} / {tot_pages}")
        pname = self.ent_project.get().strip()
        self.preview_canvas.update_data(self.items, self.current_page, self.current_index, pname)

    def on_export_pdf(self):
        if not self.items:
            messagebox.showwarning("경고", "내보낼 사진이 없습니다.")
            return
        path = filedialog.asksaveasfilename(
            title="A4 사진대지 PDF 저장",
            defaultextension=".pdf",
            filetypes=[("PDF 문서", "*.pdf")]
        )
        if path:
            exporter = PDFExporter()
            proj = self.ent_project.get().strip()
            ok = exporter.export(self.items, path, project_name=proj)
            if ok:
                if messagebox.askyesno("완료", "PDF 사진대지가 생성되었습니다!\n지금 열어보시겠습니까?"):
                    os.startfile(path)
            else:
                messagebox.showerror("오류", "PDF 생성 중 오류가 발생했습니다.")

    def on_export_excel(self):
        if not self.items:
            messagebox.showwarning("경고", "내보낼 사진이 없습니다.")
            return
        path = filedialog.asksaveasfilename(
            title="호환 엑셀 파일 저장 (.xlsx)",
            defaultextension=".xlsx",
            filetypes=[("Excel 통합 문서", "*.xlsx")]
        )
        if path:
            exporter = ExcelExporter()
            proj = self.ent_project.get().strip()
            ok = exporter.export(self.items, path, project_name=proj)
            if ok:
                if messagebox.askyesno("완료", "기성 사진대지 엑셀 파일이 생성되었습니다!\n지금 열어보시겠습니까?"):
                    os.startfile(path)
            else:
                messagebox.showerror("오류", "엑셀 파일 생성 중 오류가 발생했습니다.")
