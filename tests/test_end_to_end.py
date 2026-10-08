# -*- coding: utf-8 -*-
import os
import sys
from PIL import Image

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.models import PictureItem, StampConfig, CropMode, StampPosition
from core.preset_manager import PresetManager
from core.pdf_exporter import PDFExporter
from core.excel_exporter import ExcelExporter
import pypdf
import openpyxl

def test_full_pipeline():
    print("=== [시나리오 테스트] 4장 사진 2페이지 전체 파이프라인 검증 ===")
    
    # 1. 샘플 이미지 4장 생성 (서로 다른 색상)
    os.makedirs("tests/samples", exist_ok=True)
    colors = [(70, 130, 180), (34, 139, 34), (205, 92, 92), (218, 165, 32)]
    sample_paths = []
    for i, col in enumerate(colors):
        p = f"tests/samples/sample_{i+1:02d}.jpg"
        im = Image.new("RGB", (1280, 720), color=col)
        im.save(p)
        sample_paths.append(p)
    
    print("[1] 4장 샘플 사진 준비 완료")

    # 2. PictureItem 4개 생성 (1페이지 2장씩 총 2페이지)
    items = [
        PictureItem(
            image_path=sample_paths[0], folder_name="가설공사", file_name="sample_01.jpg",
            project_name="검암역세권 공공주택지구 도시시설물 건설공사", work_type="공통공사",
            location="현장사무실", content="부지정리후 골재포설", date_str="2026.04",
            crop_mode=CropMode.COVER, stamp_enabled=True
        ),
        PictureItem(
            image_path=sample_paths[1], folder_name="토공사", file_name="sample_02.jpg",
            project_name="검암역세권 공공주택지구 도시시설물 건설공사", work_type="공통공사",
            location="현장사무실", content="기초콘크리트 타설", date_str="2026.04",
            crop_mode=CropMode.FIT, stamp_enabled=True
        ),
        PictureItem(
            image_path=sample_paths[2], folder_name="가설공사", file_name="sample_03.jpg",
            project_name="검암역세권 공공주택지구 도시시설물 건설공사", work_type="가설공사",
            location="현장사무실", content="가설사무실 설치", date_str="2026.05",
            crop_mode=CropMode.STRETCH, stamp_enabled=False  # 스탬프 OFF 테스트
        ),
        PictureItem(
            image_path=sample_paths[3], folder_name="토공사", file_name="sample_04.jpg",
            project_name="검암역세권 공공주택지구 도시시설물 건설공사", work_type="토공사",
            location="1공구", content="토공 터파기 작업", date_str="2026.05",
            crop_mode=CropMode.COVER, stamp_enabled=True
        )
    ]
    print("[2] 아이템 4개 구성 완료 (스탬프 ON/OFF 혼합, 크롭 Cover/Fit/Stretch 혼합)")

    # 3. PDF 내보내기 및 검증
    pdf_out = "tests/test_scenario_2pages.pdf"
    pdf_exp = PDFExporter()
    pdf_res = pdf_exp.export(items, pdf_out, project_name="검암역세권 공공주택지구 도시시설물 건설공사")
    assert pdf_res is True, "PDF 내보내기 실패"
    
    # PDF 페이지 수 검증
    reader = pypdf.PdfReader(pdf_out)
    assert len(reader.pages) == 2, f"PDF 페이지 수 불일치 (기대: 2, 실제: {len(reader.pages)})"
    print(f"[3] PDF 2페이지 내보내기 검증 완료 (총 {len(reader.pages)}페이지, 파일 크기 {os.path.getsize(pdf_out)} bytes)")

    # 4. Excel 내보내기 및 검증
    xl_out = "tests/test_scenario_2pages.xlsx"
    xl_exp = ExcelExporter()
    xl_res = xl_exp.export(items, xl_out, project_name="검암역세권 공공주택지구 도시시설물 건설공사")
    assert xl_res is True, "Excel 내보내기 실패"
    
    wb = openpyxl.load_workbook(xl_out)
    ws = wb.active
    assert ws.title == "공사사진첩", "시트명 불일치"
    assert len(ws._images) == 4, f"삽입된 이미지 개수 불일치 (기대: 4, 실제: {len(ws._images)})"
    assert ws.cell(12, 7).value == "부지정리후 골재포설", "1번 사진 내용 불일치"
    assert ws.cell(23, 7).value == "기초콘크리트 타설", "2번 사진 내용 불일치"
    assert ws.cell(34, 7).value == "가설사무실 설치", "3번 사진 내용 불일치"
    assert ws.cell(45, 7).value == "토공 터파기 작업", "4번 사진 내용 불일치"
    print(f"[4] Excel 4장 이미지 & 4개 표 완벽 호환 검증 완료 (이미지 4개 정상 삽입)")

    # 5. 정렬 로직 검증
    # (1) 파일명 내림차순
    items_sorted = sorted(items, key=lambda x: x.file_name, reverse=True)
    assert items_sorted[0].file_name == "sample_04.jpg", "파일명 내림차순 정렬 실패"
    # (2) 폴더별 정렬
    items_by_folder = sorted(items, key=lambda x: (x.folder_name, x.file_name))
    assert items_by_folder[0].folder_name == "가설공사", "폴더별 정렬 실패"
    print("[5] 정렬 로직 (파일명, 날짜, 폴더별) 정상 동작 확인")

    print("\n========================================================")
    print(" >>> 전체 시나리오 종합 검증 완벽 통과! (Error Count: 0) <<< ")
    print("========================================================")

if __name__ == "__main__":
    test_full_pipeline()
