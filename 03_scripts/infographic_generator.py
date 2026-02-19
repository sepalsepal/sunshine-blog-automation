#!/usr/bin/env python3
"""
infographic_generator.py - Pillow 기반 C2 인포그래픽 생성기
v3.1 - §22 안전도 분기 규칙 적용

§22.1 안전도 ENUM 고정: SAFE / CAUTION / DANGER / FORBIDDEN
§22.3 템플릿 물리적 분리 (함수 단위)
§22.10 템플릿별 color_config 물리적 분리
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from enum import Enum
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# =============================================================================
# §22.9 Safety ENUM 정의
# =============================================================================
class Safety(Enum):
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    DANGER = "DANGER"
    FORBIDDEN = "FORBIDDEN"


def safety_validate(safety_value: str) -> Safety:
    """§22.2 안전도 검증 - 실패 시 예외 발생"""
    try:
        return Safety(safety_value.upper())
    except ValueError:
        raise ValueError(f"§22.1 위반: 허용되지 않은 안전도 값 '{safety_value}'. 허용값: SAFE/CAUTION/DANGER/FORBIDDEN")


# =============================================================================
# §22.10 템플릿별 팔레트 물리적 분리
# =============================================================================
SAFE_PALETTE = {
    "header_gradient": [(129, 199, 191), (180, 220, 215)],  # 민트
    "title": "#2D8B7F",
    "badge": "#4CAF50",
    "badge_bg": "#4CAF50",
    "accent": "#2E7D32",
    "box_do": "#E8F5E9",
    "box_dont": "#FCE4EC",
    "text_positive": "#4CAF50",
    "text_negative": "#E74C3C",
}

CAUTION_PALETTE = {
    "header_gradient": [(235, 180, 130), (240, 200, 160)],  # 주황/피치
    "title": "#E67E22",
    "badge": "#FF9800",
    "badge_bg": "#FF9800",
    "accent": "#E65100",
    "box_do": "#FFF3E0",
    "box_dont": "#FCE4EC",
    "text_positive": "#FF9800",
    "text_negative": "#E74C3C",
}

DANGER_PALETTE = {
    "header_gradient": [(255, 120, 80), (255, 150, 110)],  # 딥 오렌지
    "title": "#E64A19",
    "badge": "#FF5722",
    "badge_bg": "#FF5722",
    "accent": "#BF360C",
    "box_do": "#FBE9E7",
    "box_dont": "#FFCCBC",
    "text_positive": "#FF5722",
    "text_negative": "#D84315",
}

FORBIDDEN_PALETTE = {
    "header_gradient": [(239, 83, 80), (229, 115, 115)],  # 빨강
    "title": "#C62828",
    "badge": "#D32F2F",
    "badge_bg": "#D32F2F",
    "accent": "#B71C1C",
    "box_warning": "#FFEBEE",
    "box_danger": "#FFCDD2",
    "text_danger": "#C62828",
}


def get_palette(safety: Safety) -> dict:
    """안전도에 따른 팔레트 반환"""
    if safety == Safety.SAFE:
        return SAFE_PALETTE
    elif safety == Safety.CAUTION:
        return CAUTION_PALETTE
    elif safety == Safety.DANGER:
        return DANGER_PALETTE
    else:  # FORBIDDEN
        return FORBIDDEN_PALETTE


# 공통 색상 (안전도 무관)
COMMON_COLORS = {
    "background": "#FFF8E7",
    "white": "#FFFFFF",
    "text_dark": "#333333",
    "text_gray": "#888888",
    "subtitle": "#666666",
    "value_orange": "#E67E22",
    "box_blue": "#E3F2FD",
    "box_yellow": "#FFF9C4",
    "footer_pink": "#FFEBEE",
}

CANVAS_SIZE = (1080, 1080)
FONT_PATHS = {
    "bold": "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "regular": "/System/Library/Fonts/AppleSDGothicNeo.ttc",
}
BADGE_COLORS = ["#FF9800", "#4CAF50", "#F44336", "#2196F3", "#9C27B0", "#FF5722"]
STEP_COLORS = ["#8BC34A", "#A5D6A7", "#FFEB3B", "#90CAF9", "#FFC107"]


# =============================================================================
# 공통 유틸리티 함수
# =============================================================================
def load_font(font_type: str, size: int) -> ImageFont.FreeTypeFont:
    """폰트 로드"""
    try:
        path = FONT_PATHS.get(font_type, FONT_PATHS["regular"])
        index = 6 if font_type == "bold" else 2
        return ImageFont.truetype(path, size, index=index)
    except Exception:
        return ImageFont.load_default()


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """HEX -> RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def draw_gradient_header(draw: ImageDraw.Draw, img: Image.Image,
                         colors: List[Tuple[int, int, int]], height: int = 130):
    """그라데이션 헤더"""
    for y in range(height):
        ratio = y / height
        r = int(colors[0][0] + (colors[1][0] - colors[0][0]) * ratio)
        g = int(colors[0][1] + (colors[1][1] - colors[0][1]) * ratio)
        b = int(colors[0][2] + (colors[1][2] - colors[0][2]) * ratio)
        for x in range(CANVAS_SIZE[0]):
            img.putpixel((x, y), (r, g, b))


def draw_rounded_badge(draw: ImageDraw.Draw, text: str, position: Tuple[int, int],
                       bg_color: str, text_color: str, font: ImageFont.FreeTypeFont,
                       padding_x: int = 20, padding_y: int = 8, radius: int = 15):
    """둥근 배지 그리기"""
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    x, y = position

    draw.rounded_rectangle(
        [x, y, x + text_width + padding_x * 2, y + text_height + padding_y * 2],
        radius=radius,
        fill=bg_color
    )
    draw.text((x + padding_x, y + padding_y), text, fill=text_color, font=font)
    return text_width + padding_x * 2


