# -*- coding: utf-8 -*-
import os
from datetime import datetime
from PIL import Image, ImageDraw, ImageFont, ImageOps
from core.models import PictureItem, StampConfig, CropMode, StampPosition

try:
    import pillow_heif
    pillow_heif.register_heif_opener()
except ImportError:
    pass

FONT_PATH = "C:/Windows/Fonts/malgun.ttf"
FONT_BOLD_PATH = "C:/Windows/Fonts/malgunbd.ttf"

def get_font(size: int, bold: bool = False):
    font_file = FONT_BOLD_PATH if bold else FONT_PATH
    if os.path.exists(font_file):
        try:
            return ImageFont.truetype(font_file, size)
        except Exception:
            pass
    return ImageFont.load_default()

def extract_metadata(image_path: str):
    exif_dt = None
    mtime_dt = None
    ctime_dt = None
    
    try:
        if os.path.exists(image_path):
            stat = os.stat(image_path)
            mtime_dt = datetime.fromtimestamp(stat.st_mtime)
            ctime_dt = datetime.fromtimestamp(stat.st_ctime)
    except Exception:
        pass

    try:
        with Image.open(image_path) as img:
            exif = img.getexif()
            if exif:
                dt_str = None
                for tag in (36867, 36868, 306):
                    val = exif.get(tag)
                    if val and isinstance(val, str):
                        dt_str = val
                        break
                if dt_str:
                    try:
                        exif_dt = datetime.strptime(dt_str[:19], "%Y:%m:%d %H:%M:%S")
                    except Exception:
                        pass
    except Exception:
        pass

    return exif_dt, mtime_dt, ctime_dt

def format_date(dt: datetime, date_format: str = "YYYY.MM.DD") -> str:
    """기본 날짜 포맷: YYYY.MM.DD (일자까지 필수 표시)"""
    if not dt:
        return ""
    if date_format == "YYYY.MM.DD":
        return dt.strftime("%Y.%m.%d")
    elif date_format == "YYYY-MM-DD":
        return dt.strftime("%Y-%m-%d")
    elif date_format == "YYYY.MM":
        return dt.strftime("%Y.%m")
    elif date_format == "YYYY년 MM월 DD일":
        return dt.strftime("%Y년 %m월 %d일")
    elif date_format == "YYYY년 MM월":
        return dt.strftime("%Y년 %m월")
    else:
        return dt.strftime("%Y.%m.%d")

def load_oriented_image(image_path: str) -> Image.Image:
    img = Image.open(image_path)
    try:
        img = ImageOps.exif_transpose(img)
    except Exception:
        pass
    return img.convert("RGB")

def apply_crop(img: Image.Image, target_w: int, target_h: int, mode: CropMode) -> Image.Image:
    orig_w, orig_h = img.size
    
    if mode == CropMode.STRETCH:
        return img.resize((target_w, target_h), Image.Resampling.LANCZOS)
        
    elif mode == CropMode.FIT:
        scale = min(target_w / orig_w, target_h / orig_h)
        nw = int(orig_w * scale)
        nh = int(orig_h * scale)
        resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
        
        canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
        offset_x = (target_w - nw) // 2
        offset_y = (target_h - nh) // 2
        canvas.paste(resized, (offset_x, offset_y))
        return canvas
        
    else:  # CropMode.COVER
        scale = max(target_w / orig_w, target_h / orig_h)
        nw = int(orig_w * scale)
        nh = int(orig_h * scale)
        resized = img.resize((nw, nh), Image.Resampling.LANCZOS)
        
        left = (nw - target_w) // 2
        top = (nh - target_h) // 2
        return resized.crop((left, top, left + target_w, top + target_h))

