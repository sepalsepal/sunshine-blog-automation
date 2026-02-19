#!/usr/bin/env python3
"""
004_Cherry Blog Slides Generator (03-07)
BLOG_SLIDE_DESIGN_RULE.md v2.1 준수
Safety: CAUTION

CAUTION 색상 체계:
- 헤더 그라데이션: #FFD93D → #FFE680
- 카드 배경: #FFF8E1
- 배지: #FFD93D
- 강조 색상: #F9A825
"""

import os
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

# 경로 설정
PROJECT_ROOT = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine")
OUTPUT_DIR = PROJECT_ROOT / "01_contents" / "004_Cherry" / "02_Blog"

# 색상 설정 (CAUTION)
COLORS = {
    "background": "#FFF8F0",
    "header_start": "#FFD93D",
    "header_end": "#FFE680",
    "card_bg": "#FFF8E1",
    "badge": "#FFD93D",
    "accent": "#F9A825",
    "text_dark": "#333333",
    "text_gray": "#888888",
    "text_light": "#AAAAAA",
    "white": "#FFFFFF",
    "do_bg": "#E8F6E8",
    "dont_bg": "#FDE8E8",
    "check_green": "#4CAF50",
    "check_red": "#EF5350",
    "tip_bg": "#FFF8E1",
    "warning_bg": "#FDE8E8",
}

# 번호 아이콘 색상 순환
BADGE_COLORS = ["#FFA726", "#66BB6A", "#EF5350", "#42A5F5", "#AB47BC", "#26A69A"]
STEP_COLORS = ["#FFA726", "#66BB6A", "#42A5F5", "#AB47BC", "#26A69A"]

# 캔버스 설정
CANVAS_SIZE = (1080, 1080)

# 폰트 설정
FONT_PATH = "/System/Library/Fonts/AppleSDGothicNeo.ttc"