def draw_right_aligned_badge(draw: ImageDraw.Draw, text: str, y: int,
                              bg_color: str, text_color: str, font: ImageFont.FreeTypeFont,
                              right_margin: int = 40, padding_x: int = 20, padding_y: int = 8,
                              radius: int = 15):
    """우측 정렬 둥근 배지 그리기 (잘림 방지)"""
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    badge_width = text_width + padding_x * 2

    # 우측 마진을 고려하여 x 위치 계산
    x = CANVAS_SIZE[0] - badge_width - right_margin

    draw.rounded_rectangle(
        [x, y, x + badge_width, y + text_height + padding_y * 2],
        radius=radius,
        fill=bg_color
    )
    draw.text((x + padding_x, y + padding_y), text, fill=text_color, font=font)
    return badge_width


def draw_check_circle(draw: ImageDraw.Draw, position: Tuple[int, int],
                      font: ImageFont.FreeTypeFont, is_do: bool = True):
    """§15.10 준수: 원형 V/X 마크"""
    x, y = position
    radius = 14
    color = SAFE_PALETTE["badge"] if is_do else "#F44336"

    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)
    text = "V" if is_do else "X"
    draw.text((x - 6, y - 10), text, fill=COMMON_COLORS["white"], font=font)


def draw_number_badge(draw: ImageDraw.Draw, number: int, position: Tuple[int, int],
                      font: ImageFont.FreeTypeFont, color: str = None):
    """원형 번호 뱃지"""
    x, y = position
    radius = 25
    bg_color = color or BADGE_COLORS[(number - 1) % len(BADGE_COLORS)]

    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=bg_color)
    draw.text((x - 8, y - 15), str(number), fill=COMMON_COLORS["white"], font=font)


def draw_step_badge(draw: ImageDraw.Draw, step_num: int, position: Tuple[int, int],
                    font: ImageFont.FreeTypeFont):
    """STEP N 둥근 배지"""
    x, y = position
    text = f"STEP {step_num}"
    color = STEP_COLORS[(step_num - 1) % len(STEP_COLORS)]

    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]

    draw.rounded_rectangle(
        [x, y, x + text_width + 20, y + 32],
        radius=16,
        fill=color
    )
    draw.text((x + 10, y + 5), text, fill=COMMON_COLORS["white"], font=font)
    return text_width + 20


# =============================================================================
# §22.4 FORBIDDEN 차단 요소 검증
# =============================================================================
def validate_forbidden_content(data: Dict) -> None:
    """FORBIDDEN 생성 전 차단 요소 검증"""
    forbidden_elements = []

    if data.get("cooking_steps"):
        forbidden_elements.append("cooking_steps (조리방법)")
    if data.get("do_items"):
        forbidden_elements.append("do_items (DO 항목)")

    # 긍정적 단어 검사
    positive_words = ["안전", "좋아요", "급여 가능", "먹어도 돼"]
    for key, value in data.items():
        if isinstance(value, str):
            for word in positive_words:
                if word in value:
                    forbidden_elements.append(f"positive_word: '{word}' in {key}")

    if forbidden_elements:
        print(f"   ⚠️ FORBIDDEN 차단 요소 감지: {forbidden_elements}")
        # 경고만 출력, 생성은 계속 (데이터는 무시됨)


