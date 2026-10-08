# -*- coding: utf-8 -*-
import os
import json
from typing import List, Dict

PRESETS_FILE = "presets.json"

DEFAULT_PRESETS = {
    "work_types": [
        "공통공사", "가설공사", "토공사", "철근콘크리트공사", "포장공사", 
        "배수공사", "구조물공사", "부대토목공사", "조경공사", "안전시설공사"
    ],
    "locations": [
        "현장사무실", "1공구", "2공구", "진입도로", "주차장 부지", 
        "STA.0+000 ~ 0+100", "STA.0+100 ~ 0+200", "절토부", "성토부"
    ],
    "contents": [
        "부지정리후 골재포설", "기초콘크리트 타설", "가설사무실 설치", 
        "토공 터파기 작업", "되메우기 및 다짐", "배수관 부설 및 접합", 
        "철근 배근 검측", "콘크리트 타설 전경", "아스콘 포장 시공", "안전 펜스 설치"
    ],
    "combos": [
        {"title": "골재포설", "work_type": "공통공사", "location": "현장사무실", "content": "부지정리후 골재포설"},
        {"title": "기초타설", "work_type": "공통공사", "location": "현장사무실", "content": "기초콘크리트 타설"},
        {"title": "가설사무실", "work_type": "공통공사", "location": "현장사무실", "content": "가설사무실 설치"},
        {"title": "토공터파기", "work_type": "토공사", "location": "1공구", "content": "토공 터파기 작업"}
    ]
}

class PresetManager:
    def __init__(self, filepath: str = PRESETS_FILE):
        self.filepath = filepath
        self.data = self.load_presets()

    def load_presets(self) -> Dict:
        if os.path.exists(self.filepath):
            try:
                with open(self.filepath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    # 기본 키 누락 방어
                    for k, v in DEFAULT_PRESETS.items():
                        if k not in data:
                            data[k] = v
                    return data
            except Exception as e:
                print(f"프리셋 로드 에러 (기본값 사용): {e}")
        return json.loads(json.dumps(DEFAULT_PRESETS))

    def save_presets(self):
        try:
            with open(self.filepath, "w", encoding="utf-8") as f:
                json.dump(self.data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"프리셋 저장 실패: {e}")

    def get_work_types(self) -> List[str]:
        return self.data.get("work_types", [])

    def get_locations(self) -> List[str]:
        return self.data.get("locations", [])

    def get_contents(self) -> List[str]:
        return self.data.get("contents", [])

    def get_combos(self) -> List[Dict]:
        return self.data.get("combos", [])

    def add_work_type(self, val: str):
        val = val.strip()
        if val and val not in self.data["work_types"]:
            self.data["work_types"].append(val)
            self.save_presets()

    def add_location(self, val: str):
        val = val.strip()
        if val and val not in self.data["locations"]:
            self.data["locations"].append(val)
            self.save_presets()

    def add_content(self, val: str):
        val = val.strip()
        if val and val not in self.data["contents"]:
            self.data["contents"].append(val)
            self.save_presets()

    def add_combo(self, title: str, work_type: str, location: str, content: str):
        combo = {
            "title": title.strip() or f"{work_type}_{content}"[:15],
            "work_type": work_type.strip(),
            "location": location.strip(),
            "content": content.strip()
        }
        self.data["combos"].append(combo)
        self.save_presets()

    def delete_combo(self, index: int):
        if 0 <= index < len(self.data["combos"]):
            self.data["combos"].pop(index)
            self.save_presets()
