# -*- coding: utf-8 -*-
from typing import List, Callable
import customtkinter as ctk
from tkinter import ttk, messagebox
from core.models import PictureItem

class LeftPanel(ctk.CTkFrame):
    """사진 목록, 정렬, 트리뷰, 일괄 수정을 담당하는 좌측 패널"""
    def __init__(self, master, on_select_callback: Callable[[int], None], 
                 on_refresh_callback: Callable[[], None], **kwargs):
        super().__init__(master, **kwargs)
        self.on_select = on_select_callback
        self.on_refresh = on_refresh_callback
        self.items: List[PictureItem] = []
        self._build_ui()

    def _build_ui(self):
        # 1. 유틸리티 바 (정렬, 위/아래 이동, 스탬프 일괄, 삭제)
        util_bar = ctk.CTkFrame(self, fg_color="transparent")
        util_bar.pack(fill="x", padx=10, pady=(10, 5))

        ctk.CTkLabel(util_bar, text="정렬:", font=("맑은 고딕", 11, "bold")).pack(side="left", padx=(0, 4))
        self.sort_menu = ctk.CTkOptionMenu(
            util_bar, width=130, height=28,
            values=["촬영일자 오름차순", "촬영일자 내림차순", "파일명 오름차순", "파일명 내림차순", "폴더별 묶음"],
            command=self._on_sort
        )
        self.sort_menu.pack(side="left", padx=2)

        btn_up = ctk.CTkButton(util_bar, text="▲", width=32, height=28, command=self._on_move_up)
        btn_up.pack(side="left", padx=2)
        btn_down = ctk.CTkButton(util_bar, text="▼", width=32, height=28, command=self._on_move_down)
        btn_down.pack(side="left", padx=2)

        self.btn_toggle_stamp = ctk.CTkButton(
            util_bar, text="스탬프 전체ON", width=95, height=28,
            fg_color="#495057", hover_color="#343a40", command=self._on_toggle_all_stamps
        )
        self.btn_toggle_stamp.pack(side="left", padx=5)

        btn_del = ctk.CTkButton(
            util_bar, text="선택삭제", width=65, height=28,
            fg_color="#dc3545", hover_color="#bb2d3b", command=self._on_delete
        )
        btn_del.pack(side="right", padx=2)

        # 2. Treeview 목록
        tree_frame = ctk.CTkFrame(self)
        tree_frame.pack(fill="both", expand=True, padx=10, pady=5)

        cols = ("idx", "name", "folder", "work", "date", "stamp")
        self.tree = ttk.Treeview(tree_frame, columns=cols, show="headings", selectmode="extended")
        self.tree.heading("idx", text="No")
        self.tree.heading("name", text="파일명")
        self.tree.heading("folder", text="폴더명")
        self.tree.heading("work", text="공종")
        self.tree.heading("date", text="촬영일자")
        self.tree.heading("stamp", text="스탬프")

        self.tree.column("idx", width=35, anchor="center")
        self.tree.column("name", width=120, anchor="w")
        self.tree.column("folder", width=80, anchor="w")
        self.tree.column("work", width=80, anchor="center")
        self.tree.column("date", width=80, anchor="center")
        self.tree.column("stamp", width=60, anchor="center")

        tree_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=tree_scroll.set)
        self.tree.pack(side="left", fill="both", expand=True)
        tree_scroll.pack(side="right", fill="y")
        self.tree.bind("<<TreeviewSelect>>", self._on_tree_select)

        # 3. 일괄 수정 영역
        batch_frame = ctk.CTkFrame(self)
        batch_frame.pack(fill="x", padx=10, pady=10)
        ctk.CTkLabel(batch_frame, text="⚡ 선택 사진(또는 전체) 일괄 입력", font=("맑은 고딕", 12, "bold")).pack(anchor="w", padx=10, pady=(6, 2))

        b_row1 = ctk.CTkFrame(batch_frame, fg_color="transparent")
        b_row1.pack(fill="x", padx=5, pady=2)
        self.batch_work = ctk.CTkEntry(b_row1, placeholder_text="일괄 공종", width=120)
        self.batch_work.pack(side="left", padx=2)
        self.batch_loc = ctk.CTkEntry(b_row1, placeholder_text="일괄 위치", width=130)
        self.batch_loc.pack(side="left", padx=2)
        self.batch_date = ctk.CTkEntry(b_row1, placeholder_text="일괄 날짜", width=110)
        self.batch_date.pack(side="left", padx=2)

        btn_apply = ctk.CTkButton(b_row1, text="일괄적용", width=70, command=self._on_apply_batch)
        btn_apply.pack(side="right", padx=2)

    def set_items(self, items: List[PictureItem]):
        self.items = items
        self.refresh_tree()

    def refresh_tree(self):
        self.tree.delete(*self.tree.get_children())
        for idx, item in enumerate(self.items):
            stamp_text = "ON" if item.stamp_enabled else "OFF"
            self.tree.insert("", "end", iid=str(idx), values=(
                idx + 1, item.file_name, item.folder_name,
                item.work_type, item.date_str, stamp_text
            ))

    def select_row(self, idx: int):
        if 0 <= idx < len(self.items):
            self.tree.selection_set(str(idx))
            self.tree.see(str(idx))

    def _on_tree_select(self, event):
        selected = self.tree.selection()
        if selected:
            self.on_select(int(selected[0]))

    def _on_sort(self, choice):
        if not self.items: return
        if choice == "파일명 오름차순":
            self.items.sort(key=lambda x: (x.file_name.lower(), x.date_str))
        elif choice == "파일명 내림차순":
            self.items.sort(key=lambda x: (x.file_name.lower(), x.date_str), reverse=True)
        elif choice in ["촬영일자순", "촬영일자 오름차순"]:
            self.items.sort(key=lambda x: (x.date_str, x.file_name.lower()))
        elif choice == "촬영일자 내림차순":
            self.items.sort(key=lambda x: (x.date_str, x.file_name.lower()), reverse=True)
        elif choice == "폴더별 묶음":
            self.items.sort(key=lambda x: (x.folder_name, x.file_name))
        self.refresh_tree()
        self.on_refresh()

    def _on_move_up(self):
        selected = self.tree.selection()
        if not selected: return
        idx = int(selected[0])
        if idx > 0:
            self.items[idx], self.items[idx - 1] = self.items[idx - 1], self.items[idx]
            self.refresh_tree()
            self.select_row(idx - 1)
            self.on_select(idx - 1)

    def _on_move_down(self):
        selected = self.tree.selection()
        if not selected: return
        idx = int(selected[0])
        if idx < len(self.items) - 1:
            self.items[idx], self.items[idx + 1] = self.items[idx + 1], self.items[idx]
            self.refresh_tree()
            self.select_row(idx + 1)
            self.on_select(idx + 1)

    def _on_delete(self):
        selected = self.tree.selection()
        if not selected: return
        indices = sorted([int(s) for s in selected], reverse=True)
        for i in indices:
            self.items.pop(i)
        self.refresh_tree()
        if self.items:
            new_idx = min(indices[-1], len(self.items) - 1)
            self.select_row(new_idx)
            self.on_select(new_idx)
        else:
            self.on_refresh()

    def _on_toggle_all_stamps(self):
        if not self.items: return
        target_state = not self.items[0].stamp_enabled
        for it in self.items:
            it.stamp_enabled = target_state
        self.btn_toggle_stamp.configure(text="스탬프 전체OFF" if target_state else "스탬프 전체ON")
        self.refresh_tree()
        self.on_refresh()

    def _on_apply_batch(self):
        selected = self.tree.selection()
        targets = [int(s) for s in selected] if selected else list(range(len(self.items)))
        bw = self.batch_work.get().strip()
        bl = self.batch_loc.get().strip()
        bd = self.batch_date.get().strip()
        if not (bw or bl or bd):
            messagebox.showinfo("안내", "적용할 공종, 위치 또는 날짜를 입력하세요.")
            return
        for idx in targets:
            it = self.items[idx]
            if bw: it.work_type = bw
            if bl: it.location = bl
            if bd: it.date_str = bd
        self.refresh_tree()
        self.on_refresh()
        messagebox.showinfo("완료", f"{len(targets)}개 사진에 일괄 적용되었습니다.")