# =============================================================================
# SAFE/CAUTION 공통 템플릿 (§22.3 분리)
# =============================================================================
def generate_safe_nutrition_info(
    food_name: str,
    nutrients: List[Dict[str, str]],
    safety: Safety,
    footnote: str = "",
    output_path: Path = None
) -> Image.Image:
    """영양정보 인포그래픽 - SAFE/CAUTION용"""
    palette = get_palette(safety)

    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(COMMON_COLORS["background"]))
    draw = ImageDraw.Draw(img)

    fonts = {
        "title": load_font("bold", 55),
        "subtitle": load_font("regular", 22),
        "card_title": load_font("bold", 34),
        "card_desc": load_font("regular", 20),
        "value": load_font("bold", 40),
        "badge": load_font("bold", 22),
        "footer": load_font("regular", 16),
    }

    # 그라데이션 헤더
    draw_gradient_header(draw, img, palette["header_gradient"])

    # 제목
    title = f"{food_name} 영양성분"
    bbox = fonts["title"].getbbox(title)
    title_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - title_width) // 2, 35), title,
              fill=palette["title"], font=fonts["title"])

    # 부제목
    subtitle = "100g 기준 | 강아지에게 안전한 영양 간식"
    bbox = fonts["subtitle"].getbbox(subtitle)
    subtitle_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - subtitle_width) // 2, 95), subtitle,
              fill=COMMON_COLORS["subtitle"], font=fonts["subtitle"])

    # 안전도 배지 (우측 정렬, 잘림 방지)
    badge_text = safety.value
    draw_right_aligned_badge(draw, badge_text, 40,
                              palette["badge_bg"], COMMON_COLORS["white"], fonts["badge"])

    # 영양소 카드
    y_pos = 165
    card_height = 100
    margin = 55

    for i, nutrient in enumerate(nutrients[:6], 1):
        draw.rounded_rectangle(
            [margin, y_pos, CANVAS_SIZE[0] - margin, y_pos + card_height],
            radius=10, fill=COMMON_COLORS["box_blue"]
        )
        draw_number_badge(draw, i, (margin + 50, y_pos + card_height // 2), fonts["badge"])
        draw.text((margin + 95, y_pos + 20), nutrient["name"],
                  fill=COMMON_COLORS["text_dark"], font=fonts["card_title"])
        draw.text((margin + 95, y_pos + 58), nutrient.get("benefit", ""),
                  fill=COMMON_COLORS["text_gray"], font=fonts["card_desc"])

        value_text = f"{nutrient.get('value', '')} {nutrient.get('unit', '')}"
        bbox = fonts["value"].getbbox(value_text)
        value_width = bbox[2] - bbox[0]
        draw.text((CANVAS_SIZE[0] - margin - 25 - value_width, y_pos + 30),
                  value_text, fill=COMMON_COLORS["value_orange"], font=fonts["value"])

        y_pos += card_height + 12

    # 푸터
    if footnote:
        bbox = fonts["footer"].getbbox(footnote)
        footnote_width = bbox[2] - bbox[0]
        draw.text(((CANVAS_SIZE[0] - footnote_width) // 2, CANVAS_SIZE[1] - 55),
                  f"* {footnote}", fill=COMMON_COLORS["text_gray"], font=fonts["footer"])

    if output_path:
        img.save(output_path, "PNG")
        print(f"   [OK] 저장: {output_path}")

    return img


def generate_safe_do_dont(
    food_name: str,
    do_items: List[str],
    dont_items: List[str],
    safety: Safety,
    output_path: Path = None
) -> Image.Image:
    """급여 DO/DON'T 인포그래픽 - SAFE/CAUTION용"""
    palette = get_palette(safety)

    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(COMMON_COLORS["background"]))
    draw = ImageDraw.Draw(img)

    fonts = {
        "title": load_font("bold", 50),
        "section_title": load_font("bold", 26),
        "item": load_font("regular", 26),
        "badge": load_font("bold", 22),
        "check": load_font("bold", 16),
        "footer": load_font("regular", 20),
    }

    # 그라데이션 헤더
    draw_gradient_header(draw, img, palette["header_gradient"])

    # 안전도 배지 (상단 중앙)
    badge_text = safety.value
    badge_bbox = fonts["badge"].getbbox(badge_text)
    badge_width = badge_bbox[2] - badge_bbox[0] + 40
    badge_x = (CANVAS_SIZE[0] - badge_width) // 2

    draw.rounded_rectangle([badge_x, 30, badge_x + badge_width, 70],
                          radius=20, fill=COMMON_COLORS["white"])
    draw.text((badge_x + 20, 38), badge_text, fill=palette["badge"], font=fonts["badge"])

    # 메인 타이틀
    if safety == Safety.SAFE:
        title = "강아지가 먹어도 안전해요"
    else:
        title = "주의해서 급여하세요"

    bbox = fonts["title"].getbbox(title)
    title_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - title_width) // 2, 180), title,
              fill=COMMON_COLORS["text_dark"], font=fonts["title"])

    margin = 55
    item_spacing = 60

    # === DO 섹션 ===
    draw.text((margin + 10, 270), "이렇게 급여하세요",
              fill=palette["text_positive"], font=fonts["section_title"])

    do_box_y = 315
    do_box_height = item_spacing * min(len(do_items), 3) + 50
    draw.rounded_rectangle(
        [margin, do_box_y, CANVAS_SIZE[0] - margin, do_box_y + do_box_height],
        radius=15, fill=palette["box_do"]
    )

    y_pos = do_box_y + 30
    for item in do_items[:3]:
        draw_check_circle(draw, (margin + 35, y_pos + 12), fonts["check"], is_do=True)
        draw.text((margin + 60, y_pos), item, fill=COMMON_COLORS["text_dark"], font=fonts["item"])
        y_pos += item_spacing

    # === DON'T 섹션 ===
    dont_section_y = do_box_y + do_box_height + 50
    draw.text((margin + 10, dont_section_y), "이것만은 피해주세요",
              fill=palette["text_negative"], font=fonts["section_title"])

    dont_box_y = dont_section_y + 45
    dont_box_height = item_spacing * min(len(dont_items), 3) + 50
    draw.rounded_rectangle(
        [margin, dont_box_y, CANVAS_SIZE[0] - margin, dont_box_y + dont_box_height],
        radius=15, fill=palette["box_dont"]
    )

    y_pos = dont_box_y + 30
    for item in dont_items[:3]:
        draw_check_circle(draw, (margin + 35, y_pos + 12), fonts["check"], is_do=False)
        draw.text((margin + 60, y_pos), item, fill=COMMON_COLORS["text_dark"], font=fonts["item"])
        y_pos += item_spacing

    # 푸터
    footer_y = CANVAS_SIZE[1] - 120
    draw.rounded_rectangle(
        [margin, footer_y, CANVAS_SIZE[0] - margin, footer_y + 55],
        radius=10, fill=COMMON_COLORS["box_blue"]
    )
    footer_text = "11살 노령견 햇살이도 안전하게 먹고 있어요"
    bbox = fonts["footer"].getbbox(footer_text)
    footer_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - footer_width) // 2, footer_y + 15),
              footer_text, fill=COMMON_COLORS["value_orange"], font=fonts["footer"])

    if output_path:
        img.save(output_path, "PNG")
        print(f"   [OK] 저장: {output_path}")

    return img


