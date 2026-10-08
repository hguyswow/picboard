# -*- coding: utf-8 -*-
import os
import sys
import tempfile

try:
    sys.stdout.reconfigure(encoding="utf-8")
    sys.stderr.reconfigure(encoding="utf-8")
except Exception:
    pass

from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.models import PictureItem, StampConfig, CropMode, StampPosition
from core.image_processor import process_picture, render_stamp
from core.pdf_exporter import PDFExporter
from core.excel_exporter import ExcelExporter

def test_separation_and_fallback():
    print("=== 1. 스탬프 분리 및 Fallback 단위 테스트 ===")
    
    # 1. 임시 테스트 이미지 생성
    temp_dir = tempfile.mkdtemp()
    img_path = os.path.join(temp_dir, "test.jpg")
    img = Image.new("RGB", (800, 600), color=(100, 150, 200))
    img.save(img_path)

    # 2. 케이스 A: stamp_content가 지정된 경우
    item_a = PictureItem(
        image_path=img_path,
        work_type="토공사",
        location="STA. 0+120",
        content="신호수 배치 및 안전통로 확보 후 기초 터파기 작업 진행 확인",
        stamp_content="신호수 및 터파기",
        date_str="2026.04.15",
        stamp_enabled=True,
        stamp_config=StampConfig(enabled=True, show_content=True)
    )

    # 스탬프 렌더링
    res_a = process_picture(item_a, 800, 600)
    assert res_a is not None, "Case A: process_picture failed"
    print("[OK] Case A (stamp_content 지정): 스탬프 합성 성공")

    # 3. 케이스 B: stamp_content가 비어있는 경우 (Fallback 테스트)
    item_b = PictureItem(
        image_path=img_path,
        work_type="구조물공",
        location="교대 1",
        content="벽체 철근 배근 간격 확인",
        stamp_content="",  # 비어있음
        date_str="2026.04.16",
        stamp_enabled=True,
        stamp_config=StampConfig(enabled=True, show_content=True)
    )

    res_b = process_picture(item_b, 800, 600)
    assert res_b is not None, "Case B: process_picture fallback failed"
    print("[OK] Case B (stamp_content 공백 Fallback): 스탬프 합성 성공")

    # 4. PDF 내보내기 검증
    print("=== 2. PDF 내보내기 연동 테스트 ===")
    pdf_path = os.path.join(temp_dir, "test_out.pdf")
    pdf_exporter = PDFExporter()
    pdf_ok = pdf_exporter.export([item_a, item_b], pdf_path, project_name="스탬프분리테스트")
    assert pdf_ok and os.path.exists(pdf_path) and os.path.getsize(pdf_path) > 0, "PDF export failed"
    print(f"[OK] PDF 정상 생성: {os.path.getsize(pdf_path):,} bytes")

    # 5. Excel 내보내기 검증
    print("=== 3. Excel 내보내기 연동 테스트 ===")
    excel_path = os.path.join(temp_dir, "test_out.xlsx")
    excel_exporter = ExcelExporter()
    excel_ok = excel_exporter.export([item_a, item_b], excel_path, project_name="스탬프분리테스트")
    assert excel_ok and os.path.exists(excel_path) and os.path.getsize(excel_path) > 0, "Excel export failed"
    print(f"[OK] Excel 정상 생성: {os.path.getsize(excel_path):,} bytes")

    # 정리
    import shutil
    shutil.rmtree(temp_dir, ignore_errors=True)
    print("=== 모든 스탬프 분리 및 내보내기 테스트 100% 통과 (Error Count: 0) ===")

if __name__ == "__main__":
    test_separation_and_fallback()
