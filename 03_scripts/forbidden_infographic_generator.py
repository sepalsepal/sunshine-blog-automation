#!/usr/bin/env python3
"""
forbidden_infographic_generator.py - FORBIDDEN 음식용 인포그래픽 생성
§22.11.2 안전도별 캡션 구조 준수

FORBIDDEN 이미지 구조:
- 3번: 위험 성분 (not 영양 정보)
- 4번: 절대 급여 금지 (not 급여 방법)
- 5번: 위험 증상
- 6번: 응급 대처법 (not 주의사항)
- 7번: 수의사 상담 (not 조리 방법)
"""

import json
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = Path(__file__).parent.parent
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["4_posted", "3_approved", "2_body_ready", "1_cover_only"]

# 색상 정의 (FORBIDDEN용 - 빨간/검은 톤)
COLORS = {
    "danger_start": (220, 53, 69),       # 빨강 그라데이션 시작
    "danger_end": (185, 43, 56),         # 빨강 그라데이션 끝
    "cream": (255, 248, 231),            # 크림 배경
    "card_red": (255, 235, 238),         # 연한 빨강 카드
    "card_dark": (45, 45, 45),           # 어두운 카드
    "card_warning": (255, 243, 224),     # 경고 카드 (주황)
    "text_dark": (51, 51, 51),
    "text_gray": (100, 100, 100),
    "text_light": (170, 170, 170),
    "danger_red": (220, 53, 69),
    "warning_orange": (255, 152, 0),
    "white": (255, 255, 255),
    "black": (0, 0, 0),
}

# 폰트 경로
FONT_PATH = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

def get_font(style: str, size: int):
    try:
        if style == "bold":
            return ImageFont.truetype(FONT_PATH, size, index=5)
        else:
            return ImageFont.truetype(FONT_PATH, size, index=0)
    except:
        return ImageFont.load_default()


def draw_gradient(draw, bbox, color_start, color_end, direction="vertical"):
    x1, y1, x2, y2 = bbox
    for y in range(y1, y2):
        ratio = (y - y1) / (y2 - y1) if y2 > y1 else 0
        r = int(color_start[0] + (color_end[0] - color_start[0]) * ratio)
        g = int(color_start[1] + (color_end[1] - color_start[1]) * ratio)
        b = int(color_start[2] + (color_end[2] - color_start[2]) * ratio)
        draw.line([(x1, y), (x2, y)], fill=(r, g, b))


def draw_rounded_rect(draw, bbox, radius, fill):
    x1, y1, x2, y2 = bbox
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.ellipse([x1, y1, x1 + 2*radius, y1 + 2*radius], fill=fill)
    draw.ellipse([x2 - 2*radius, y1, x2, y1 + 2*radius], fill=fill)
    draw.ellipse([x1, y2 - 2*radius, x1 + 2*radius, y2], fill=fill)
    draw.ellipse([x2 - 2*radius, y2 - 2*radius, x2, y2], fill=fill)


def center_text(draw, text, font, x, y):
    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    return int(x - tw / 2), int(y - th / 2)


def generate_danger_components(data: dict, output_path: Path):
    """3번 위험 성분 이미지"""
    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 (빨강 그라데이션)
    draw_gradient(draw, (0, 0, 1080, 150), COLORS["danger_start"], COLORS["danger_end"])

    # 경고 아이콘 + 제목
    font_title = get_font("bold", 56)
    title = f"위험 성분"
    tx, _ = center_text(draw, title, font_title, 540, 60)
    draw.text((tx, 35), title, fill=COLORS["white"], font=font_title)

    font_sub = get_font("regular", 28)
    subtitle = f"{data['korean']}에 포함된 독성 물질"
    sx, _ = center_text(draw, subtitle, font_sub, 540, 115)
    draw.text((sx, 100), subtitle, fill=COLORS["white"], font=font_sub)

    # FORBIDDEN 뱃지
    badge_rect = (920, 45, 1040, 95)
    draw_rounded_rect(draw, badge_rect, 25, COLORS["white"])
    font_badge = get_font("bold", 24)
    bx, by = center_text(draw, "FORBIDDEN", font_badge, 980, 70)
    draw.text((bx, by), "FORBIDDEN", fill=COLORS["danger_red"], font=font_badge)

    # 위험 성분 카드
    toxic = data.get("toxic_components", [
        {"name": "독성 물질", "effect": "강아지에게 해로운 성분", "severity": "높음"},
        {"name": "유해 성분", "effect": "소화기/신경계 손상 가능", "severity": "높음"},
        {"name": "첨가물", "effect": "알레르기/중독 위험", "severity": "중간"},
    ])

    y_start = 200
    card_height = 120
    font_name = get_font("bold", 36)
    font_effect = get_font("regular", 24)
    font_severity = get_font("bold", 22)

    for i, t in enumerate(toxic[:5]):
        y = y_start + i * (card_height + 20)
        draw_rounded_rect(draw, (60, y, 1020, y + card_height), 15, COLORS["card_red"])

        # 번호 (빨간 원)
        draw.ellipse([80, y + 35, 130, y + 85], fill=COLORS["danger_red"])
        font_num = get_font("bold", 28)
        nx, ny = center_text(draw, str(i+1), font_num, 105, 60 + y)
        draw.text((nx, ny), str(i+1), fill=COLORS["white"], font=font_num)

        # 성분명
        draw.text((160, y + 25), t.get("name", "독성 물질"), fill=COLORS["danger_red"], font=font_name)
        # 효과
        draw.text((160, y + 75), t.get("effect", "강아지에게 해로움"), fill=COLORS["text_gray"], font=font_effect)

        # 위험도 뱃지
        severity = t.get("severity", "높음")
        sev_rect = (880, y + 40, 1000, y + 80)
        draw_rounded_rect(draw, sev_rect, 20, COLORS["danger_red"])
        sevx, sevy = center_text(draw, f"위험: {severity}", font_severity, 940, y + 60)
        draw.text((sevx, sevy), f"위험: {severity}", fill=COLORS["white"], font=font_severity)

    # 하단 경고
    font_warning = get_font("bold", 24)
    warning = "절대 급여하지 마세요"
    wx, _ = center_text(draw, warning, font_warning, 540, 1020)
    draw.text((wx, 1000), warning, fill=COLORS["danger_red"], font=font_warning)

    img.save(output_path)
    return output_path