def generate_safe_dosage_table(
    dosages: Dict[str, Dict[str, str]],
    warning_text: List[str] = None,
    footnote: str = "",
    safety: Safety = Safety.SAFE,
    output_path: Path = None
) -> Image.Image:
    """급여량표 인포그래픽 - SAFE/CAUTION용"""
    palette = get_palette(safety)

    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(COMMON_COLORS["background"]))
    draw = ImageDraw.Draw(img)

    fonts = {
        "title": load_font("bold", 55),
        "subtitle": load_font("regular", 22),
        "table_header": load_font("bold", 26),
        "dog_size": load_font("bold", 26),
        "weight": load_font("regular", 20),
        "amount": load_font("bold", 30),
        "desc": load_font("regular", 18),
        "warning": load_font("bold", 22),
        "warning_text": load_font("regular", 18),
        "footer": load_font("regular", 16),
    }

    # 그라데이션 헤더
    draw_gradient_header(draw, img, palette["header_gradient"])

    # 제목
    title = "체중별 급여량 가이드"
    bbox = fonts["title"].getbbox(title)
    title_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - title_width) // 2, 35), title,
              fill=palette["title"], font=fonts["title"])

    # 부제목
    subtitle = "하루 기준 | 간식으로 급여 시"
    bbox = fonts["subtitle"].getbbox(subtitle)
    subtitle_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - subtitle_width) // 2, 95), subtitle,
              fill=COMMON_COLORS["subtitle"], font=fonts["subtitle"])

    # 테이블
    margin = 100
    table_y = 165
    header_height = 50
    row_height = 85

    # 테이블 헤더
    header_color = palette["header_gradient"][0]
    draw.rounded_rectangle(
        [margin, table_y, CANVAS_SIZE[0] - margin, table_y + header_height],
        radius=10, fill=header_color
    )

    col_x = [margin + 50, margin + 220, margin + 420]
    headers = ["구분", "체중", "급여량"]
    for i, header in enumerate(headers):
        draw.text((col_x[i], table_y + 12), header, fill=COMMON_COLORS["white"], font=fonts["table_header"])

    # 테이블 행
    row_y = table_y + header_height + 15
    dog_sizes = ["소형견", "중형견", "대형견", "초대형견"]

    for size in dog_sizes:
        data = dosages.get(size, {})
        draw.text((col_x[0], row_y + 10), size, fill=COMMON_COLORS["text_dark"], font=fonts["dog_size"])
        draw.text((col_x[1], row_y + 15), data.get("weight", ""), fill=COMMON_COLORS["text_gray"], font=fonts["weight"])
        draw.text((col_x[2], row_y + 5), data.get("amount", ""), fill=COMMON_COLORS["value_orange"], font=fonts["amount"])

        desc = data.get("desc", "")
        if desc:
            draw.text((col_x[2], row_y + 45), f"({desc})", fill=COMMON_COLORS["text_gray"], font=fonts["desc"])

        row_y += row_height

    # 주의사항 박스
    if warning_text:
        box_y = row_y + 10
        draw.rounded_rectangle(
            [margin, box_y, CANVAS_SIZE[0] - margin, box_y + 95],
            radius=10, fill=COMMON_COLORS["box_yellow"]
        )
        draw.rounded_rectangle([margin + 15, box_y + 12, margin + 65, box_y + 42],
                              radius=5, fill=CAUTION_PALETTE["badge"])
        draw.text((margin + 23, box_y + 15), "주의", fill=COMMON_COLORS["white"], font=fonts["warning"])
        draw.text((margin + 80, box_y + 15), "급여 시 주의사항", fill=CAUTION_PALETTE["badge"], font=fonts["warning"])

        for i, text in enumerate(warning_text[:2]):
            draw.text((margin + 25, box_y + 50 + i * 22), f"• {text}",
                     fill=COMMON_COLORS["text_gray"], font=fonts["warning_text"])

    # 푸터
    if footnote:
        bbox = fonts["footer"].getbbox(footnote)
        footnote_width = bbox[2] - bbox[0]
        draw.text(((CANVAS_SIZE[0] - footnote_width) // 2, CANVAS_SIZE[1] - 55),
                  f"* {footnote}", fill=COMMON_COLORS["text_gray"], font=fonts["footer"])

    if output_path:
        img.save(output_path, "PNG")
        print(f"   [OK] 저장: {output_path}")

    return img


def generate_safe_precautions(
    food_name: str,
    items: List[Dict[str, str]],
    emergency_note: str = "",
    safety: Safety = Safety.SAFE,
    output_path: Path = None
) -> Image.Image:
    """주의사항 인포그래픽 - SAFE/CAUTION용"""
    # 주의사항은 항상 주황 헤더 사용
    palette = CAUTION_PALETTE

    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(COMMON_COLORS["background"]))
    draw = ImageDraw.Draw(img)

    fonts = {
        "badge": load_font("bold", 24),
        "title": load_font("bold", 50),
        "card_title": load_font("bold", 32),
        "card_desc": load_font("regular", 20),
        "number": load_font("bold", 24),
        "footer": load_font("regular", 20),
    }

    # 주황 그라데이션 헤더
    draw_gradient_header(draw, img, [(235, 150, 130), (240, 180, 160)])

    # "주의" 배지 + 제목
    draw.rounded_rectangle([420, 35, 490, 70], radius=15, fill=palette["badge"])
    draw.text((435, 40), "주의", fill=COMMON_COLORS["white"], font=fonts["badge"])
    draw.text((510, 30), "주의사항", fill=palette["title"], font=fonts["title"])

    # 주의사항 카드들
    y_pos = 165
    card_height = 95
    margin = 55

    for i, item in enumerate(items[:5], 1):
        draw.rounded_rectangle(
            [margin, y_pos, CANVAS_SIZE[0] - margin, y_pos + card_height],
            radius=12, fill=COMMON_COLORS["box_blue"]
        )
        draw_number_badge(draw, i, (margin + 50, y_pos + card_height // 2), fonts["number"])
        draw.text((margin + 95, y_pos + 18), item["title"],
                  fill=COMMON_COLORS["text_dark"], font=fonts["card_title"])
        draw.text((margin + 95, y_pos + 55), item.get("desc", ""),
                  fill=COMMON_COLORS["text_gray"], font=fonts["card_desc"])

        y_pos += card_height + 12

    # 응급 안내 푸터
    if emergency_note:
        footer_y = CANVAS_SIZE[1] - 100
        draw.rounded_rectangle(
            [margin, footer_y, CANVAS_SIZE[0] - margin, footer_y + 55],
            radius=10, fill=COMMON_COLORS["footer_pink"]
        )
        draw.ellipse([margin + 15, footer_y + 12, margin + 45, footer_y + 42],
                    fill=FORBIDDEN_PALETTE["badge"])
        draw.text((margin + 24, footer_y + 12), "+", fill=COMMON_COLORS["white"], font=fonts["number"])
        draw.text((margin + 60, footer_y + 15), emergency_note,
                  fill=FORBIDDEN_PALETTE["badge"], font=fonts["footer"])

    if output_path:
        img.save(output_path, "PNG")
        print(f"   [OK] 저장: {output_path}")

    return img


def generate_safe_cooking_method(
    food_name: str,
    steps: List[Dict[str, str]],
    tip: str = "",
    safety: Safety = Safety.SAFE,
    output_path: Path = None
) -> Image.Image:
    """조리방법 인포그래픽 - SAFE/CAUTION용"""
    palette = get_palette(safety)

    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(COMMON_COLORS["background"]))
    draw = ImageDraw.Draw(img)

    fonts = {
        "title": load_font("bold", 50),
        "subtitle": load_font("regular", 22),
        "step_badge": load_font("bold", 18),
        "step_title": load_font("bold", 32),
        "step_desc": load_font("regular", 20),
        "tip_badge": load_font("bold", 22),
        "tip_text": load_font("regular", 18),
    }

    # 그라데이션 헤더
    draw_gradient_header(draw, img, palette["header_gradient"])

    # 제목
    title = "안전한 조리 방법"
    bbox = fonts["title"].getbbox(title)
    title_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - title_width) // 2, 30), title,
              fill=COMMON_COLORS["white"], font=fonts["title"])

    # 부제목
    subtitle = f"강아지를 위한 {food_name} 준비 5단계"
    bbox = fonts["subtitle"].getbbox(subtitle)
    subtitle_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - subtitle_width) // 2, 85), subtitle,
              fill=COMMON_COLORS["white"], font=fonts["subtitle"])

    # STEP 카드들
    y_pos = 165
    card_height = 90
    margin = 55

    for i, step in enumerate(steps[:5], 1):
        draw.rounded_rectangle(
            [margin, y_pos, CANVAS_SIZE[0] - margin, y_pos + card_height],
            radius=12, fill=COMMON_COLORS["box_blue"]
        )
        badge_width = draw_step_badge(draw, i, (margin + 15, y_pos + 15), fonts["step_badge"])
        draw.text((margin + badge_width + 30, y_pos + 15), step["title"],
                  fill=COMMON_COLORS["text_dark"], font=fonts["step_title"])
        draw.text((margin + 20, y_pos + 55), step.get("desc", ""),
                  fill=COMMON_COLORS["text_gray"], font=fonts["step_desc"])

        y_pos += card_height + 12

    # TIP 박스 (중앙 정렬)
    if tip:
        tip_y = y_pos + 10
        box_left = margin
        box_right = CANVAS_SIZE[0] - margin
        box_center = (box_left + box_right) // 2

        draw.rounded_rectangle(
            [box_left, tip_y, box_right, tip_y + 70],
            radius=10, fill=COMMON_COLORS["box_yellow"]
        )
        draw.ellipse([margin + 15, tip_y + 15, margin + 45, tip_y + 45],
                    fill=CAUTION_PALETTE["badge"])
        draw.text((margin + 27, tip_y + 15), "!", fill=COMMON_COLORS["white"], font=fonts["tip_badge"])
        draw.text((margin + 60, tip_y + 12), "TIP", fill=FORBIDDEN_PALETTE["badge"], font=fonts["tip_badge"])

        # TIP 텍스트 중앙 정렬
        tip_bbox = fonts["tip_text"].getbbox(tip)
        tip_text_width = tip_bbox[2] - tip_bbox[0]
        tip_text_x = box_center - (tip_text_width // 2)
        draw.text((tip_text_x, tip_y + 40), tip, fill=COMMON_COLORS["text_gray"], font=fonts["tip_text"])

    if output_path:
        img.save(output_path, "PNG")
        print(f"   [OK] 저장: {output_path}")

    return img


# =============================================================================
# §22.7 FORBIDDEN 전용 템플릿
# =============================================================================
def generate_forbidden_danger_info(
    food_name: str,
    danger_components: List[Dict[str, str]],
    output_path: Path = None
) -> Image.Image:
    """위험 성분 상세 - FORBIDDEN용 (3번 슬라이드 대체)"""
    palette = FORBIDDEN_PALETTE

    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(COMMON_COLORS["background"]))
    draw = ImageDraw.Draw(img)

    fonts = {
        "title": load_font("bold", 55),
        "subtitle": load_font("regular", 22),
        "card_title": load_font("bold", 34),
        "card_desc": load_font("regular", 20),
        "badge": load_font("bold", 22),
        "footer": load_font("regular", 16),
    }

    # 빨간 그라데이션 헤더
    draw_gradient_header(draw, img, palette["header_gradient"])

    # 제목
    title = f"{food_name} 위험 성분"
    bbox = fonts["title"].getbbox(title)
    title_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - title_width) // 2, 35), title,
              fill=palette["title"], font=fonts["title"])

    # 부제목
    subtitle = "강아지에게 치명적인 독성 성분"
    bbox = fonts["subtitle"].getbbox(subtitle)
    subtitle_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - subtitle_width) // 2, 95), subtitle,
              fill=COMMON_COLORS["subtitle"], font=fonts["subtitle"])

    # FORBIDDEN 배지 (우측 정렬, 잘림 방지)
    draw_right_aligned_badge(draw, "FORBIDDEN", 40,
                              palette["badge_bg"], COMMON_COLORS["white"], fonts["badge"])

    # 위험 성분 카드
    y_pos = 165
    card_height = 100
    margin = 55

    for i, component in enumerate(danger_components[:6], 1):
        # 빨간 테두리 박스
        draw.rounded_rectangle(
            [margin, y_pos, CANVAS_SIZE[0] - margin, y_pos + card_height],
            radius=10, fill=palette["box_warning"], outline=palette["badge"], width=2
        )

        # 위험 아이콘 (빨간 원 + !)
        draw.ellipse([margin + 25, y_pos + 25, margin + 75, y_pos + 75], fill=palette["badge"])
        draw.text((margin + 44, y_pos + 30), "!", fill=COMMON_COLORS["white"], font=fonts["card_title"])

        draw.text((margin + 95, y_pos + 20), component.get("name", ""),
                  fill=palette["text_danger"], font=fonts["card_title"])
        draw.text((margin + 95, y_pos + 58), component.get("effect", ""),
                  fill=COMMON_COLORS["text_gray"], font=fonts["card_desc"])

        y_pos += card_height + 12

    # 경고 푸터
    footer_text = "소량 섭취도 치명적일 수 있습니다"
    bbox = fonts["footer"].getbbox(footer_text)
    footer_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - footer_width) // 2, CANVAS_SIZE[1] - 55),
              f"⚠️ {footer_text}", fill=palette["text_danger"], font=fonts["footer"])

    if output_path:
        img.save(output_path, "PNG")
        print(f"   [OK] 저장: {output_path}")

    return img


