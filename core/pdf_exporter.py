# -*- coding: utf-8 -*-
import os
from typing import List
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from PIL import Image

from core.models import PictureItem
from core.image_processor import process_picture

# 한글 폰트 등록
FONT_NAME = "MalgunGothic"
FONT_BOLD_NAME = "MalgunGothicBold"

def init_fonts():
    try:
        if FONT_NAME not in pdfmetrics.getRegisteredFontNames():
            if os.path.exists("C:/Windows/Fonts/malgun.ttf"):
                pdfmetrics.registerFont(TTFont(FONT_NAME, "C:/Windows/Fonts/malgun.ttf"))
            else:
                pdfmetrics.registerFont(TTFont(FONT_NAME, "C:/Windows/Fonts/gulim.ttc", subfontIndex=0))
        if FONT_BOLD_NAME not in pdfmetrics.getRegisteredFontNames():
            if os.path.exists("C:/Windows/Fonts/malgunbd.ttf"):
                pdfmetrics.registerFont(TTFont(FONT_BOLD_NAME, "C:/Windows/Fonts/malgunbd.ttf"))
            else:
                pdfmetrics.registerFont(TTFont(FONT_BOLD_NAME, "C:/Windows/Fonts/gulim.ttc", subfontIndex=0))
    except Exception as e:
        print(f"폰트 등록 경고: {e}")

init_fonts()

