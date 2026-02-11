#!/usr/bin/env python3
"""
infographic_generator.py - Pillow 기반 C2 인포그래픽 생성기
R7 Phase 2: 블로그 본문 인포그래픽 (3~7장) 자동 생성

골든 샘플 기준: contents/0_Golden sample/Blog/
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Tuple, Optional
from PIL import Image, ImageDraw, ImageFont

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# === 디자인 상수 ===
CANVAS_SIZE = (1080, 1080)
BACKGROUND_COLOR = "#FFF8E7"  # 크림/베이지

# 그라데이션 색상 (민트)
GRADIENT_START = (129, 199, 191, 255)  # 민트 #81C7BF
GRADIENT_END = (255, 248, 231, 0)       # 투명 크림

# 폰트 설정 (macOS 기준)
FONT_PATHS = {
    "bold": "/System/Library/Fonts/AppleSDGothicNeo.ttc",  # Bold는 index 6
    "regular": "/System/Library/Fonts/AppleSDGothicNeo.ttc",  # Regular는 index 0
}

# 폰트 크기 (§2.4.2 기준)
FONT_SIZES = {
    "header_title": 60,
    "header_subtitle": 24,
    "card_title": 36,
    "card_desc": 22,
    "value": 44,
    "unit": 28,
    "footer": 18,
    "tip_box": 20,
    "badge": 24,
}

# 색상 팔레트
COLORS = {
    "header_title_safe": "#2D8B7F",      # 민트 계열
    "header_title_caution": "#E67E22",   # 주황
    "header_title_danger": "#C0392B",    # 빨강
    "header_subtitle": "#666666",
    "card_title": "#333333",
    "card_desc": "#888888",
    "value": "#E67E22",                  # 주황
    "footer": "#AAAAAA",
    "white": "#FFFFFF",
    "badge_safe": "#4CAF50",             # 초록
    "badge_caution": "#FF9800",          # 주황
    "badge_danger": "#F44336",           # 빨강
}

# 번호 뱃지 색상
BADGE_COLORS = [
    "#FF9800",  # 1 - 주황
    "#4CAF50",  # 2 - 초록
    "#F44336",  # 3 - 빨강
    "#2196F3",  # 4 - 파랑
    "#9C27B0",  # 5 - 보라
    "#FF5722",  # 6 - 딥오렌지
]


def load_font(font_type: str, size: int) -> ImageFont.FreeTypeFont:
    """폰트 로드"""
    try:
        path = FONT_PATHS.get(font_type, FONT_PATHS["regular"])
        # AppleSDGothicNeo.ttc: 0=Light, 2=Medium, 4=SemiBold, 6=Bold, 8=Heavy
        index = 6 if font_type == "bold" else 2
        return ImageFont.truetype(path, size, index=index)
    except Exception as e:
        print(f"   폰트 로드 실패: {e}, 기본 폰트 사용")
        return ImageFont.load_default()


def hex_to_rgb(hex_color: str) -> Tuple[int, int, int]:
    """HEX → RGB 변환"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def draw_gradient_header(draw: ImageDraw.Draw, img: Image.Image, height: int = 150):
    """상단 그라데이션 헤더 그리기"""
    for y in range(height):
        ratio = y / height
        r = int(GRADIENT_START[0] + (GRADIENT_END[0] - GRADIENT_START[0]) * ratio)
        g = int(GRADIENT_START[1] + (GRADIENT_END[1] - GRADIENT_START[1]) * ratio)
        b = int(GRADIENT_START[2] + (GRADIENT_END[2] - GRADIENT_START[2]) * ratio)
        a = int(GRADIENT_START[3] + (GRADIENT_END[3] - GRADIENT_START[3]) * ratio)

        for x in range(CANVAS_SIZE[0]):
            if a < 255:
                bg = hex_to_rgb(BACKGROUND_COLOR)
                r = int((r * a + bg[0] * (255 - a)) / 255)
                g = int((g * a + bg[1] * (255 - a)) / 255)
                b = int((b * a + bg[2] * (255 - a)) / 255)
            img.putpixel((x, y), (r, g, b))