def generate_forbidden_warning(
    food_name: str,
    output_path: Path = None
) -> Image.Image:
    """절대 급여 금지 경고 - FORBIDDEN용 (4번 슬라이드 대체)"""
    palette = FORBIDDEN_PALETTE

    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(COMMON_COLORS["background"]))
    draw = ImageDraw.Draw(img)

    fonts = {
        "title": load_font("bold", 60),
        "warning": load_font("bold", 80),
        "desc": load_font("regular", 28),
        "badge": load_font("bold", 26),
    }

    # 빨간 그라데이션 헤더 (더 높게)
    draw_gradient_header(draw, img, palette["header_gradient"], height=200)

    # FORBIDDEN 배지 (중앙)
    badge_text = "FORBIDDEN"
    bbox = fonts["badge"].getbbox(badge_text)
    badge_width = bbox[2] - bbox[0] + 50
    badge_x = (CANVAS_SIZE[0] - badge_width) // 2
    draw.rounded_rectangle([badge_x, 50, badge_x + badge_width, 100],
                          radius=25, fill=COMMON_COLORS["white"])
    draw.text((badge_x + 25, 58), badge_text, fill=palette["badge"], font=fonts["badge"])

    # 메인 경고
    title = "절대 급여 금지"
    bbox = fonts["title"].getbbox(title)
    title_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - title_width) // 2, 130), title,
              fill=COMMON_COLORS["white"], font=fonts["title"])

    # 중앙 경고 박스
    margin = 80
    box_y = 280
    box_height = 400
    draw.rounded_rectangle(
        [margin, box_y, CANVAS_SIZE[0] - margin, box_y + box_height],
        radius=20, fill=palette["box_danger"], outline=palette["badge"], width=4
    )

    # 큰 X 마크 (정확한 중앙 정렬)
    x_center = CANVAS_SIZE[0] // 2
    circle_y_center = box_y + 130  # 원의 중심 Y좌표
    draw.ellipse([x_center - 80, box_y + 50, x_center + 80, box_y + 210],
                fill=palette["badge"])
    # X 문자 정확한 중앙 계산
    x_bbox = fonts["warning"].getbbox("X")
    x_text_width = x_bbox[2] - x_bbox[0]
    x_text_height = x_bbox[3] - x_bbox[1]
    x_text_x = x_center - (x_text_width // 2)
    x_text_y = circle_y_center - (x_text_height // 2) - x_bbox[1]
    draw.text((x_text_x, x_text_y), "X", fill=COMMON_COLORS["white"], font=fonts["warning"])

    # 경고 메시지들
    warnings = [
        f"{food_name}은(는) 강아지에게",
        "치명적인 독성이 있습니다",
        "",
        "어떤 형태로도 급여하지 마세요"
    ]

    y_pos = box_y + 230
    for warning in warnings:
        if warning:
            bbox = fonts["desc"].getbbox(warning)
            text_width = bbox[2] - bbox[0]
            draw.text(((CANVAS_SIZE[0] - text_width) // 2, y_pos), warning,
                      fill=palette["text_danger"], font=fonts["desc"])
        y_pos += 40

    # 하단 응급 안내
    footer_y = CANVAS_SIZE[1] - 120
    draw.rounded_rectangle(
        [margin, footer_y, CANVAS_SIZE[0] - margin, footer_y + 70],
        radius=10, fill=palette["box_warning"]
    )
    footer_text = "실수로 섭취 시 즉시 동물병원으로!"
    bbox = fonts["badge"].getbbox(footer_text)
    footer_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - footer_width) // 2, footer_y + 20),
              footer_text, fill=palette["text_danger"], font=fonts["badge"])

    if output_path:
        img.save(output_path, "PNG")
        print(f"   [OK] 저장: {output_path}")

    return img


def generate_forbidden_zero_dosage(
    output_path: Path = None
) -> Image.Image:
    """급여량 = 0g 고정 - FORBIDDEN용 (5번 슬라이드 대체)"""
    palette = FORBIDDEN_PALETTE

    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(COMMON_COLORS["background"]))
    draw = ImageDraw.Draw(img)

    fonts = {
        "title": load_font("bold", 55),
        "subtitle": load_font("regular", 22),
        "zero": load_font("bold", 200),
        "unit": load_font("bold", 60),
        "desc": load_font("regular", 26),
        "footer": load_font("regular", 18),
    }

    # 빨간 그라데이션 헤더
    draw_gradient_header(draw, img, palette["header_gradient"])

    # 제목
    title = "급여량 가이드"
    bbox = fonts["title"].getbbox(title)
    title_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - title_width) // 2, 35), title,
              fill=palette["title"], font=fonts["title"])

    # 부제목
    subtitle = "어떤 체중, 어떤 상황에서도"
    bbox = fonts["subtitle"].getbbox(subtitle)
    subtitle_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - subtitle_width) // 2, 95), subtitle,
              fill=COMMON_COLORS["subtitle"], font=fonts["subtitle"])

    # 중앙 0g 표시
    margin = 100
    box_y = 200
    draw.rounded_rectangle(
        [margin, box_y, CANVAS_SIZE[0] - margin, box_y + 400],
        radius=30, fill=palette["box_danger"], outline=palette["badge"], width=4
    )

    # 큰 0
    zero_text = "0"
    bbox = fonts["zero"].getbbox(zero_text)
    zero_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - zero_width) // 2 - 30, box_y + 50), zero_text,
              fill=palette["badge"], font=fonts["zero"])

    # g 단위
    draw.text(((CANVAS_SIZE[0] + zero_width) // 2 - 20, box_y + 150), "g",
              fill=palette["badge"], font=fonts["unit"])

    # 설명
    desc_lines = [
        "소형견, 중형견, 대형견, 초대형견",
        "모든 견종에게 급여 금지"
    ]
    y_pos = box_y + 290
    for line in desc_lines:
        bbox = fonts["desc"].getbbox(line)
        line_width = bbox[2] - bbox[0]
        draw.text(((CANVAS_SIZE[0] - line_width) // 2, y_pos), line,
                  fill=palette["text_danger"], font=fonts["desc"])
        y_pos += 40

    # 하단 경고
    footer_text = "독성 음식은 체중과 관계없이 어떤 양도 위험합니다"
    bbox = fonts["footer"].getbbox(footer_text)
    footer_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - footer_width) // 2, CANVAS_SIZE[1] - 80),
              footer_text, fill=palette["text_danger"], font=fonts["footer"])

    if output_path:
        img.save(output_path, "PNG")
        print(f"   [OK] 저장: {output_path}")

    return img


