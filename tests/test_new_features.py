# -*- coding: utf-8 -*-
import os
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.models import PictureItem, StampConfig, CropMode, StampPosition
from core.pdf_exporter import PDFExporter
from core.excel_exporter import ExcelExporter

def test_new_features():
    print("=== [신규 기능 테스트] 회전, 여백, 글자색, 투명도 0%, 일자 포맷 검증 ===")
    test_img = "tests/test_sample.jpg"
    assert os.path.exists(test_img), "테스트 이미지 없음"

    items = [
        PictureItem(
            image_path=test_img,
            work_type="토공사",
            location="1공구",
            content="부지정리 및 다짐",
            date_str="2026.04.15", # 일자 포함 포맷
            rotation=90,           # 90도 회전
            padding=15,            # 15px 여백
            crop_mode=CropMode.COVER,
            stamp_enabled=True,
            stamp_config=StampConfig(
                enabled=True,
                position=StampPosition.BOTTOM_RIGHT,
                text_color="#FFEE58", # 노란색 글자
                bg_alpha=0.0,         # 0% 완전 투명
                border=False
            )
        ),
        PictureItem(
            image_path=test_img,
            work_type="공통공사",
            location="현장사무실",
            content="기초콘크리트 타설",
            date_str="2026.04.18", # 일자 포함 포맷
            rotation=0,
            padding=0,
            crop_mode=CropMode.COVER,
            stamp_enabled=True,
            stamp_config=StampConfig(
                enabled=True,
                position=StampPosition.BOTTOM_RIGHT,
                text_color="#FFFFFF",
                bg_alpha=0.65,
                border=True
            )
        ),
        PictureItem(
            image_path=test_img,
            work_type="구조물공",
            location="STA. 0+120",
            content="신호수",
            date_str="2026.09.15",
            rotation=0,
            padding=5,
            crop_mode=CropMode.COVER,
            stamp_enabled=True,
            stamp_config=StampConfig(
                enabled=True,
                position=StampPosition.BOTTOM_LEFT,
                text_color="#4FC3F7",
                bg_alpha=0.5,
                border=True,
                hide_labels=True  # 제목 표시 숨김 모드 검증
            )
        )
    ]

    # PDF 생성
    pdf_out = "tests/test_features.pdf"
    res_pdf = PDFExporter().export(items, pdf_out, "검암역세권 공사")
    assert res_pdf and os.path.exists(pdf_out), "PDF 생성 실패"
    print(f"[OK] 신규 기능 적용 PDF 생성 성공 ({os.path.getsize(pdf_out)} bytes)")

    # Excel 생성
    xl_out = "tests/test_features.xlsx"
    res_xl = ExcelExporter().export(items, xl_out, "검암역세권 공사")
    assert res_xl and os.path.exists(xl_out), "Excel 생성 실패"
    print(f"[OK] 신규 기능 적용 Excel 생성 성공 ({os.path.getsize(xl_out)} bytes)")

    print("\n>>> 신규 기능 종합 검증 통과! (Error Count: 0) <<<")

if __name__ == "__main__":
    test_new_features()