def draw_badge(draw: ImageDraw.Draw, text: str, position: Tuple[int, int],
               color: str, font: ImageFont.FreeTypeFont):
    """안전도 뱃지 그리기"""
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    padding_x, padding_y = 20, 8
    x, y = position

    # 둥근 사각형 배경
    draw.rounded_rectangle(
        [x, y, x + text_width + padding_x * 2, y + text_height + padding_y * 2],
        radius=15,
        fill=color
    )

    # 텍스트
    draw.text(
        (x + padding_x, y + padding_y),
        text,
        fill=COLORS["white"],
        font=font
    )


def draw_number_badge(draw: ImageDraw.Draw, number: int, position: Tuple[int, int],
                      font: ImageFont.FreeTypeFont):
    """번호 뱃지 그리기 (원형)"""
    color = BADGE_COLORS[(number - 1) % len(BADGE_COLORS)]
    x, y = position
    radius = 25

    # 원 그리기
    draw.ellipse(
        [x - radius, y - radius, x + radius, y + radius],
        fill=color
    )

    # 번호 텍스트
    text = str(number)
    bbox = font.getbbox(text)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    draw.text(
        (x - text_width // 2, y - text_height // 2 - 5),
        text,
        fill=COLORS["white"],
        font=font
    )


def draw_card(draw: ImageDraw.Draw, y_pos: int, number: int,
              title: str, desc: str, value: str, unit: str,
              fonts: Dict[str, ImageFont.FreeTypeFont]) -> int:
    """영양성분 카드 그리기"""
    card_height = 110
    card_margin = 60
    card_padding = 25

    # 카드 배경 (연한 민트)
    card_color = (230, 245, 243)
    draw.rounded_rectangle(
        [card_margin, y_pos, CANVAS_SIZE[0] - card_margin, y_pos + card_height],
        radius=10,
        fill=card_color
    )

    # 번호 뱃지
    draw_number_badge(draw, number, (card_margin + 50, y_pos + card_height // 2), fonts["badge"])

    # 제목 (성분명)
    title_x = card_margin + 100
    draw.text(
        (title_x, y_pos + 25),
        title,
        fill=COLORS["card_title"],
        font=fonts["card_title"]
    )

    # 설명 (효능)
    draw.text(
        (title_x, y_pos + 65),
        desc,
        fill=COLORS["card_desc"],
        font=fonts["card_desc"]
    )

    # 수치 + 단위 (오른쪽 정렬)
    value_text = f"{value} {unit}"
    bbox = fonts["value"].getbbox(value_text)
    value_width = bbox[2] - bbox[0]

    draw.text(
        (CANVAS_SIZE[0] - card_margin - card_padding - value_width, y_pos + 35),
        value_text,
        fill=COLORS["value"],
        font=fonts["value"]
    )

    return y_pos + card_height + 15


def generate_nutrition_info(
    food_name: str,
    nutrients: List[Dict[str, str]],
    safety: str = "SAFE",
    footnote: str = "",
    output_path: Path = None
) -> Image.Image:
    """
    영양정보 인포그래픽 생성 (3번 이미지)

    Args:
        food_name: 음식 이름 (예: "당근")
        nutrients: 영양소 목록 [{"name": "베타카로틴", "benefit": "눈 건강", "value": "8,285", "unit": "μg"}, ...]
        safety: 안전도 ("SAFE", "CAUTION", "DANGER")
        footnote: 하단 주석
        output_path: 저장 경로
    """
    # 캔버스 생성
    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(BACKGROUND_COLOR))
    draw = ImageDraw.Draw(img)

    # 폰트 로드
    fonts = {
        "header_title": load_font("bold", FONT_SIZES["header_title"]),
        "header_subtitle": load_font("regular", FONT_SIZES["header_subtitle"]),
        "card_title": load_font("bold", FONT_SIZES["card_title"]),
        "card_desc": load_font("regular", FONT_SIZES["card_desc"]),
        "value": load_font("bold", FONT_SIZES["value"]),
        "badge": load_font("bold", FONT_SIZES["badge"]),
        "footer": load_font("regular", FONT_SIZES["footer"]),
    }

    # 그라데이션 헤더
    draw_gradient_header(draw, img)

    # 헤더 제목
    title = f"{food_name} 영양성분"
    title_color = COLORS.get(f"header_title_{safety.lower()}", COLORS["header_title_safe"])
    bbox = fonts["header_title"].getbbox(title)
    title_width = bbox[2] - bbox[0]
    draw.text(
        ((CANVAS_SIZE[0] - title_width) // 2, 40),
        title,
        fill=title_color,
        font=fonts["header_title"]
    )

    # 헤더 부제목
    subtitle = "100g 기준 | 강아지에게 안전한 영양 간식"
    bbox = fonts["header_subtitle"].getbbox(subtitle)
    subtitle_width = bbox[2] - bbox[0]
    draw.text(
        ((CANVAS_SIZE[0] - subtitle_width) // 2, 105),
        subtitle,
        fill=COLORS["header_subtitle"],
        font=fonts["header_subtitle"]
    )

    # 안전도 뱃지
    badge_color = COLORS.get(f"badge_{safety.lower()}", COLORS["badge_safe"])
    draw_badge(draw, safety, (CANVAS_SIZE[0] - 120, 45), badge_color, fonts["badge"])

    # 영양소 카드들
    y_pos = 180
    for i, nutrient in enumerate(nutrients[:6], 1):
        y_pos = draw_card(
            draw, y_pos, i,
            nutrient["name"],
            nutrient.get("benefit", ""),
            nutrient.get("value", ""),
            nutrient.get("unit", ""),
            fonts
        )

    # 하단 주석
    if footnote:
        bbox = fonts["footer"].getbbox(footnote)
        footnote_width = bbox[2] - bbox[0]
        draw.text(
            ((CANVAS_SIZE[0] - footnote_width) // 2, CANVAS_SIZE[1] - 60),
            f"* {footnote}",
            fill=COLORS["footer"],
            font=fonts["footer"]
        )

    # 저장
    if output_path:
        img.save(output_path, "PNG")
        print(f"   ✅ 저장: {output_path}")

    return img


def generate_dosage_table(
    dosages: Dict[str, Dict[str, str]],
    warning_text: List[str] = None,
    footnote: str = "",
    output_path: Path = None
) -> Image.Image:
    """
    급여량표 인포그래픽 생성 (5번 이미지)

    Args:
        dosages: {"소형견": {"weight": "5kg 이하", "amount": "10~20g", "desc": "동전 크기 2~3조각"}, ...}
        warning_text: 주의사항 리스트
        footnote: 하단 주석
        output_path: 저장 경로
    """
    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(BACKGROUND_COLOR))
    draw = ImageDraw.Draw(img)

    fonts = {
        "header_title": load_font("bold", FONT_SIZES["header_title"]),
        "header_subtitle": load_font("regular", FONT_SIZES["header_subtitle"]),
        "card_title": load_font("bold", 28),
        "card_desc": load_font("regular", FONT_SIZES["card_desc"]),
        "value": load_font("bold", 32),
        "badge": load_font("bold", FONT_SIZES["badge"]),
        "footer": load_font("regular", FONT_SIZES["footer"]),
        "tip_box": load_font("regular", FONT_SIZES["tip_box"]),
    }

    # 그라데이션 헤더
    draw_gradient_header(draw, img)

    # 헤더 제목
    title = "체중별 급여량 가이드"
    bbox = fonts["header_title"].getbbox(title)
    title_width = bbox[2] - bbox[0]
    draw.text(
        ((CANVAS_SIZE[0] - title_width) // 2, 40),
        title,
        fill=COLORS["header_title_safe"],
        font=fonts["header_title"]
    )

    # 헤더 부제목
    subtitle = "하루 기준 | 간식으로 급여 시"
    bbox = fonts["header_subtitle"].getbbox(subtitle)
    subtitle_width = bbox[2] - bbox[0]
    draw.text(
        ((CANVAS_SIZE[0] - subtitle_width) // 2, 105),
        subtitle,
        fill=COLORS["header_subtitle"],
        font=fonts["header_subtitle"]
    )

    # 테이블 헤더
    table_y = 180
    header_height = 50
    col_widths = [180, 200, 300]  # 구분, 체중, 급여량
    margin = 110

    # 테이블 헤더 배경
    header_color = (129, 199, 191)  # 민트
    draw.rounded_rectangle(
        [margin, table_y, CANVAS_SIZE[0] - margin, table_y + header_height],
        radius=10,
        fill=header_color
    )

    # 테이블 헤더 텍스트
    headers = ["구분", "체중", "급여량"]
    x_pos = margin + 30
    for i, header in enumerate(headers):
        draw.text(
            (x_pos + col_widths[i] // 2 - 30, table_y + 12),
            header,
            fill=COLORS["white"],
            font=fonts["card_title"]
        )
        x_pos += col_widths[i]

    # 테이블 행
    row_y = table_y + header_height + 20
    row_height = 90

    dog_sizes = ["소형견", "중형견", "대형견", "초대형견"]
    for size in dog_sizes:
        data = dosages.get(size, {})

        # 구분
        draw.text(
            (margin + 50, row_y + 15),
            size,
            fill=COLORS["card_title"],
            font=fonts["card_title"]
        )

        # 체중
        draw.text(
            (margin + col_widths[0] + 40, row_y + 20),
            data.get("weight", ""),
            fill=COLORS["card_desc"],
            font=fonts["card_desc"]
        )

        # 급여량 (주황색)
        draw.text(
            (margin + col_widths[0] + col_widths[1] + 30, row_y + 10),
            data.get("amount", ""),
            fill=COLORS["value"],
            font=fonts["value"]
        )

        # 급여량 설명 (회색)
        desc = data.get("desc", "")
        if desc:
            draw.text(
                (margin + col_widths[0] + col_widths[1] + 30, row_y + 50),
                f"({desc})",
                fill=COLORS["card_desc"],
                font=fonts["card_desc"]
            )

        row_y += row_height

    # 주의사항 박스
    if warning_text:
        box_y = row_y + 20
        box_color = (255, 243, 205)  # 연한 노랑
        draw.rounded_rectangle(
            [margin, box_y, CANVAS_SIZE[0] - margin, box_y + 100],
            radius=10,
            fill=box_color
        )

        # "주의" 뱃지
        draw.rounded_rectangle(
            [margin + 20, box_y + 15, margin + 70, box_y + 45],
            radius=5,
            fill=COLORS["badge_caution"]
        )
        draw.text(
            (margin + 28, box_y + 17),
            "주의",
            fill=COLORS["white"],
            font=fonts["badge"]
        )

        # 주의 텍스트
        draw.text(
            (margin + 85, box_y + 18),
            "급여 시 주의사항",
            fill=COLORS["badge_caution"],
            font=fonts["card_title"]
        )

        for i, text in enumerate(warning_text[:2]):
            draw.text(
                (margin + 30, box_y + 55 + i * 25),
                f"• {text}",
                fill=COLORS["card_desc"],
                font=fonts["tip_box"]
            )

    # 하단 주석
    if footnote:
        bbox = fonts["footer"].getbbox(footnote)
        footnote_width = bbox[2] - bbox[0]
        draw.text(
            ((CANVAS_SIZE[0] - footnote_width) // 2, CANVAS_SIZE[1] - 60),
            f"* {footnote}",
            fill=COLORS["footer"],
            font=fonts["footer"]
        )

    if output_path:
        img.save(output_path, "PNG")
        print(f"   ✅ 저장: {output_path}")

    return img


def generate_precautions(
    food_name: str,
    items: List[Dict[str, str]],
    emergency_note: str = "",
    output_path: Path = None
) -> Image.Image:
    """
    주의사항 인포그래픽 생성 (6번 이미지)

    Args:
        food_name: 음식 이름
        items: [{"title": "껍질 제거", "desc": "소화가 어려워 반드시 제거"}, ...]
        emergency_note: 응급 안내
        output_path: 저장 경로
    """
    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(BACKGROUND_COLOR))
    draw = ImageDraw.Draw(img)

    fonts = {
        "header_title": load_font("bold", FONT_SIZES["header_title"]),
        "header_subtitle": load_font("regular", FONT_SIZES["header_subtitle"]),
        "card_title": load_font("bold", FONT_SIZES["card_title"]),
        "card_desc": load_font("regular", FONT_SIZES["card_desc"]),
        "badge": load_font("bold", FONT_SIZES["badge"]),
        "footer": load_font("regular", FONT_SIZES["footer"]),
    }

    # 그라데이션 헤더
    draw_gradient_header(draw, img)

    # 헤더 제목
    title = f"{food_name} 급여 시 주의사항"
    bbox = fonts["header_title"].getbbox(title)
    title_width = bbox[2] - bbox[0]
    draw.text(
        ((CANVAS_SIZE[0] - title_width) // 2, 40),
        title,
        fill=COLORS["header_title_caution"],
        font=fonts["header_title"]
    )

    # 헤더 부제목
    subtitle = "안전한 급여를 위한 필수 체크리스트"
    bbox = fonts["header_subtitle"].getbbox(subtitle)
    subtitle_width = bbox[2] - bbox[0]
    draw.text(
        ((CANVAS_SIZE[0] - subtitle_width) // 2, 105),
        subtitle,
        fill=COLORS["header_subtitle"],
        font=fonts["header_subtitle"]
    )

    # 주의사항 카드들
    y_pos = 180
    card_height = 110
    margin = 60

    for i, item in enumerate(items[:6], 1):
        # 카드 배경
        card_color = (255, 243, 205) if i % 2 == 1 else (255, 238, 186)  # 연한 노랑 계열
        draw.rounded_rectangle(
            [margin, y_pos, CANVAS_SIZE[0] - margin, y_pos + card_height],
            radius=10,
            fill=card_color
        )

        # 번호 뱃지 (빨강 계열)
        badge_colors = ["#F44336", "#FF5722", "#E91E63", "#9C27B0", "#FF9800", "#795548"]
        x, y = margin + 50, y_pos + card_height // 2
        radius = 25
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=badge_colors[i - 1]
        )
        draw.text(
            (x - 8, y - 18),
            str(i),
            fill=COLORS["white"],
            font=fonts["badge"]
        )

        # 제목
        draw.text(
            (margin + 100, y_pos + 25),
            item["title"],
            fill=COLORS["card_title"],
            font=fonts["card_title"]
        )

        # 설명
        draw.text(
            (margin + 100, y_pos + 65),
            item.get("desc", ""),
            fill=COLORS["card_desc"],
            font=fonts["card_desc"]
        )

        y_pos += card_height + 15

    # 응급 안내
    if emergency_note:
        bbox = fonts["footer"].getbbox(emergency_note)
        note_width = bbox[2] - bbox[0]
        draw.text(
            ((CANVAS_SIZE[0] - note_width) // 2, CANVAS_SIZE[1] - 60),
            f"* {emergency_note}",
            fill=COLORS["footer"],
            font=fonts["footer"]
        )

    if output_path:
        img.save(output_path, "PNG")
        print(f"   ✅ 저장: {output_path}")

    return img


def generate_cooking_method(
    food_name: str,
    steps: List[Dict[str, str]],
    tip: str = "",
    output_path: Path = None
) -> Image.Image:
    """
    조리방법 인포그래픽 생성 (7번 이미지)

    Args:
        food_name: 음식 이름
        steps: [{"title": "깨끗이 씻기", "desc": "흐르는 물에 깨끗이 세척"}, ...]
        tip: 팁 텍스트
        output_path: 저장 경로
    """
    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(BACKGROUND_COLOR))
    draw = ImageDraw.Draw(img)

    fonts = {
        "header_title": load_font("bold", FONT_SIZES["header_title"]),
        "header_subtitle": load_font("regular", FONT_SIZES["header_subtitle"]),
        "card_title": load_font("bold", FONT_SIZES["card_title"]),
        "card_desc": load_font("regular", FONT_SIZES["card_desc"]),
        "badge": load_font("bold", FONT_SIZES["badge"]),
        "footer": load_font("regular", FONT_SIZES["footer"]),
        "tip_box": load_font("regular", FONT_SIZES["tip_box"]),
    }

    # 그라데이션 헤더
    draw_gradient_header(draw, img)

    # 헤더 제목
    title = f"{food_name} 조리방법"
    bbox = fonts["header_title"].getbbox(title)
    title_width = bbox[2] - bbox[0]
    draw.text(
        ((CANVAS_SIZE[0] - title_width) // 2, 40),
        title,
        fill=COLORS["header_title_safe"],
        font=fonts["header_title"]
    )

    # 헤더 부제목
    subtitle = "강아지를 위한 안전한 조리 가이드"
    bbox = fonts["header_subtitle"].getbbox(subtitle)
    subtitle_width = bbox[2] - bbox[0]
    draw.text(
        ((CANVAS_SIZE[0] - subtitle_width) // 2, 105),
        subtitle,
        fill=COLORS["header_subtitle"],
        font=fonts["header_subtitle"]
    )

    # 스텝 카드들
    y_pos = 180
    card_height = 100
    margin = 60

    step_colors = ["#4CAF50", "#8BC34A", "#CDDC39", "#FFEB3B", "#FFC107"]

    for i, step in enumerate(steps[:5], 1):
        # 카드 배경
        card_color = (230, 245, 233)  # 연한 초록
        draw.rounded_rectangle(
            [margin, y_pos, CANVAS_SIZE[0] - margin, y_pos + card_height],
            radius=10,
            fill=card_color
        )

        # STEP 뱃지
        x, y = margin + 50, y_pos + card_height // 2
        radius = 25
        draw.ellipse(
            [x - radius, y - radius, x + radius, y + radius],
            fill=step_colors[i - 1]
        )
        draw.text(
            (x - 8, y - 18),
            str(i),
            fill=COLORS["white"],
            font=fonts["badge"]
        )

        # 제목
        draw.text(
            (margin + 100, y_pos + 20),
            f"STEP {i}: {step['title']}",
            fill=COLORS["card_title"],
            font=fonts["card_title"]
        )

        # 설명
        draw.text(
            (margin + 100, y_pos + 60),
            step.get("desc", ""),
            fill=COLORS["card_desc"],
            font=fonts["card_desc"]
        )

        y_pos += card_height + 15

    # TIP 박스
    if tip:
        box_y = y_pos + 10
        box_color = (230, 245, 233)  # 연한 초록
        draw.rounded_rectangle(
            [margin, box_y, CANVAS_SIZE[0] - margin, box_y + 80],
            radius=10,
            fill=box_color
        )

        # "TIP" 뱃지
        draw.rounded_rectangle(
            [margin + 20, box_y + 15, margin + 65, box_y + 45],
            radius=5,
            fill=COLORS["badge_safe"]
        )
        draw.text(
            (margin + 30, box_y + 17),
            "TIP",
            fill=COLORS["white"],
            font=fonts["badge"]
        )

        # 팁 텍스트
        draw.text(
            (margin + 80, box_y + 18),
            tip,
            fill=COLORS["card_desc"],
            font=fonts["tip_box"]
        )

    if output_path:
        img.save(output_path, "PNG")
        print(f"   ✅ 저장: {output_path}")

    return img


def generate_do_dont(
    food_name: str,
    do_items: List[str],
    dont_items: List[str],
    output_path: Path = None
) -> Image.Image:
    """
    급여 가능/불가 인포그래픽 생성 (4번 이미지)

    Args:
        food_name: 음식 이름
        do_items: 가능한 항목 리스트
        dont_items: 불가능한 항목 리스트
        output_path: 저장 경로
    """
    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(BACKGROUND_COLOR))
    draw = ImageDraw.Draw(img)

    fonts = {
        "header_title": load_font("bold", FONT_SIZES["header_title"]),
        "header_subtitle": load_font("regular", FONT_SIZES["header_subtitle"]),
        "card_title": load_font("bold", 32),
        "card_desc": load_font("regular", FONT_SIZES["card_desc"]),
        "footer": load_font("regular", FONT_SIZES["footer"]),
    }

    # 그라데이션 헤더
    draw_gradient_header(draw, img)

    # 헤더 제목
    title = f"{food_name} 급여 가이드"
    bbox = fonts["header_title"].getbbox(title)
    title_width = bbox[2] - bbox[0]
    draw.text(
        ((CANVAS_SIZE[0] - title_width) // 2, 40),
        title,
        fill=COLORS["header_title_safe"],
        font=fonts["header_title"]
    )

    # 헤더 부제목
    subtitle = "DO와 DON'T를 확인하세요"
    bbox = fonts["header_subtitle"].getbbox(subtitle)
    subtitle_width = bbox[2] - bbox[0]
    draw.text(
        ((CANVAS_SIZE[0] - subtitle_width) // 2, 105),
        subtitle,
        fill=COLORS["header_subtitle"],
        font=fonts["header_subtitle"]
    )

    # DO 섹션
    margin = 60
    section_width = (CANVAS_SIZE[0] - margin * 3) // 2

    # DO 제목
    draw.rounded_rectangle(
        [margin, 180, margin + section_width, 230],
        radius=10,
        fill=COLORS["badge_safe"]
    )
    draw.text(
        (margin + section_width // 2 - 20, 190),
        "DO",
        fill=COLORS["white"],
        font=fonts["card_title"]
    )

    # DO 항목들
    y_pos = 250
    for item in do_items[:5]:
        draw.text(
            (margin + 20, y_pos),
            f"✅ {item}",
            fill=COLORS["badge_safe"],
            font=fonts["card_desc"]
        )
        y_pos += 45

    # DON'T 섹션
    dont_x = margin * 2 + section_width

    # DON'T 제목
    draw.rounded_rectangle(
        [dont_x, 180, dont_x + section_width, 230],
        radius=10,
        fill=COLORS["badge_danger"]
    )
    draw.text(
        (dont_x + section_width // 2 - 40, 190),
        "DON'T",
        fill=COLORS["white"],
        font=fonts["card_title"]
    )

    # DON'T 항목들
    y_pos = 250
    for item in dont_items[:5]:
        draw.text(
            (dont_x + 20, y_pos),
            f"❌ {item}",
            fill=COLORS["badge_danger"],
            font=fonts["card_desc"]
        )
        y_pos += 45

    if output_path:
        img.save(output_path, "PNG")
        print(f"   ✅ 저장: {output_path}")

    return img


# === 테스트 실행 ===
if __name__ == "__main__":
    print("=" * 60)
    print("📊 Pillow 인포그래픽 생성기 테스트")
    print("=" * 60)

    output_dir = PROJECT_ROOT / "debug" / "infographic_test"
    output_dir.mkdir(parents=True, exist_ok=True)

    # 테스트 데이터 (당근)
    nutrients = [
        {"name": "베타카로틴", "benefit": "눈 건강", "value": "8,285", "unit": "μg"},
        {"name": "식이섬유", "benefit": "장 건강", "value": "2.8", "unit": "g"},
        {"name": "비타민 A", "benefit": "피부 보호", "value": "835", "unit": "μg"},
        {"name": "비타민 C", "benefit": "항산화", "value": "5.9", "unit": "mg"},
        {"name": "칼륨", "benefit": "심장 건강", "value": "320", "unit": "mg"},
        {"name": "칼로리", "benefit": "저칼로리", "value": "41", "unit": "kcal"},
    ]

    dosages = {
        "소형견": {"weight": "5kg 이하", "amount": "10~20g", "desc": "동전 크기 2~3조각"},
        "중형견": {"weight": "5~15kg", "amount": "20~40g", "desc": "손가락 한 마디 3~4조각"},
        "대형견": {"weight": "15~30kg", "amount": "40~60g", "desc": "중간 당근 1/3개"},
        "초대형견": {"weight": "30kg 이상", "amount": "60~80g", "desc": "중간 당근 1/2개"},
    }

    precautions = [
        {"title": "껍질 벗기기", "desc": "농약 잔류 가능성이 있으므로 껍질 제거 권장"},
        {"title": "작게 썰기", "desc": "질식 방지를 위해 작은 조각으로 잘라서 급여"},
        {"title": "익혀서 급여", "desc": "생으로도 가능하지만 익히면 소화가 더 쉬움"},
        {"title": "과다 급여 금지", "desc": "비타민 A 과다 섭취 주의, 적정량 준수"},
    ]

    steps = [
        {"title": "깨끗이 씻기", "desc": "흐르는 물에 깨끗이 세척합니다"},
        {"title": "껍질 벗기기", "desc": "필러로 껍질을 벗겨냅니다"},
        {"title": "작게 썰기", "desc": "강아지가 먹기 좋은 크기로 잘라줍니다"},
        {"title": "익히기 (선택)", "desc": "찌거나 삶아서 부드럽게 조리합니다"},
        {"title": "식혀서 급여", "desc": "적당히 식힌 후 급여합니다"},
    ]

    do_items = ["껍질 벗겨서 급여", "작게 잘라서 급여", "익혀서 급여 가능", "간식으로 소량 급여", "식힌 후 급여"]
    dont_items = ["통째로 급여 금지", "과다 급여 금지", "매일 급여 금지", "양념된 당근 금지", "통조림 당근 금지"]

    # 생성
    print("\n1. 영양정보 생성...")
    generate_nutrition_info(
        "당근", nutrients, "SAFE",
        "노령견에게 특히 좋은 베타카로틴이 풍부합니다",
        output_dir / "3_영양정보.png"
    )

    print("2. 급여 DO/DON'T 생성...")
    generate_do_dont(
        "당근", do_items, dont_items,
        output_dir / "4_급여가능불가.png"
    )

    print("3. 급여량표 생성...")
    generate_dosage_table(
        dosages,
        ["하루 칼로리의 10% 이내로 급여해주세요", "처음 급여 시 소량부터 시작하세요"],
        "개체별 차이가 있으므로 반응을 보며 조절하세요",
        output_dir / "5_급여량표.png"
    )

    print("4. 주의사항 생성...")
    generate_precautions(
        "당근", precautions,
        "이상 증상 발견 시 즉시 수의사와 상담하세요",
        output_dir / "6_주의사항.png"
    )

    print("5. 조리방법 생성...")
    generate_cooking_method(
        "당근", steps,
        "익힌 당근은 영양 흡수율이 더 높아요!",
        output_dir / "7_조리방법.png"
    )

    print("\n" + "=" * 60)
    print(f"✅ 테스트 완료! 결과 위치: {output_dir}")
    print("=" * 60)