def generate_forbidden_emergency(
    food_name: str,
    symptoms: List[str],
    output_path: Path = None
) -> Image.Image:
    """섭취 시 응급 대처 - FORBIDDEN용 (6번 슬라이드 대체)"""
    palette = FORBIDDEN_PALETTE

    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(COMMON_COLORS["background"]))
    draw = ImageDraw.Draw(img)

    fonts = {
        "badge": load_font("bold", 24),
        "title": load_font("bold", 50),
        "card_title": load_font("bold", 28),
        "card_desc": load_font("regular", 20),
        "number": load_font("bold", 24),
        "footer": load_font("regular", 22),
    }

    # 빨간 그라데이션 헤더
    draw_gradient_header(draw, img, palette["header_gradient"])

    # "응급" 배지 + 제목
    draw.rounded_rectangle([380, 35, 460, 70], radius=15, fill=COMMON_COLORS["white"])
    draw.text((395, 40), "응급", fill=palette["badge"], font=fonts["badge"])
    draw.text((480, 30), "섭취 시 대처법", fill=COMMON_COLORS["white"], font=fonts["title"])

    # 응급 대처 단계
    emergency_steps = [
        {"title": "침착하게 상황 파악", "desc": "섭취량과 시간을 기억하세요"},
        {"title": "즉시 동물병원 연락", "desc": "24시간 응급병원 번호를 확인하세요"},
        {"title": "구토 유도 금지", "desc": "임의로 구토를 유도하지 마세요"},
        {"title": "증상 관찰 및 기록", "desc": "구토, 설사, 떨림 등 증상을 기록하세요"},
        {"title": "포장지/남은 음식 지참", "desc": "병원 방문 시 증거물을 가져가세요"},
    ]

    y_pos = 165
    card_height = 90
    margin = 55

    for i, step in enumerate(emergency_steps, 1):
        # 빨간 테두리 카드
        draw.rounded_rectangle(
            [margin, y_pos, CANVAS_SIZE[0] - margin, y_pos + card_height],
            radius=12, fill=palette["box_warning"], outline=palette["badge"], width=2
        )

        # 번호 뱃지 (빨간색)
        draw.ellipse([margin + 25, y_pos + 20, margin + 75, y_pos + 70], fill=palette["badge"])
        draw.text((margin + 44, y_pos + 28), str(i), fill=COMMON_COLORS["white"], font=fonts["number"])

        draw.text((margin + 95, y_pos + 15), step["title"],
                  fill=palette["text_danger"], font=fonts["card_title"])
        draw.text((margin + 95, y_pos + 50), step["desc"],
                  fill=COMMON_COLORS["text_gray"], font=fonts["card_desc"])

        y_pos += card_height + 10

    # 응급 연락처 푸터
    footer_y = CANVAS_SIZE[1] - 100
    draw.rounded_rectangle(
        [margin, footer_y, CANVAS_SIZE[0] - margin, footer_y + 55],
        radius=10, fill=palette["box_danger"]
    )
    footer_text = "응급상황 시 지체 없이 동물병원으로!"
    bbox = fonts["footer"].getbbox(footer_text)
    footer_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - footer_width) // 2, footer_y + 15),
              footer_text, fill=palette["text_danger"], font=fonts["footer"])

    if output_path:
        img.save(output_path, "PNG")
        print(f"   [OK] 저장: {output_path}")

    return img