class PDFExporter:
    """pictureboard.pdf 양식과 100% 일치하는 A4 사진대지 PDF 생성기"""
    def __init__(self, default_project_name: str = "공사명 미지정"):
        self.default_project_name = default_project_name

    def export(self, items: List[PictureItem], output_path: str, project_name: str = None, table_config: dict = None) -> bool:
        if not items:
            return False
            
        proj_name = project_name or self.default_project_name
        
        # A4 크기 (595.27 x 841.89 pt)
        c = canvas.Canvas(output_path, pagesize=A4)
        c.setTitle("사진대지")
        
        # 1페이지당 2장
        total_items = len(items)
        pages_count = (total_items + 1) // 2
        
        # 임시 이미지 저장용 폴더
        temp_dir = os.path.join(os.path.dirname(output_path), "_temp_pdf_imgs")
        os.makedirs(temp_dir, exist_ok=True)

        try:
            for page_idx in range(pages_count):
                idx1 = page_idx * 2
                idx2 = idx1 + 1
                
                item1 = items[idx1] if idx1 < total_items else None
                item2 = items[idx2] if idx2 < total_items else None
                
                self._render_page(c, page_idx + 1, pages_count, proj_name, item1, item2, temp_dir, table_config=table_config)
                c.showPage()
                
            c.save()
            return True
        finally:
            # 임시 파일 정리
            try:
                import shutil
                if os.path.exists(temp_dir):
                    shutil.rmtree(temp_dir, ignore_errors=True)
            except Exception:
                pass

    def _render_page(self, c: canvas.Canvas, page_num: int, total_pages: int, 
                     project_name: str, item1: PictureItem, item2: PictureItem, temp_dir: str, table_config: dict = None):
        page_w, page_h = A4  # 595.27, 841.89
        
        # 1. 상단 제목 "사  진  대  지"
        c.setFont(FONT_BOLD_NAME, 20)
        title_text = "사  진  대  지"
        c.drawCentredString(page_w / 2.0, page_h - 78, title_text)
        
        # 제목 밑줄
        title_w = c.stringWidth(title_text, FONT_BOLD_NAME, 20)
        c.setLineWidth(0.8)
        c.line((page_w - title_w) / 2.0, page_h - 82, (page_w + title_w) / 2.0, page_h - 82)
        
        # 2. 공사명
        p_name = item1.project_name if (item1 and item1.project_name) else project_name
        c.setFont(FONT_NAME, 10.5)
        c.drawString(64, page_h - 105, f"공사명 : {p_name}")

        # 3. table_config 분석 (1~2개 선택 시 1줄, 3~4개 선택 시 2줄)
        default_fields = [
            {"key": "work_type", "label": "공    종", "enabled": True},
            {"key": "content", "label": "내       용", "enabled": True},
            {"key": "location", "label": "위    치", "enabled": True},
            {"key": "date_str", "label": "촬 영 일 자", "enabled": True},
        ]
        cfg_fields = (table_config.get("fields") if table_config else None) or default_fields
        active_fields = [f for f in cfg_fields if f.get("enabled", True)]
        if not active_fields:
            active_fields = default_fields
            
        field_count = len(active_fields)
        row_count = 1 if field_count <= 2 else 2

        # 4. 레이아웃 좌표 설정 (pt 기준)
        # 전체 슬롯 높이 318pt는 절대 불변!
        # 1줄일 때: 표 20.5pt + 사진 297.5pt = 318.0pt (사진이 시원하게 위아래 확장!)
        # 2줄일 때: 표 41.0pt + 사진 277.0pt = 318.0pt
        box_x = 64.0
        box_w = 470.0
        box1_y = page_h - 436.0  # 상단 슬롯
        box1_h = 318.0
        
        if row_count == 1:
            table_h = 20.5
        else:
            table_h = 41.0
        photo_h = box1_h - table_h
        
        box2_y = page_h - 764.0  # 하단 슬롯
        box2_h = 318.0

        # 상단 슬롯 (사진 1)
        if item1:
            self._render_slot(c, item1, box_x, box1_y, box_w, photo_h, table_h, temp_dir, slot_num=1, active_fields=active_fields, row_count=row_count)
        else:
            self._render_empty_slot(c, box_x, box1_y, box_w, photo_h, table_h, active_fields=active_fields, row_count=row_count)

        # 하단 슬롯 (사진 2)
        if item2:
            self._render_slot(c, item2, box_x, box2_y, box_w, photo_h, table_h, temp_dir, slot_num=2, active_fields=active_fields, row_count=row_count)
        else:
            self._render_empty_slot(c, box_x, box2_y, box_w, photo_h, table_h, active_fields=active_fields, row_count=row_count)

    def _render_slot(self, c: canvas.Canvas, item: PictureItem, 
                     x: float, y: float, w: float, photo_h: float, table_h: float, temp_dir: str, slot_num: int,
                     active_fields: list, row_count: int):
        # 1. 외곽 사각형 (전체 슬롯 318pt 불변)
        c.setLineWidth(1.2)
        c.rect(x, y, w, photo_h + table_h)
        
        # 2. 사진 렌더링
        photo_y = y + table_h
        target_w_px = int(w * 3)  # 고해상도 (300dpi급)
        target_h_px = int(photo_h * 3)
        
        processed = process_picture(item, target_w_px, target_h_px)
        temp_img_path = os.path.join(temp_dir, f"slot_{slot_num}_{item.item_id[:8]}.jpg")
        processed.save(temp_img_path, "JPEG", quality=95)
        
        c.drawImage(temp_img_path, x + 0.6, photo_y + 0.6, width=w - 1.2, height=photo_h - 1.2)
        
        # 3. 사진과 표 사이 경계선
        c.setLineWidth(1.0)
        c.line(x, photo_y, x + w, photo_y)
        
        # 4. 표 내부 그리드 렌더링
        self._render_table_grid(c, x, y, w, table_h, item, active_fields, row_count)

    def _render_empty_slot(self, c: canvas.Canvas, x: float, y: float, w: float, photo_h: float, table_h: float,
                           active_fields: list, row_count: int):
        c.setLineWidth(1.2)
        c.rect(x, y, w, photo_h + table_h)
        c.line(x, y + table_h, x + w, y + table_h)
        self._render_table_grid(c, x, y, w, table_h, None, active_fields, row_count)

    def _render_table_grid(self, c: canvas.Canvas, x: float, y: float, w: float, h: float, 
                           item: PictureItem, active_fields: list, row_count: int):
        def _get_item_val(key: str) -> str:
            if not item: return ""
            if key == "work_type": return item.work_type or ""
            if key == "content": return item.content or ""
            if key == "location": return item.location or ""
            if key == "date_str": return item.date_str or ""
            if key == "custom1": return getattr(item, "custom1", "") or ""
            if key == "custom2": return getattr(item, "custom2", "") or ""
            return ""

        c.setLineWidth(0.8)
        
        if row_count == 1:
            # 단일행 (1줄) 모드: h = 20.5pt
            text_y = y + 5.5
            if len(active_fields) == 1:
                f = active_fields[0]
                lbl_w = 85.0
                c.line(x + lbl_w, y, x + lbl_w, y + h)
                c.setFont(FONT_BOLD_NAME, 9.5)
                c.drawCentredString(x + (lbl_w / 2.0), text_y, f.get("label", ""))
                c.setFont(FONT_NAME, 9.5)
                val = _get_item_val(f.get("key", ""))
                c.drawCentredString(x + lbl_w + ((w - lbl_w) / 2.0), text_y, val)
            else: # 2개 항목 좌우 50:50 분할
                f1, f2 = active_fields[0], active_fields[1]
                half_w = w / 2.0
                c.line(x + half_w, y, x + half_w, y + h)
                
                # 1번째 항목
                lbl1_w = 75.0
                c.line(x + lbl1_w, y, x + lbl1_w, y + h)
                c.setFont(FONT_BOLD_NAME, 9.5)
                c.drawCentredString(x + (lbl1_w / 2.0), text_y, f1.get("label", ""))
                c.setFont(FONT_NAME, 9.5)
                val1 = _get_item_val(f1.get("key", ""))
                c.drawCentredString(x + lbl1_w + ((half_w - lbl1_w) / 2.0), text_y, val1)
                
                # 2번째 항목
                x_r = x + half_w
                lbl2_w = 75.0
                c.line(x_r + lbl2_w, y, x_r + lbl2_w, y + h)
                c.setFont(FONT_BOLD_NAME, 9.5)
                c.drawCentredString(x_r + (lbl2_w / 2.0), text_y, f2.get("label", ""))
                c.setFont(FONT_NAME, 9.5)
                val2 = _get_item_val(f2.get("key", ""))
                c.drawCentredString(x_r + lbl2_w + ((half_w - lbl2_w) / 2.0), text_y, val2)
                
        else:
            # 2줄 모드: h = 41.0pt, mid_y 분할
            mid_y = y + (h / 2.0)
            c.line(x, mid_y, x + w, mid_y)
            top_text_y = mid_y + 5.5
            bot_text_y = y + 5.5
            
            if len(active_fields) == 3:
                # 1행 2개 + 2행 1개 전폭 병합
                f1, f2, f3 = active_fields[0], active_fields[1], active_fields[2]
                half_w = w / 2.0
                c.line(x + half_w, mid_y, x + half_w, y + h)
                
                # 1행 1번
                lbl1_w = 75.0
                c.line(x + lbl1_w, mid_y, x + lbl1_w, y + h)
                c.setFont(FONT_BOLD_NAME, 9.5)
                c.drawCentredString(x + (lbl1_w / 2.0), top_text_y, f1.get("label", ""))
                c.setFont(FONT_NAME, 9.5)
                val1 = _get_item_val(f1.get("key", ""))
                c.drawCentredString(x + lbl1_w + ((half_w - lbl1_w) / 2.0), top_text_y, val1)
                
                # 1행 2번
                x_r = x + half_w
                lbl2_w = 75.0
                c.line(x_r + lbl2_w, mid_y, x_r + lbl2_w, y + h)
                c.setFont(FONT_BOLD_NAME, 9.5)
                c.drawCentredString(x_r + (lbl2_w / 2.0), top_text_y, f2.get("label", ""))
                c.setFont(FONT_NAME, 9.5)
                val2 = _get_item_val(f2.get("key", ""))
                c.drawCentredString(x_r + lbl2_w + ((half_w - lbl2_w) / 2.0), top_text_y, val2)
                
                # 2행 3번 (전폭 병합)
                lbl3_w = 75.0
                c.line(x + lbl3_w, y, x + lbl3_w, mid_y)
                c.setFont(FONT_BOLD_NAME, 9.5)
                c.drawCentredString(x + (lbl3_w / 2.0), bot_text_y, f3.get("label", ""))
                c.setFont(FONT_NAME, 9.5)
                val3 = _get_item_val(f3.get("key", ""))
                c.drawCentredString(x + lbl3_w + ((w - lbl3_w) / 2.0), bot_text_y, val3)
                
            else:
                # 4개 항목 (표준 2x2)
                f1, f2, f3, f4 = active_fields[0], active_fields[1], active_fields[2], active_fields[3]
                col1_w = 81.0
                col2_w = 132.0
                col3_w = 95.0
                col4_w = w - (col1_w + col2_w + col3_w)
                
                x1 = x + col1_w
                x2 = x1 + col2_w
                x3 = x2 + col3_w
                
                c.line(x1, y, x1, y + h)
                c.line(x2, y, x2, y + h)
                c.line(x3, y, x3, y + h)
                
                # 라벨
                c.setFont(FONT_BOLD_NAME, 9.5)
                c.drawCentredString(x + (col1_w / 2.0), top_text_y, f1.get("label", "공    종"))
                c.drawCentredString(x2 + (col3_w / 2.0), top_text_y, f2.get("label", "내       용"))
                c.drawCentredString(x + (col1_w / 2.0), bot_text_y, f3.get("label", "위    치"))
                c.drawCentredString(x2 + (col3_w / 2.0), bot_text_y, f4.get("label", "촬 영 일 자"))
                
                # 값
                c.setFont(FONT_NAME, 9.5)
                c.drawCentredString(x1 + (col2_w / 2.0), top_text_y, _get_item_val(f1.get("key", "work_type")))
                c.drawCentredString(x3 + (col4_w / 2.0), top_text_y, _get_item_val(f2.get("key", "content")))
                c.drawCentredString(x1 + (col2_w / 2.0), bot_text_y, _get_item_val(f3.get("key", "location")))
                c.drawCentredString(x3 + (col4_w / 2.0), bot_text_y, _get_item_val(f4.get("key", "date_str")))
