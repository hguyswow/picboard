# -*- coding: utf-8 -*-
import customtkinter as ctk
from tkinter import colorchooser
from core.models import StampConfig, StampPosition
from core.preset_manager import PresetManager

class StampSettingsDialog(ctk.CTkToplevel):
    """스탬프 세부 스타일 및 표시 항목 설정 다이얼로그"""
    def __init__(self, parent, current_config: StampConfig, on_save_callback):
        super().__init__(parent)
        self.title("스탬프 상세 설정")
        self.geometry("450x550")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.config = current_config
        self.on_save = on_save_callback

        self._build_ui()

    def _build_ui(self):
        pad = {"padx": 15, "pady": 8}

        # 1. 위치 설정
        pos_frame = ctk.CTkFrame(self)
        pos_frame.pack(fill="x", **pad)
        ctk.CTkLabel(pos_frame, text="스탬프 위치:", font=("맑은 고딕", 13, "bold")).pack(side="left", padx=10, pady=10)
        
        self.pos_var = ctk.StringVar(value=self.config.position.value)
        positions = [
            ("우측 하단 (기본)", StampPosition.BOTTOM_RIGHT.value),
            ("좌측 하단", StampPosition.BOTTOM_LEFT.value),
            ("우측 상단", StampPosition.TOP_RIGHT.value),
            ("좌측 상단", StampPosition.TOP_LEFT.value),
        ]
        self.pos_menu = ctk.CTkOptionMenu(
            pos_frame, 
            values=[p[0] for p in positions],
            command=self._on_pos_changed
        )
        # 현재 위치로 기본값 설정
        for label, val in positions:
            if val == self.config.position.value:
                self.pos_menu.set(label)
                break
        self.pos_menu.pack(side="right", padx=10, pady=10)
        self.pos_map = {p[0]: p[1] for p in positions}

        # 2. 표시 항목 선택 (체크박스)
        item_frame = ctk.CTkFrame(self)
        item_frame.pack(fill="x", **pad)
        ctk.CTkLabel(item_frame, text="스탬프 표시 항목 선택", font=("맑은 고딕", 13, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

        self.chk_proj = ctk.CTkCheckBox(item_frame, text="공사명 표시")
        if self.config.show_project: self.chk_proj.select()
        self.chk_proj.pack(anchor="w", padx=15, pady=3)

        self.chk_work = ctk.CTkCheckBox(item_frame, text="공종 표시 (예: 공종 : 공통공사)")
        if self.config.show_work_type: self.chk_work.select()
        self.chk_work.pack(anchor="w", padx=15, pady=3)

        self.chk_loc = ctk.CTkCheckBox(item_frame, text="위치 표시 (예: 위치 : 현장사무실)")
        if self.config.show_location: self.chk_loc.select()
        self.chk_loc.pack(anchor="w", padx=15, pady=3)

        self.chk_cnt = ctk.CTkCheckBox(item_frame, text="내용 표시 (예: 내용 : 기초콘크리트 타설)")
        if self.config.show_content: self.chk_cnt.select()
        self.chk_cnt.pack(anchor="w", padx=15, pady=3)

        self.chk_date = ctk.CTkCheckBox(item_frame, text="일자 표시 (예: 일자 : 2026.04)")
        if self.config.show_date: self.chk_date.select()
        self.chk_date.pack(anchor="w", padx=15, pady=3)

        # 추가 사용자 문구
        custom_box = ctk.CTkFrame(item_frame, fg_color="transparent")
        custom_box.pack(fill="x", padx=15, pady=(5, 10))
        ctk.CTkLabel(custom_box, text="추가 문구:").pack(side="left")
        self.ent_custom = ctk.CTkEntry(custom_box, placeholder_text="예: (주)한국건설 감리확인")
        self.ent_custom.insert(0, self.config.custom_text)
        self.ent_custom.pack(side="right", fill="x", expand=True, padx=(10, 0))

        # 3. 스타일 설정 (크기, 투명도, 테두리)
        style_frame = ctk.CTkFrame(self)
        style_frame.pack(fill="x", **pad)
        ctk.CTkLabel(style_frame, text="스타일 및 투명도", font=("맑은 고딕", 13, "bold")).pack(anchor="w", padx=10, pady=(10, 5))

        # 글자 크기
        size_box = ctk.CTkFrame(style_frame, fg_color="transparent")
        size_box.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(size_box, text="글꼴 기준 크기:").pack(side="left")
        self.slider_size = ctk.CTkSlider(size_box, from_=12, to=30, number_of_steps=18)
        self.slider_size.set(self.config.font_size)
        self.slider_size.pack(side="left", fill="x", expand=True, padx=10)
        self.lbl_size_val = ctk.CTkLabel(size_box, text=f"{self.config.font_size}pt", width=35)
        self.lbl_size_val.pack(side="right")
        self.slider_size.configure(command=lambda v: self.lbl_size_val.configure(text=f"{int(v)}pt"))

        # 배경 투명도
        alpha_box = ctk.CTkFrame(style_frame, fg_color="transparent")
        alpha_box.pack(fill="x", padx=10, pady=5)
        ctk.CTkLabel(alpha_box, text="배경 불투명도:").pack(side="left")
        self.slider_alpha = ctk.CTkSlider(alpha_box, from_=0.1, to=1.0, number_of_steps=9)
        self.slider_alpha.set(self.config.bg_alpha)
        self.slider_alpha.pack(side="left", fill="x", expand=True, padx=10)
        self.lbl_alpha_val = ctk.CTkLabel(alpha_box, text=f"{int(self.config.bg_alpha*100)}%", width=35)
        self.lbl_alpha_val.pack(side="right")
        self.slider_alpha.configure(command=lambda v: self.lbl_alpha_val.configure(text=f"{int(v*100)}%"))

        # 테두리 여부
        self.chk_border = ctk.CTkCheckBox(style_frame, text="흰색 테두리 표시")
        if self.config.border: self.chk_border.select()
        self.chk_border.pack(anchor="w", padx=15, pady=(5, 10))

        # 4. 하단 저장 버튼
        btn_box = ctk.CTkFrame(self, fg_color="transparent")
        btn_box.pack(fill="x", padx=15, pady=10)
        ctk.CTkButton(btn_box, text="취소", fg_color="#6c757d", hover_color="#5a6268", command=self.destroy).pack(side="right", padx=5)
        ctk.CTkButton(btn_box, text="적용하기", fg_color="#0d6efd", hover_color="#0b5ed7", command=self._save_and_close).pack(side="right", padx=5)

    def _on_pos_changed(self, choice):
        self.pos_var.set(self.pos_map.get(choice, StampPosition.BOTTOM_RIGHT.value))

    def _save_and_close(self):
        new_cfg = StampConfig(
            enabled=True,
            position=StampPosition(self.pos_var.get()),
            show_project=bool(self.chk_proj.get()),
            show_work_type=bool(self.chk_work.get()),
            show_location=bool(self.chk_loc.get()),
            show_content=bool(self.chk_cnt.get()),
            show_date=bool(self.chk_date.get()),
            custom_text=self.ent_custom.get().strip(),
            font_size=int(self.slider_size.get()),
            bg_alpha=round(self.slider_alpha.get(), 2),
            border=bool(self.chk_border.get()),
            bg_color=self.config.bg_color,
            text_color=self.config.text_color
        )
        self.on_save(new_cfg)
        self.destroy()

class PresetManagerDialog(ctk.CTkToplevel):
    """자주 쓰는 공종/위치/내용 프리셋 관리 창"""
    def __init__(self, parent, preset_manager: PresetManager, on_change_callback):
        super().__init__(parent)
        self.title("프리셋 관리 (공종 / 위치 / 내용)")
        self.geometry("500x520")
        self.resizable(False, False)
        self.transient(parent)
        self.grab_set()

        self.pm = preset_manager
        self.on_change = on_change_callback
        self._build_ui()

    def _build_ui(self):
        tabs = ctk.CTkTabview(self)
        tabs.pack(fill="both", expand=True, padx=15, pady=15)
        
        tab_combo = tabs.add("콤보 세트")
        tab_work = tabs.add("공종 목록")
        tab_loc = tabs.add("위치 목록")
        tab_cnt = tabs.add("내용 목록")

        # 콤보 세트 탭
        self._build_combo_tab(tab_combo)
        # 단일 항목 탭들
        self._build_list_tab(tab_work, "공종", self.pm.get_work_types, self.pm.add_work_type)
        self._build_list_tab(tab_loc, "위치", self.pm.get_locations, self.pm.add_location)
        self._build_list_tab(tab_cnt, "내용", self.pm.get_contents, self.pm.add_content)

    def _build_combo_tab(self, parent):
        ctk.CTkLabel(parent, text="자주 쓰는 공종 + 위치 + 내용 묶음 세트", font=("맑은 고딕", 12, "bold")).pack(anchor="w", pady=(0, 5))
        
        # 목록
        self.combo_scroll = ctk.CTkScrollableFrame(parent, height=220)
        self.combo_scroll.pack(fill="both", expand=True, pady=5)
        self._refresh_combos()

        # 새로 추가
        add_frame = ctk.CTkFrame(parent)
        add_frame.pack(fill="x", pady=5)
        
        row1 = ctk.CTkFrame(add_frame, fg_color="transparent")
        row1.pack(fill="x", padx=5, pady=3)
        self.ent_title = ctk.CTkEntry(row1, placeholder_text="세트 이름 (예: 골재포설)", width=140)
        self.ent_title.pack(side="left", padx=3)
        self.ent_w = ctk.CTkEntry(row1, placeholder_text="공종", width=120)
        self.ent_w.pack(side="left", padx=3)
        self.ent_l = ctk.CTkEntry(row1, placeholder_text="위치", width=140)
        self.ent_l.pack(side="left", padx=3)

        row2 = ctk.CTkFrame(add_frame, fg_color="transparent")
        row2.pack(fill="x", padx=5, pady=3)
        self.ent_c = ctk.CTkEntry(row2, placeholder_text="상세 내용", fill="x", expand=True)
        self.ent_c.pack(side="left", fill="x", expand=True, padx=3)
        ctk.CTkButton(row2, text="세트 추가", width=90, fg_color="#198754", hover_color="#157347", command=self._add_combo).pack(side="right", padx=3)

    def _refresh_combos(self):
        for w in self.combo_scroll.winfo_children():
            w.destroy()
        
        combos = self.pm.get_combos()
        for idx, cb in enumerate(combos):
            item_f = ctk.CTkFrame(self.combo_scroll)
            item_f.pack(fill="x", pady=3, padx=2)
            
            txt = f"[{cb.get('title')}] {cb.get('work_type')} | {cb.get('location')} | {cb.get('content')}"
            ctk.CTkLabel(item_f, text=txt, font=("맑은 고딕", 11), anchor="w").pack(side="left", fill="x", expand=True, padx=8, pady=5)
            
            del_btn = ctk.CTkButton(item_f, text="삭제", width=50, height=24, fg_color="#dc3545", hover_color="#bb2d3b",
                                    command=lambda i=idx: self._del_combo(i))
            del_btn.pack(side="right", padx=5, pady=5)

    def _add_combo(self):
        t = self.ent_title.get().strip()
        w = self.ent_w.get().strip()
        l = self.ent_l.get().strip()
        c = self.ent_c.get().strip()
        if w or c:
            self.pm.add_combo(t, w, l, c)
            self._refresh_combos()
            self.ent_title.delete(0, "end")
            self.ent_w.delete(0, "end")
            self.ent_l.delete(0, "end")
            self.ent_c.delete(0, "end")
            self.on_change()

    def _del_combo(self, index: int):
        self.pm.delete_combo(index)
        self._refresh_combos()
        self.on_change()

    def _build_list_tab(self, parent, label: str, get_fn, add_fn):
        ctk.CTkLabel(parent, text=f"등록된 {label} 목록", font=("맑은 고딕", 12, "bold")).pack(anchor="w", pady=(0, 5))
        
        scroll = ctk.CTkScrollableFrame(parent, height=280)
        scroll.pack(fill="both", expand=True, pady=5)
        
        def refresh():
            for w in scroll.winfo_children():
                w.destroy()
            for val in get_fn():
                f = ctk.CTkFrame(scroll)
                f.pack(fill="x", pady=2)
                ctk.CTkLabel(f, text=val, font=("맑은 고딕", 11), anchor="w").pack(side="left", padx=8, pady=4)
        
        refresh()

        add_box = ctk.CTkFrame(parent, fg_color="transparent")
        add_box.pack(fill="x", pady=5)
        ent = ctk.CTkEntry(add_box, placeholder_text=f"새 {label} 입력")
        ent.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        def on_add():
            v = ent.get().strip()
            if v:
                add_fn(v)
                refresh()
                ent.delete(0, "end")
                self.on_change()

        ctk.CTkButton(add_box, text="추가", width=70, command=on_add).pack(side="right")