def generate_forbidden_vet_consult(
    food_name: str,
    output_path: Path = None
) -> Image.Image:
    """수의사 상담 안내 - FORBIDDEN용 (7번 슬라이드 대체)"""
    palette = FORBIDDEN_PALETTE

    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(COMMON_COLORS["background"]))
    draw = ImageDraw.Draw(img)

    fonts = {
        "title": load_font("bold", 50),
        "subtitle": load_font("regular", 22),
        "main": load_font("bold", 36),
        "desc": load_font("regular", 24),
        "tip_badge": load_font("bold", 22),
        "tip_text": load_font("regular", 18),
    }

    # 빨간 그라데이션 헤더
    draw_gradient_header(draw, img, palette["header_gradient"])

    # 제목
    title = "수의사 상담 필수"
    bbox = fonts["title"].getbbox(title)
    title_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - title_width) // 2, 30), title,
              fill=COMMON_COLORS["white"], font=fonts["title"])

    # 부제목
    subtitle = f"{food_name} 섭취 의심 시"
    bbox = fonts["subtitle"].getbbox(subtitle)
    subtitle_width = bbox[2] - bbox[0]
    draw.text(((CANVAS_SIZE[0] - subtitle_width) // 2, 85), subtitle,
              fill=COMMON_COLORS["white"], font=fonts["subtitle"])

    # 상담 정보 카드들
    margin = 55
    y_pos = 180

    consult_items = [
        {"icon": "🏥", "title": "가까운 동물병원", "desc": "24시간 응급 진료 가능한 병원을 미리 확인하세요"},
        {"icon": "📞", "title": "응급 상담 전화", "desc": "증상 발현 시 즉시 전화 상담을 받으세요"},
        {"icon": "📋", "title": "섭취 정보 전달", "desc": "섭취량, 시간, 현재 증상을 정확히 전달하세요"},
        {"icon": "🚗", "title": "신속한 병원 이동", "desc": "증상이 없어도 예방적 진료를 권장합니다"},
    ]

    for item in consult_items:
        draw.rounded_rectangle(
            [margin, y_pos, CANVAS_SIZE[0] - margin, y_pos + 120],
            radius=15, fill=palette["box_warning"]
        )

        # 아이콘 영역 (텍스트로 대체)
        draw.ellipse([margin + 20, y_pos + 25, margin + 90, y_pos + 95],
                    fill=palette["badge"])

        draw.text((margin + 110, y_pos + 25), item["title"],
                  fill=palette["text_danger"], font=fonts["main"])
        draw.text((margin + 110, y_pos + 70), item["desc"],
                  fill=COMMON_COLORS["text_gray"], font=fonts["desc"])

        y_pos += 135

    # 안전 간식 안내 (Phase 2 예고) - 중앙 정렬
    tip_y = y_pos + 20
    box_left = margin
    box_right = CANVAS_SIZE[0] - margin
    box_center = (box_left + box_right) // 2

    draw.rounded_rectangle(
        [box_left, tip_y, box_right, tip_y + 70],
        radius=10, fill=COMMON_COLORS["box_yellow"]
    )
    draw.text((margin + 25, tip_y + 12), "TIP", fill=palette["badge"], font=fonts["tip_badge"])

    # TIP 텍스트 중앙 정렬
    tip_text = "안전한 대체 간식은 수의사와 상담 후 결정하세요"
    tip_bbox = fonts["tip_text"].getbbox(tip_text)
    tip_text_width = tip_bbox[2] - tip_bbox[0]
    tip_text_x = box_center - (tip_text_width // 2)
    draw.text((tip_text_x, tip_y + 40), tip_text,
              fill=COMMON_COLORS["text_gray"], font=fonts["tip_text"])

    if output_path:
        img.save(output_path, "PNG")
        print(f"   [OK] 저장: {output_path}")

    return img


# =============================================================================
# §22.8 통합 생성 함수 (안전도별 분기)
# =============================================================================
def generate_nutrition_info(food_name, nutrients, safety_str, footnote="", output_path=None):
    """3번 영양정보 - 안전도별 분기"""
    safety = safety_validate(safety_str)

    if safety == Safety.FORBIDDEN:
        # FORBIDDEN: 위험 성분 상세로 대체
        danger_components = [
            {"name": n.get("name", ""), "effect": n.get("benefit", "")}
            for n in nutrients[:6]
        ]
        return generate_forbidden_danger_info(food_name, danger_components, output_path)
    else:
        return generate_safe_nutrition_info(food_name, nutrients, safety, footnote, output_path)


def generate_do_dont(food_name, do_items, dont_items, safety_str, output_path=None):
    """4번 급여 DO/DON'T - 안전도별 분기"""
    safety = safety_validate(safety_str)

    if safety == Safety.FORBIDDEN:
        # §22.4: FORBIDDEN에서 DO 아이콘 차단
        return generate_forbidden_warning(food_name, output_path)
    else:
        return generate_safe_do_dont(food_name, do_items, dont_items, safety, output_path)


def generate_dosage_table(dosages, warning_text=None, footnote="", safety_str="SAFE", output_path=None):
    """5번 급여량표 - 안전도별 분기"""
    safety = safety_validate(safety_str)

    if safety == Safety.FORBIDDEN:
        # §22.7: FORBIDDEN 급여량 = 0g 고정
        return generate_forbidden_zero_dosage(output_path)
    else:
        return generate_safe_dosage_table(dosages, warning_text, footnote, safety, output_path)


def generate_precautions(food_name, items, emergency_note="", safety_str="SAFE", output_path=None):
    """6번 주의사항 - 안전도별 분기"""
    safety = safety_validate(safety_str)

    if safety == Safety.FORBIDDEN:
        # FORBIDDEN: 응급 대처로 대체
        symptoms = [item.get("title", "") for item in items[:5]]
        return generate_forbidden_emergency(food_name, symptoms, output_path)
    else:
        return generate_safe_precautions(food_name, items, emergency_note, safety, output_path)


def generate_cooking_method(food_name, steps, tip="", safety_str="SAFE", output_path=None):
    """7번 조리방법 - 안전도별 분기"""
    safety = safety_validate(safety_str)

    if safety == Safety.FORBIDDEN:
        # §22.4: FORBIDDEN에서 조리방법 차단 → 수의사 상담으로 대체
        return generate_forbidden_vet_consult(food_name, output_path)
    else:
        return generate_safe_cooking_method(food_name, steps, tip, safety, output_path)


# =============================================================================
# 테스트
# =============================================================================
if __name__ == "__main__":
    print("=" * 60)
    print("Pillow Infographic Generator v3.0 (§22 Safety Rules)")
    print("=" * 60)

    output_dir = PROJECT_ROOT / "debug" / "infographic_test"
    output_dir.mkdir(parents=True, exist_ok=True)

    # SAFE 테스트
    print("\n[SAFE 테스트]")
    generate_do_dont("당근", ["생으로", "익혀서", "작게"], ["큰 조각", "양념", "과다"], "SAFE",
                    output_dir / "safe_4.png")

    # FORBIDDEN 테스트
    print("\n[FORBIDDEN 테스트]")
    generate_do_dont("포도", [], [], "FORBIDDEN", output_dir / "forbidden_4.png")
    generate_dosage_table({}, [], "", "FORBIDDEN", output_dir / "forbidden_5.png")
    generate_cooking_method("포도", [], "", "FORBIDDEN", output_dir / "forbidden_7.png")

    print(f"\n[OK] 테스트 완료: {output_dir}")