def hex_to_rgb(hex_color):
    """HEX -> RGB"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))


def load_font(size, bold=False):
    """폰트 로드"""
    try:
        index = 6 if bold else 2
        return ImageFont.truetype(FONT_PATH, size, index=index)
    except:
        return ImageFont.load_default()


def draw_gradient_header(draw, img, height=120):
    """CAUTION 그라데이션 헤더"""
    start = hex_to_rgb(COLORS["header_start"])
    end = hex_to_rgb(COLORS["header_end"])

    for y in range(height):
        ratio = y / height
        r = int(start[0] + (end[0] - start[0]) * ratio)
        g = int(start[1] + (end[1] - start[1]) * ratio)
        b = int(start[2] + (end[2] - start[2]) * ratio)
        for x in range(CANVAS_SIZE[0]):
            img.putpixel((x, y), (r, g, b))


def draw_badge(draw, text, position, font):
    """안전도 배지"""
    x, y = position
    bbox = font.getbbox(text)
    w = bbox[2] - bbox[0] + 30
    h = 36

    draw.rounded_rectangle([x, y, x + w, y + h], radius=18, fill=COLORS["badge"])
    draw.text((x + 15, y + 8), text, fill=COLORS["white"], font=font)
    return w


def draw_number_icon(draw, num, position, font):
    """번호 원형 아이콘"""
    x, y = position
    color = BADGE_COLORS[(num - 1) % len(BADGE_COLORS)]
    draw.ellipse([x, y, x + 40, y + 40], fill=color)

    # 숫자 중앙 정렬
    text = str(num)
    bbox = font.getbbox(text)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    draw.text((x + 20 - tw // 2, y + 20 - th // 2 - 2), text, fill=COLORS["white"], font=font)


def draw_check_icon(draw, position, is_check=True, font=None):
    """체크/X 아이콘 (§6.1 준수)"""
    x, y = position
    color = COLORS["check_green"] if is_check else COLORS["check_red"]
    draw.ellipse([x, y, x + 32, y + 32], fill=color)

    text = "V" if is_check else "X"
    if font:
        bbox = font.getbbox(text)
        tw = bbox[2] - bbox[0]
        draw.text((x + 16 - tw // 2, y + 5), text, fill=COLORS["white"], font=font)


def draw_step_badge(draw, step_num, position, font):
    """STEP N 배지"""
    x, y = position
    color = STEP_COLORS[(step_num - 1) % len(STEP_COLORS)]
    text = f"STEP {step_num}"

    bbox = font.getbbox(text)
    w = bbox[2] - bbox[0] + 24

    draw.rounded_rectangle([x, y, x + w, y + 32], radius=16, fill=color)
    draw.text((x + 12, y + 6), text, fill=COLORS["white"], font=font)
    return w


def center_text(draw, text, y, font, color):
    """텍스트 수평 중앙 정렬"""
    bbox = font.getbbox(text)
    w = bbox[2] - bbox[0]
    x = (CANVAS_SIZE[0] - w) // 2
    draw.text((x, y), text, fill=color, font=font)


# =============================================================================
# 03_Nutrition - 영양성분
# =============================================================================
def generate_03_nutrition():
    """03번 영양성분 슬라이드"""
    print("\n[03_Nutrition] 생성 시작...")

    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(COLORS["background"]))
    draw = ImageDraw.Draw(img)

    # 폰트
    font_title = load_font(52, bold=True)
    font_subtitle = load_font(22)
    font_badge = load_font(14, bold=True)
    font_card_title = load_font(30, bold=True)
    font_card_desc = load_font(18)
    font_value = load_font(38, bold=True)
    font_num = load_font(18, bold=True)
    font_footer = load_font(16)

    # 헤더
    draw_gradient_header(draw, img)

    # 제목
    center_text(draw, "체리 영양성분", 30, font_title, COLORS["white"])
    center_text(draw, "100g 기준 | 적정량 급여 시 도움이 되는 영양소", 90, font_subtitle, COLORS["white"])

    # 배지
    draw_badge(draw, "CAUTION", (CANVAS_SIZE[0] - 120, 24), font_badge)

    # 영양소 데이터
    nutrients = [
        ("비타민 A", "면역력 강화", "200", "μg"),
        ("수분", "수분 보충", "85", "%"),
        ("식이섬유", "장 건강", "2", "g"),
        ("비타민 C", "면역력 강화", "8", "mg"),
        ("칼륨", "심장 건강", "150", "mg"),
        ("칼로리", "저칼로리", "40", "kcal"),
    ]

    # 카드들
    y = 155
    card_height = 95
    margin = 45

    for i, (name, benefit, value, unit) in enumerate(nutrients, 1):
        # 카드 배경
        draw.rounded_rectangle(
            [margin, y, CANVAS_SIZE[0] - margin, y + card_height],
            radius=12, fill=COLORS["card_bg"]
        )

        # 번호 아이콘
        draw_number_icon(draw, i, (margin + 15, y + 27), font_num)

        # 텍스트
        draw.text((margin + 70, y + 20), name, fill=COLORS["text_dark"], font=font_card_title)
        draw.text((margin + 70, y + 55), benefit, fill=COLORS["text_gray"], font=font_card_desc)

        # 수치 (우측 정렬)
        val_text = f"{value} {unit}"
        bbox = font_value.getbbox(val_text)
        val_w = bbox[2] - bbox[0]
        draw.text((CANVAS_SIZE[0] - margin - val_w - 20, y + 28), val_text,
                  fill=COLORS["accent"], font=font_value)

        y += card_height + 12

    # 하단 참고
    center_text(draw, "* 체리는 개체별 차이가 있으므로 반응을 보며 조절하세요",
                CANVAS_SIZE[1] - 50, font_footer, COLORS["text_light"])

    # 저장
    output = OUTPUT_DIR / "Cherry_Blog_03_Nutrition.png"
    img.save(output, "PNG")
    print(f"   [OK] 저장: {output}")
    return img


# =============================================================================
# 04_Feeding - 급여법 DO/DON'T
# =============================================================================
def generate_04_feeding():
    """04번 급여법 슬라이드"""
    print("\n[04_Feeding] 생성 시작...")

    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(COLORS["background"]))
    draw = ImageDraw.Draw(img)

    # 폰트
    font_badge = load_font(20, bold=True)
    font_title = load_font(46, bold=True)
    font_section = load_font(24, bold=True)
    font_item = load_font(24)
    font_check = load_font(14, bold=True)
    font_footer = load_font(18)

    # 헤더
    draw_gradient_header(draw, img)

    # 배지 (중앙 상단)
    badge_text = "CAUTION"
    bbox = font_badge.getbbox(badge_text)
    badge_w = bbox[2] - bbox[0] + 30
    badge_x = (CANVAS_SIZE[0] - badge_w) // 2
    draw.rounded_rectangle([badge_x, 30, badge_x + badge_w, 66], radius=18, fill=COLORS["white"])
    draw.text((badge_x + 15, 38), badge_text, fill=COLORS["badge"], font=font_badge)

    # 제목
    center_text(draw, "조건부로 급여 가능해요", 170, font_title, COLORS["text_dark"])

    margin = 45

    # DO 섹션
    draw.text((margin + 10, 250), "이 조건에서만 급여", fill=COLORS["check_green"], font=font_section)

    do_items = [
        "씨와 줄기는 반드시 제거",
        "소량씩 간식으로만 급여",
        "신선한 것만 급여"
    ]

    do_y = 295
    do_height = len(do_items) * 52 + 30
    draw.rounded_rectangle([margin, do_y, CANVAS_SIZE[0] - margin, do_y + do_height],
                          radius=12, fill=COLORS["do_bg"])

    item_y = do_y + 20
    for item in do_items:
        draw_check_icon(draw, (margin + 15, item_y + 3), is_check=True, font=font_check)
        draw.text((margin + 60, item_y), item, fill=COLORS["text_dark"], font=font_item)
        item_y += 52

    # DON'T 섹션
    dont_y = do_y + do_height + 40
    draw.text((margin + 10, dont_y), "반드시 피해야 할 것", fill=COLORS["check_red"], font=font_section)

    dont_items = [
        "과다 급여는 금지",
        "씨와 줄기 급여 금지 (독성)",
        "상한 체리 급여 금지"
    ]

    dont_box_y = dont_y + 40
    dont_height = len(dont_items) * 52 + 30
    draw.rounded_rectangle([margin, dont_box_y, CANVAS_SIZE[0] - margin, dont_box_y + dont_height],
                          radius=12, fill=COLORS["dont_bg"])

    item_y = dont_box_y + 20
    for item in dont_items:
        draw_check_icon(draw, (margin + 15, item_y + 3), is_check=False, font=font_check)
        draw.text((margin + 60, item_y), item, fill=COLORS["text_dark"], font=font_item)
        item_y += 52

    # 하단 응원
    footer_y = CANVAS_SIZE[1] - 100
    draw.rounded_rectangle([margin, footer_y, CANVAS_SIZE[0] - margin, footer_y + 55],
                          radius=10, fill="#E3F2FD")
    center_text(draw, "11살 노령견 햇살이도 조심히 먹고 있어요", footer_y + 15, font_footer, COLORS["accent"])

    # 저장
    output = OUTPUT_DIR / "Cherry_Blog_04_Feeding.png"
    img.save(output, "PNG")
    print(f"   [OK] 저장: {output}")
    return img


# =============================================================================
# 05_Amount - 급여량
# =============================================================================
def generate_05_amount():
    """05번 급여량 슬라이드"""
    print("\n[05_Amount] 생성 시작...")

    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(COLORS["background"]))
    draw = ImageDraw.Draw(img)

    # 폰트
    font_title = load_font(52, bold=True)
    font_subtitle = load_font(22)
    font_header = load_font(22, bold=True)
    font_size = load_font(24, bold=True)
    font_weight = load_font(20)
    font_amount = load_font(30, bold=True)
    font_desc = load_font(16)
    font_warning = load_font(20, bold=True)
    font_warning_text = load_font(16)

    # 헤더
    draw_gradient_header(draw, img)

    # 제목
    center_text(draw, "체중별 급여량 가이드", 30, font_title, COLORS["white"])
    center_text(draw, "하루 기준 | 제한적 급여 시", 90, font_subtitle, COLORS["white"])

    # 표 설정
    margin = 80
    table_y = 160
    header_h = 50
    row_h = 90
    col_w = (CANVAS_SIZE[0] - margin * 2) // 3

    # 표 헤더
    draw.rounded_rectangle([margin, table_y, CANVAS_SIZE[0] - margin, table_y + header_h],
                          radius=10, fill=COLORS["card_bg"])

    headers = ["구분", "체중", "급여량"]
    for i, h in enumerate(headers):
        bbox = font_header.getbbox(h)
        hw = bbox[2] - bbox[0]
        x = margin + col_w * i + (col_w - hw) // 2
        draw.text((x, table_y + 12), h, fill=COLORS["accent"], font=font_header)

    # 표 데이터
    dosages = [
        ("소형견", "5kg 이하", "1~2알", "씨 제거 필수"),
        ("중형견", "5~15kg", "2~3알", "씨 제거 필수"),
        ("대형견", "15~30kg", "3~5알", "씨 제거 필수"),
        ("초대형견", "30kg 이상", "5~7알", "씨 제거 필수"),
    ]

    row_y = table_y + header_h + 15
    for size, weight, amount, desc in dosages:
        # 구분
        bbox = font_size.getbbox(size)
        sw = bbox[2] - bbox[0]
        draw.text((margin + (col_w - sw) // 2, row_y + 15), size,
                  fill=COLORS["text_dark"], font=font_size)

        # 체중
        bbox = font_weight.getbbox(weight)
        ww = bbox[2] - bbox[0]
        draw.text((margin + col_w + (col_w - ww) // 2, row_y + 18), weight,
                  fill=COLORS["text_gray"], font=font_weight)

        # 급여량
        bbox = font_amount.getbbox(amount)
        aw = bbox[2] - bbox[0]
        draw.text((margin + col_w * 2 + (col_w - aw) // 2, row_y + 8), amount,
                  fill=COLORS["accent"], font=font_amount)

        # 부연
        bbox = font_desc.getbbox(f"({desc})")
        dw = bbox[2] - bbox[0]
        draw.text((margin + col_w * 2 + (col_w - dw) // 2, row_y + 48), f"({desc})",
                  fill=COLORS["text_light"], font=font_desc)

        row_y += row_h

    # 주의사항 박스
    warning_y = row_y + 20
    draw.rounded_rectangle([margin, warning_y, CANVAS_SIZE[0] - margin, warning_y + 90],
                          radius=10, fill=COLORS["tip_bg"])

    # 주의 배지
    draw.rounded_rectangle([margin + 15, warning_y + 12, margin + 65, warning_y + 42],
                          radius=5, fill=COLORS["badge"])
    draw.text((margin + 23, warning_y + 15), "주의", fill=COLORS["white"], font=font_warning)
    draw.text((margin + 80, warning_y + 15), "급여 시 주의사항", fill=COLORS["badge"], font=font_warning)

    # 주의 텍스트
    warnings = [
        "체리 씨에는 시안화물(청산)이 포함되어 있어 위험합니다",
        "처음 급여 시 1알부터 시작하세요"
    ]
    for i, w in enumerate(warnings):
        draw.text((margin + 25, warning_y + 50 + i * 20), f"• {w}",
                  fill=COLORS["text_gray"], font=font_warning_text)

    # 저장
    output = OUTPUT_DIR / "Cherry_Blog_05_Amount.png"
    img.save(output, "PNG")
    print(f"   [OK] 저장: {output}")
    return img


# =============================================================================
# 06_Caution - 주의사항
# =============================================================================
def generate_06_caution():
    """06번 주의사항 슬라이드"""
    print("\n[06_Caution] 생성 시작...")

    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(COLORS["background"]))
    draw = ImageDraw.Draw(img)

    # 폰트
    font_badge = load_font(22, bold=True)
    font_title = load_font(48, bold=True)
    font_card_title = load_font(28, bold=True)
    font_card_desc = load_font(18)
    font_num = load_font(18, bold=True)
    font_footer = load_font(18)

    # 주황 헤더 (주의사항용)
    for y in range(120):
        ratio = y / 120
        r = int(235 + (240 - 235) * ratio)
        g = int(150 + (180 - 150) * ratio)
        b = int(130 + (160 - 130) * ratio)
        for x in range(CANVAS_SIZE[0]):
            img.putpixel((x, y), (r, g, b))

    # "주의" 배지 + 제목
    draw.rounded_rectangle([420, 35, 490, 70], radius=15, fill=COLORS["badge"])
    draw.text((435, 40), "주의", fill=COLORS["white"], font=font_badge)
    draw.text((510, 30), "주의사항", fill="#E67E22", font=font_title)

    # 주의사항 데이터
    precautions = [
        ("씨와 줄기 제거 필수", "시안화물(청산) 독성 위험"),
        ("구토/설사 확인", "처음 급여 후 이상 반응 관찰하세요"),
        ("알러지 체크", "가려움, 발진 등 24시간 모니터링"),
        ("변 상태 관찰", "묽어지면 급여량을 줄여주세요"),
        ("적정량 준수", "하루 칼로리의 10% 이내로 급여"),
    ]

    # 카드들
    y = 155
    card_height = 90
    margin = 50

    for i, (title, desc) in enumerate(precautions, 1):
        draw.rounded_rectangle([margin, y, CANVAS_SIZE[0] - margin, y + card_height],
                              radius=12, fill="#E3F2FD")
        draw_number_icon(draw, i, (margin + 15, y + 25), font_num)
        draw.text((margin + 70, y + 18), title, fill=COLORS["text_dark"], font=font_card_title)
        draw.text((margin + 70, y + 52), desc, fill=COLORS["text_gray"], font=font_card_desc)
        y += card_height + 10

    # 응급 안내 푸터
    footer_y = CANVAS_SIZE[1] - 95
    draw.rounded_rectangle([margin, footer_y, CANVAS_SIZE[0] - margin, footer_y + 55],
                          radius=10, fill=COLORS["warning_bg"])

    # + 아이콘
    draw.ellipse([margin + 15, footer_y + 12, margin + 45, footer_y + 42], fill=COLORS["check_red"])
    draw.text((margin + 24, footer_y + 12), "+", fill=COLORS["white"], font=font_badge)

    draw.text((margin + 60, footer_y + 15), "이상 증상 발견 시 즉시 수의사와 상담하세요",
              fill=COLORS["check_red"], font=font_footer)

    # 저장
    output = OUTPUT_DIR / "Cherry_Blog_06_Caution.png"
    img.save(output, "PNG")
    print(f"   [OK] 저장: {output}")
    return img


# =============================================================================
# 07_Cooking - 조리방법
# =============================================================================
def generate_07_cooking():
    """07번 조리방법 슬라이드"""
    print("\n[07_Cooking] 생성 시작...")

    img = Image.new('RGB', CANVAS_SIZE, hex_to_rgb(COLORS["background"]))
    draw = ImageDraw.Draw(img)

    # 폰트
    font_title = load_font(48, bold=True)
    font_subtitle = load_font(22)
    font_step = load_font(14, bold=True)
    font_card_title = load_font(28, bold=True)
    font_card_desc = load_font(18)
    font_tip = load_font(20, bold=True)
    font_tip_text = load_font(16)

    # 헤더
    draw_gradient_header(draw, img)

    # 제목
    center_text(draw, "안전한 급여 방법", 25, font_title, COLORS["white"])
    center_text(draw, "강아지를 위한 체리 준비 5단계", 80, font_subtitle, COLORS["white"])

    # 조리 단계
    steps = [
        ("깨끗이 씻기", "흐르는 물에 깨끗이 세척하세요"),
        ("씨 완전 제거", "씨에 독성이 있어 반드시 제거하세요"),
        ("줄기 제거", "줄기도 독성이 있으니 제거하세요"),
        ("작게 썰기", "질식 위험 방지를 위해 작게 자르세요"),
        ("소량 급여", "처음엔 1알부터 시작하세요"),
    ]

    y = 155
    card_height = 85
    margin = 50

    for i, (title, desc) in enumerate(steps, 1):
        draw.rounded_rectangle([margin, y, CANVAS_SIZE[0] - margin, y + card_height],
                              radius=12, fill="#E3F2FD")
        badge_w = draw_step_badge(draw, i, (margin + 15, y + 15), font_step)
        draw.text((margin + badge_w + 30, y + 13), title, fill=COLORS["text_dark"], font=font_card_title)
        draw.text((margin + 20, y + 50), desc, fill=COLORS["text_gray"], font=font_card_desc)
        y += card_height + 10

    # TIP 박스
    tip_y = y + 10
    draw.rounded_rectangle([margin, tip_y, CANVAS_SIZE[0] - margin, tip_y + 70],
                          radius=10, fill=COLORS["tip_bg"])

    # ! 아이콘
    draw.ellipse([margin + 15, tip_y + 15, margin + 45, tip_y + 45], fill=COLORS["badge"])
    draw.text((margin + 27, tip_y + 15), "!", fill=COLORS["white"], font=font_tip)

    draw.text((margin + 60, tip_y + 12), "TIP", fill=COLORS["check_red"], font=font_tip)

    # TIP 텍스트 중앙
    tip_text = "체리 씨를 제거하는 도구(체리 피터)를 사용하면 더 안전해요"
    center_text(draw, tip_text, tip_y + 42, font_tip_text, COLORS["text_gray"])

    # 저장
    output = OUTPUT_DIR / "Cherry_Blog_07_Cooking.png"
    img.save(output, "PNG")
    print(f"   [OK] 저장: {output}")
    return img


# =============================================================================
# 메인
# =============================================================================
def main():
    print("=" * 60)
    print("004_Cherry 블로그 슬라이드 생성기")
    print("BLOG_SLIDE_DESIGN_RULE.md v2.1 준수")
    print("Safety: CAUTION")
    print("=" * 60)

    # 출력 폴더 확인
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # 슬라이드 생성
    generate_03_nutrition()
    generate_04_feeding()
    generate_05_amount()
    generate_06_caution()
    generate_07_cooking()

    print("\n" + "=" * 60)
    print("[완료] 5개 슬라이드 생성 완료")
    print(f"출력 폴더: {OUTPUT_DIR}")
    print("=" * 60)


if __name__ == "__main__":
    main()
