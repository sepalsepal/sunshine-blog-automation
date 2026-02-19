#!/usr/bin/env python3
"""
golden_slide_generator.py - 안전도별 블로그 골든 샘플 생성
BLOG_SLIDE_DESIGN_RULE.md 규칙 기반 Pillow 생성기

대상: rules/02_Image/Blog_04-07/{SAFE|CAUTION|DANGER|FORBIDDEN}/
생성: Golden_Blog_{Safety}_03~07.png (각 안전도별 5개)

v1.0 - 2026-02-14
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
GOLDEN_DIR = PROJECT_ROOT / "00_rules" / "02_Image_rules" / "Blog_04-07"

# 해상도: 1080 x 1350px (4:5 세로)
WIDTH = 1080
HEIGHT = 1350

# 안전도별 색상 체계 (BLOG_SLIDE_DESIGN_RULE.md 기준)
SAFETY_COLORS = {
    "SAFE": {
        "header_start": (126, 206, 193),   # #7ECEC1
        "header_end": (168, 222, 210),     # #A8DED2
        "card_bg": (232, 246, 243),        # #E8F6F3
        "badge": (76, 175, 80),            # #4CAF50
        "accent": (76, 175, 80),           # #4CAF50
        "do_card": (232, 246, 232),        # #E8F6E8
        "dont_card": (253, 232, 232),      # #FDE8E8
        "tip_card": (255, 248, 225),       # #FFF8E1
    },
    "CAUTION": {
        "header_start": (255, 217, 61),    # #FFD93D
        "header_end": (255, 230, 128),     # #FFE680
        "card_bg": (255, 248, 225),        # #FFF8E1
        "badge": (255, 217, 61),           # #FFD93D
        "accent": (249, 168, 37),          # #F9A825
        "do_card": (232, 246, 232),        # #E8F6E8
        "dont_card": (253, 232, 232),      # #FDE8E8
        "tip_card": (255, 253, 231),       # #FFFDE7
    },
    "DANGER": {
        "header_start": (255, 107, 107),   # #FF6B6B
        "header_end": (255, 155, 155),     # #FF9B9B
        "card_bg": (253, 232, 232),        # #FDE8E8
        "badge": (255, 107, 107),          # #FF6B6B
        "accent": (229, 57, 53),           # #E53935
        "do_card": (232, 246, 232),        # #E8F6E8
        "dont_card": (253, 232, 232),      # #FDE8E8
        "tip_card": (255, 235, 238),       # #FFEBEE
    },
    "FORBIDDEN": {
        "header_start": (255, 82, 82),     # #FF5252
        "header_end": (255, 123, 123),     # #FF7B7B
        "card_bg": (255, 235, 238),        # #FFEBEE
        "badge": (255, 82, 82),            # #FF5252
        "accent": (211, 47, 47),           # #D32F2F
        "do_card": (232, 246, 232),        # #E8F6E8
        "dont_card": (255, 205, 210),      # #FFCDD2
        "tip_card": (255, 235, 238),       # #FFEBEE
    },
}

# 공통 색상
COLORS = {
    "cream": (255, 248, 240),          # #FFF8F0 배경
    "white": (255, 255, 255),
    "text_dark": (51, 51, 51),         # #333333
    "text_gray": (136, 136, 136),      # #888888
    "text_light": (170, 170, 170),     # #AAAAAA
    "check_green": (76, 175, 80),      # #4CAF50
    "x_red": (239, 83, 80),            # #EF5350
}

# 뱃지 색상 순환
BADGE_COLORS = [
    (255, 167, 38),   # 주황 #FFA726
    (102, 187, 106),  # 초록 #66BB6A
    (239, 83, 80),    # 빨강 #EF5350
    (66, 165, 245),   # 파랑 #42A5F5
    (171, 71, 188),   # 보라 #AB47BC
]

# ============================================================================
# 폰트 설정 (SAFE 기준 - 모든 안전도에 동일 적용)
# ============================================================================
# AppleSDGothicNeo.ttc 인덱스:
#   0 = Regular, 1 = Thin, 2 = UltraLight, 3 = Light
#   4 = Medium, 5 = SemiBold, 6 = Bold, 7 = Heavy (ExtraBold)
FONT_PATH = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

# SAFE 기준 폰트 크기 (모든 안전도에 동일 적용)
FONT_SIZES = {
    "header_title": 52,      # 헤더 제목: ExtraBold 48~56px → 52px
    "header_sub": 20,        # 헤더 부제: Regular 20px
    "card_title": 30,        # 카드 제목: Bold 28~32px → 30px
    "card_desc": 20,         # 카드 설명: Regular 18~20px → 20px
    "value": 38,             # 수치/강조: ExtraBold 36~40px → 38px
    "badge": 14,             # 배지 텍스트: Bold 12~14px → 14px
    "note": 16,              # 하단 주석: Regular 16px
}

# 안전도별 배지 너비 (overflow 방지 - padding 포함)
BADGE_WIDTHS = {
    "SAFE": 80,
    "CAUTION": 115,
    "DANGER": 105,
    "FORBIDDEN": 135,
}


def get_font(style: str, size: int):
    """폰트 로드 - AppleSDGothicNeo (SAFE 기준 통일)"""
    try:
        if style == "extrabold":
            return ImageFont.truetype(FONT_PATH, size, index=7)  # Heavy
        elif style == "bold":
            return ImageFont.truetype(FONT_PATH, size, index=6)  # Bold
        elif style == "semibold":
            return ImageFont.truetype(FONT_PATH, size, index=5)  # SemiBold
        else:  # regular
            return ImageFont.truetype(FONT_PATH, size, index=0)  # Regular
    except Exception as e:
        print(f"폰트 로드 실패: {e}")
        return ImageFont.load_default()


def draw_gradient(draw, bbox, color_start, color_end):
    """수직 그라데이션"""
    x1, y1, x2, y2 = bbox
    for y in range(y1, y2):
        ratio = (y - y1) / (y2 - y1) if y2 > y1 else 0
        r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
        g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
        b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
        draw.line([(x1, y), (x2, y)], fill=(r, g, b))


def draw_rounded_rect(draw, bbox, radius, fill):
    """둥근 사각형"""
    x1, y1, x2, y2 = bbox
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.ellipse([x1, y1, x1 + 2*radius, y1 + 2*radius], fill=fill)
    draw.ellipse([x2 - 2*radius, y1, x2, y1 + 2*radius], fill=fill)
    draw.ellipse([x1, y2 - 2*radius, x1 + 2*radius, y2], fill=fill)
    draw.ellipse([x2 - 2*radius, y2 - 2*radius, x2, y2], fill=fill)


def draw_text_centered(draw, text, font, x, y, fill):
    """텍스트 중앙정렬 (x, y가 중심점)"""
    bbox = draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    text_height = bbox[3] - bbox[1]
    text_x = int(x - text_width / 2 - bbox[0])
    text_y = int(y - text_height / 2 - bbox[1])
    draw.text((text_x, text_y), text, fill=fill, font=font)


def draw_text_centered_in_rect(draw, rect_bbox, text, font, fill):
    """사각형 내부 텍스트 중앙정렬"""
    x1, y1, x2, y2 = rect_bbox
    center_x = (x1 + x2) / 2
    center_y = (y1 + y2) / 2
    draw_text_centered(draw, text, font, center_x, center_y, fill)


def draw_circle_badge(draw, center, radius, color, text, font):
    """원형 뱃지"""
    x, y = center
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)
    draw_text_centered(draw, text, font, x, y, COLORS["white"])


# =============================================================================
# 슬라이드별 생성 함수
# =============================================================================

def generate_03_nutrition(safety: str, food_data: dict, output_path: Path):
    """03번 영양성분 / 독성성분 슬라이드"""
    colors = SAFETY_COLORS[safety]

    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션 (120px)
    draw_gradient(draw, (0, 0, WIDTH, 120), colors["header_start"], colors["header_end"])

    # 제목 (SAFE 기준 통일)
    font_title = get_font("extrabold", FONT_SIZES["header_title"])
    title = food_data.get("title", f"{food_data['korean']} 영양성분")
    if safety == "FORBIDDEN":
        title = f"{food_data['korean']} 독성 성분"
    elif safety == "DANGER":
        title = f"{food_data['korean']} 성분 분석"
    draw_text_centered(draw, title, font_title, WIDTH / 2, 50, COLORS["white"])

    # 부제 (SAFE 기준 통일)
    font_sub = get_font("regular", FONT_SIZES["header_sub"])
    subtitle = food_data.get("subtitle", "100g 기준 | 강아지에게 안전한 영양 간식")
    if safety == "CAUTION":
        subtitle = "100g 기준 | 적정량 급여 시 도움이 되는 영양소"
    elif safety == "DANGER":
        subtitle = "100g 기준 | 위험 성분 포함 주의"
    elif safety == "FORBIDDEN":
        subtitle = "강아지에게 치명적인 성분 경고"
    draw_text_centered(draw, subtitle, font_sub, WIDTH / 2, 95, (255, 255, 255, 204))

    # 안전도 배지 (우측 상단) - 동적 너비
    badge_width = BADGE_WIDTHS.get(safety, 100)
    badge_rect = (WIDTH - 24 - badge_width, 24, WIDTH - 24, 24 + 36)
    draw_rounded_rect(draw, badge_rect, 18, colors["badge"])
    font_badge = get_font("bold", 14)
    draw_text_centered_in_rect(draw, badge_rect, safety, font_badge, COLORS["white"])

    # 영양소 카드들 (6개)
    nutrition = food_data.get("nutrition", [
        {"name": "베타카로틴", "benefit": "눈 건강", "value": "8,285", "unit": "μg"},
        {"name": "식이섬유", "benefit": "장 건강", "value": "2.8", "unit": "g"},
        {"name": "비타민 A", "benefit": "피부 보호", "value": "835", "unit": "μg"},
        {"name": "비타민 C", "benefit": "항산화", "value": "5.9", "unit": "mg"},
        {"name": "칼륨", "benefit": "심장 건강", "value": "320", "unit": "mg"},
        {"name": "칼로리", "benefit": "저칼로리", "value": "41", "unit": "kcal"},
    ])

    y_start = 170
    card_height = 120
    card_margin = 16

    # 카드 폰트 (SAFE 기준 통일)
    font_name = get_font("bold", FONT_SIZES["card_title"])
    font_benefit = get_font("regular", FONT_SIZES["card_desc"])
    font_value = get_font("extrabold", FONT_SIZES["value"])
    font_num = get_font("bold", 18)

    for i, n in enumerate(nutrition[:6]):
        y = y_start + i * (card_height + card_margin)

        # 카드 배경
        draw_rounded_rect(draw, (40, y, WIDTH - 40, y + card_height), 12, colors["card_bg"])

        # 번호 뱃지
        badge_color = BADGE_COLORS[i % len(BADGE_COLORS)]
        draw_circle_badge(draw, (90, y + card_height / 2), 20, badge_color, str(i + 1), font_num)

        # 성분명
        draw.text((130, y + 30), n["name"], fill=COLORS["text_dark"], font=font_name)

        # 효능
        draw.text((130, y + 70), n["benefit"], fill=COLORS["text_gray"], font=font_benefit)

        # 수치 (우측)
        value_text = f"{n['value']} {n['unit']}"
        bbox = draw.textbbox((0, 0), value_text, font=font_value)
        tw = bbox[2] - bbox[0]
        draw.text((WIDTH - 60 - tw, y + 40), value_text, fill=colors["accent"], font=font_value)

    # 하단 주석
    font_note = get_font("regular", 16)
    if safety == "FORBIDDEN":
        note = "* 소량이라도 절대 급여하지 마세요"
    else:
        note = "* 노령견에게 특히 좋은 베타카로틴이 풍부합니다"
    draw_text_centered(draw, note, font_note, WIDTH / 2, HEIGHT - 50, COLORS["text_light"])

    img.save(output_path)
    print(f"   ✅ {output_path.name}")


def generate_04_feeding(safety: str, food_data: dict, output_path: Path):
    """04번 급여방법 / 위험요소 슬라이드"""
    colors = SAFETY_COLORS[safety]

    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션
    draw_gradient(draw, (0, 0, WIDTH, 120), colors["header_start"], colors["header_end"])

    # 안전도 배지 (상단 중앙) - 동적 너비
    badge_width_04 = BADGE_WIDTHS.get(safety, 100) + 20  # 04번은 좀 더 넓게
    badge_rect = (WIDTH / 2 - badge_width_04 / 2, 30, WIDTH / 2 + badge_width_04 / 2, 80)
    draw_rounded_rect(draw, badge_rect, 25, COLORS["white"])
    font_badge = get_font("bold", 24)  # FORBIDDEN도 들어가도록 크기 조정
    draw_text_centered_in_rect(draw, badge_rect, safety, font_badge, colors["badge"])

    # 제목
    font_title = get_font("bold", 32)
    if safety == "SAFE":
        title = "강아지가 먹어도 안전해요"
    elif safety == "CAUTION":
        title = "조건부로 급여 가능해요"
    elif safety == "DANGER":
        title = "급여를 권장하지 않아요"
    else:  # FORBIDDEN
        title = "절대 급여 금지"
    draw_text_centered(draw, title, font_title, WIDTH / 2, 165, COLORS["text_dark"])

    font_section = get_font("bold", 22)
    font_item = get_font("regular", 24)
    font_check = get_font("bold", 18)

    if safety in ["SAFE", "CAUTION"]:
        # DO 섹션
        do_title = "이렇게 급여하세요" if safety == "SAFE" else "이 조건에서만 급여"
        draw.text((60, 220), do_title, fill=COLORS["check_green"], font=font_section)

        do_items = food_data.get("do", ["생으로 아삭하게", "익혀서 부드럽게", "작게 썰어서"])
        y_do_card = 260
        draw_rounded_rect(draw, (40, y_do_card, WIDTH - 40, y_do_card + 50 * len(do_items) + 30), 12, colors["do_card"])

        for i, item in enumerate(do_items[:3]):
            y = y_do_card + 25 + i * 55
            draw_circle_badge(draw, (80, y + 20), 16, COLORS["check_green"], "V", font_check)
            draw.text((115, y + 5), item, fill=COLORS["text_dark"], font=font_item)

        # DON'T 섹션
        dont_title = "이것만은 피해주세요" if safety == "SAFE" else "반드시 피해야 할 것"
        y_dont = y_do_card + 50 * len(do_items) + 80
        draw.text((60, y_dont), dont_title, fill=COLORS["x_red"], font=font_section)

        dont_items = food_data.get("dont", ["큰 조각 그대로", "양념/버터 추가", "과다 급여"])
        y_dont_card = y_dont + 40
        draw_rounded_rect(draw, (40, y_dont_card, WIDTH - 40, y_dont_card + 50 * len(dont_items) + 30), 12, colors["dont_card"])

        for i, item in enumerate(dont_items[:3]):
            y = y_dont_card + 25 + i * 55
            draw_circle_badge(draw, (80, y + 20), 16, COLORS["x_red"], "X", font_check)
            draw.text((115, y + 5), item, fill=COLORS["text_dark"], font=font_item)

        # 하단 메시지
        y_msg = HEIGHT - 200
        msg_rect = (40, y_msg, WIDTH - 40, y_msg + 70)
        draw_rounded_rect(draw, msg_rect, 12, (230, 247, 255))
        font_msg = get_font("regular", 22)
        msg = "11살 노령견 햇살이도 안전하게 먹고 있어요"
        if safety == "CAUTION":
            msg = "주의사항을 지켜 소량만 급여해주세요"
        draw_text_centered_in_rect(draw, msg_rect, msg, font_msg, colors["header_start"])

    else:  # DANGER, FORBIDDEN
        # 위험 요소 섹션
        risk_title = "위험 요소" if safety == "DANGER" else "독성 증상"
        draw.text((60, 220), risk_title, fill=colors["accent"], font=font_section)

        risk_items = food_data.get("risks", [
            "신장 손상 유발 가능",
            "소화기 장애 발생",
            "급성 중독 위험"
        ])
        y_risk_card = 260
        draw_rounded_rect(draw, (40, y_risk_card, WIDTH - 40, y_risk_card + 60 * len(risk_items) + 30), 12, colors["card_bg"])

        for i, item in enumerate(risk_items[:3]):
            y = y_risk_card + 25 + i * 60
            draw_circle_badge(draw, (80, y + 20), 16, colors["badge"], "!", font_check)
            draw.text((115, y + 5), item, fill=COLORS["text_dark"], font=font_item)

        # 응급 섹션
        emergency_title = "만약 섭취했다면" if safety == "DANGER" else "섭취 시 즉시 조치"
        y_emergency = y_risk_card + 60 * len(risk_items) + 80
        draw.text((60, y_emergency), emergency_title, fill=colors["accent"], font=font_section)

        emergency_items = food_data.get("emergency", [
            "즉시 수의사에게 연락",
            "구토 유도하지 말 것",
            "섭취량과 시간 기록"
        ])
        y_em_card = y_emergency + 40
        draw_rounded_rect(draw, (40, y_em_card, WIDTH - 40, y_em_card + 60 * len(emergency_items) + 30), 12, colors["dont_card"])

        for i, item in enumerate(emergency_items[:3]):
            y = y_em_card + 25 + i * 60
            draw_circle_badge(draw, (80, y + 20), 16, colors["badge"], str(i + 1), font_check)
            draw.text((115, y + 5), item, fill=COLORS["text_dark"], font=font_item)

        # 하단 경고
        y_warn = HEIGHT - 200
        warn_rect = (40, y_warn, WIDTH - 40, y_warn + 70)
        draw_rounded_rect(draw, warn_rect, 12, colors["dont_card"])
        font_warn = get_font("bold", 22)
        warn = "응급 상황 발생 시 즉시 동물병원으로"
        draw_text_centered_in_rect(draw, warn_rect, warn, font_warn, colors["accent"])

    img.save(output_path)
    print(f"   ✅ {output_path.name}")


def generate_05_amount(safety: str, food_data: dict, output_path: Path):
    """05번 급여량표 / 응급대처 슬라이드"""
    colors = SAFETY_COLORS[safety]

    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션
    draw_gradient(draw, (0, 0, WIDTH, 120), colors["header_start"], colors["header_end"])

    # 제목 (SAFE 기준 통일)
    font_title = get_font("extrabold", FONT_SIZES["header_title"])
    if safety in ["SAFE", "CAUTION"]:
        title = "체중별 급여량 가이드"
    else:
        title = "응급 대처 가이드"
    draw_text_centered(draw, title, font_title, WIDTH / 2, 50, COLORS["white"])

    # 부제 (SAFE 기준 통일)
    font_sub = get_font("regular", FONT_SIZES["header_sub"])
    if safety == "SAFE":
        subtitle = "하루 기준 | 간식으로 급여 시"
    elif safety == "CAUTION":
        subtitle = "하루 기준 | 제한적 급여 시"
    elif safety == "DANGER":
        subtitle = "섭취량별 위험도"
    else:
        subtitle = "섭취 시 즉시 행동"
    draw_text_centered(draw, subtitle, font_sub, WIDTH / 2, 95, (255, 255, 255, 204))

    # 테이블 헤더
    y_table = 170
    header_rect = (40, y_table, WIDTH - 40, y_table + 60)
    draw_rounded_rect(draw, header_rect, 10, colors["header_start"])

    font_header = get_font("bold", 22)
    col_width = (WIDTH - 80) / 3

    if safety in ["SAFE", "CAUTION"]:
        headers = ["구분", "체중", "급여량"]
    elif safety == "DANGER":
        headers = ["섭취량", "위험도", "조치"]
    else:  # FORBIDDEN
        headers = ["시간", "증상", "조치"]

    for i, h in enumerate(headers):
        x_center = 40 + col_width * i + col_width / 2
        draw_text_centered(draw, h, font_header, x_center, y_table + 30, COLORS["white"])

    # 테이블 행
    font_row = get_font("regular", 22)
    font_value = get_font("bold", 26)
    font_unit = get_font("regular", 16)
    row_height = 120

    if safety in ["SAFE", "CAUTION"]:
        rows = [
            ("소형견", "5kg 이하", "10~20g", "(동전 크기 2~3조각)"),
            ("중형견", "5~15kg", "20~40g", "(손가락 한 마디 3~4조각)"),
            ("대형견", "15~30kg", "40~60g", "(중간 당근 1/3개)"),
            ("초대형견", "30kg 이상", "60~80g", "(중간 당근 1/2개)"),
        ]
    elif safety == "DANGER":
        rows = [
            ("소량", "경미", "관찰 필요"),
            ("중량", "위험", "수의사 상담"),
            ("대량", "심각", "즉시 병원"),
            ("", "", ""),
        ]
    else:  # FORBIDDEN
        rows = [
            ("즉시", "구토/설사 시작", "동물병원 연락"),
            ("30분 내", "무기력/떨림", "이동 준비"),
            ("1시간 내", "경련/실신", "응급 이송"),
            ("", "", ""),
        ]

    for i, row in enumerate(rows[:4]):
        if not row[0]:
            continue
        y = y_table + 60 + i * row_height + 10

        for j, val in enumerate(row[:3]):
            x_center = 40 + col_width * j + col_width / 2
            if j == 2 and safety in ["SAFE", "CAUTION"]:
                # 급여량 (강조)
                draw_text_centered(draw, val, font_value, x_center, y + 35, colors["accent"])
                if len(row) > 3 and row[3]:
                    draw_text_centered(draw, row[3], font_unit, x_center, y + 65, COLORS["text_gray"])
            else:
                font_use = font_value if j == 1 and safety in ["DANGER", "FORBIDDEN"] else font_row
                color_use = colors["accent"] if j == 1 and safety in ["DANGER", "FORBIDDEN"] else COLORS["text_dark"]
                draw_text_centered(draw, val, font_use, x_center, y + 45, color_use)

    # 주의사항 박스
    y_caution = 680
    draw_rounded_rect(draw, (40, y_caution, WIDTH - 40, y_caution + 130), 12, colors["tip_card"])

    # 주의 뱃지
    caution_badge_rect = (80, y_caution + 20, 160, y_caution + 60)
    draw_rounded_rect(draw, caution_badge_rect, 5, colors["badge"])
    font_badge_small = get_font("bold", 20)
    draw_text_centered_in_rect(draw, caution_badge_rect, "주의", font_badge_small, COLORS["white"])

    font_caution_title = get_font("bold", 20)
    draw.text((175, y_caution + 28), "급여 시 주의사항" if safety in ["SAFE", "CAUTION"] else "응급 상황 대처", fill=colors["accent"], font=font_caution_title)

    font_caution = get_font("regular", 20)
    if safety in ["SAFE", "CAUTION"]:
        draw.text((80, y_caution + 70), "• 하루 칼로리의 10% 이내로 급여해주세요", fill=COLORS["text_gray"], font=font_caution)
        draw.text((80, y_caution + 100), "• 처음 급여 시 소량부터 시작하세요", fill=COLORS["text_gray"], font=font_caution)
    else:
        draw.text((80, y_caution + 70), "• 구토 유도는 수의사 지시 후에만", fill=COLORS["text_gray"], font=font_caution)
        draw.text((80, y_caution + 100), "• 섭취량과 시간을 정확히 기록", fill=COLORS["text_gray"], font=font_caution)

    # 하단 주석
    font_note = get_font("regular", 16)
    if safety in ["SAFE", "CAUTION"]:
        note = "* 개체별 차이가 있으므로 반응을 보며 조절하세요"
    else:
        note = "* 24시간 응급 동물병원 연락처를 미리 저장해두세요"
    draw_text_centered(draw, note, font_note, WIDTH / 2, HEIGHT - 50, COLORS["text_light"])

    img.save(output_path)
    print(f"   ✅ {output_path.name}")


def generate_06_caution(safety: str, food_data: dict, output_path: Path):
    """06번 주의사항 / 대체음식 슬라이드"""
    colors = SAFETY_COLORS[safety]

    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션 (주황/코랄 계열)
    coral_start = (247, 168, 139) if safety == "SAFE" else colors["header_start"]
    coral_end = (251, 196, 174) if safety == "SAFE" else colors["header_end"]
    draw_gradient(draw, (0, 0, WIDTH, 120), coral_start, coral_end)

    # 제목 뱃지 + 텍스트
    if safety in ["SAFE", "CAUTION"]:
        badge_rect = (380, 35, 470, 85)
        draw_rounded_rect(draw, badge_rect, 10, COLORS["white"])
        font_badge = get_font("bold", 26)
        draw_text_centered_in_rect(draw, badge_rect, "주의", font_badge, coral_start)

        font_title = get_font("extrabold", 44)
        draw.text((490, 43), "주의사항", fill=COLORS["white"], font=font_title)
    else:
        font_title = get_font("extrabold", 44)
        draw_text_centered(draw, "대체 음식 추천", font_title, WIDTH / 2, 60, COLORS["white"])

        font_sub = get_font("regular", 20)
        sub = "안전하게 급여할 수 있는 대체 간식"
        draw_text_centered(draw, sub, font_sub, WIDTH / 2, 95, (255, 255, 255, 204))

    font_num = get_font("bold", 18)
    font_title_card = get_font("bold", 26)
    font_desc = get_font("regular", 18)

    y_start = 170
    card_height = 130
    card_margin = 16

    if safety in ["SAFE", "CAUTION"]:
        caution_items = food_data.get("caution", [
            {"title": "크기 주의", "desc": "목에 걸릴 수 있으니 작게 썰어주세요"},
            {"title": "껍질 세척", "desc": "농약 잔류 가능, 깨끗이 씻거나 벗기기"},
            {"title": "양념 금지", "desc": "소금, 버터 등 첨가물 금지"},
            {"title": "과다 급여 주의", "desc": "하루 칼로리 10% 이내"},
            {"title": "알레르기 확인", "desc": "처음엔 소량 급여 후 반응 관찰"},
        ])

        for i, c in enumerate(caution_items[:5]):
            y = y_start + i * (card_height + card_margin)

            draw_rounded_rect(draw, (40, y, WIDTH - 40, y + card_height), 12, colors["card_bg"])

            badge_color = BADGE_COLORS[i % len(BADGE_COLORS)]
            draw_circle_badge(draw, (90, y + card_height / 2), 22, badge_color, str(i + 1), font_num)

            draw.text((140, y + 35), c["title"], fill=COLORS["text_dark"], font=font_title_card)
            draw.text((140, y + 75), c["desc"], fill=COLORS["text_gray"], font=font_desc)

        # 하단 응급 안내
        y_emergency = HEIGHT - 200
        draw_rounded_rect(draw, (40, y_emergency, WIDTH - 40, y_emergency + 70), 12, colors["dont_card"])

        font_emergency = get_font("bold", 20)
        msg = "이상 반응 발생 시 즉시 수의사와 상담하세요"
        if safety == "CAUTION":
            msg = "반드시 수의사와 상담 후 급여하세요"

        # 응급 아이콘
        draw_circle_badge(draw, (80, y_emergency + 35), 18, COLORS["x_red"], "+", font_num)
        draw.text((110, y_emergency + 22), msg, fill=COLORS["x_red"], font=font_emergency)

    else:  # DANGER, FORBIDDEN
        alternatives = food_data.get("alternatives", [
            {"name": "당근", "benefit": "베타카로틴 풍부", "safety": "SAFE"},
            {"name": "호박", "benefit": "소화에 좋음", "safety": "SAFE"},
            {"name": "사과", "benefit": "비타민 풍부", "safety": "SAFE"},
            {"name": "블루베리", "benefit": "항산화 효과", "safety": "SAFE"},
            {"name": "수박", "benefit": "수분 보충", "safety": "SAFE"},
        ])

        for i, alt in enumerate(alternatives[:5]):
            y = y_start + i * (card_height + card_margin)

            draw_rounded_rect(draw, (40, y, WIDTH - 40, y + card_height), 12, (232, 246, 243))

            # SAFE 뱃지
            safe_badge = (WIDTH - 130, y + 45, WIDTH - 60, y + 85)
            draw_rounded_rect(draw, safe_badge, 20, COLORS["check_green"])
            font_safe = get_font("bold", 16)
            draw_text_centered_in_rect(draw, safe_badge, "SAFE", font_safe, COLORS["white"])

            draw_circle_badge(draw, (90, y + card_height / 2), 22, BADGE_COLORS[i % len(BADGE_COLORS)], str(i + 1), font_num)

            draw.text((140, y + 35), alt["name"], fill=COLORS["text_dark"], font=font_title_card)
            draw.text((140, y + 75), alt["benefit"], fill=COLORS["text_gray"], font=font_desc)

        # 하단 메시지
        y_msg = HEIGHT - 200
        draw_rounded_rect(draw, (40, y_msg, WIDTH - 40, y_msg + 70), 12, (232, 246, 243))
        font_msg = get_font("bold", 20)
        msg = f"이 음식 대신 위 간식을 급여하세요"
        draw_text_centered_in_rect(draw, (40, y_msg, WIDTH - 40, y_msg + 70), msg, font_msg, COLORS["check_green"])

    img.save(output_path)
    print(f"   ✅ {output_path.name}")


def generate_07_cooking(safety: str, food_data: dict, output_path: Path):
    """07번 조리방법 / 최종경고 슬라이드"""
    colors = SAFETY_COLORS[safety]

    img = Image.new("RGB", (WIDTH, HEIGHT), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션
    draw_gradient(draw, (0, 0, WIDTH, 120), colors["header_start"], colors["header_end"])

    # 제목 (SAFE 기준 통일)
    font_title = get_font("extrabold", FONT_SIZES["header_title"])
    if safety in ["SAFE", "CAUTION"]:
        title = "안전한 조리 방법"
    else:
        title = "최종 경고"
    draw_text_centered(draw, title, font_title, WIDTH / 2, 50, COLORS["white"])

    # 부제 (SAFE 기준 통일)
    font_sub = get_font("regular", FONT_SIZES["header_sub"])
    if safety == "SAFE":
        subtitle = f"강아지를 위한 {food_data['korean']} 준비 5단계"
    elif safety == "CAUTION":
        subtitle = f"안전하게 {food_data['korean']} 준비하기"
    elif safety == "DANGER":
        subtitle = "절대 급여하지 마세요"
    else:
        subtitle = "이 음식은 강아지에게 독입니다"
    draw_text_centered(draw, subtitle, font_sub, WIDTH / 2, 95, (255, 255, 255, 204))

    font_step = get_font("bold", 16)
    font_title_card = get_font("bold", 26)
    font_desc = get_font("regular", 18)

    y_start = 170
    card_height = 130
    card_margin = 16

    if safety in ["SAFE", "CAUTION"]:
        cooking_steps = food_data.get("cooking", [
            {"step": "깨끗이 씻기", "desc": "흐르는 물에 흙과 이물질 제거"},
            {"step": "껍질 벗기기", "desc": "필러로 껍질을 벗기거나 깨끗이 세척"},
            {"step": "적당히 썰기", "desc": "아이 입 크기에 맞게 작게 썰기"},
            {"step": "생으로 또는 익히기", "desc": "생으로 주거나 5~10분 쪄서"},
            {"step": "식혀서 급여", "desc": "화상 방지를 위해 충분히 식힌 후"},
        ])

        for i, step in enumerate(cooking_steps[:5]):
            y = y_start + i * (card_height + card_margin)

            draw_rounded_rect(draw, (40, y, WIDTH - 40, y + card_height), 12, colors["card_bg"])

            # STEP 뱃지
            badge_color = BADGE_COLORS[i % len(BADGE_COLORS)]
            step_rect = (60, y + 30, 150, y + 70)
            draw_rounded_rect(draw, step_rect, 20, badge_color)
            draw_text_centered_in_rect(draw, step_rect, f"STEP {i + 1}", font_step, COLORS["white"])

            draw.text((170, y + 35), step["step"], fill=COLORS["text_dark"], font=font_title_card)
            draw.text((60, y + 85), step["desc"], fill=COLORS["text_gray"], font=font_desc)

        # TIP 박스
        y_tip = HEIGHT - 230
        draw_rounded_rect(draw, (40, y_tip, WIDTH - 40, y_tip + 100), 12, colors["tip_card"])

        # TIP 아이콘
        font_exclaim = get_font("bold", 24)
        draw_circle_badge(draw, (80, y_tip + 35), 18, (255, 167, 38), "!", font_exclaim)

        font_tip_title = get_font("bold", 20)
        font_tip = get_font("regular", 18)
        draw.text((110, y_tip + 22), "TIP", fill=(255, 167, 38), font=font_tip_title)

        tip = food_data.get("tip", f"남은 {food_data['korean']}은 밀폐용기에 냉장 보관하면 3~4일 먹일 수 있어요")
        if safety == "CAUTION":
            tip = "반드시 주의사항을 확인 후 소량만 급여하세요"
        draw.text((70, y_tip + 60), tip, fill=COLORS["text_gray"], font=font_tip)

    else:  # DANGER, FORBIDDEN
        warnings = [
            {"title": "독성 성분 포함", "desc": "강아지 체내에서 분해되지 않음"},
            {"title": "신장/간 손상", "desc": "소량으로도 장기 손상 가능"},
            {"title": "사망 위험", "desc": "대량 섭취 시 치명적"},
            {"title": "해독제 없음", "desc": "증상 완화 치료만 가능"},
            {"title": "영구 손상", "desc": "회복 후에도 후유증 가능"},
        ]

        for i, w in enumerate(warnings[:5]):
            y = y_start + i * (card_height + card_margin)

            draw_rounded_rect(draw, (40, y, WIDTH - 40, y + card_height), 12, colors["card_bg"])

            draw_circle_badge(draw, (90, y + card_height / 2), 22, colors["badge"], "!", font_step)

            draw.text((140, y + 35), w["title"], fill=COLORS["text_dark"], font=font_title_card)
            draw.text((140, y + 75), w["desc"], fill=COLORS["text_gray"], font=font_desc)

        # 응급 연락처
        y_emergency = HEIGHT - 230
        draw_rounded_rect(draw, (40, y_emergency, WIDTH - 40, y_emergency + 100), 12, colors["dont_card"])

        font_emergency = get_font("bold", 24)
        draw_text_centered(draw, "24시간 동물병원 응급 연락처", font_emergency, WIDTH / 2, y_emergency + 35, colors["accent"])

        font_number = get_font("bold", 28)
        draw_text_centered(draw, "미리 저장해두세요!", font_number, WIDTH / 2, y_emergency + 70, COLORS["text_dark"])

    img.save(output_path)
    print(f"   ✅ {output_path.name}")


# =============================================================================
# 메인 생성 함수
# =============================================================================

def generate_golden_samples(safety: str):
    """특정 안전도의 골든 샘플 5개 생성"""
    output_dir = GOLDEN_DIR / safety
    output_dir.mkdir(parents=True, exist_ok=True)

    # 예시 음식 데이터 (안전도별)
    if safety == "SAFE":
        food_data = {"korean": "당근", "english": "Carrot"}
    elif safety == "CAUTION":
        food_data = {"korean": "체리", "english": "Cherry"}
    elif safety == "DANGER":
        food_data = {"korean": "포도", "english": "Grape"}
    else:  # FORBIDDEN
        food_data = {"korean": "초콜릿", "english": "Chocolate"}

    print(f"\n📊 {safety} 골든 샘플 생성 ({food_data['korean']})")

    # 슬라이드 네이밍 (SLIDE_NAMING_BY_SAFETY.md 기준)
    if safety in ["SAFE", "CAUTION"]:
        slides = {
            "03": ("Nutrition", generate_03_nutrition),
            "04": ("Feeding", generate_04_feeding),
            "05": ("Amount", generate_05_amount),
            "06": ("Caution", generate_06_caution),
            "07": ("Cooking", generate_07_cooking),
        }
    elif safety == "DANGER":
        slides = {
            "03": ("Nutrition", generate_03_nutrition),
            "04": ("Risk", generate_04_feeding),
            "05": ("Symptoms", generate_05_amount),
            "06": ("Alternative", generate_06_caution),
            "07": ("Warning", generate_07_cooking),
        }
    else:  # FORBIDDEN
        slides = {
            "03": ("Toxicity", generate_03_nutrition),
            "04": ("Symptoms", generate_04_feeding),
            "05": ("Emergency", generate_05_amount),
            "06": ("Alternative", generate_06_caution),
            "07": ("Warning", generate_07_cooking),
        }

    for num, (name, func) in slides.items():
        output_path = output_dir / f"Golden_Blog_{safety}_{num}_{name}.png"
        func(safety, food_data, output_path)

    print(f"   완료: {len(slides)}개 생성")


def main():
    """메인 함수 - 모든 안전도 골든 샘플 생성"""
    print("=" * 60)
    print("WO-GOLDEN-SLIDE-FIX: 안전도별 블로그 골든 샘플 재생성")
    print("수정사항: 폰트 통일, 배지 overflow 수정, 헤더 배지 위치 수정")
    print("=" * 60)

    # 모든 안전도 재생성 (SAFE 포함 - 비교 기준용)
    for safety in ["SAFE", "CAUTION", "DANGER", "FORBIDDEN"]:
        generate_golden_samples(safety)

    print("\n" + "=" * 60)
    print("완료: 20개 골든 샘플 생성 (SAFE 5개 + CAUTION 5개 + DANGER 5개 + FORBIDDEN 5개)")
    print("=" * 60)


if __name__ == "__main__":
    main()
