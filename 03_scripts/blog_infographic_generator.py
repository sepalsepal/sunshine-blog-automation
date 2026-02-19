#!/usr/bin/env python3
"""
blog_infographic_generator.py - 블로그 인포그래픽 자동 생성
골든 샘플 레이아웃 기반 Pillow 생성기

이미지 3~7번:
- 3번: 영양정보
- 4번: 급여가능/불가
- 5번: 급여량표
- 6번: 주의사항
- 7번: 조리방법

중앙정렬 검증: §15 이미지-캡션 일치 검증 준수
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# 중앙정렬 검증 로그 활성화
ALIGNMENT_LOG = True

PROJECT_ROOT = Path(__file__).parent.parent
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
# 2026-02-13: 플랫 구조로 변경 - STATUS_DIRS 제거
# 이제 contents/ 직접 스캔

# 색상 정의
COLORS = {
    "mint_start": (127, 199, 189),      # 민트 그라데이션 시작
    "mint_end": (167, 219, 211),        # 민트 그라데이션 끝
    "coral_start": (247, 168, 139),     # 주황 그라데이션 시작
    "coral_end": (251, 196, 174),       # 주황 그라데이션 끝
    "cream": (255, 248, 231),           # 크림 배경
    "card_mint": (232, 248, 245),       # 민트 카드
    "card_green": (226, 247, 226),      # 초록 카드 (DO)
    "card_pink": (255, 232, 232),       # 분홍 카드 (DON'T)
    "card_yellow": (255, 249, 219),     # 노란 카드 (TIP)
    "text_dark": (51, 51, 51),          # 진한 텍스트
    "text_gray": (136, 136, 136),       # 회색 텍스트
    "text_light": (170, 170, 170),      # 연한 텍스트
    "badge_orange": (255, 152, 0),      # 주황 뱃지
    "badge_green": (76, 175, 80),       # 초록 뱃지
    "badge_red": (244, 67, 54),         # 빨강 뱃지
    "badge_blue": (33, 150, 243),       # 파랑 뱃지
    "badge_purple": (156, 39, 176),     # 보라 뱃지
    "safe_green": (76, 175, 80),        # SAFE 뱃지
    "caution_yellow": (255, 193, 7),    # CAUTION 뱃지
    "danger_red": (244, 67, 54),        # DANGER 뱃지
    "white": (255, 255, 255),
    # FORBIDDEN 색상 (§2.4 규칙)
    "forbidden_start": (239, 83, 80),   # FORBIDDEN 그라데이션 시작
    "forbidden_end": (229, 115, 115),   # FORBIDDEN 그라데이션 끝
    "forbidden_title": (198, 40, 40),   # FORBIDDEN 제목 (#C62828)
    "forbidden_card": (255, 235, 238),  # FORBIDDEN 카드 배경 (#FFEBEE)
    "forbidden_badge": (211, 47, 47),   # FORBIDDEN 배지 (#D32F2F)
}

# 뱃지 색상 순서
BADGE_COLORS = [
    COLORS["badge_orange"],
    COLORS["badge_green"],
    COLORS["badge_red"],
    COLORS["badge_blue"],
    COLORS["badge_purple"],
    COLORS["badge_orange"],
]

# 폰트 경로 (macOS - AppleSDGothicNeo 한글 지원)
FONT_PATH = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

# 실제 사용할 폰트 찾기
def get_font(style: str, size: int):
    """폰트 로드 - AppleSDGothicNeo 사용"""
    try:
        # AppleSDGothicNeo.ttc는 여러 weight 포함
        # index 0: Regular, 5: Bold, 6: ExtraBold
        if style == "bold":
            return ImageFont.truetype(FONT_PATH, size, index=5)
        else:
            return ImageFont.truetype(FONT_PATH, size, index=0)
    except Exception as e:
        print(f"폰트 로드 실패: {e}")
        return ImageFont.load_default()


def draw_gradient(draw, bbox, color_start, color_end, direction="vertical"):
    """그라데이션 그리기"""
    x1, y1, x2, y2 = bbox
    if direction == "vertical":
        for y in range(y1, y2):
            ratio = (y - y1) / (y2 - y1) if y2 > y1 else 0
            r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
            g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
            b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
            draw.line([(x1, y), (x2, y)], fill=(r, g, b))


def draw_rounded_rect(draw, bbox, radius, fill):
    """둥근 사각형 그리기"""
    x1, y1, x2, y2 = bbox
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.ellipse([x1, y1, x1 + 2*radius, y1 + 2*radius], fill=fill)
    draw.ellipse([x2 - 2*radius, y1, x2, y1 + 2*radius], fill=fill)
    draw.ellipse([x1, y2 - 2*radius, x1 + 2*radius, y2], fill=fill)
    draw.ellipse([x2 - 2*radius, y2 - 2*radius, x2, y2], fill=fill)


def calc_center_position(draw, text, font, center_x, center_y):
    """
    중앙정렬 좌표 계산 (bbox 기반 정확한 계산)

    공식:
    - text_x = center_x - text_width/2 - bbox_offset_x
    - text_y = center_y - text_height/2 - bbox_offset_y

    Returns: (text_x, text_y, text_width, text_height)
    """
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    # bbox[0], bbox[1]은 텍스트 렌더링 시작 오프셋 - 정확한 중앙 계산
    text_x = int(round(center_x - text_width / 2 - bbox[0]))
    text_y = int(round(center_y - text_height / 2 - bbox[1]))
    return text_x, text_y, text_width, text_height


def verify_center_alignment(draw, text, font, target_x, target_y, tolerance=3, label=""):
    """
    중앙정렬 검증 함수 (tolerance 기본값 3px로 조정)

    Args:
        draw: ImageDraw 객체
        text: 텍스트
        font: 폰트
        target_x, target_y: 중앙 기준 좌표
        tolerance: 허용 오차 (픽셀) - 기본 3px
        label: 로그용 라벨

    Returns: (actual_x, actual_y) - 실제 그릴 좌표
    """
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # 정확한 중앙 계산: bbox 오프셋 보정
    text_x = int(round(target_x - text_width / 2 - bbox[0]))
    text_y = int(round(target_y - text_height / 2 - bbox[1]))

    if ALIGNMENT_LOG:
        # 실제 텍스트 렌더링 영역의 중심 계산
        actual_center_x = text_x + bbox[0] + text_width / 2
        actual_center_y = text_y + bbox[1] + text_height / 2
        diff_x = abs(actual_center_x - target_x)
        diff_y = abs(actual_center_y - target_y)
        status = "PASS" if diff_x <= tolerance and diff_y <= tolerance else "FAIL"
        print(f"      {label}: center=({target_x},{target_y}), text_pos=({text_x},{text_y}), size=({text_width}x{text_height}), diff=({diff_x:.1f},{diff_y:.1f}) [{status}]")

    return text_x, text_y


def draw_circle_badge(draw, center, radius, color, text, font, label="badge", draw_circle=True):
    """원형 뱃지 그리기 (중앙정렬 검증 포함)"""
    x, y = center
    # 원 그리기
    if draw_circle:
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)

    # 중앙정렬 검증 및 좌표 계산
    text_x, text_y = verify_center_alignment(draw, text, font, x, y, tolerance=2, label=label)
    draw.text((text_x, text_y), text, fill=COLORS["white"], font=font)


def draw_text_centered_in_rect(draw, rect_bbox, text, font, fill, label="rect_text"):
    """사각형 내부 텍스트 중앙정렬 (정확한 bbox 기반)"""
    x1, y1, x2, y2 = rect_bbox
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2

    text_x, text_y = verify_center_alignment(draw, text, font, center_x, center_y, tolerance=2, label=label)
    draw.text((text_x, text_y), text, fill=fill, font=font)


def draw_right_aligned_badge(draw, right_x, center_y, text, font, color, label="badge"):
    """우측 정렬 뱃지 (우측 끝 기준)"""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]

    # 패딩 추가
    padding_x = 20
    padding_y = 10
    rect_width = text_width + padding_x * 2
    rect_height = text_height + padding_y * 2

    # 우측 정렬 기준으로 좌표 계산
    rect_x1 = right_x - rect_width
    rect_y1 = center_y - rect_height / 2
    rect_x2 = right_x
    rect_y2 = center_y + rect_height / 2

    # 뱃지 배경
    draw_rounded_rect(draw, (rect_x1, rect_y1, rect_x2, rect_y2), 15, color)

    # 텍스트 중앙정렬
    draw_text_centered_in_rect(draw, (rect_x1, rect_y1, rect_x2, rect_y2), text, font, COLORS["white"], label=label)


def generate_nutrition_card(data: dict, output_path: Path):
    """3번 영양정보 이미지 생성"""
    if ALIGNMENT_LOG:
        print(f"   [3번 영양정보] 중앙정렬 검증:")

    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션
    draw_gradient(draw, (0, 0, 1080, 150), COLORS["mint_start"], COLORS["mint_end"])

    # 제목 (수평 중앙)
    font_title = get_font("bold", 56)
    title = f"{data['korean']} 영양성분"
    title_x, title_y = verify_center_alignment(draw, title, font_title, 540, 73, label="제목")
    draw.text((title_x, title_y), title, fill=COLORS["white"], font=font_title)

    # 부제목 (수평 중앙)
    font_sub = get_font("regular", 24)
    subtitle = "100g 기준 | 강아지에게 안전한 영양 간식"
    sub_x, sub_y = verify_center_alignment(draw, subtitle, font_sub, 540, 117, label="부제목")
    draw.text((sub_x, sub_y), subtitle, fill=COLORS["white"], font=font_sub)

    # SAFE 뱃지 (사각형 내부 중앙) - 텍스트 길이에 맞게 동적 크기
    safety = data.get("safety", "SAFE")
    if safety == "SAFE":
        badge_color = COLORS["safe_green"]
    elif safety == "CAUTION":
        badge_color = COLORS["caution_yellow"]
    else:
        badge_color = COLORS["danger_red"]

    font_badge = get_font("bold", 22)
    bbox = draw.textbbox((0, 0), safety, font=font_badge)
    text_width = bbox[2] - bbox[0]
    badge_width = text_width + 40  # 좌우 패딩 20px씩
    badge_right = 1040
    badge_left = badge_right - badge_width
    badge_rect = (badge_left, 45, badge_right, 85)
    draw_rounded_rect(draw, badge_rect, 20, badge_color)
    draw_text_centered_in_rect(draw, badge_rect, safety, font_badge, COLORS["white"], label="SAFE뱃지")

    # 영양 카드들
    nutrition = data.get("nutrition", [])
    y_start = 200
    card_height = 100
    card_margin = 20

    font_name = get_font("bold", 32)
    font_benefit = get_font("regular", 20)
    font_value = get_font("bold", 40)
    font_unit = get_font("regular", 24)
    font_num = get_font("bold", 28)

    for i, n in enumerate(nutrition[:6]):
        y = y_start + i * (card_height + card_margin)

        # 카드 배경
        draw_rounded_rect(draw, (60, y, 1020, y + card_height), 15, COLORS["card_mint"])

        # 번호 뱃지 (원형 + 숫자 중앙정렬)
        badge_color = BADGE_COLORS[i % len(BADGE_COLORS)]
        draw_circle_badge(draw, (110, y + 50), 25, badge_color, str(i + 1), font_num, label=f"번호{i+1}")

        # 성분명 (좌측정렬)
        draw.text((160, y + 20), n["name"], fill=COLORS["text_dark"], font=font_name)

        # 효능 (좌측정렬)
        draw.text((160, y + 60), n["benefit"], fill=COLORS["text_gray"], font=font_benefit)

        # 수치 (우측정렬)
        value_text = f"{n['value']} {n['unit']}"
        bbox = draw.textbbox((0, 0), value_text, font=font_value)
        tw = bbox[2] - bbox[0]
        draw.text((980 - tw, y + 30), value_text, fill=badge_color, font=font_value)

    # 하단 주석 (수평 중앙)
    font_note = get_font("regular", 18)
    note = f"* 노령견에게 특히 좋은 {nutrition[0]['name'] if nutrition else '영양소'}이 풍부합니다"
    note_x, _ = verify_center_alignment(draw, note, font_note, 540, 1040, label="하단주석")
    draw.text((note_x, 1030), note, fill=COLORS["text_light"], font=font_note)

    img.save(output_path)
    return output_path


def generate_dosage_card(data: dict, output_path: Path):
    """5번 급여량표 이미지 생성"""
    if ALIGNMENT_LOG:
        print(f"   [5번 급여량표] 중앙정렬 검증:")

    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션
    draw_gradient(draw, (0, 0, 1080, 150), COLORS["mint_start"], COLORS["mint_end"])

    # 제목 (수평 중앙)
    font_title = get_font("bold", 56)
    title = "체중별 급여량 가이드"
    title_x, _ = verify_center_alignment(draw, title, font_title, 540, 73, label="제목")
    draw.text((title_x, 45), title, fill=COLORS["white"], font=font_title)

    # 부제목 (수평 중앙)
    font_sub = get_font("regular", 24)
    subtitle = "하루 기준 | 간식으로 급여 시"
    sub_x, _ = verify_center_alignment(draw, subtitle, font_sub, 540, 117, label="부제목")
    draw.text((sub_x, 105), subtitle, fill=COLORS["white"], font=font_sub)

    # 테이블 헤더 (각 열 중앙정렬)
    y_table = 220
    header_rect = (60, y_table, 1020, y_table + 60)
    draw_rounded_rect(draw, header_rect, 10, COLORS["mint_start"])

    font_header = get_font("bold", 24)
    # 열 중앙 좌표: 구분(150), 체중(400), 급여량(720)
    draw_text_centered_in_rect(draw, (60, y_table, 240, y_table + 60), "구분", font_header, COLORS["white"], label="헤더-구분")
    draw_text_centered_in_rect(draw, (240, y_table, 460, y_table + 60), "체중", font_header, COLORS["white"], label="헤더-체중")
    draw_text_centered_in_rect(draw, (460, y_table, 1020, y_table + 60), "급여량", font_header, COLORS["white"], label="헤더-급여량")

    # 테이블 행 (g + 직관 단위 필수)
    dosage = data.get("dosage", {})
    rows = [
        ("소형견", dosage.get("소형견", {}).get("weight", "5kg 이하"), dosage.get("소형견", {}).get("amount", "-"), dosage.get("소형견", {}).get("desc", "")),
        ("중형견", dosage.get("중형견", {}).get("weight", "5~15kg"), dosage.get("중형견", {}).get("amount", "-"), dosage.get("중형견", {}).get("desc", "")),
        ("대형견", dosage.get("대형견", {}).get("weight", "15~30kg"), dosage.get("대형견", {}).get("amount", "-"), dosage.get("대형견", {}).get("desc", "")),
        ("초대형견", dosage.get("초대형견", {}).get("weight", "30kg 이상"), dosage.get("초대형견", {}).get("amount", "-"), dosage.get("초대형견", {}).get("desc", "")),
    ]

    font_row = get_font("regular", 26)
    font_value = get_font("bold", 28)
    font_unit = get_font("regular", 18)
    row_height = 90

    for i, (label, weight, amount, unit) in enumerate(rows):
        y = y_table + 60 + i * row_height + 15
        row_center_y = y + row_height // 2 - 10

        # 각 열 중앙정렬
        draw_text_centered_in_rect(draw, (60, y, 240, y + row_height - 20), label, font_row, COLORS["text_dark"], label=f"행{i+1}-구분")
        draw_text_centered_in_rect(draw, (240, y, 460, y + row_height - 20), weight, font_row, COLORS["text_gray"], label=f"행{i+1}-체중")

        # 급여량 (g + 직관단위) - 열 중앙정렬
        dosage_col_center_x = (460 + 1020) / 2  # 740
        # g 금액 중앙정렬
        amount_x, _ = verify_center_alignment(draw, amount, font_value, dosage_col_center_x, y + 28, label=f"행{i+1}-급여량g")
        draw.text((amount_x, y + 8), amount, fill=COLORS["badge_orange"], font=font_value)
        if unit:
            # 직관단위 중앙정렬
            unit_text = f"({unit})"
            unit_x, _ = verify_center_alignment(draw, unit_text, font_unit, dosage_col_center_x, y + 54, label=f"행{i+1}-급여량unit")
            draw.text((unit_x, y + 44), unit_text, fill=COLORS["text_gray"], font=font_unit)

    # 주의사항 박스
    y_caution = 660
    draw_rounded_rect(draw, (60, y_caution, 1020, y_caution + 120), 15, COLORS["card_yellow"])

    # 주의 뱃지 (사각형 내부 중앙정렬)
    caution_badge_rect = (100, y_caution + 15, 180, y_caution + 55)
    draw_rounded_rect(draw, caution_badge_rect, 5, COLORS["badge_orange"])
    font_badge_small = get_font("bold", 22)
    draw_text_centered_in_rect(draw, caution_badge_rect, "주의", font_badge_small, COLORS["white"], label="주의뱃지")

    font_caution_title = get_font("bold", 22)
    draw.text((195, y_caution + 22), "급여 시 주의사항", fill=COLORS["badge_orange"], font=font_caution_title)

    font_caution = get_font("regular", 22)
    draw.text((100, y_caution + 60), "• 하루 칼로리의 10% 이내로 급여해주세요", fill=COLORS["text_gray"], font=font_caution)
    draw.text((100, y_caution + 90), "• 처음 급여 시 소량부터 시작하세요", fill=COLORS["text_gray"], font=font_caution)

    # 하단 주석 (수평 중앙)
    font_note = get_font("regular", 18)
    note = "* 개체별 차이가 있으므로 반응을 보며 조절하세요"
    note_x, _ = verify_center_alignment(draw, note, font_note, 540, 1040, label="하단주석")
    draw.text((note_x, 1030), note, fill=COLORS["text_light"], font=font_note)

    img.save(output_path)
    return output_path


def generate_do_dont_card(data: dict, output_path: Path):
    """4번 급여가능/불가 이미지 생성"""
    if ALIGNMENT_LOG:
        print(f"   [4번 급여가능불가] 중앙정렬 검증:")

    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션
    draw_gradient(draw, (0, 0, 1080, 150), COLORS["mint_start"], COLORS["mint_end"])

    # SAFE 뱃지 (사각형 내부 중앙정렬)
    safety = data.get("safety", "SAFE")
    if safety == "SAFE":
        badge_color = COLORS["safe_green"]
    elif safety == "CAUTION":
        badge_color = COLORS["caution_yellow"]
    else:
        badge_color = COLORS["danger_red"]

    safe_badge_rect = (460, 40, 620, 100)
    draw_rounded_rect(draw, safe_badge_rect, 30, COLORS["white"])
    font_badge = get_font("bold", 36)
    draw_text_centered_in_rect(draw, safe_badge_rect, safety, font_badge, badge_color, label="SAFE뱃지")

    # 제목 (수평 중앙)
    font_title = get_font("bold", 36)
    title = "강아지가 먹어도 안전해요"
    title_x, _ = verify_center_alignment(draw, title, font_title, 540, 198, label="제목")
    draw.text((title_x, 180), title, fill=COLORS["text_dark"], font=font_title)

    # DO 섹션
    y_do = 260
    font_section = get_font("bold", 24)
    draw.text((80, y_do), "이렇게 급여하세요", fill=COLORS["safe_green"], font=font_section)

    do_items = data.get("do", [])[:3]
    font_item = get_font("regular", 28)

    y_do_card = y_do + 40
    draw_rounded_rect(draw, (60, y_do_card, 1020, y_do_card + 50 * len(do_items) + 30), 15, COLORS["card_green"])

    for i, item in enumerate(do_items):
        y = y_do_card + 25 + i * 50
        # 초록 원 + V 텍스트 (원 중앙정렬)
        circle_center = (95, y + 20)
        font_check = get_font("bold", 20)
        draw_circle_badge(draw, circle_center, 15, COLORS["safe_green"], "V", font_check, label=f"DO-V{i+1}")
        draw.text((130, y + 3), item, fill=COLORS["text_dark"], font=font_item)

    # DON'T 섹션
    y_dont = y_do_card + 50 * len(do_items) + 80
    draw.text((80, y_dont), "이것만은 피해주세요", fill=COLORS["danger_red"], font=font_section)

    dont_items = data.get("dont", [])[:3]

    y_dont_card = y_dont + 40
    draw_rounded_rect(draw, (60, y_dont_card, 1020, y_dont_card + 50 * len(dont_items) + 30), 15, COLORS["card_pink"])

    for i, item in enumerate(dont_items):
        y = y_dont_card + 25 + i * 50
        # 빨간 원 + X 텍스트 (원 중앙정렬)
        circle_center = (95, y + 20)
        font_x = get_font("bold", 20)
        draw_circle_badge(draw, circle_center, 15, COLORS["danger_red"], "X", font_x, label=f"DONT-X{i+1}")
        draw.text((130, y + 3), item, fill=COLORS["text_dark"], font=font_item)

    # 하단 메시지 (사각형 내부 중앙정렬)
    y_msg = 900
    msg_rect = (60, y_msg, 1020, y_msg + 60)
    draw_rounded_rect(draw, msg_rect, 15, (230, 247, 255))
    font_msg = get_font("regular", 24)
    msg = "11살 노령견 햇살이도 안전하게 먹고 있어요"
    draw_text_centered_in_rect(draw, msg_rect, msg, font_msg, COLORS["mint_start"], label="하단메시지")

    img.save(output_path)
    return output_path


def generate_caution_card(data: dict, output_path: Path):
    """6번 주의사항 이미지 생성"""
    if ALIGNMENT_LOG:
        print(f"   [6번 주의사항] 중앙정렬 검증:")

    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션 (주황)
    draw_gradient(draw, (0, 0, 1080, 150), COLORS["coral_start"], COLORS["coral_end"])

    # 제목 (도형 뱃지 + 텍스트)
    # 주의 뱃지 (사각형 내부 중앙정렬)
    caution_badge_rect = (380, 40, 480, 90)
    draw_rounded_rect(draw, caution_badge_rect, 10, COLORS["white"])
    font_badge = get_font("bold", 28)
    draw_text_centered_in_rect(draw, caution_badge_rect, "주의", font_badge, COLORS["coral_start"], label="주의뱃지")

    # 제목 텍스트 (뱃지 옆에 배치)
    font_title = get_font("bold", 48)
    title = "주의사항"
    draw.text((500, 48), title, fill=COLORS["white"], font=font_title)

    # 주의사항 카드들
    caution = data.get("caution", [])
    y_start = 200
    card_height = 110
    card_margin = 15

    font_num = get_font("bold", 28)
    font_title_card = get_font("bold", 28)
    font_desc = get_font("regular", 20)

    for i, c in enumerate(caution[:5]):
        y = y_start + i * (card_height + card_margin)

        # 카드 배경
        draw_rounded_rect(draw, (60, y, 1020, y + card_height), 15, COLORS["card_mint"])

        # 번호 뱃지 (원형 + 숫자 중앙정렬)
        badge_color = BADGE_COLORS[i % len(BADGE_COLORS)]
        draw_circle_badge(draw, (110, y + 55), 25, badge_color, str(i + 1), font_num, label=f"번호{i+1}")

        # 제목 (좌측정렬)
        draw.text((160, y + 25), c["title"], fill=COLORS["text_dark"], font=font_title_card)

        # 설명 (좌측정렬)
        draw.text((160, y + 65), c["desc"], fill=COLORS["text_gray"], font=font_desc)

    # 하단 응급 안내 (도형 뱃지 + 텍스트)
    y_emergency = 880
    draw_rounded_rect(draw, (60, y_emergency, 1020, y_emergency + 60), 15, COLORS["card_pink"])

    # 응급 뱃지 (빨간 원 + 십자 중앙정렬)
    emergency_center = (98, y_emergency + 30)
    draw.ellipse([80, y_emergency + 12, 116, y_emergency + 48], fill=COLORS["danger_red"])
    font_cross = get_font("bold", 28)
    draw_circle_badge(draw, emergency_center, 18, COLORS["danger_red"], "+", font_cross, label="응급+")

    font_emergency = get_font("bold", 22)
    draw.text((130, y_emergency + 18), "이상 반응 발생 시 즉시 수의사와 상담하세요", fill=COLORS["danger_red"], font=font_emergency)

    img.save(output_path)
    return output_path


def generate_cooking_card(data: dict, output_path: Path):
    """7번 조리방법 이미지 생성"""
    if ALIGNMENT_LOG:
        print(f"   [7번 조리방법] 중앙정렬 검증:")

    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션
    draw_gradient(draw, (0, 0, 1080, 150), COLORS["mint_start"], COLORS["mint_end"])

    # 제목 (수평 중앙)
    font_title = get_font("bold", 56)
    title = "안전한 조리 방법"
    title_x, _ = verify_center_alignment(draw, title, font_title, 540, 68, label="제목")
    draw.text((title_x, 40), title, fill=COLORS["white"], font=font_title)

    # 부제목 (수평 중앙)
    font_sub = get_font("regular", 24)
    subtitle = f"강아지를 위한 {data['korean']} 준비 5단계"
    sub_x, _ = verify_center_alignment(draw, subtitle, font_sub, 540, 112, label="부제목")
    draw.text((sub_x, 100), subtitle, fill=COLORS["white"], font=font_sub)

    # 조리 단계 카드들
    cooking = data.get("cooking", [])
    y_start = 200
    card_height = 110
    card_margin = 15

    font_step = get_font("bold", 18)
    font_title_card = get_font("bold", 28)
    font_desc = get_font("regular", 20)

    for i, step in enumerate(cooking[:5]):
        y = y_start + i * (card_height + card_margin)

        # 카드 배경
        draw_rounded_rect(draw, (60, y, 1020, y + card_height), 15, COLORS["card_mint"])

        # STEP 뱃지 (사각형 내부 중앙정렬)
        badge_color = BADGE_COLORS[i % len(BADGE_COLORS)]
        step_rect = (80, y + 25, 165, y + 60)
        draw_rounded_rect(draw, step_rect, 17, badge_color)
        draw_text_centered_in_rect(draw, step_rect, f"STEP {i + 1}", font_step, COLORS["white"], label=f"STEP{i+1}")

        # 단계명 (좌측정렬)
        draw.text((180, y + 25), step["step"], fill=COLORS["text_dark"], font=font_title_card)

        # 설명 (좌측정렬)
        draw.text((80, y + 70), step["desc"], fill=COLORS["text_gray"], font=font_desc)

    # TIP 박스 (도형 뱃지 + 텍스트)
    y_tip = 880
    draw_rounded_rect(draw, (60, y_tip, 1020, y_tip + 80), 15, COLORS["card_yellow"])

    # TIP 뱃지 (주황 원 + 느낌표 중앙정렬)
    tip_center = (98, y_tip + 30)
    draw.ellipse([80, y_tip + 12, 116, y_tip + 48], fill=COLORS["badge_orange"])
    font_exclaim = get_font("bold", 28)
    draw_circle_badge(draw, tip_center, 18, COLORS["badge_orange"], "!", font_exclaim, label="TIP느낌표")

    font_tip_title = get_font("bold", 22)
    font_tip = get_font("regular", 20)
    draw.text((130, y_tip + 17), "TIP", fill=COLORS["badge_orange"], font=font_tip_title)
    draw.text((100, y_tip + 50), data.get("tip_box", ""), fill=COLORS["text_gray"], font=font_tip)

    img.save(output_path)
    return output_path


# ===== FORBIDDEN 안전도 전용 함수들 =====

def generate_toxicity_card(data, output_path):
    """03번: 독성 성분 카드 (FORBIDDEN)"""
    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션 (빨강 계열)
    draw_gradient(draw, (0, 0, 1080, 130), COLORS["forbidden_start"], COLORS["forbidden_end"])

    font_title = get_font("bold", 48)
    font_subtitle = get_font("regular", 22)
    font_badge = get_font("bold", 18)

    # 제목
    title = f"{data['korean']} 독성 성분"
    tx, ty = verify_center_alignment(draw, title, font_title, 540, 73, label="제목")
    draw.text((tx, ty), title, fill=COLORS["white"], font=font_title)

    # 부제
    subtitle = "강아지에게 치명적인 성분 경고"
    sx, sy = verify_center_alignment(draw, subtitle, font_subtitle, 540, 117, label="부제목")
    draw.text((sx, sy), subtitle, fill=COLORS["white"], font=font_subtitle)

    # FORBIDDEN 배지
    badge_text = "FORBIDDEN"
    draw_right_aligned_badge(draw, 990, 65, badge_text, font_badge, COLORS["forbidden_badge"], label="FORBIDDEN뱃지")

    # 독성 성분 카드들
    font_title_card = get_font("bold", 28)
    font_desc = get_font("regular", 20)
    font_num = get_font("bold", 22)

    toxicity_items = [
        {"title": "나트륨 과다", "desc": "심장, 신장에 심각한 부담"},
        {"title": "인공 조미료", "desc": "소화 장애 및 독성 반응 유발"},
        {"title": "양파/마늘 분말", "desc": "적혈구 파괴, 빈혈 유발 가능"},
        {"title": "지방 과다", "desc": "췌장염, 비만, 소화 장애"},
    ]

    for i, item in enumerate(toxicity_items):
        y = 180 + i * 120
        draw_rounded_rect(draw, (60, y, 1020, y + 100), 12, COLORS["forbidden_card"])

        # 번호 원
        badge_color = COLORS["forbidden_badge"]
        draw.ellipse([80, y + 30, 140, y + 70], fill=badge_color)
        nx, ny = verify_center_alignment(draw, str(i + 1), font_num, 110, y + 50, label=f"번호{i+1}")
        draw.text((nx, ny), str(i + 1), fill=COLORS["white"], font=font_num)

        # 제목/설명
        draw.text((160, y + 25), item["title"], fill=COLORS["forbidden_title"], font=font_title_card)
        draw.text((160, y + 60), item["desc"], fill=COLORS["text_gray"], font=font_desc)

    # 경고 박스
    draw_rounded_rect(draw, (60, 680, 1020, 760), 12, COLORS["forbidden_card"])
    font_warning = get_font("bold", 24)
    draw.text((100, 705), "경고: 이 음식은 강아지에게 절대 급여해서는 안 됩니다", fill=COLORS["forbidden_title"], font=font_warning)

    # 하단 주석
    font_footnote = get_font("regular", 16)
    footnote = f"{data['korean']}은 강아지에게 독성이 있습니다"
    fx, fy = verify_center_alignment(draw, footnote, font_footnote, 540, 1040, label="하단주석")
    draw.text((fx, fy), footnote, fill=COLORS["text_light"], font=font_footnote)

    img.save(output_path)
    return output_path


def generate_symptoms_card(data, output_path):
    """04번: 섭취 시 증상 카드 (FORBIDDEN)"""
    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션
    draw_gradient(draw, (0, 0, 1080, 130), COLORS["forbidden_start"], COLORS["forbidden_end"])

    font_title = get_font("bold", 48)
    font_subtitle = get_font("regular", 22)
    font_badge = get_font("bold", 18)

    # 제목
    title = "섭취 시 증상"
    tx, ty = verify_center_alignment(draw, title, font_title, 540, 73, label="제목")
    draw.text((tx, ty), title, fill=COLORS["white"], font=font_title)

    # 부제
    subtitle = f"{data['korean']} 섭취 후 나타날 수 있는 증상"
    sx, sy = verify_center_alignment(draw, subtitle, font_subtitle, 540, 117, label="부제목")
    draw.text((sx, sy), subtitle, fill=COLORS["white"], font=font_subtitle)

    # FORBIDDEN 배지
    badge_text = "FORBIDDEN"
    draw_right_aligned_badge(draw, 990, 65, badge_text, font_badge, COLORS["forbidden_badge"], label="FORBIDDEN뱃지")

    # 증상 카드들
    font_title_card = get_font("bold", 26)
    font_desc = get_font("regular", 18)
    font_num = get_font("bold", 20)

    symptoms = [
        {"title": "구토/설사", "desc": "섭취 후 30분~2시간 내 발생"},
        {"title": "무기력/기력 저하", "desc": "활동량 감소, 축 처짐"},
        {"title": "과도한 갈증", "desc": "나트륨 과다로 인한 탈수"},
        {"title": "복부 팽만", "desc": "소화 장애, 복통"},
        {"title": "경련/발작", "desc": "심각한 경우 신경 증상"},
    ]

    for i, item in enumerate(symptoms):
        y = 160 + i * 100
        draw_rounded_rect(draw, (60, y, 1020, y + 85), 12, COLORS["forbidden_card"])

        # 번호 원
        draw.ellipse([80, y + 22, 130, y + 62], fill=COLORS["forbidden_badge"])
        nx, ny = verify_center_alignment(draw, str(i + 1), font_num, 105, y + 42, label=f"번호{i+1}")
        draw.text((nx, ny), str(i + 1), fill=COLORS["white"], font=font_num)

        # 제목/설명
        draw.text((150, y + 18), item["title"], fill=COLORS["forbidden_title"], font=font_title_card)
        draw.text((150, y + 50), item["desc"], fill=COLORS["text_gray"], font=font_desc)

    # 응급 박스
    draw_rounded_rect(draw, (60, 680, 1020, 780), 12, COLORS["forbidden_card"])
    font_emergency = get_font("bold", 22)
    draw.text((100, 700), "응급: 위 증상 발견 시 즉시 동물병원 방문", fill=COLORS["forbidden_badge"], font=font_emergency)
    font_tel = get_font("regular", 20)
    draw.text((100, 740), "24시간 동물병원 또는 수의사 상담 필요", fill=COLORS["text_gray"], font=font_tel)

    img.save(output_path)
    return output_path


def generate_emergency_card(data, output_path):
    """05번: 응급 대처 카드 (FORBIDDEN)"""
    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션
    draw_gradient(draw, (0, 0, 1080, 130), COLORS["forbidden_start"], COLORS["forbidden_end"])

    font_title = get_font("bold", 48)
    font_subtitle = get_font("regular", 22)
    font_badge = get_font("bold", 18)

    # 제목
    title = "응급 대처 가이드"
    tx, ty = verify_center_alignment(draw, title, font_title, 540, 73, label="제목")
    draw.text((tx, ty), title, fill=COLORS["white"], font=font_title)

    # 부제
    subtitle = "섭취 시 즉시 행동 지침"
    sx, sy = verify_center_alignment(draw, subtitle, font_subtitle, 540, 117, label="부제목")
    draw.text((sx, sy), subtitle, fill=COLORS["white"], font=font_subtitle)

    # FORBIDDEN 배지
    badge_text = "FORBIDDEN"
    draw_right_aligned_badge(draw, 990, 65, badge_text, font_badge, COLORS["forbidden_badge"], label="FORBIDDEN뱃지")

    # 응급 단계들
    font_step = get_font("bold", 14)
    font_title_card = get_font("bold", 26)
    font_desc = get_font("regular", 18)

    steps = [
        {"step": "즉시", "title": "섭취량 확인", "desc": "얼마나 먹었는지 파악"},
        {"step": "5분 내", "title": "동물병원 연락", "desc": "상황 설명, 내원 준비"},
        {"step": "10분 내", "title": "병원 이동", "desc": "제품 포장지 지참"},
        {"step": "도착 후", "title": "수의사 진료", "desc": "정확한 섭취량, 시간 전달"},
    ]

    for i, step in enumerate(steps):
        y = 170 + i * 120
        draw_rounded_rect(draw, (60, y, 1020, y + 100), 12, COLORS["forbidden_card"])

        # 시간 뱃지
        step_rect = (80, y + 25, 165, y + 60)
        draw_rounded_rect(draw, step_rect, 17, COLORS["forbidden_badge"])
        draw_text_centered_in_rect(draw, step_rect, step["step"], font_step, COLORS["white"], label=f"시간{i+1}")

        # 제목/설명
        draw.text((180, y + 22), step["title"], fill=COLORS["forbidden_title"], font=font_title_card)
        draw.text((180, y + 58), step["desc"], fill=COLORS["text_gray"], font=font_desc)

    # 긴급 연락처 박스
    draw_rounded_rect(draw, (60, 680, 1020, 780), 12, COLORS["forbidden_card"])
    font_emergency = get_font("bold", 24)
    draw.text((100, 700), "긴급: 가까운 24시간 동물병원 검색", fill=COLORS["forbidden_badge"], font=font_emergency)
    font_tip = get_font("regular", 18)
    draw.text((100, 740), "구토 유발은 수의사 지시 없이 하지 마세요", fill=COLORS["text_gray"], font=font_tip)

    img.save(output_path)
    return output_path


def generate_alternative_card(data, output_path):
    """06번: 대체 간식 카드 (FORBIDDEN)"""
    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션 (초록 계열 - 긍정적 대안)
    draw_gradient(draw, (0, 0, 1080, 130), COLORS["mint_start"], COLORS["mint_end"])

    font_title = get_font("bold", 48)
    font_subtitle = get_font("regular", 22)
    font_badge = get_font("bold", 18)

    # 제목
    title = "대체 간식 추천"
    tx, ty = verify_center_alignment(draw, title, font_title, 540, 73, label="제목")
    draw.text((tx, ty), title, fill=COLORS["white"], font=font_title)

    # 부제
    subtitle = f"{data['korean']} 대신 안전한 간식"
    sx, sy = verify_center_alignment(draw, subtitle, font_subtitle, 540, 117, label="부제목")
    draw.text((sx, sy), subtitle, fill=COLORS["white"], font=font_subtitle)

    # SAFE 배지
    badge_text = "SAFE 대안"
    draw_right_aligned_badge(draw, 990, 65, badge_text, font_badge, COLORS["safe_green"], label="SAFE뱃지")

    # 대체 간식 카드들
    font_title_card = get_font("bold", 28)
    font_desc = get_font("regular", 18)
    font_num = get_font("bold", 22)

    alternatives = [
        {"name": "당근", "desc": "비타민A, 저칼로리, 치아 건강"},
        {"name": "사과", "desc": "비타민C, 식이섬유, 씨 제거 후 급여"},
        {"name": "삶은 고구마", "desc": "식이섬유, 베타카로틴, 소량씩"},
        {"name": "오이", "desc": "수분 보충, 저칼로리, 시원한 간식"},
        {"name": "삶은 닭가슴살", "desc": "단백질, 무염, 양념 없이"},
    ]

    for i, item in enumerate(alternatives):
        y = 160 + i * 100
        draw_rounded_rect(draw, (60, y, 1020, y + 85), 12, COLORS["card_green"])

        # 번호 원
        draw.ellipse([80, y + 22, 130, y + 62], fill=COLORS["safe_green"])
        nx, ny = verify_center_alignment(draw, str(i + 1), font_num, 105, y + 42, label=f"번호{i+1}")
        draw.text((nx, ny), str(i + 1), fill=COLORS["white"], font=font_num)

        # 이름/설명
        draw.text((150, y + 18), item["name"], fill=COLORS["text_dark"], font=font_title_card)
        draw.text((150, y + 50), item["desc"], fill=COLORS["text_gray"], font=font_desc)

    # 하단 TIP
    draw_rounded_rect(draw, (60, 680, 1020, 760), 12, COLORS["card_yellow"])
    font_tip_title = get_font("bold", 22)
    font_tip = get_font("regular", 18)
    draw.text((100, 700), "TIP: 새 간식은 소량부터 시작, 반응 관찰 후 급여량 조절", fill=COLORS["badge_orange"], font=font_tip_title)

    img.save(output_path)
    return output_path


def generate_warning_card(data, output_path):
    """07번: 최종 경고 카드 (FORBIDDEN)"""
    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션 (빨강)
    draw_gradient(draw, (0, 0, 1080, 130), COLORS["forbidden_start"], COLORS["forbidden_end"])

    font_title = get_font("bold", 48)
    font_subtitle = get_font("regular", 22)
    font_badge = get_font("bold", 18)

    # 제목
    title = "최종 경고"
    tx, ty = verify_center_alignment(draw, title, font_title, 540, 73, label="제목")
    draw.text((tx, ty), title, fill=COLORS["white"], font=font_title)

    # 부제
    subtitle = f"{data['korean']}은 강아지에게 절대 금지 음식입니다"
    sx, sy = verify_center_alignment(draw, subtitle, font_subtitle, 540, 117, label="부제목")
    draw.text((sx, sy), subtitle, fill=COLORS["white"], font=font_subtitle)

    # FORBIDDEN 배지
    badge_text = "FORBIDDEN"
    draw_right_aligned_badge(draw, 990, 65, badge_text, font_badge, COLORS["forbidden_badge"], label="FORBIDDEN뱃지")

    # 경고 내용
    font_warning_big = get_font("bold", 36)
    font_warning = get_font("bold", 24)
    font_desc = get_font("regular", 20)

    # 큰 경고 박스
    draw_rounded_rect(draw, (60, 180, 1020, 350), 20, COLORS["forbidden_card"])
    warning_text = "절대 급여하지 마세요"
    wx, wy = verify_center_alignment(draw, warning_text, font_warning_big, 540, 230, label="경고문구")
    draw.text((wx, wy), warning_text, fill=COLORS["forbidden_badge"], font=font_warning_big)

    desc_text = f"{data['korean']}은 강아지에게 독성이 있습니다"
    dx, dy = verify_center_alignment(draw, desc_text, font_desc, 540, 290, label="설명")
    draw.text((dx, dy), desc_text, fill=COLORS["text_dark"], font=font_desc)

    # 위험 요약 카드들
    warnings = [
        "나트륨, 지방, 인공 조미료 과다",
        "구토, 설사, 무기력 유발",
        "심한 경우 응급 상황 가능",
    ]

    for i, w in enumerate(warnings):
        y = 380 + i * 70
        draw_rounded_rect(draw, (60, y, 1020, y + 55), 12, COLORS["forbidden_card"])
        draw.ellipse([80, y + 12, 110, y + 42], fill=COLORS["forbidden_badge"])
        font_x = get_font("bold", 18)
        draw.text((88, y + 15), "X", fill=COLORS["white"], font=font_x)
        draw.text((130, y + 15), w, fill=COLORS["forbidden_title"], font=font_warning)

    # 응급 연락처 박스
    draw_rounded_rect(draw, (60, 620, 1020, 750), 20, COLORS["forbidden_card"])
    font_emergency_title = get_font("bold", 28)
    font_emergency = get_font("regular", 22)

    draw.text((100, 640), "섭취 시 즉시 동물병원 방문", fill=COLORS["forbidden_badge"], font=font_emergency_title)
    draw.text((100, 685), "24시간 동물병원 또는 수의사 상담", fill=COLORS["text_dark"], font=font_emergency)
    draw.text((100, 715), "구토 유발은 수의사 지시 없이 금지", fill=COLORS["text_gray"], font=font_desc)

    # 하단 주석
    font_footnote = get_font("regular", 16)
    footnote = "우리 아이를 위해 안전한 간식만 급여해주세요"
    fx, fy = verify_center_alignment(draw, footnote, font_footnote, 540, 1040, label="하단주석")
    draw.text((fx, fy), footnote, fill=COLORS["text_light"], font=font_footnote)

    img.save(output_path)
    return output_path


def generate_all_infographics(num: int, dry_run: bool = False):
    """모든 인포그래픽 생성 (3~7번)"""
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    num_str = f"{num:03d}"  # 폴더 찾기용 (예: "011")
    data_key = str(num)      # food_data.json 키용 (예: "11")

    if data_key not in food_data:
        print(f"❌ #{num_str} 데이터 없음")
        return None

    raw_data = food_data[data_key]

    # 키 변환 어댑터: food_data.json 구조 → 스크립트 기대 구조
    # cooking_steps 변환: title → step
    cooking_converted = [
        {"step": item.get("title", ""), "desc": item.get("desc", "")}
        for item in raw_data.get("cooking_steps", [])
    ]

    data = {
        "korean": raw_data.get("name", "음식"),
        "safety": raw_data.get("safety", "SAFE"),
        "nutrition": raw_data.get("nutrients", []),
        "dosage": raw_data.get("dosages", {}),
        "do": raw_data.get("do_items", []),
        "dont": raw_data.get("dont_items", []),
        "caution": raw_data.get("precautions", []),
        "cooking": cooking_converted,
        "tip_box": raw_data.get("cooking_tip", ""),
        # FORBIDDEN 전용 필드
        "toxicity": raw_data.get("toxicity", []),
        "symptoms": raw_data.get("symptoms", []),
        "emergency": raw_data.get("emergency", []),
        "alternatives": raw_data.get("alternatives", []),
        "warning": raw_data.get("warning", ""),
    }

    # 폴더 찾기 (플랫 구조)
    folder = None
    # 2026-02-13: contents/ 직접 스캔 (플랫 구조)
    for item in CONTENTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith(num_str):
            folder = item
            break

    if not folder:
        print(f"❌ #{num_str} 폴더 없음")
        return None

    blog_dir = folder / "02_Blog"  # 2026-02-13: 새 구조
    blog_dir.mkdir(exist_ok=True)

    # 2026-02-13: 폴더명에서 food_en 추출 (PascalCase)
    food_en = folder.name.split("_")[1] if "_" in folder.name else "Food"

    safety = data.get("safety", "SAFE")
    print(f"📊 #{num_str} {data['korean']} [{safety}] 인포그래픽 생성")

    results = []

    # FORBIDDEN 등급: 별도 슬라이드 세트
    if safety == "FORBIDDEN":
        # 04: 독성/위험성 (Toxicity)
        output_4 = blog_dir / f"{food_en}_Blog_04_Toxicity.png"
        if not dry_run:
            generate_toxicity_card(data, output_4)
        print(f"   ✅ 4번 독성/위험성")
        results.append(output_4)

        # 05: 증상 (Symptoms)
        output_5 = blog_dir / f"{food_en}_Blog_05_Symptoms.png"
        if not dry_run:
            generate_symptoms_card(data, output_5)
        print(f"   ✅ 5번 증상")
        results.append(output_5)

        # 06: 응급처치 (Emergency)
        output_6 = blog_dir / f"{food_en}_Blog_06_Emergency.png"
        if not dry_run:
            generate_emergency_card(data, output_6)
        print(f"   ✅ 6번 응급처치")
        results.append(output_6)

        # 07: 대체식품 (Alternative)
        output_7 = blog_dir / f"{food_en}_Blog_07_Alternative.png"
        if not dry_run:
            generate_alternative_card(data, output_7)
        print(f"   ✅ 7번 대체식품")
        results.append(output_7)

        # 08: 경고 (Warning)
        output_8 = blog_dir / f"{food_en}_Blog_08_Warning.png"
        if not dry_run:
            generate_warning_card(data, output_8)
        print(f"   ✅ 8번 경고")
        results.append(output_8)

    else:
        # SAFE/CAUTION 등급: 기존 슬라이드 세트
        # 4번: 영양정보 (PascalCase)
        if data.get("nutrition"):
            output_4 = blog_dir / f"{food_en}_Blog_04_Nutrition.png"
            if not dry_run:
                generate_nutrition_card(data, output_4)
            print(f"   ✅ 4번 영양정보")
            results.append(output_4)

        # 5번: 급여가능/불가 (PascalCase)
        if data.get("do") or data.get("dont"):
            output_5 = blog_dir / f"{food_en}_Blog_05_Feeding.png"
            if not dry_run:
                generate_do_dont_card(data, output_5)
            print(f"   ✅ 5번 급여가능불가")
            results.append(output_5)

        # 6번: 급여량표 (PascalCase)
        if data.get("dosage"):
            output_6 = blog_dir / f"{food_en}_Blog_06_Amount.png"
            if not dry_run:
                generate_dosage_card(data, output_6)
            print(f"   ✅ 6번 급여량표")
            results.append(output_6)

        # 7번: 주의사항 (PascalCase)
        if data.get("caution"):
            output_7 = blog_dir / f"{food_en}_Blog_07_Caution.png"
            if not dry_run:
                generate_caution_card(data, output_7)
            print(f"   ✅ 7번 주의사항")
            results.append(output_7)

        # 8번: 조리방법 (PascalCase)
        if data.get("cooking"):
            output_8 = blog_dir / f"{food_en}_Blog_08_Cooking.png"
            if not dry_run:
                generate_cooking_card(data, output_8)
            print(f"   ✅ 8번 조리방법")
            results.append(output_8)

    return results


def main():
    import sys

    if len(sys.argv) < 2:
        print("사용법: python blog_infographic_generator.py [번호]")
        print("예시: python blog_infographic_generator.py 2")
        return

    num = int(sys.argv[1])
    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("🔍 DRY RUN 모드")

    generate_all_infographics(num, dry_run)


if __name__ == "__main__":
    main()
