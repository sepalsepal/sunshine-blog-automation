#!/usr/bin/env python3
"""
Project Sunshine - 블로그 SAFE/CAUTION 슬라이드 04~08 렌더러 v4
김부장 직접 작성
macOS 폰트 경로 적용 (최부장)

수정사항:
  1. 05번 타이틀 이모지 겹침 → 이모지+텍스트 통합 배치
  2. 05번 DON'T ✕ → 텍스트로 "X" 사용
  3. CAUTION 🍳 매핑 오류 → 대체 이모지
  4. 카드 gap 축소
  5. 헤더 서브텍스트/영문라벨 컬러 정확 보정
  6. FORBIDDEN 🚫 크기 통일 (일괄 36px)
  7. 06번 우측 숫자+단위 정렬 안정화
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

# 이모지 폰트 로드 시도
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

    # Fallback to system font
    try:
        return ImageFont.truetype("/System/Library/Fonts/AppleSDGothicNeo.ttc", size)
    except:
        return ImageFont.load_default()


def render_emoji(emoji_char, target_size):
    """이모지를 이미지로 렌더링"""
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
# 정렬 유틸 (v3 계승)
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


def draw_two_lines_right_vcentered(draw, val, val_fnt, val_fill,
                                     unit, unit_fnt, unit_fill,
                                     right_x, card_y, card_h, line_gap=4):
    v_ah, v_off = get_text_actual_height(draw, val, val_fnt)
    u_ah, u_off = get_text_actual_height(draw, unit, unit_fnt)
    total_h = v_ah + line_gap + u_ah
    start_y = card_y + (card_h - total_h) // 2
    vw = get_text_actual_width(draw, val, val_fnt)
    uw = get_text_actual_width(draw, unit, unit_fnt)
    draw.text((right_x - vw, start_y - v_off), val, font=val_fnt, fill=val_fill)
    draw.text((right_x - uw, start_y + v_ah + line_gap - u_off), unit, font=unit_fnt, fill=unit_fill)


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
SAFETY_COLORS = {
    'SAFE': {
        'primary': (76, 175, 80),
        'light': (232, 245, 233),
        'accent': (46, 125, 50),
        'dark': (27, 94, 32),
        'on_primary': (255, 255, 255),
        'header_sub': (210, 240, 212),
        'header_eng': (185, 220, 187),
    },
    'CAUTION': {
        'primary': (255, 217, 61),
        'light': (255, 248, 225),
        'accent': (249, 168, 37),
        'dark': (230, 81, 0),
        'on_primary': (51, 51, 51),
        'header_sub': (140, 120, 40),
        'header_eng': (160, 140, 50),
    },
}

BG_LIGHT = (250, 250, 250)
WHITE = (255, 255, 255)
TEXT_DARK = (26, 26, 26)
TEXT_GRAY = (153, 153, 153)
TEXT_LIGHT_GRAY = (170, 170, 170)
TEXT_MID_GRAY = (136, 136, 136)
BORDER_LIGHT = (240, 240, 240)
DO_BG = (232, 245, 233)
DO_TEXT = (46, 125, 50)
DONT_BG = (255, 235, 238)
DONT_TEXT = (198, 40, 40)

W, H = 1080, 1080


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


def create_header(img, draw, title, subtitle, eng_label, c):
    draw.rectangle([0, 0, W, 140], fill=c['primary'])
    on = c['on_primary']
    f_title = font(900, 52)
    draw.text((56, 24), title, font=f_title, fill=on)
    f_sub = font(400, 24)
    draw.text((56, 96), subtitle, font=f_sub, fill=c['header_sub'])
    f_eng = font(700, 22)
    aw = get_text_actual_width(draw, eng_label, f_eng)
    draw.text((W - 56 - aw, 56), eng_label, font=f_eng, fill=c['header_eng'])


def create_base():
    img = Image.new('RGBA', (W, H), BG_LIGHT)
    draw = ImageDraw.Draw(img)
    return img, draw


# ============================================================
# 04. 영양성분
# ============================================================
def render_04_nutrition(food_name, items, c):
    img, draw = create_base()
    create_header(img, draw, f"{food_name} 영양성분", "100g 기준", "NUTRITION", c)

    card_top = 152
    card_bottom = H - 16
    n = len(items)
    gap = 6
    card_h = (card_bottom - card_top - (n - 1) * gap) // n
    pad_x = 32
    emoji_size = 48
    text_left = pad_x + 24 + emoji_size + 18

    for i, item in enumerate(items):
        y = card_top + i * (card_h + gap)
        bg = c['light'] if i % 2 == 0 else WHITE
        draw_rounded_rect(draw, (pad_x, y, W - pad_x, y + card_h), 22, fill=bg)

        paste_emoji_vcentered(img, item['icon'], pad_x + 24, y, card_h, emoji_size)
        draw = ImageDraw.Draw(img)

        f_name = font(800, 42)
        f_sub = font(400, 22)
        draw_two_lines_vcentered(draw, item['name'], f_name, TEXT_DARK,
                                  item['sub'], f_sub, TEXT_GRAY,
                                  text_left, y, card_h, line_gap=12)

        f_val = font(900, 56)
        f_unit = font(600, 26)
        val_text = item['val']
        unit_text = item['unit']
        val_w = get_text_actual_width(draw, val_text, f_val)
        unit_w = get_text_actual_width(draw, unit_text, f_unit)
        total_w = val_w + 6 + unit_w
        right_edge = W - pad_x - 28
        start_x = right_edge - total_w

        val_ah, val_off = get_text_actual_height(draw, val_text, f_val)
        unit_ah, unit_off = get_text_actual_height(draw, unit_text, f_unit)
        val_y = y + (card_h - val_ah) // 2 - val_off
        draw.text((start_x, val_y), val_text, font=f_val, fill=c['accent'])
        val_bottom = y + (card_h + val_ah) // 2
        unit_bottom_y = val_bottom - unit_ah - unit_off
        draw.text((start_x + val_w + 6, unit_bottom_y), unit_text, font=f_unit, fill=c['primary'])

    return img.convert('RGB')


# ============================================================
# 05. 급여 가이드 (DO & DON'T)
# ============================================================
def render_05_dodont(food_name, dos, donts, c):
    img, draw = create_base()
    create_header(img, draw, "급여 가이드", f"{food_name} | 급여 시 참고", "DO & DON'T", c)

    col_gap = 16
    col_w = (W - 32 * 2 - col_gap) // 2
    col_top = 158
    col_bottom = H - 20
    col_h = col_bottom - col_top

    left_x = 32
    right_x = 32 + col_w + col_gap

    draw_rounded_rect(draw, (left_x, col_top, left_x + col_w, col_top + col_h), 24, fill=DO_BG)
    draw_rounded_rect(draw, (right_x, col_top, right_x + col_w, col_top + col_h), 24, fill=DONT_BG)

    f_col_title = font(900, 34)
    title_h = 56
    title_emoji_size = 30

    # DO 타이틀: ✅ + "이렇게 하세요"
    do_title = "이렇게 하세요"
    do_tw = get_text_actual_width(draw, do_title, f_col_title)
    do_total = title_emoji_size + 10 + do_tw
    do_sx = left_x + (col_w - do_total) // 2
    paste_emoji_vcentered(img, '✅', do_sx, col_top + 8, title_h, title_emoji_size)
    draw = ImageDraw.Draw(img)
    draw_text_vcentered(draw, do_title, do_sx + title_emoji_size + 10, col_top + 8, title_h, f_col_title, DO_TEXT)

    # DON'T 타이틀: 🚫 + "이건 안 돼요"
    dont_title = "이건 안 돼요"
    dont_tw = get_text_actual_width(draw, dont_title, f_col_title)
    dont_total = title_emoji_size + 10 + dont_tw
    dont_sx = right_x + (col_w - dont_total) // 2
    paste_emoji_vcentered(img, '🚫', dont_sx, col_top + 8, title_h, title_emoji_size)
    draw = ImageDraw.Draw(img)
    draw_text_vcentered(draw, dont_title, dont_sx + title_emoji_size + 10, col_top + 8, title_h, f_col_title, DONT_TEXT)

    # 아이템 카드들
    items_top = col_top + title_h + 16
    items_bottom = col_bottom - 14
    card_pad = 10

    def draw_column_items(items, col_x, col_width, text_color, check_char):
        n = len(items)
        item_gap = 6
        item_h = (items_bottom - items_top - (n - 1) * item_gap) // n
        f_item = font(600, 24)
        f_check = font(700, 26)

        for j, item_text in enumerate(items):
            iy = items_top + j * (item_h + item_gap)
            draw_rounded_rect(draw, (col_x + card_pad, iy, col_x + col_width - card_pad, iy + item_h),
                             16, fill=WHITE)
            check_x = col_x + card_pad + 16
            text_x = check_x + 32
            draw_text_vcentered(draw, check_char, check_x, iy, item_h, f_check, text_color)
            draw_text_vcentered(draw, item_text, text_x, iy, item_h, f_item, text_color)

    draw_column_items(dos, left_x, col_w, DO_TEXT, '✓')
    draw_column_items(donts, right_x, col_w, DONT_TEXT, 'X')

    return img.convert('RGB')


# ============================================================
# 06. 체급별 급여량
# ============================================================
def render_06_serving(food_name, sizes, tip_text, c):
    img, draw = create_base()
    create_header(img, draw, "체급별 급여량", "1일 기준 | 처음엔 절반부터", "SERVING", c)

    card_top = 158
    card_bottom = H - 74
    n = len(sizes)
    gap = 8
    card_h = (card_bottom - card_top - (n - 1) * gap) // n
    pad_x = 32
    emoji_size = 52
    text_left = pad_x + 24 + emoji_size + 16

    for i, s in enumerate(sizes):
        y = card_top + i * (card_h + gap)
        draw_rounded_rect(draw, (pad_x, y, W - pad_x, y + card_h), 24,
                         fill=WHITE, outline=c['light'], width=3)

        paste_emoji_vcentered(img, s['icon'], pad_x + 24, y, card_h, emoji_size)
        draw = ImageDraw.Draw(img)

        f_label = font(800, 40)
        f_range = font(400, 22)
        draw_two_lines_vcentered(draw, s['label'], f_label, TEXT_DARK,
                                  s['range'], f_range, TEXT_LIGHT_GRAY,
                                  text_left, y, card_h, line_gap=12)

        f_amount = font(900, 44)
        f_detail = font(400, 22)
        right_edge = W - pad_x - 28
        draw_two_lines_right_vcentered(draw, s['amount'], f_amount, c['accent'],
                                        s['detail'], f_detail, TEXT_LIGHT_GRAY,
                                        right_edge, y, card_h, line_gap=10)

    # 하단 팁
    tip_y = card_bottom + 8
    tip_h = 52
    draw_rounded_rect(draw, (0, tip_y, W, tip_y + tip_h), 0, fill=c['light'])
    f_tip = font(700, 26)
    draw_text_centered_in_box(draw, tip_text, 0, tip_y, W, tip_h, f_tip, c['accent'])

    return img.convert('RGB')


# ============================================================
# 07. 주의사항
# ============================================================
def render_07_warnings(food_name, warnings, c):
    img, draw = create_base()
    create_header(img, draw, "주의사항", f"{food_name} 급여 시 주의", "WARNING", c)

    card_top = 158
    card_bottom = H - 20
    n = len(warnings)
    gap = 8
    card_h = (card_bottom - card_top - (n - 1) * gap) // n
    pad_x = 32
    emoji_size = 46
    text_left = pad_x + 24 + emoji_size + 18

    for i, w in enumerate(warnings):
        y = card_top + i * (card_h + gap)
        is_first = (i == 0)

        if is_first:
            draw_rounded_rect(draw, (pad_x, y, W - pad_x, y + card_h), 22,
                             fill=c['light'], outline=c['primary'], width=4)
        else:
            draw_rounded_rect(draw, (pad_x, y, W - pad_x, y + card_h), 22,
                             fill=WHITE, outline=BORDER_LIGHT, width=2)

        paste_emoji_vcentered(img, w['icon'], pad_x + 24, y, card_h, emoji_size)
        draw = ImageDraw.Draw(img)

        title_color = c['accent'] if is_first else TEXT_DARK
        f_title = font(800, 38)
        f_desc = font(400, 24)
        draw_two_lines_vcentered(draw, w['title'], f_title, title_color,
                                  w['desc'], f_desc, TEXT_MID_GRAY,
                                  text_left, y, card_h, line_gap=14)

        # 우측 ⚠️ 이모지 추가
        paste_emoji_vcentered(img, '⚠️', W - pad_x - 24 - 36, y, card_h, 36)
        draw = ImageDraw.Draw(img)

    return img.convert('RGB')


# ============================================================
# 08. 급여 방법
# ============================================================
def render_08_recipe(food_name, steps, tip_text, c):
    img, draw = create_base()
    create_header(img, draw, "급여 방법", f"{food_name} 급여 단계", "RECIPE", c)

    step_top = 166
    step_bottom = H - 100
    n = len(steps)
    gap = 14
    step_h = (step_bottom - step_top - (n - 1) * gap) // n
    pad_x = 36
    circle_r = 44
    emoji_size = 44

    for i, s in enumerate(steps):
        y = step_top + i * (step_h + gap)
        is_last = (i == n - 1)

        cx = pad_x + circle_r + 8
        cy = y + step_h // 2
        circle_bg = c['primary'] if is_last else c['light']
        num_color = c['on_primary'] if is_last else c['accent']
        draw.ellipse([cx - circle_r, cy - circle_r, cx + circle_r, cy + circle_r],
                     fill=circle_bg)
        f_step = font(900, 38)
        draw_text_centered_in_box(draw, str(s['step']),
                                   cx - circle_r, cy - circle_r,
                                   circle_r * 2, circle_r * 2, f_step, num_color)

        card_x = pad_x + circle_r * 2 + 26
        card_right = W - pad_x

        draw_rounded_rect(draw, (card_x, y, card_right, y + step_h), 22,
                         fill=WHITE, outline=c['light'], width=3)

        f_title = font(800, 38)
        f_desc = font(400, 24)
        draw_two_lines_vcentered(draw, s['title'], f_title, TEXT_DARK,
                                  s['desc'], f_desc, TEXT_GRAY,
                                  card_x + 24, y, step_h, line_gap=14)

        paste_emoji_vcentered(img, s['icon'], card_right - 24 - emoji_size, y, step_h, emoji_size)
        draw = ImageDraw.Draw(img)

    tip_h = 60
    tip_y = H - tip_h - 16
    draw_rounded_rect(draw, (36, tip_y, W - 36, tip_y + tip_h), 22, fill=c['light'])
    f_tip = font(700, 26)

    # 💡 + 팁 텍스트 함께 중앙 정렬
    tip_w = get_text_actual_width(draw, tip_text, f_tip)
    emoji_w = 36
    total_w = emoji_w + 10 + tip_w
    sx = (W - total_w) // 2
    paste_emoji_vcentered(img, '💡', sx, tip_y, tip_h, emoji_w)
    draw = ImageDraw.Draw(img)
    draw_text_vcentered(draw, tip_text, sx + emoji_w + 10, tip_y, tip_h, f_tip, c['accent'])

    return img.convert('RGB')


# ============================================================
# 테스트 데이터 & 메인
# ============================================================

APPLE_04 = [
    {'icon': '🔥', 'name': '칼로리', 'sub': '에너지원', 'val': '52', 'unit': 'kcal'},
    {'icon': '💪', 'name': '단백질', 'sub': '근육 유지', 'val': '1.1', 'unit': 'g'},
    {'icon': '⚡', 'name': '탄수화물', 'sub': '활동 에너지', 'val': '12', 'unit': 'g'},
    {'icon': '🌿', 'name': '식이섬유', 'sub': '장 건강', 'val': '2.4', 'unit': 'g'},
    {'icon': '🍊', 'name': '비타민C', 'sub': '면역력 강화', 'val': '4.6', 'unit': 'mg'},
]

APPLE_05_DO = ['깨끗이 씻어서 급여', '씨앗과 심 반드시 제거', '작게 잘라서 급여', '껍질째 OK (소화 약하면 제거)', '신선한 것만 급여']
APPLE_05_DONT = ['씨앗/심 급여 (독성 위험)', '과다 급여 (설사 유발)', '사과잼/주스 등 가공식품', '상한 사과 급여', '큰 조각 통째로 (질식 위험)']

APPLE_06 = [
    {'icon': '🐕', 'label': '소형견', 'range': '5kg 이하', 'amount': '15~20g', 'detail': '작은 조각 2~3개'},
    {'icon': '🦮', 'label': '중형견', 'range': '5~15kg', 'amount': '30~40g', 'detail': '약 1/4개'},
    {'icon': '🐕', 'label': '대형견', 'range': '15~30kg', 'amount': '50~70g', 'detail': '약 1/3개'},
    {'icon': '🦁', 'label': '초대형견', 'range': '30kg 이상', 'amount': '80~100g', 'detail': '약 1/2개'},
]

APPLE_07 = [
    {'icon': '🍎', 'title': '씨앗 제거 필수', 'desc': '아미그달린(시안화물) 포함'},
    {'icon': '🤢', 'title': '구토/설사 관찰', 'desc': '처음 급여 후 24시간 모니터링'},
    {'icon': '😿', 'title': '알러지 체크', 'desc': '가려움, 발진, 눈물 등 확인'},
    {'icon': '💩', 'title': '변 상태 확인', 'desc': '묽어지면 급여량 줄이기'},
    {'icon': '⚖️', 'title': '적정량 준수', 'desc': '하루 칼로리의 10% 이내'},
]

APPLE_08 = [
    {'step': 1, 'title': '깨끗이 씻기', 'desc': '흐르는 물에 30초 이상', 'icon': '🚿'},
    {'step': 2, 'title': '씨/심 제거', 'desc': '시안화물 성분 완전히 제거', 'icon': '🔪'},
    {'step': 3, 'title': '한 입 크기로', 'desc': '강아지 입에 맞게 자르기', 'icon': '🍽️'},
    {'step': 4, 'title': '소량부터 시작', 'desc': '알러지 확인 후 늘리기', 'icon': '👀'},
]


if __name__ == '__main__':
    out = OUTPUT_DIR / 'SAFE'
    out.mkdir(parents=True, exist_ok=True)

    c = SAFETY_COLORS['SAFE']
    food = '사과'

    print("=" * 50)
    print("SAFE/CAUTION 슬라이드 렌더러 v4 (김부장)")
    print("=" * 50)

    print("\n[SAFE] 사과 테스트...")
    render_04_nutrition(food, APPLE_04, c).save(f'{out}/Golden_Blog_SAFE_04_Nutrition.png'); print("  04 완료")
    render_05_dodont(food, APPLE_05_DO, APPLE_05_DONT, c).save(f'{out}/Golden_Blog_SAFE_05_DosDonts.png'); print("  05 완료")
    render_06_serving(food, APPLE_06, "간식은 하루 칼로리의 10% 이내 | 주 2~3회 권장", c).save(f'{out}/Golden_Blog_SAFE_06_Serving.png'); print("  06 완료")
    render_07_warnings(food, APPLE_07, c).save(f'{out}/Golden_Blog_SAFE_07_Warnings.png'); print("  07 완료")
    render_08_recipe(food, APPLE_08, "여름엔 냉장 보관 후 시원하게 주면 더 좋아해요!", c).save(f'{out}/Golden_Blog_SAFE_08_Recipe.png'); print("  08 완료")

    print(f"\n완료! 출력: {out}")
