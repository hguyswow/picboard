import unittest
import os
import sys
import tempfile

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from PIL import Image
from core.models import PictureItem
from core.pdf_exporter import PDFExporter
from core.excel_exporter import ExcelExporter

class TestCustomTableFeatures(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.temp_dir = tempfile.mkdtemp()
        # Create dummy image
        cls.img_path = os.path.join(cls.temp_dir, "test_table_img.jpg")
        img = Image.new("RGB", (800, 600), color=(100, 150, 200))
        img.save(cls.img_path, "JPEG")

    def _create_sample_item(self):
        return PictureItem(
            image_path=self.img_path,
            file_name="test_table_img.jpg",
            work_type="토공사",
            location="STA. 10+20",
            content="터파기 및 면정리 완료",
            custom1="설계두께 150mm",
            custom2="실측치 152mm (합격)",
            date_str="2026.09.18",
            crop_mode="cover"
        )

    def test_preset_1_row_1_item(self):
        """1개 항목 (1줄 모드): 전폭 병합 테스트"""
        cfg = {
            "row_count": 1,
            "fields": [
                {"key": "content", "label": "내용", "enabled": True}
            ]
        }
        item = self._create_sample_item()
        
        # PDF 테스트
        pdf_out = os.path.join(self.temp_dir, "out_1item.pdf")
        pdf_exp = PDFExporter()
        pdf_exp.export([item], pdf_out, project_name="1개항목 테스트", table_config=cfg)
        self.assertTrue(os.path.exists(pdf_out))
        self.assertGreater(os.path.getsize(pdf_out), 10000)

        # Excel 테스트
        xls_out = os.path.join(self.temp_dir, "out_1item.xlsx")
        xls_exp = ExcelExporter()
        xls_exp.export([item], xls_out, project_name="1개항목 테스트", table_config=cfg)
        self.assertTrue(os.path.exists(xls_out))
        self.assertGreater(os.path.getsize(xls_out), 5000)

    def test_preset_1_row_2_items(self):
        """2개 항목 (1줄 모드): 50:50 분할 테스트"""
        cfg = {
            "row_count": 1,
            "fields": [
                {"key": "work_type", "label": "공종", "enabled": True},
                {"key": "content", "label": "내용", "enabled": True}
            ]
        }
        item = self._create_sample_item()

        pdf_out = os.path.join(self.temp_dir, "out_2items.pdf")
        PDFExporter().export([item], pdf_out, project_name="2개항목 테스트", table_config=cfg)
        self.assertTrue(os.path.exists(pdf_out))

        xls_out = os.path.join(self.temp_dir, "out_2items.xlsx")
        ExcelExporter().export([item], xls_out, project_name="2개항목 테스트", table_config=cfg)
        self.assertTrue(os.path.exists(xls_out))

    def test_preset_2_rows_3_items(self):
        """3개 항목 (2줄 모드): 1행 50:50, 2행 전폭 병합 테스트"""
        cfg = {
            "row_count": 2,
            "fields": [
                {"key": "work_type", "label": "공종", "enabled": True},
                {"key": "date_str", "label": "촬영일자", "enabled": True},
                {"key": "content", "label": "설명 및 조치", "enabled": True}
            ]
        }
        item = self._create_sample_item()

        pdf_out = os.path.join(self.temp_dir, "out_3items.pdf")
        PDFExporter().export([item], pdf_out, project_name="3개항목 테스트", table_config=cfg)
        self.assertTrue(os.path.exists(pdf_out))

        xls_out = os.path.join(self.temp_dir, "out_3items.xlsx")
        ExcelExporter().export([item], xls_out, project_name="3개항목 테스트", table_config=cfg)
        self.assertTrue(os.path.exists(xls_out))

    def test_preset_2_rows_4_items_with_custom_fields(self):
        """4개 항목 (2줄 모드) + 커스텀 필드(custom1, custom2) 및 자유 라벨명 테스트"""
        cfg = {
            "row_count": 2,
            "fields": [
                {"key": "work_type", "label": "세부공종", "enabled": True},
                {"key": "custom1", "label": "설계기준", "enabled": True},
                {"key": "custom2", "label": "검측결과", "enabled": True},
                {"key": "date_str", "label": "검측일시", "enabled": True}
            ]
        }
        item = self._create_sample_item()

        pdf_out = os.path.join(self.temp_dir, "out_custom_4items.pdf")
        PDFExporter().export([item], pdf_out, project_name="커스텀속성 테스트", table_config=cfg)
        self.assertTrue(os.path.exists(pdf_out))

        xls_out = os.path.join(self.temp_dir, "out_custom_4items.xlsx")
        ExcelExporter().export([item], xls_out, project_name="커스텀속성 테스트", table_config=cfg)
        self.assertTrue(os.path.exists(xls_out))

    def test_api_table_settings(self):
        """서버 /api/table_settings GET 및 POST 통신 무결성 테스트"""
        from fastapi.testclient import TestClient
        from server import app

        client = TestClient(app)
        test_payload = {
            "row_count": 1,
            "fields": [
                {"key": "content", "label": "점검내용", "enabled": True}
            ]
        }
        # POST
        res = client.post("/api/table_settings", json=test_payload)
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.json(), {"status": "ok"})

        # GET
        res = client.get("/api/table_settings")
        self.assertEqual(res.status_code, 200)
        saved = res.json()
        self.assertIsNotNone(saved)
        self.assertEqual(saved.get("row_count"), 1)
        self.assertEqual(saved["fields"][0]["label"], "점검내용")

if __name__ == "__main__":
    unittest.main()
