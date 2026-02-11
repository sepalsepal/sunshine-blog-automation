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
"""

import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).parent.parent
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
CONTENTS_DIR = PROJECT_ROOT / "contents"
STATUS_DIRS = ["4_posted", "3_approved", "2_body_ready", "1_cover_only"]

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


def draw_circle_badge(draw, center, radius, color, text, font):
    """원형 뱃지 그리기 (중앙정렬 필수)"""
    x, y = center
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color)
    # bbox 기반 정확한 중앙정렬
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    # 텍스트 시작점 보정 (bbox[0], bbox[1] 오프셋 고려)
    text_x = x - tw // 2 - bbox[0]
    text_y = y - th // 2 - bbox[1]
    draw.text((text_x, text_y), text, fill=COLORS["white"], font=font)


def generate_nutrition_card(data: dict, output_path: Path):
    """3번 영양정보 이미지 생성"""
    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션
    draw_gradient(draw, (0, 0, 1080, 150), COLORS["mint_start"], COLORS["mint_end"])

    # 제목
    font_title = get_font("bold", 56)
    title = f"{data['korean']} 영양성분"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    tw = bbox[2] - bbox[0]
    draw.text((540 - tw // 2, 45), title, fill=COLORS["white"], font=font_title)

    # 부제목
    font_sub = get_font("regular", 24)
    subtitle = "100g 기준 | 강아지에게 안전한 영양 간식"
    bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
    tw = bbox[2] - bbox[0]
    draw.text((540 - tw // 2, 105), subtitle, fill=COLORS["white"], font=font_sub)

    # SAFE 뱃지
    safety = data.get("safety", "SAFE")
    if safety == "SAFE":
        badge_color = COLORS["safe_green"]
    elif safety == "CAUTION":
        badge_color = COLORS["caution_yellow"]
    else:
        badge_color = COLORS["danger_red"]

    draw_rounded_rect(draw, (940, 45, 1040, 85), 20, badge_color)
    font_badge = get_font("bold", 22)
    draw.text((960, 52), safety, fill=COLORS["white"], font=font_badge)

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

        # 번호 뱃지
        badge_color = BADGE_COLORS[i % len(BADGE_COLORS)]
        draw_circle_badge(draw, (110, y + 50), 25, badge_color, str(i + 1), font_num)

        # 성분명
        draw.text((160, y + 20), n["name"], fill=COLORS["text_dark"], font=font_name)

        # 효능
        draw.text((160, y + 60), n["benefit"], fill=COLORS["text_gray"], font=font_benefit)

        # 수치
        value_text = f"{n['value']} {n['unit']}"
        bbox = draw.textbbox((0, 0), value_text, font=font_value)
        tw = bbox[2] - bbox[0]
        draw.text((980 - tw, y + 30), value_text, fill=badge_color, font=font_value)

    # 하단 주석
    font_note = get_font("regular", 18)
    note = f"* 노령견에게 특히 좋은 {nutrition[0]['name'] if nutrition else '영양소'}이 풍부합니다"
    bbox = draw.textbbox((0, 0), note, font=font_note)
    tw = bbox[2] - bbox[0]
    draw.text((540 - tw // 2, 1030), note, fill=COLORS["text_light"], font=font_note)

    img.save(output_path)
    return output_path


def generate_dosage_card(data: dict, output_path: Path):
    """5번 급여량표 이미지 생성"""
    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션
    draw_gradient(draw, (0, 0, 1080, 150), COLORS["mint_start"], COLORS["mint_end"])

    # 제목
    font_title = get_font("bold", 56)
    title = "체중별 급여량 가이드"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    tw = bbox[2] - bbox[0]
    draw.text((540 - tw // 2, 45), title, fill=COLORS["white"], font=font_title)

    # 부제목
    font_sub = get_font("regular", 24)
    subtitle = "하루 기준 | 간식으로 급여 시"
    bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
    tw = bbox[2] - bbox[0]
    draw.text((540 - tw // 2, 105), subtitle, fill=COLORS["white"], font=font_sub)

    # 테이블 헤더
    y_table = 220
    draw_rounded_rect(draw, (60, y_table, 1020, y_table + 60), 10, COLORS["mint_start"])

    font_header = get_font("bold", 24)
    draw.text((150, y_table + 18), "구분", fill=COLORS["white"], font=font_header)
    draw.text((400, y_table + 18), "체중", fill=COLORS["white"], font=font_header)
    draw.text((720, y_table + 18), "급여량", fill=COLORS["white"], font=font_header)

    # 테이블 행 (g + 직관 단위 필수)
    dosage = data.get("dosage", {})
    rows = [
        ("소형견", "5kg 이하", dosage.get("small", {}).get("g", "-"), dosage.get("small", {}).get("unit", "")),
        ("중형견", "5~15kg", dosage.get("medium", {}).get("g", "-"), dosage.get("medium", {}).get("unit", "")),
        ("대형견", "15~30kg", dosage.get("large", {}).get("g", "-"), dosage.get("large", {}).get("unit", "")),
        ("초대형견", "30kg 이상", dosage.get("xlarge", {}).get("g", "-"), dosage.get("xlarge", {}).get("unit", "")),
    ]

    font_row = get_font("regular", 26)
    font_value = get_font("bold", 28)
    font_unit = get_font("regular", 18)
    row_height = 90

    for i, (label, weight, amount, unit) in enumerate(rows):
        y = y_table + 60 + i * row_height + 15
        draw.text((100, y + 18), label, fill=COLORS["text_dark"], font=font_row)
        draw.text((280, y + 18), weight, fill=COLORS["text_gray"], font=font_row)
        # g 단위
        draw.text((480, y + 12), amount, fill=COLORS["badge_orange"], font=font_value)
        # 직관 단위 (필수)
        if unit:
            draw.text((480, y + 48), f"({unit})", fill=COLORS["text_gray"], font=font_unit)

    # 주의사항 박스 (주황 박스 + 텍스트)
    y_caution = 660
    draw_rounded_rect(draw, (60, y_caution, 1020, y_caution + 120), 15, COLORS["card_yellow"])

    # 주의 뱃지 (도형 + 텍스트)
    draw_rounded_rect(draw, (100, y_caution + 15, 180, y_caution + 50), 5, COLORS["badge_orange"])
    font_badge_small = get_font("bold", 20)
    draw.text((117, y_caution + 20), "주의", fill=COLORS["white"], font=font_badge_small)

    font_caution_title = get_font("bold", 22)
    draw.text((195, y_caution + 20), "급여 시 주의사항", fill=COLORS["badge_orange"], font=font_caution_title)

    font_caution = get_font("regular", 22)
    draw.text((100, y_caution + 55), "• 하루 칼로리의 10% 이내로 급여해주세요", fill=COLORS["text_gray"], font=font_caution)
    draw.text((100, y_caution + 85), "• 처음 급여 시 소량부터 시작하세요", fill=COLORS["text_gray"], font=font_caution)

    # 하단 주석
    font_note = get_font("regular", 18)
    note = "* 개체별 차이가 있으므로 반응을 보며 조절하세요"
    bbox = draw.textbbox((0, 0), note, font=font_note)
    tw = bbox[2] - bbox[0]
    draw.text((540 - tw // 2, 1030), note, fill=COLORS["text_light"], font=font_note)

    img.save(output_path)
    return output_path


def generate_do_dont_card(data: dict, output_path: Path):
    """4번 급여가능/불가 이미지 생성"""
    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션
    draw_gradient(draw, (0, 0, 1080, 150), COLORS["mint_start"], COLORS["mint_end"])

    # SAFE 뱃지 (중앙)
    safety = data.get("safety", "SAFE")
    if safety == "SAFE":
        badge_color = COLORS["safe_green"]
    elif safety == "CAUTION":
        badge_color = COLORS["caution_yellow"]
    else:
        badge_color = COLORS["danger_red"]

    draw_rounded_rect(draw, (460, 40, 620, 100), 30, COLORS["white"])
    font_badge = get_font("bold", 36)
    bbox = draw.textbbox((0, 0), safety, font=font_badge)
    tw = bbox[2] - bbox[0]
    draw.text((540 - tw // 2, 55), safety, fill=badge_color, font=font_badge)

    # 제목
    font_title = get_font("bold", 36)
    title = "강아지가 먹어도 안전해요"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    tw = bbox[2] - bbox[0]
    draw.text((540 - tw // 2, 180), title, fill=COLORS["text_dark"], font=font_title)

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
        # 초록 원 + V 텍스트 (도형 기반)
        draw.ellipse([80, y + 5, 110, y + 35], fill=COLORS["safe_green"])
        font_check = get_font("bold", 18)
        draw.text((88, y + 9), "V", fill=COLORS["white"], font=font_check)
        draw.text((130, y + 3), item, fill=COLORS["text_dark"], font=font_item)

    # DON'T 섹션
    y_dont = y_do_card + 50 * len(do_items) + 80
    draw.text((80, y_dont), "이것만은 피해주세요", fill=COLORS["danger_red"], font=font_section)

    dont_items = data.get("dont", [])[:3]

    y_dont_card = y_dont + 40
    draw_rounded_rect(draw, (60, y_dont_card, 1020, y_dont_card + 50 * len(dont_items) + 30), 15, COLORS["card_pink"])

    for i, item in enumerate(dont_items):
        y = y_dont_card + 25 + i * 50
        # 빨간 원 + X 텍스트 (도형 기반)
        draw.ellipse([80, y + 5, 110, y + 35], fill=COLORS["danger_red"])
        font_x = get_font("bold", 18)
        draw.text((88, y + 9), "X", fill=COLORS["white"], font=font_x)
        draw.text((130, y + 3), item, fill=COLORS["text_dark"], font=font_item)

    # 하단 메시지
    y_msg = 900
    draw_rounded_rect(draw, (60, y_msg, 1020, y_msg + 60), 15, (230, 247, 255))
    font_msg = get_font("regular", 24)
    msg = "11살 노령견 햇살이도 안전하게 먹고 있어요"
    bbox = draw.textbbox((0, 0), msg, font=font_msg)
    tw = bbox[2] - bbox[0]
    draw.text((540 - tw // 2, y_msg + 18), msg, fill=COLORS["mint_start"], font=font_msg)

    img.save(output_path)
    return output_path


def generate_caution_card(data: dict, output_path: Path):
    """6번 주의사항 이미지 생성"""
    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션 (주황)
    draw_gradient(draw, (0, 0, 1080, 150), COLORS["coral_start"], COLORS["coral_end"])

    # 제목 (도형 뱃지 + 텍스트)
    # 주의 뱃지 (삼각형 대신 둥근 사각형)
    draw_rounded_rect(draw, (380, 40, 480, 85), 10, COLORS["white"])
    font_badge = get_font("bold", 26)
    draw.text((400, 48), "주의", fill=COLORS["coral_start"], font=font_badge)

    font_title = get_font("bold", 48)
    title = "주의사항"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    tw = bbox[2] - bbox[0]
    draw.text((540 - tw // 2 + 30, 50), title, fill=COLORS["white"], font=font_title)

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

        # 번호 뱃지
        badge_color = BADGE_COLORS[i % len(BADGE_COLORS)]
        draw_circle_badge(draw, (110, y + 55), 25, badge_color, str(i + 1), font_num)

        # 제목
        draw.text((160, y + 25), c["title"], fill=COLORS["text_dark"], font=font_title_card)

        # 설명
        draw.text((160, y + 65), c["desc"], fill=COLORS["text_gray"], font=font_desc)

    # 하단 응급 안내 (도형 뱃지 + 텍스트)
    y_emergency = 880
    draw_rounded_rect(draw, (60, y_emergency, 1020, y_emergency + 60), 15, COLORS["card_pink"])

    # 응급 뱃지 (빨간 원 + 십자)
    draw.ellipse([80, y_emergency + 12, 116, y_emergency + 48], fill=COLORS["danger_red"])
    font_cross = get_font("bold", 24)
    draw.text((90, y_emergency + 15), "+", fill=COLORS["white"], font=font_cross)

    font_emergency = get_font("bold", 22)
    draw.text((130, y_emergency + 18), "이상 반응 발생 시 즉시 수의사와 상담하세요", fill=COLORS["danger_red"], font=font_emergency)

    img.save(output_path)
    return output_path


def generate_cooking_card(data: dict, output_path: Path):
    """7번 조리방법 이미지 생성"""
    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 그라데이션
    draw_gradient(draw, (0, 0, 1080, 150), COLORS["mint_start"], COLORS["mint_end"])

    # 제목
    font_title = get_font("bold", 56)
    title = "안전한 조리 방법"
    bbox = draw.textbbox((0, 0), title, font=font_title)
    tw = bbox[2] - bbox[0]
    draw.text((540 - tw // 2, 40), title, fill=COLORS["white"], font=font_title)

    # 부제목
    font_sub = get_font("regular", 24)
    subtitle = f"강아지를 위한 {data['korean']} 준비 5단계"
    bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
    tw = bbox[2] - bbox[0]
    draw.text((540 - tw // 2, 100), subtitle, fill=COLORS["white"], font=font_sub)

    # 조리 단계 카드들
    cooking = data.get("cooking", [])
    y_start = 200
    card_height = 110
    card_margin = 15

    font_step = get_font("bold", 20)
    font_title_card = get_font("bold", 28)
    font_desc = get_font("regular", 20)

    for i, step in enumerate(cooking[:5]):
        y = y_start + i * (card_height + card_margin)

        # 카드 배경
        draw_rounded_rect(draw, (60, y, 1020, y + card_height), 15, COLORS["card_mint"])

        # STEP 뱃지
        badge_color = BADGE_COLORS[i % len(BADGE_COLORS)]
        draw_rounded_rect(draw, (80, y + 25, 160, y + 60), 17, badge_color)
        draw.text((90, y + 30), f"STEP {i + 1}", fill=COLORS["white"], font=font_step)

        # 단계명
        draw.text((180, y + 25), step["step"], fill=COLORS["text_dark"], font=font_title_card)

        # 설명
        draw.text((80, y + 70), step["desc"], fill=COLORS["text_gray"], font=font_desc)

    # TIP 박스 (도형 뱃지 + 텍스트)
    y_tip = 880
    draw_rounded_rect(draw, (60, y_tip, 1020, y_tip + 80), 15, COLORS["card_yellow"])

    # TIP 뱃지 (주황 원 + 느낌표)
    draw.ellipse([80, y_tip + 12, 116, y_tip + 48], fill=COLORS["badge_orange"])
    font_exclaim = get_font("bold", 26)
    draw.text((93, y_tip + 13), "!", fill=COLORS["white"], font=font_exclaim)

    font_tip_title = get_font("bold", 22)
    font_tip = get_font("regular", 20)
    draw.text((130, y_tip + 15), "TIP", fill=COLORS["badge_orange"], font=font_tip_title)
    draw.text((100, y_tip + 48), data.get("tip_box", ""), fill=COLORS["text_gray"], font=font_tip)

    img.save(output_path)
    return output_path


def generate_all_infographics(num: int, dry_run: bool = False):
    """모든 인포그래픽 생성 (3~7번)"""
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    num_str = f"{num:03d}"
    if num_str not in food_data:
        print(f"❌ #{num_str} 데이터 없음")
        return None

    data = food_data[num_str]

    # 폴더 찾기
    folder = None
    for status_dir in STATUS_DIRS:
        status_path = CONTENTS_DIR / status_dir
        if not status_path.exists():
            continue
        for item in status_path.iterdir():
            if item.is_dir() and item.name.startswith(num_str):
                folder = item
                break
        if folder:
            break

    if not folder:
        print(f"❌ #{num_str} 폴더 없음")
        return None

    blog_dir = folder / "blog"
    blog_dir.mkdir(exist_ok=True)

    print(f"📊 #{num_str} {data['korean']} 인포그래픽 생성")

    results = []

    # 3번: 영양정보
    if data.get("nutrition"):
        output_3 = blog_dir / "3_영양정보.png"
        if not dry_run:
            generate_nutrition_card(data, output_3)
        print(f"   ✅ 3번 영양정보")
        results.append(output_3)

    # 4번: 급여가능/불가
    if data.get("do") or data.get("dont"):
        output_4 = blog_dir / "4_급여가능불가.png"
        if not dry_run:
            generate_do_dont_card(data, output_4)
        print(f"   ✅ 4번 급여가능불가")
        results.append(output_4)

    # 5번: 급여량표
    if data.get("dosage"):
        output_5 = blog_dir / "5_급여량표.png"
        if not dry_run:
            generate_dosage_card(data, output_5)
        print(f"   ✅ 5번 급여량표")
        results.append(output_5)

    # 6번: 주의사항
    if data.get("caution"):
        output_6 = blog_dir / "6_주의사항.png"
        if not dry_run:
            generate_caution_card(data, output_6)
        print(f"   ✅ 6번 주의사항")
        results.append(output_6)

    # 7번: 조리방법
    if data.get("cooking"):
        output_7 = blog_dir / "7_조리방법.png"
        if not dry_run:
            generate_cooking_card(data, output_7)
        print(f"   ✅ 7번 조리방법")
        results.append(output_7)

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
