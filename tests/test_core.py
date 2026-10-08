# -*- coding: utf-8 -*-
import os
import sys

# UTF-8 입출력 방어 (Rule 3)
sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')

# 프로젝트 루트 경로 추가
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PIL import Image
from core.models import PictureItem, StampConfig, CropMode, StampPosition
from core.image_processor import process_picture, extract_metadata
from core.preset_manager import PresetManager
from core.pdf_exporter import PDFExporter
from core.excel_exporter import ExcelExporter

def run_tests():
    print("=== [1] 테스트 이미지 준비 ===")
    test_img_path = "tests/test_sample.jpg"
    img = Image.new("RGB", (1920, 1080), color=(73, 109, 137))
    img.save(test_img_path)
    assert os.path.exists(test_img_path), "테스트 이미지 생성 실패"
    print("[OK] 테스트 이미지 생성 성공")

    print("\n=== [2] PresetManager 테스트 ===")
    pm = PresetManager("tests/test_presets.json")
    assert len(pm.get_work_types()) > 0, "공종 프리셋 로드 실패"
    assert len(pm.get_locations()) > 0, "위치 프리셋 로드 실패"
    assert len(pm.get_contents()) > 0, "내용 프리셋 로드 실패"
    print(f"[OK] 프리셋 로드 성공 (공종 {len(pm.get_work_types())}개, 위치 {len(pm.get_locations())}개)")

    print("\n=== [3] ImageProcessor & Stamp 테스트 ===")
    item = PictureItem(
        image_path=test_img_path,
        folder_name="테스트폴더",
        file_name="test_sample.jpg",
        project_name="검암역세권 공공주택지구 도시시설물 건설공사",
        work_type="공통공사",
        location="현장사무실",
        content="부지정리후 골재포설",
        date_str="2026.04",
        crop_mode=CropMode.COVER,
        stamp_enabled=True,
        stamp_config=StampConfig(
            enabled=True,
            position=StampPosition.BOTTOM_RIGHT,
            show_work_type=True,
            show_location=True,
            show_content=True,
            show_date=True
        )
    )
    processed = process_picture(item, 800, 500)
    assert processed.size == (800, 500), f"크롭 크기 불일치: {processed.size}"
    print("[OK] 이미지 회전/크롭/스탬프 합성 성공")

    print("\n=== [4] PDFExporter 테스트 ===")
    pdf_path = "tests/output_test.pdf"
    exporter_pdf = PDFExporter()
    items = [
        item,
        PictureItem(
            image_path=test_img_path,
            work_type="공통공사",
            location="현장사무실",
            content="기초콘크리트 타설",
            date_str="2026.04"
        )
    ]
    res_pdf = exporter_pdf.export(items, pdf_path, project_name=item.project_name)
    assert res_pdf is True and os.path.exists(pdf_path), "PDF 생성 실패"
    print(f"[OK] PDF 내보내기 성공 ({os.path.getsize(pdf_path)} bytes)")

    print("\n=== [5] ExcelExporter 테스트 ===")
    excel_path = "tests/output_test.xlsx"
    exporter_xl = ExcelExporter()
    res_xl = exporter_xl.export(items, excel_path, project_name=item.project_name)
    assert res_xl is True and os.path.exists(excel_path), "Excel 생성 실패"
    print(f"[OK] Excel 내보내기 성공 ({os.path.getsize(excel_path)} bytes)")

    print("\n>>> 모든 핵심 코어 테스트 통과! (Error Count: 0) <<<")

if __name__ == "__main__":
    run_tests()
