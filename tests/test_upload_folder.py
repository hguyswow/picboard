# -*- coding: utf-8 -*-
"""
폴더 업로드(상대경로 포함 파일명) 방어 검증 테스트
"""
import os
import sys
import io
from PIL import Image

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.testclient import TestClient
from server import app

client = TestClient(app)

def create_dummy_image_bytes():
    buf = io.BytesIO()
    img = Image.new("RGB", (100, 100), color=(255, 0, 0))
    img.save(buf, format="JPEG")
    return buf.getvalue()

def test_folder_upload_with_subpaths():
    img_data = create_dummy_image_bytes()
    
    # 브라우저 webkitdirectory 전송 시뮬레이션:
    # 1. 1단계 폴더 경로: "점검사진/KakaoTalk_20260706_140921920_04.jpg"
    # 2. 윈도우 역슬래시 혼용: "현장사진\\기초공사\\IMG_001.jpg"
    # 3. 3단계 중첩 경로: "2026공사/토목/배수/drain_01.png"
    # 4. 순수 파일명: "single_photo.jpg"
    files = [
        ("files", ("점검사진/KakaoTalk_20260706_140921920_04.jpg", io.BytesIO(img_data), "image/jpeg")),
        ("files", ("현장사진\\기초공사\\IMG_001.jpg", io.BytesIO(img_data), "image/jpeg")),
        ("files", ("2026공사/토목/배수/drain_01.png", io.BytesIO(img_data), "image/png")),
        ("files", ("single_photo.jpg", io.BytesIO(img_data), "image/jpeg")),
    ]
    
    response = client.post("/api/upload", data={"folder_name": ""}, files=files)
    assert response.status_code == 200, f"Upload failed with {response.status_code}: {response.text}"
    
    data = response.json()
    assert len(data) == 4, f"Expected 4 items, got {len(data)}"
    
    # 1번 아이템 검증
    item1 = data[0]
    assert item1["filename"] == "KakaoTalk_20260706_140921920_04.jpg"
    assert item1["folder_name"] == "점검사진"
    assert os.path.exists(item1["server_path"])
    
    # 2번 아이템 검증
    item2 = data[1]
    assert item2["filename"] == "IMG_001.jpg"
    assert item2["folder_name"] == "현장사진"
    assert os.path.exists(item2["server_path"])
    
    # 3번 아이템 검증
    item3 = data[2]
    assert item3["filename"] == "drain_01.png"
    assert item3["folder_name"] == "2026공사"
    assert os.path.exists(item3["server_path"])
    
    # 4번 아이템 검증
    item4 = data[3]
    assert item4["filename"] == "single_photo.jpg"
    assert item4["folder_name"] == "기본폴더"
    assert os.path.exists(item4["server_path"])
    
    print(">>> [OK] 폴더 업로드 상대경로 방어 테스트 100% 성공! (Error Count: 0) <<<")

if __name__ == "__main__":
    test_folder_upload_with_subpaths()