def generate_absolute_no(data: dict, output_path: Path):
    """4번 절대 급여 금지 이미지"""
    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더
    draw_gradient(draw, (0, 0, 1080, 150), COLORS["danger_start"], COLORS["danger_end"])

    # 큰 X 마크
    font_x = get_font("bold", 120)
    draw.text((480, 180), "X", fill=COLORS["danger_red"], font=font_x)

    # 제목
    font_title = get_font("bold", 48)
    title = "절대 급여 금지"
    tx, _ = center_text(draw, title, font_title, 540, 75)
    draw.text((tx, 50), title, fill=COLORS["white"], font=font_title)

    font_sub = get_font("regular", 28)
    subtitle = f"{data['korean']}은(는) 강아지에게 위험합니다"
    sx, _ = center_text(draw, subtitle, font_sub, 540, 115)
    draw.text((sx, 100), subtitle, fill=COLORS["white"], font=font_sub)

    # 금지 사항 카드
    dont_items = data.get("forbidden_reasons", [
        "소량만 먹어도 중독 위험",
        "심각한 건강 문제 유발",
        "응급 상황 발생 가능",
    ])

    y_start = 350
    font_item = get_font("regular", 32)

    for i, item in enumerate(dont_items[:5]):
        y = y_start + i * 100
        draw_rounded_rect(draw, (60, y, 1020, y + 80), 15, COLORS["card_red"])

        # X 아이콘
        draw.ellipse([80, y + 15, 130, y + 65], fill=COLORS["danger_red"])
        font_xx = get_font("bold", 28)
        draw.text((95, y + 22), "X", fill=COLORS["white"], font=font_xx)

        # 텍스트
        draw.text((160, y + 22), item, fill=COLORS["text_dark"], font=font_item)

    # 하단 강조
    y_bottom = 900
    draw_rounded_rect(draw, (60, y_bottom, 1020, y_bottom + 100), 15, COLORS["danger_red"])
    font_bottom = get_font("bold", 36)
    msg = "단 한 입도 주지 마세요!"
    mx, _ = center_text(draw, msg, font_bottom, 540, y_bottom + 50)
    draw.text((mx, y_bottom + 30), msg, fill=COLORS["white"], font=font_bottom)

    img.save(output_path)
    return output_path


