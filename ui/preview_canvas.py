# -*- coding: utf-8 -*-
import os
from typing import Optional, List
import customtkinter as ctk
from PIL import ImageTk
from core.models import PictureItem
from core.image_processor import process_picture

class A4PreviewCanvas(ctk.CTkCanvas):
    """pictureboard.pdf 규격의 A4 2단 실시간 미리보기 캔버스"""
    def __init__(self, master, **kwargs):
        super().__init__(master, bg="#f8f9fa", highlightthickness=0, **kwargs)
        self.items: List[PictureItem] = []
        self.current_page: int = 0
        self.selected_index: int = -1
        self.project_name: str = ""
        self._cache_imgs = []
        self.bind("<Configure>", lambda e: self.render())

    def update_data(self, items: List[PictureItem], page: int, selected_idx: int, project_name: str):
        self.items = items
        self.current_page = page
        self.selected_index = selected_idx
        self.project_name = project_name
        self.render()

    def render(self):
        self.delete("all")
        self._cache_imgs.clear()

        cw = self.winfo_width()
        ch = self.winfo_height()
        if cw < 60 or ch < 60:
            return

        # A4 종이 비율 (595.27 x 841.89 pt -> 비율 1 : 1.414)
        a4_ratio = 841.89 / 595.27
        margin = 15
        avail_w = cw - (margin * 2)
        avail_h = ch - (margin * 2)

        if avail_h / avail_w > a4_ratio:
            paper_w = avail_w
            paper_h = avail_w * a4_ratio
        else:
            paper_h = avail_h
            paper_w = avail_h / a4_ratio

        ox = (cw - paper_w) / 2
        oy = (ch - paper_h) / 2

        # A4 종이 배경 및 그림자
        self.create_rectangle(ox + 3, oy + 3, ox + paper_w + 3, oy + paper_h + 3, fill="#cccccc", outline="")
        self.create_rectangle(ox, oy, ox + paper_w, oy + paper_h, fill="#ffffff", outline="#999999", width=1)

        scale = paper_w / 595.27

        # 1. 상단 제목 "사  진  대  지"
        title_y = oy + (75 * scale)
        self.create_text(
            ox + (paper_w / 2), title_y,
            text="사  진  대  지",
            font=("맑은 고딕", max(10, int(18 * scale)), "bold"),
            fill="#000000"
        )
        self.create_line(
            ox + (paper_w / 2) - (80 * scale), title_y + (12 * scale),
            ox + (paper_w / 2) + (80 * scale), title_y + (12 * scale),
            fill="#000000", width=max(1, int(scale))
        )

        # 2. 공사명
        pname = self.project_name.strip() or "공사명 미지정"
        self.create_text(
            ox + (64 * scale), oy + (105 * scale),
            text=f"공사명 : {pname}",
            anchor="w",
            font=("맑은 고딕", max(8, int(9.5 * scale))),
            fill="#000000"
        )

        # 3. 사진 슬롯 2개 렌더링
        slot_w = 470.0 * scale
        slot_h = 318.0 * scale
        slot_x = ox + (64.0 * scale)

        idx1 = self.current_page * 2
        idx2 = idx1 + 1

        item1 = self.items[idx1] if idx1 < len(self.items) else None
        item2 = self.items[idx2] if idx2 < len(self.items) else None

        # 슬롯 1 (상단)
        slot1_y = oy + (118.0 * scale)
        self._render_slot(slot_x, slot1_y, slot_w, slot_h, scale, item1, slot_idx=idx1)

        # 슬롯 2 (하단)
        slot2_y = oy + (446.0 * scale)
        self._render_slot(slot_x, slot2_y, slot_w, slot_h, scale, item2, slot_idx=idx2)

    def _render_slot(self, x, y, w, h, scale, item: Optional[PictureItem], slot_idx: int):
        table_h = 41.0 * scale
        photo_h = h - table_h

        is_selected = (item and self.selected_index == slot_idx)
        border_col = "#0d6efd" if is_selected else "#000000"
        border_w = 3 if is_selected else 1

        self.create_rectangle(x, y, x + w, y + h, outline=border_col, width=border_w)
        self.create_line(x, y + photo_h, x + w, y + photo_h, fill="#000000", width=1)

        # 사진 렌더링
        if item and os.path.exists(item.image_path):
            try:
                pw = max(10, int(w))
                ph = max(10, int(photo_h))
                proc = process_picture(item, pw, ph)
                tk_img = ImageTk.PhotoImage(proc)
                self._cache_imgs.append(tk_img)
                self.create_image(x + (w / 2), y + (photo_h / 2), image=tk_img)
            except Exception as e:
                self.create_text(x + (w / 2), y + (photo_h / 2), text=f"이미지 오류: {e}", fill="red")
        else:
            self.create_text(x + (w / 2), y + (photo_h / 2), text="[ 사진 없음 ]", fill="#888888")

        # 표 그리드
        mid_y = y + photo_h + (table_h / 2)
        self.create_line(x, mid_y, x + w, mid_y, fill="#000000")

        c1 = 81.0 * scale
        c2 = 132.0 * scale
        c3 = 95.0 * scale
        x1 = x + c1
        x2 = x1 + c2
        x3 = x2 + c3

        self.create_line(x1, y + photo_h, x1, y + h, fill="#000000")
        self.create_line(x2, y + photo_h, x2, y + h, fill="#000000")
        self.create_line(x3, y + photo_h, x3, y + h, fill="#000000")

        lbl_f = ("맑은 고딕", max(7, int(8.5 * scale)), "bold")
        val_f = ("맑은 고딕", max(7, int(8.5 * scale)))

        # 1행 라벨
        self.create_text(x + (c1 / 2), y + photo_h + (table_h / 4), text="공  종", font=lbl_f)
        self.create_text(x2 + (c3 / 2), y + photo_h + (table_h / 4), text="내  용", font=lbl_f)

        # 2행 라벨
        self.create_text(x + (c1 / 2), mid_y + (table_h / 4), text="위  치", font=lbl_f)
        self.create_text(x2 + (c3 / 2), mid_y + (table_h / 4), text="촬영일자", font=lbl_f)

        # 데이터 값
        if item:
            self.create_text(x1 + (c2 / 2), y + photo_h + (table_h / 4), text=item.work_type, font=val_f)
            self.create_text(x3 + ((w - c1 - c2 - c3) / 2), y + photo_h + (table_h / 4), text=item.content, font=val_f)
            self.create_text(x1 + (c2 / 2), mid_y + (table_h / 4), text=item.location, font=val_f)
            self.create_text(x3 + ((w - c1 - c2 - c3) / 2), mid_y + (table_h / 4), text=item.date_str, font=val_f)
