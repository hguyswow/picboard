# -*- coding: utf-8 -*-
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from datetime import datetime
import uuid

class CropMode(str, Enum):
    COVER = 'cover'      # 비율유지 꽉채우기
    FIT = 'fit'          # 비율유지 여백
    STRETCH = 'stretch'  # 늘임

class StampPosition(str, Enum):
    BOTTOM_RIGHT = 'bottom_right'
    BOTTOM_LEFT = 'bottom_left'
    TOP_RIGHT = 'top_right'
    TOP_LEFT = 'top_left'

@dataclass
class StampConfig:
    enabled: bool = True
    position: StampPosition = StampPosition.BOTTOM_RIGHT
    show_project: bool = False
    show_work_type: bool = True
    show_location: bool = True
    show_content: bool = True
    show_date: bool = True
    custom_text: str = ''
    font_size: int = 18
    text_color: str = '#FFFFFF'  # 스탬프 글자색
    bg_color: str = '#000000'    # 스탬프 배경색
    bg_alpha: float = 0.65       # 배경 투명도 (0.0 ~ 1.0, 0% 가능)
    border: bool = True
    hide_labels: bool = False    # 항목 라벨(제목: 공종:, 내용:, 일자: 등) 숨김 여부

@dataclass
class PictureItem:
    image_path: str
    folder_name: str = ''
    file_name: str = ''
    project_name: str = ''
    work_type: str = ''
    location: str = ''
    content: str = ''
    stamp_content: str = ''      # 스탬프 표시용 요약/키워드 (비어있으면 content로 자동 대체)
    date_str: str = ''
    custom1: str = ''            # 사용자 정의 속성 1 (예: 검측부위, 설계두께 등)
    custom2: str = ''            # 사용자 정의 속성 2 (예: 실측치, 비고 등)
    date_source: str = 'exif'
    exif_date: Optional[datetime] = None
    file_date: Optional[datetime] = None
    rotation: int = 0            # 회전 각도: 0, 90, 180, 270
    padding: int = 0             # 사진 여백: 0 ~ 40px
    crop_mode: CropMode = CropMode.COVER
    stamp_enabled: bool = True
    stamp_config: StampConfig = field(default_factory=StampConfig)
    item_id: str = field(default_factory=lambda: str(uuid.uuid4()))