def generate_danger_symptoms(data: dict, output_path: Path):
    """5번 위험 증상 이미지"""
    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더
    draw_gradient(draw, (0, 0, 1080, 150), COLORS["warning_orange"], (255, 180, 50))

    font_title = get_font("bold", 56)
    title = "섭취 시 증상"
    tx, _ = center_text(draw, title, font_title, 540, 55)
    draw.text((tx, 30), title, fill=COLORS["white"], font=font_title)

    font_sub = get_font("regular", 28)
    subtitle = f"{data['korean']} 섭취 후 나타나는 증상"
    sx, _ = center_text(draw, subtitle, font_sub, 540, 110)
    draw.text((sx, 95), subtitle, fill=COLORS["white"], font=font_sub)

    # 증상 목록
    symptoms = data.get("symptoms", [
        {"symptom": "구토", "time": "섭취 후 1~2시간"},
        {"symptom": "설사", "time": "섭취 후 2~4시간"},
        {"symptom": "무기력", "time": "섭취 후 수시간"},
        {"symptom": "경련", "time": "심각한 경우"},
        {"symptom": "호흡 곤란", "time": "응급 상황"},
    ])

    y_start = 200
    card_height = 110
    font_symptom = get_font("bold", 32)
    font_time = get_font("regular", 22)

    for i, s in enumerate(symptoms[:5]):
        y = y_start + i * (card_height + 20)
        draw_rounded_rect(draw, (60, y, 1020, y + card_height), 15, COLORS["card_warning"])

        # 번호
        draw.ellipse([80, y + 30, 130, y + 80], fill=COLORS["warning_orange"])
        font_num = get_font("bold", 28)
        nx, ny = center_text(draw, str(i+1), font_num, 105, y + 55)
        draw.text((nx, ny), str(i+1), fill=COLORS["white"], font=font_num)

        # 증상
        draw.text((160, y + 25), s.get("symptom", "증상"), fill=COLORS["text_dark"], font=font_symptom)
        # 발현 시간
        draw.text((160, y + 70), s.get("time", "섭취 후"), fill=COLORS["text_gray"], font=font_time)

    # 하단 경고
    y_warn = 900
    draw_rounded_rect(draw, (60, y_warn, 1020, y_warn + 100), 15, COLORS["danger_red"])
    font_warn = get_font("bold", 28)
    warn = "위 증상 발견 시 즉시 동물병원으로!"
    wx, _ = center_text(draw, warn, font_warn, 540, y_warn + 50)
    draw.text((wx, y_warn + 35), warn, fill=COLORS["white"], font=font_warn)

    img.save(output_path)
    return output_path


def generate_emergency_response(data: dict, output_path: Path):
    """6번 응급 대처법 이미지"""
    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더
    draw_gradient(draw, (0, 0, 1080, 150), COLORS["danger_start"], COLORS["danger_end"])

    # 응급 뱃지
    font_title = get_font("bold", 56)
    title = "응급 대처법"
    tx, _ = center_text(draw, title, font_title, 540, 55)
    draw.text((tx, 30), title, fill=COLORS["white"], font=font_title)

    font_sub = get_font("regular", 28)
    subtitle = f"{data['korean']} 섭취 시 즉시 대응"
    sx, _ = center_text(draw, subtitle, font_sub, 540, 110)
    draw.text((sx, 95), subtitle, fill=COLORS["white"], font=font_sub)

    # 응급 단계
    steps = [
        {"step": "1. 침착하게 상황 파악", "desc": "먹은 양과 시간을 기억하세요"},
        {"step": "2. 입 안 확인", "desc": "남은 음식물이 있으면 제거"},
        {"step": "3. 즉시 동물병원 연락", "desc": "24시간 응급병원 번호 저장 필수"},
        {"step": "4. 구토 유도 금지", "desc": "전문가 지시 없이 임의로 구토 유도 금지"},
        {"step": "5. 병원 이동", "desc": "음식 포장지/남은 음식 지참"},
    ]

    y_start = 200
    card_height = 110
    font_step = get_font("bold", 28)
    font_desc = get_font("regular", 22)

    for i, s in enumerate(steps):
        y = y_start + i * (card_height + 20)
        color = COLORS["card_red"] if i < 3 else COLORS["card_warning"]
        draw_rounded_rect(draw, (60, y, 1020, y + card_height), 15, color)

        # 단계
        draw.text((100, y + 25), s["step"], fill=COLORS["danger_red"], font=font_step)
        # 설명
        draw.text((100, y + 65), s["desc"], fill=COLORS["text_gray"], font=font_desc)

    # 하단 - 전화번호
    y_phone = 900
    draw_rounded_rect(draw, (60, y_phone, 1020, y_phone + 100), 15, COLORS["danger_red"])
    font_phone = get_font("bold", 32)
    phone = "동물병원 응급실: 지금 바로 연락!"
    px, _ = center_text(draw, phone, font_phone, 540, y_phone + 50)
    draw.text((px, y_phone + 30), phone, fill=COLORS["white"], font=font_phone)

    img.save(output_path)
    return output_path


