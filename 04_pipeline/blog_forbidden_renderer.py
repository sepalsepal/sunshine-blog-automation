#!/usr/bin/env python3
"""
Project Sunshine - 블로그 FORBIDDEN 슬라이드 04~08 렌더러 v3
김부장 직접 작성 - 정확한 수직/수평 중앙 정렬 적용
macOS 폰트 경로 적용 (최부장)
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import os

# ============================================================
# 폰트 설정 (macOS)
# ============================================================
PROJECT_ROOT = Path(__file__).parent.parent
FONTS_DIR = PROJECT_ROOT / "02_config" / "fonts"
OUTPUT_DIR = PROJECT_ROOT / "00_rules" / "02_Image_rules" / "_golden" / "Blog"

# macOS 폰트 경로
FONT_PATHS = {
    "Black": FONTS_DIR / "NotoSansCJK-Black.ttc",
    "Bold": FONTS_DIR / "NotoSansCJK-Bold.ttc",
    "Medium": FONTS_DIR / "NotoSansCJK-Medium.ttc",
    "Regular": FONTS_DIR / "NotoSansCJK-Regular.ttc",
    "Light": FONTS_DIR / "NotoSansCJK-Light.ttc",
}

# Noto Color Emoji 폰트 (프로젝트 내 설치)
EMOJI_FONT_PATH = FONTS_DIR / "NotoColorEmoji.ttf"

try:
    EMOJI_FONT = ImageFont.truetype(str(EMOJI_FONT_PATH), 109)
    EMOJI_AVAILABLE = True
    print("[OK] Noto Color Emoji 폰트 로드 성공")
except Exception as e:
    EMOJI_AVAILABLE = False
    print(f"[WARN] 이모지 폰트 로드 실패: {e}")


def font(weight, size):
    weight_map = {
        900: "Black", 800: "Bold", 700: "Bold",
        600: "Medium", 400: "Regular", 300: "Light",
    }
    w = weight_map.get(weight, "Regular")
    path = FONT_PATHS.get(w, FONT_PATHS["Regular"])

    if path.exists():
        return ImageFont.truetype(str(path), size)

    try:
        return ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", size)
    except:
        return ImageFont.load_default()


def render_emoji(emoji_char, target_size):
    if not EMOJI_AVAILABLE:
        return None

    try:
        canvas = Image.new('RGBA', (150, 150), (0, 0, 0, 0))
        d = ImageDraw.Draw(canvas)
        d.text((0, 0), emoji_char, font=EMOJI_FONT, embedded_color=True)
        bbox = canvas.getbbox()
        if bbox:
            emoji_crop = canvas.crop(bbox)
            emoji_crop = emoji_crop.resize((target_size, target_size), Image.LANCZOS)
            return emoji_crop
    except:
        pass
    return None


# ============================================================
# 정렬 유틸리티
# ============================================================

def get_text_actual_height(draw, text, fnt):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    return bbox[3] - bbox[1], bbox[1]


def get_text_actual_width(draw, text, fnt):
    bbox = draw.textbbox((0, 0), text, font=fnt)
    return bbox[2] - bbox[0]


def draw_text_vcentered(draw, text, x, card_y, card_h, fnt, fill):
    ah, y_off = get_text_actual_height(draw, text, fnt)
    y = card_y + (card_h - ah) // 2 - y_off
    draw.text((x, y), text, font=fnt, fill=fill)
    return y


def draw_text_centered_in_box(draw, text, box_x, box_y, box_w, box_h, fnt, fill):
    aw = get_text_actual_width(draw, text, fnt)
    ah, y_off = get_text_actual_height(draw, text, fnt)
    x = box_x + (box_w - aw) // 2
    y = box_y + (box_h - ah) // 2 - y_off
    draw.text((x, y), text, font=fnt, fill=fill)


def draw_two_lines_vcentered(draw, title, title_fnt, title_fill,
                              sub, sub_fnt, sub_fill,
                              x, card_y, card_h, line_gap=6):
    t_ah, t_off = get_text_actual_height(draw, title, title_fnt)
    s_ah, s_off = get_text_actual_height(draw, sub, sub_fnt)
    total_h = t_ah + line_gap + s_ah
    start_y = card_y + (card_h - total_h) // 2
    draw.text((x, start_y - t_off), title, font=title_fnt, fill=title_fill)
    draw.text((x, start_y + t_ah + line_gap - s_off), sub, font=sub_fnt, fill=sub_fill)
    return start_y, start_y + t_ah + line_gap


def paste_emoji_vcentered(img, emoji_char, x, card_y, card_h, size):
    emoji_img = render_emoji(emoji_char, size)
    if emoji_img:
        ey = card_y + (card_h - size) // 2
        img.paste(emoji_img, (x, ey), emoji_img)


def draw_text_hcentered(draw, text, center_x, y, fnt, fill):
    aw = get_text_actual_width(draw, text, fnt)
    draw.text((center_x - aw // 2, y), text, font=fnt, fill=fill)


# ============================================================
# 컬러
# ============================================================
PRIMARY = (255, 82, 82)
ACCENT = (198, 40, 40)
DARK_BG = (26, 10, 10)
TEXT_LIGHT = (255, 205, 210)
TEXT_SUB = (239, 154, 154)
TEXT_DANGER = (229, 115, 115)
WHITE = (255, 255, 255)
CARD_BG = (38, 14, 14)
CARD_BG_URGENT = (52, 16, 16)
BORDER_SUBTLE = (100, 35, 35)
BORDER_URGENT = (198, 40, 40)

W, H = 1080, 1080


# ============================================================
# 둥근 사각형
# ============================================================
def draw_rounded_rect(draw, xy, radius, fill=None, outline=None, width=0):
    x0, y0, x1, y1 = xy
    r = min(radius, (x1-x0)//2, (y1-y0)//2)
    if fill:
        draw.rectangle([x0+r, y0, x1-r, y1], fill=fill)
        draw.rectangle([x0, y0+r, x1, y1-r], fill=fill)
        draw.pieslice([x0, y0, x0+2*r, y0+2*r], 180, 270, fill=fill)
        draw.pieslice([x1-2*r, y0, x1, y0+2*r], 270, 360, fill=fill)
        draw.pieslice([x0, y1-2*r, x0+2*r, y1], 90, 180, fill=fill)
        draw.pieslice([x1-2*r, y1-2*r, x1, y1], 0, 90, fill=fill)
    if outline and width > 0:
        draw.arc([x0, y0, x0+2*r, y0+2*r], 180, 270, fill=outline, width=width)
        draw.arc([x1-2*r, y0, x1, y0+2*r], 270, 360, fill=outline, width=width)
        draw.arc([x0, y1-2*r, x0+2*r, y1], 90, 180, fill=outline, width=width)
        draw.arc([x1-2*r, y1-2*r, x1, y1], 0, 90, fill=outline, width=width)
        draw.line([x0+r, y0, x1-r, y0], fill=outline, width=width)
        draw.line([x0+r, y1, x1-r, y1], fill=outline, width=width)
        draw.line([x0, y0+r, x0, y1-r], fill=outline, width=width)
        draw.line([x1, y0+r, x1, y1-r], fill=outline, width=width)


# ============================================================
# 헤더
# ============================================================
def create_header(img, draw, title, subtitle, eng_label):
    draw.rectangle([0, 0, W, 140], fill=PRIMARY)
    f_title = font(900, 52)
    draw.text((56, 24), title, font=f_title, fill=WHITE)
    f_sub = font(400, 24)
    draw.text((56, 96), subtitle, font=f_sub, fill=(255, 220, 220))
    f_eng = font(700, 22)
    aw = get_text_actual_width(draw, eng_label, f_eng)
    draw.text((W - 56 - aw, 56), eng_label, font=f_eng, fill=(255, 220, 220))


def create_base():
    img = Image.new('RGBA', (W, H), DARK_BG)
    draw = ImageDraw.Draw(img)
    return img, draw


# ============================================================
# 04. 독성 성분
# ============================================================
def render_04_toxicity(food_name, toxins):
    img, draw = create_base()
    create_header(img, draw, "독성 성분", f"{food_name} 기준 | 소량도 위험", "TOXIN")

    card_top = 158
    card_bottom = H - 88
    n = len(toxins)
    gap = 14
    card_h = (card_bottom - card_top - (n - 1) * gap) // n
    pad_x = 36
    emoji_size = 48
    text_left = pad_x + 30 + emoji_size + 22

    severity_colors = {
        '치명적': ACCENT, '고위험': (229, 57, 53),
        '독성': (239, 83, 80), '경고': (239, 83, 80),
    }

    for i, t in enumerate(toxins):
        y = card_top + i * (card_h + gap)
        draw_rounded_rect(draw, (pad_x, y, W - pad_x, y + card_h), 22,
                         fill=CARD_BG, outline=BORDER_SUBTLE, width=2)

        paste_emoji_vcentered(img, t['icon'], pad_x + 30, y, card_h, emoji_size)
        draw = ImageDraw.Draw(img)

        f_name = font(800, 38)
        f_sub = font(400, 22)
        draw_two_lines_vcentered(draw, t['name'], f_name, TEXT_LIGHT,
                                  t['sub'], f_sub, TEXT_SUB,
                                  text_left, y, card_h, line_gap=8)

        sev_color = severity_colors.get(t['severity'], ACCENT)
        badge_font = font(900, 28)
        bw = get_text_actual_width(draw, t['severity'], badge_font)
        badge_w = bw + 36
        badge_h = 44
        bx = W - pad_x - 24 - badge_w
        by = y + (card_h - badge_h) // 2
        draw_rounded_rect(draw, (bx, by, bx + badge_w, by + badge_h), 12, fill=sev_color)
        draw_text_centered_in_box(draw, t['severity'], bx, by, badge_w, badge_h, badge_font, WHITE)

    # 하단 경고 바 (⚠️ + 텍스트)
    bar_h = 72
    bar_y = H - bar_h
    draw.rectangle([0, bar_y, W, H], fill=ACCENT)
    f_warn = font(800, 28)
    warn_text = "가열해도 독성이 사라지지 않습니다"
    warn_w = get_text_actual_width(draw, warn_text, f_warn)
    total_warn_w = 42 + warn_w  # 이모지 + 간격 + 텍스트
    start_x = (W - total_warn_w) // 2
    paste_emoji_vcentered(img, '⚠️', start_x, bar_y, bar_h, 36)
    draw = ImageDraw.Draw(img)
    draw_text_vcentered(draw, warn_text, start_x + 42, bar_y, bar_h, f_warn, WHITE)

    return img.convert('RGB')


# ============================================================
# 05. 절대 급여 금지
# ============================================================
def render_05_allbanned(food_name, banned_items):
    img, draw = create_base()
    create_header(img, draw, "절대 급여 금지", f"{food_name} | 모든 형태 금지", "ALL BANNED")

    card_top = 158
    card_bottom = H - 20
    n = len(banned_items)
    gap = 10
    card_h = (card_bottom - card_top - (n - 1) * gap) // n
    pad_x = 36
    emoji_size = 36
    text_left = pad_x + 28 + emoji_size + 18

    for i, item in enumerate(banned_items):
        y = card_top + i * (card_h + gap)
        is_last = (i == n - 1)

        if is_last:
            draw_rounded_rect(draw, (pad_x, y, W - pad_x, y + card_h), 22, fill=ACCENT)
            f_text = font(900, 36)
            draw_text_vcentered(draw, item, text_left, y, card_h, f_text, WHITE)
        else:
            draw_rounded_rect(draw, (pad_x, y, W - pad_x, y + card_h), 22,
                             fill=CARD_BG, outline=BORDER_SUBTLE, width=2)
            f_text = font(700, 32)
            draw_text_vcentered(draw, item, text_left, y, card_h, f_text, TEXT_SUB)

        # 🚫 아이콘 — 카드 수직 중앙
        paste_emoji_vcentered(img, '🚫', pad_x + 28, y, card_h, emoji_size)
        draw = ImageDraw.Draw(img)

    return img.convert('RGB')


# ============================================================
# 06. 안전한 양은 없습니다
# ============================================================
def render_06_nodose(food_name, dose_info):
    img, draw = create_base()
    create_header(img, draw, "안전한 양은 없습니다", f"{food_name} | 어떤 양이든", "DANGER")

    # ============================================================
    # 수직 중앙 정렬 (김부장 지시서 #23-2)
    # ============================================================
    area_top = 140
    area_bottom = H - 70  # 하단 텍스트 공간 확보
    area_h = area_bottom - area_top

    # 각 요소 높이 및 폰트 준비
    emoji_h = 110
    gap1 = 20      # 아이콘 → 메인 텍스트
    f_main = font(900, 60)
    main_text = "어떤 양이든 위험합니다"
    ah_main, _ = get_text_actual_height(draw, main_text, f_main)
    gap2 = 28      # 메인 → 설명
    f_desc = font(400, 28)
    desc_ah, _ = get_text_actual_height(draw, dose_info['desc'], f_desc)
    gap3 = 36      # 설명 → 카드
    card_h = 200

    # 전체 콘텐츠 높이
    total_h = emoji_h + gap1 + ah_main + gap2 + desc_ah + gap3 + card_h

    # 수직 중앙 시작점
    start_y = area_top + (area_h - total_h) // 2
    cy = start_y  # 현재 Y 커서

    # 🚫 아이콘
    emoji_img = render_emoji('🚫', emoji_h)
    if emoji_img:
        ex = W // 2 - emoji_h // 2
        img.paste(emoji_img, (ex, cy), emoji_img)
    draw = ImageDraw.Draw(img)
    cy += emoji_h + gap1

    # "어떤 양이든 위험합니다" (한 줄)
    draw_text_hcentered(draw, main_text, W // 2, cy, f_main, PRIMARY)
    cy += ah_main + gap2

    # 설명
    draw_text_hcentered(draw, dose_info['desc'], W // 2, cy, f_desc, TEXT_SUB)
    cy += desc_ah + gap3

    # 체중별 위험량 카드 3개 (기존 로직 유지, Y만 cy 사용)
    examples = dose_info['examples']
    card_w = 280
    card_gap = 30
    total_w = card_w * len(examples) + card_gap * (len(examples) - 1)
    start_x = (W - total_w) // 2
    card_y = cy

    f_label = font(600, 24)
    f_danger = font(900, 48)
    f_small = font(400, 20)

    for i, ex in enumerate(examples):
        x = start_x + i * (card_w + card_gap)
        draw_rounded_rect(draw, (x, card_y, x + card_w, card_y + card_h), 24,
                         fill=CARD_BG, outline=BORDER_SUBTLE, width=2)

        lh, _ = get_text_actual_height(draw, ex['label'], f_label)
        dh, _ = get_text_actual_height(draw, ex['danger'], f_danger)
        sh, _ = get_text_actual_height(draw, "만으로 위험", f_small)
        total_text_h = lh + 14 + dh + 10 + sh
        sy = card_y + (card_h - total_text_h) // 2

        draw_text_centered_in_box(draw, ex['label'], x, sy - 4, card_w, lh + 8, f_label, TEXT_SUB)
        draw_text_centered_in_box(draw, ex['danger'], x, sy + lh + 14 - 4, card_w, dh + 8, f_danger, PRIMARY)
        draw_text_centered_in_box(draw, "만으로 위험", x, sy + lh + 14 + dh + 10 - 4, card_w, sh + 8, f_small, TEXT_DANGER)

    # 하단 텍스트 (고정 위치)
    f_bottom = font(700, 26)
    draw_text_hcentered(draw, dose_info.get('bottom', '소량 섭취도 즉시 동물병원 방문'),
                        W // 2, H - 60, f_bottom, TEXT_SUB)

    return img.convert('RGB')


# ============================================================
# 07. 중독 증상
# ============================================================
def render_07_symptoms(food_name, symptoms):
    img, draw = create_base()
    create_header(img, draw, "중독 증상", f"{food_name} 섭취 시 나타나는 증상", "SYMPTOMS")

    card_top = 164
    card_bottom = H - 30
    n = len(symptoms)
    gap = 14
    card_h = (card_bottom - card_top - (n - 1) * gap) // n
    pad_x = 36
    emoji_size = 48
    text_left = pad_x + 24 + emoji_size + 20

    severity_colors = {
        '초기': (239, 83, 80), '심각': (229, 57, 53), '위급': ACCENT,
    }

    for i, s in enumerate(symptoms):
        y = card_top + i * (card_h + gap)
        is_critical = s['severity'] == '위급'

        bg = CARD_BG_URGENT if is_critical else CARD_BG
        border = BORDER_URGENT if is_critical else BORDER_SUBTLE
        bw = 3 if is_critical else 2

        draw_rounded_rect(draw, (pad_x, y, W - pad_x, y + card_h), 22,
                         fill=bg, outline=border, width=bw)

        paste_emoji_vcentered(img, s['icon'], pad_x + 24, y, card_h, emoji_size)
        draw = ImageDraw.Draw(img)

        title_color = PRIMARY if is_critical else TEXT_LIGHT
        f_title = font(800, 34)
        f_desc = font(400, 22)
        draw_two_lines_vcentered(draw, s['title'], f_title, title_color,
                                  s['desc'], f_desc, TEXT_SUB,
                                  text_left, y, card_h, line_gap=6)

        sev_color = severity_colors.get(s['severity'], (239, 83, 80))
        badge_font = font(800, 20)
        btext_w = get_text_actual_width(draw, s['severity'], badge_font)
        badge_w = btext_w + 24
        badge_h = 32
        bx = W - pad_x - 24 - badge_w
        by = y + (card_h - badge_h) // 2
        draw_rounded_rect(draw, (bx, by, bx + badge_w, by + badge_h), 8, fill=sev_color)
        draw_text_centered_in_box(draw, s['severity'], bx, by, badge_w, badge_h, badge_font, WHITE)

    return img.convert('RGB')


# ============================================================
# 08. 응급 대처법
# ============================================================
def render_08_emergency(food_name, steps):
    img, draw = create_base()
    create_header(img, draw, "응급 대처법", f"{food_name} 섭취 시 즉시 행동", "EMERGENCY")

    step_top = 172
    step_bottom = H - 100
    n = len(steps)
    gap = 18
    step_h = (step_bottom - step_top - (n - 1) * gap) // n
    pad_x = 36
    circle_r = 46
    emoji_size = 44

    for i, s in enumerate(steps):
        y = step_top + i * (step_h + gap)
        urgent = s.get('urgent', False)

        cx = pad_x + circle_r + 8
        cy = y + step_h // 2
        circle_color = ACCENT if urgent else (60, 22, 22)
        draw.ellipse([cx - circle_r, cy - circle_r, cx + circle_r, cy + circle_r],
                     fill=circle_color)
        f_step = font(900, 40)
        draw_text_centered_in_box(draw, str(s['step']),
                                   cx - circle_r, cy - circle_r,
                                   circle_r * 2, circle_r * 2, f_step, WHITE)

        card_x = pad_x + circle_r * 2 + 28
        card_right = W - pad_x

        bg = CARD_BG_URGENT if urgent else CARD_BG
        border = BORDER_URGENT if urgent else BORDER_SUBTLE
        bw = 3 if urgent else 2

        draw_rounded_rect(draw, (card_x, y, card_right, y + step_h), 22,
                         fill=bg, outline=border, width=bw)

        title_color = PRIMARY if urgent else TEXT_LIGHT
        f_title = font(800, 34)
        f_desc = font(400, 22)
        draw_two_lines_vcentered(draw, s['title'], f_title, title_color,
                                  s['desc'], f_desc, TEXT_SUB,
                                  card_x + 24, y, step_h, line_gap=6)

        paste_emoji_vcentered(img, s['icon'], card_right - 24 - emoji_size, y, step_h, emoji_size)
        draw = ImageDraw.Draw(img)

    # 하단 경고 바 (🏥 + 텍스트)
    bar_h = 64
    bar_y = H - bar_h - 16
    draw_rounded_rect(draw, (36, bar_y, W - 36, bar_y + bar_h), 22, fill=ACCENT)
    f_warn = font(900, 26)
    warn_text = "24시간 동물병원 전화번호를 미리 저장하세요"
    warn_w = get_text_actual_width(draw, warn_text, f_warn)
    emoji_w = 36
    total_w = emoji_w + 10 + warn_w
    sx = (W - total_w) // 2
    paste_emoji_vcentered(img, '🏥', sx, bar_y, bar_h, emoji_w)
    draw = ImageDraw.Draw(img)
    draw_text_vcentered(draw, warn_text, sx + emoji_w + 10, bar_y, bar_h, f_warn, WHITE)

    return img.convert('RGB')


# ============================================================
# 양파 테스트 데이터
# ============================================================

ONION_04 = [
    {'icon': '☠️', 'name': '알릴 프로필 이황화물', 'sub': '적혈구 파괴', 'severity': '치명적'},
    {'icon': '⚗️', 'name': '티오황산염', 'sub': '산화 스트레스 유발', 'severity': '고위험'},
    {'icon': '🧬', 'name': 'N-프로필 이황화물', 'sub': '용혈성 빈혈', 'severity': '치명적'},
    {'icon': '💀', 'name': '유기황 화합물', 'sub': '소화기 손상', 'severity': '고위험'},
]

ONION_05 = [
    '생양파 급여', '익힌 양파 급여', '양파 가루/분말',
    '양파가 든 소스/국물', '양파링, 양파튀김 등 가공',
    '다른 음식에 소량 혼합', '양파즙, 양파차',
    '어떤 형태든 절대 불가',
]

ONION_06 = {
    'desc': '체중 1kg당 5g만 섭취해도 용혈성 빈혈 유발',
    'examples': [
        {'label': '소형견 5kg', 'danger': '25g'},
        {'label': '중형견 15kg', 'danger': '75g'},
        {'label': '대형견 30kg', 'danger': '150g'},
    ],
    'bottom': '소량 섭취도 즉시 동물병원 방문',
}

ONION_07 = [
    {'icon': '🤮', 'title': '구토 / 설사', 'desc': '섭취 후 1~2시간 내', 'severity': '초기'},
    {'icon': '😵', 'title': '무기력 / 식욕 감퇴', 'desc': '1~3일 이내', 'severity': '초기'},
    {'icon': '💛', 'title': '잇몸/눈 황달', 'desc': '2~5일 이내 (빈혈 징후)', 'severity': '심각'},
    {'icon': '🫀', 'title': '빈맥 / 호흡 곤란', 'desc': '용혈성 빈혈 진행', 'severity': '위급'},
    {'icon': '🩸', 'title': '갈색/붉은 소변', 'desc': '적혈구 파괴 증거', 'severity': '위급'},
]

ONION_08 = [
    {'step': 1, 'title': '추가 섭취 차단', 'desc': '입 안에 남은 것 즉시 제거', 'icon': '🛑', 'urgent': True},
    {'step': 2, 'title': '섭취량 파악', 'desc': '언제, 얼마나 먹었는지 확인', 'icon': '📝', 'urgent': False},
    {'step': 3, 'title': '동물병원 즉시 연락', 'desc': '24시간 응급 동물병원 확인', 'icon': '📞', 'urgent': True},
    {'step': 4, 'title': '임의 구토 유발 금지', 'desc': '수의사 지시 없이 절대 금지', 'icon': '🚫', 'urgent': False},
]


if __name__ == '__main__':
    out = OUTPUT_DIR / 'FORBIDDEN'
    out.mkdir(parents=True, exist_ok=True)
    food = '양파'

    print("=" * 50)
    print("FORBIDDEN 슬라이드 렌더러 v3 (김부장)")
    print("=" * 50)

    print("\n[FORBIDDEN] 양파 테스트...")
    render_04_toxicity(food, ONION_04).save(f'{out}/Golden_Blog_FORBIDDEN_04_Toxicity.png'); print("  04 완료")
    render_05_allbanned(food, ONION_05).save(f'{out}/Golden_Blog_FORBIDDEN_05_AllBanned.png'); print("  05 완료")
    render_06_nodose(food, ONION_06).save(f'{out}/Golden_Blog_FORBIDDEN_06_NoDose.png'); print("  06 완료")
    render_07_symptoms(food, ONION_07).save(f'{out}/Golden_Blog_FORBIDDEN_07_Symptoms.png'); print("  07 완료")
    render_08_emergency(food, ONION_08).save(f'{out}/Golden_Blog_FORBIDDEN_08_Emergency.png'); print("  08 완료")

    print(f"\n완료! 출력: {out}")
