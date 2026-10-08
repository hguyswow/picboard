# -*- coding: utf-8 -*-
import os
import sys
import json
import tempfile
import unittest

sys.stdout.reconfigure(encoding='utf-8')
sys.stderr.reconfigure(encoding='utf-8')
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

class TestUiSettingsPersistence(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_user_settings.json")

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_default_when_missing(self):
        from server import load_user_settings
        data = load_user_settings()
        self.assertIn("ui_mode", data)
        self.assertIn("custom_ui", data)

    def test_save_and_reload(self):
        # 1. Easy 모드 저장
        sample_easy = {"ui_mode": "easy", "custom_ui": {}}
        with open(self.test_file, "w", encoding="utf-8") as f:
            json.dump(sample_easy, f, ensure_ascii=False, indent=2)

        with open(self.test_file, "r", encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded["ui_mode"], "easy")

        # 2. Custom 모드 및 체크박스 상태 저장
        sample_custom = {
            "ui_mode": "custom",
            "custom_ui": {
                "folder": True,
                "paste": False,
                "dateExtract": True,
                "presets": False,
                "tableSettings": True
            }
        }
        with open(self.test_file, "w", encoding="utf-8") as f:
            json.dump(sample_custom, f, ensure_ascii=False, indent=2)

        with open(self.test_file, "r", encoding="utf-8") as f:
            loaded_custom = json.load(f)
        self.assertEqual(loaded_custom["ui_mode"], "custom")
        self.assertTrue(loaded_custom["custom_ui"]["folder"])
        self.assertFalse(loaded_custom["custom_ui"]["paste"])
        self.assertTrue(loaded_custom["custom_ui"]["tableSettings"])

        # 3. Expert 모드 저장
        sample_expert = {"ui_mode": "expert", "custom_ui": {}}
        with open(self.test_file, "w", encoding="utf-8") as f:
            json.dump(sample_expert, f, ensure_ascii=False, indent=2)

        with open(self.test_file, "r", encoding="utf-8") as f:
            loaded_expert = json.load(f)
        self.assertEqual(loaded_expert["ui_mode"], "expert")

if __name__ == "__main__":
    unittest.main()