def generate_vet_consult(data: dict, output_path: Path):
    """7번 수의사 상담 이미지"""
    img = Image.new("RGB", (1080, 1080), COLORS["cream"])
    draw = ImageDraw.Draw(img)

    # 헤더 (파란색 계열 - 전문가)
    draw_gradient(draw, (0, 0, 1080, 150), (41, 128, 185), (52, 152, 219))

    font_title = get_font("bold", 56)
    title = "수의사 상담 필수"
    tx, _ = center_text(draw, title, font_title, 540, 55)
    draw.text((tx, 30), title, fill=COLORS["white"], font=font_title)

    font_sub = get_font("regular", 28)
    subtitle = f"{data['korean']} 관련 전문 상담"
    sx, _ = center_text(draw, subtitle, font_sub, 540, 110)
    draw.text((sx, 95), subtitle, fill=COLORS["white"], font=font_sub)

    # 상담 체크리스트
    checklist = [
        "섭취한 양과 시간 정확히 전달",
        "반려견 체중, 나이 정보 준비",
        "현재 나타난 증상 설명",
        "기존 질환 여부 알려주기",
        "수의사 지시 정확히 따르기",
    ]

    y_start = 200
    card_height = 100
    font_check = get_font("regular", 30)

    for i, item in enumerate(checklist):
        y = y_start + i * (card_height + 15)
        draw_rounded_rect(draw, (60, y, 1020, y + card_height), 15, (230, 247, 255))

        # 체크 아이콘
        draw.ellipse([80, y + 25, 130, y + 75], fill=(41, 128, 185))
        font_v = get_font("bold", 28)
        draw.text((95, y + 32), "V", fill=COLORS["white"], font=font_v)

        # 텍스트
        draw.text((160, y + 32), item, fill=COLORS["text_dark"], font=font_check)

    # 하단 메시지
    y_msg = 850
    draw_rounded_rect(draw, (60, y_msg, 1020, y_msg + 150), 15, (41, 128, 185))
    font_msg1 = get_font("bold", 32)
    font_msg2 = get_font("regular", 24)

    msg1 = "자가 치료 금지!"
    m1x, _ = center_text(draw, msg1, font_msg1, 540, y_msg + 40)
    draw.text((m1x, y_msg + 25), msg1, fill=COLORS["white"], font=font_msg1)

    msg2 = "인터넷 정보에 의존하지 말고"
    m2x, _ = center_text(draw, msg2, font_msg2, 540, y_msg + 80)
    draw.text((m2x, y_msg + 70), msg2, fill=COLORS["white"], font=font_msg2)

    msg3 = "반드시 전문 수의사와 상담하세요"
    m3x, _ = center_text(draw, msg3, font_msg2, 540, y_msg + 115)
    draw.text((m3x, y_msg + 105), msg3, fill=COLORS["white"], font=font_msg2)

    img.save(output_path)
    return output_path


def generate_forbidden_infographics(num: int):
    """FORBIDDEN 음식 인포그래픽 생성 (3~7번)"""
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    num_str = str(num)
    if num_str not in food_data:
        print(f"  {num}: 데이터 없음")
        return None

    data = food_data[num_str]

    if data.get("safety") != "FORBIDDEN":
        print(f"  {num}. {data.get('name', '')}: FORBIDDEN 아님 (스킵)")
        return None

    # 데이터 정규화
    data["korean"] = data.get("name", "음식")

    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    folder = None
    num_prefix = f"{num:03d}"
    for item in CONTENTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith(num_prefix):
            folder = item
            break

    if not folder:
        print(f"  {num}. {data['korean']}: 폴더 없음")
        return None

    blog_dir = folder / "02_Blog"
    blog_dir.mkdir(exist_ok=True)

    print(f"  {num}. {data['korean']} [FORBIDDEN]")

    # 기존 SAFE용 이미지 백업 및 삭제
    for old_file in ["3_영양정보.png", "4_급여가능불가.png", "7_조리방법.png"]:
        old_path = blog_dir / old_file
        if old_path.exists():
            old_path.unlink()

    # FORBIDDEN 인포그래픽 생성
    generate_danger_components(data, blog_dir / "3_위험성분.png")
    generate_absolute_no(data, blog_dir / "4_절대급여금지.png")
    generate_danger_symptoms(data, blog_dir / "5_위험증상.png")
    generate_emergency_response(data, blog_dir / "6_응급대처법.png")
    generate_vet_consult(data, blog_dir / "7_수의사상담.png")

    return folder


def main():
    # FORBIDDEN 음식 목록
    forbidden_nums = [
        20, 22, 23, 32, 51, 53, 55, 56, 57, 61, 65, 66, 70, 74, 75, 76, 77, 78,
        85, 87, 88, 89, 92, 93, 94, 95, 96, 98, 99, 101, 102, 103, 104, 107, 112, 113, 127
    ]

    print("=" * 60)
    print("FORBIDDEN 인포그래픽 재생성")
    print("=" * 60)
    print(f"대상: {len(forbidden_nums)}개\n")

    success = 0
    for num in forbidden_nums:
        result = generate_forbidden_infographics(num)
        if result:
            success += 1

    print()
    print("=" * 60)
    print(f"완료: {success}/{len(forbidden_nums)}개")
    print("=" * 60)


if __name__ == "__main__":
    main()