def render_stamp(img: Image.Image, item: PictureItem, config: StampConfig = None) -> Image.Image:
    cfg = config or item.stamp_config
    if not item.stamp_enabled or not cfg.enabled:
        return img

    lines = []
    hide_labels = getattr(cfg, 'hide_labels', False)

    if cfg.show_project:
        val = item.project_name or ''
        if hide_labels:
            if val: lines.append(val)
        else:
            lines.append(f"공사명 : {val}")

    if cfg.show_work_type:
        val = item.work_type or ''
        if hide_labels:
            if val: lines.append(val)
        else:
            lines.append(f"공  종 : {val}")

    if cfg.show_location:
        val = item.location or ''
        if hide_labels:
            if val: lines.append(val)
        else:
            lines.append(f"위  치 : {val}")

    if cfg.show_content:
        # 스탬프 요약문(stamp_content)이 있으면 우선 사용하고, 없으면 상세 설명(content)으로 자동 fallback
        val = getattr(item, 'stamp_content', '') or item.content or ''
        if hide_labels:
            if val: lines.append(val)
        else:
            lines.append(f"내  용 : {val}")

    if cfg.show_date:
        val = item.date_str or ''
        if hide_labels:
            if val: lines.append(val)
        else:
            lines.append(f"일  자 : {val}")

    if cfg.custom_text:
        lines.append(cfg.custom_text)

    if not lines:
        return img

    base = img.convert("RGBA")
    overlay = Image.new("RGBA", base.size, (255, 255, 255, 0))
    draw = ImageDraw.Draw(overlay)

    font_size = max(14, int(cfg.font_size * (base.width / 1000.0)))
    font = get_font(font_size, bold=True)
    
    line_spacings = int(font_size * 0.35)
    max_line_w = 0
    total_text_h = 0
    line_dims = []
    for line in lines:
        bbox = draw.textbbox((0, 0), line, font=font)
        lw = bbox[2] - bbox[0]
        lh = bbox[3] - bbox[1]
        line_dims.append((lw, lh))
        max_line_w = max(max_line_w, lw)
        total_text_h += lh

    total_text_h += line_spacings * (len(lines) - 1)
    
    pad_x = int(font_size * 0.8)
    pad_y = int(font_size * 0.6)
    box_w = max_line_w + (pad_x * 2)
    box_h = total_text_h + (pad_y * 2)

    margin = int(font_size * 0.8)
    
    pos = cfg.position
    if pos == StampPosition.BOTTOM_RIGHT:
        bx = base.width - box_w - margin
        by = base.height - box_h - margin
    elif pos == StampPosition.BOTTOM_LEFT:
        bx = margin
        by = base.height - box_h - margin
    elif pos == StampPosition.TOP_RIGHT:
        bx = base.width - box_w - margin
        by = margin
    else:  # TOP_LEFT
        bx = margin
        by = margin

    # 배경 투명도 (0.0 ~ 1.0)
    alpha = int(255 * max(0.0, min(1.0, cfg.bg_alpha)))
    bg_hex = (cfg.bg_color or "#000000").lstrip("#")
    if len(bg_hex) == 6:
        bg_rgb = tuple(int(bg_hex[i:i+2], 16) for i in (0, 2, 4))
    else:
        bg_rgb = (0, 0, 0)
    bg_rgba = (*bg_rgb, alpha)

    # 0% 투명도가 아닐 때만 배경 박스 렌더링
    if alpha > 0:
        draw.rounded_rectangle(
            [bx, by, bx + box_w, by + box_h],
            radius=6,
            fill=bg_rgba,
            outline=(255, 255, 255, min(200, int(alpha * 1.5))) if cfg.border else None,
            width=2
        )
    elif cfg.border:
        # 배경 투명이어도 테두리만 있는 경우
        draw.rounded_rectangle([bx, by, bx + box_w, by + box_h], radius=6, outline=(255, 255, 255, 180), width=1)

    # 글자색
    txt_col = cfg.text_color or "#FFFFFF"

    curr_y = by + pad_y
    for i, line in enumerate(lines):
        lx = bx + pad_x
        # 투명 배경일 때 가독성을 위한 약한 텍스트 그림자
        if alpha < 50:
            draw.text((lx + 1, curr_y + 1), line, fill=(0, 0, 0, 180), font=font)
        draw.text((lx, curr_y), line, fill=txt_col, font=font)
        curr_y += line_dims[i][1] + line_spacings

    combined = Image.alpha_composite(base, overlay)
    return combined.convert("RGB")

def process_picture(item: PictureItem, target_w: int = 1600, target_h: int = 1000) -> Image.Image:
    """회전 -> 여백(Padding) -> 크롭 -> 스탬프 합성의 전체 파이프라인"""
    img = load_oriented_image(item.image_path)
    
    # 1. 수동 회전 적용 (90, 180, 270도)
    if hasattr(item, "rotation") and item.rotation % 360 != 0:
        rot = item.rotation % 360
        # PIL rotate는 반시계방향이 기본이므로 시계방향을 위해 360 - rot 또는 -rot
        img = img.rotate(360 - rot, expand=True)

    # 2. 여백(Padding) 계산
    pad = getattr(item, "padding", 0)
    if pad > 0:
        inner_w = max(10, target_w - (pad * 2))
        inner_h = max(10, target_h - (pad * 2))
        inner_cropped = apply_crop(img, inner_w, inner_h, item.crop_mode)
        
        # 흰색 배경에 패딩을 두고 중앙 배치
        padded_canvas = Image.new("RGB", (target_w, target_h), (255, 255, 255))
        padded_canvas.paste(inner_cropped, (pad, pad))
        final_img = render_stamp(padded_canvas, item)
    else:
        cropped = apply_crop(img, target_w, target_h, item.crop_mode)
        final_img = render_stamp(cropped, item)

    return final_img
