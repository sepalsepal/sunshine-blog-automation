#!/usr/bin/env python3
"""
Golden Slide Generator - SAFE, DANGER, FORBIDDEN
Based on BLOG_SLIDE_DESIGN_RULE v2.1
"""

from PIL import Image, ImageDraw, ImageFont
import os

# ============================================================
# COLOR SCHEMES (per safety level)
# ============================================================
COLORS = {
    "SAFE": {
        "header_start": "#7ECEC1",
        "header_end": "#A8DED2",
        "card_bg": "#E8F6F3",
        "badge": "#4CAF50",
        "accent": "#4CAF50",
        "check_icon": "#4CAF50"
    },
    "DANGER": {
        "header_start": "#FF6B6B",
        "header_end": "#FF9B9B",
        "card_bg": "#FDE8E8",
        "badge": "#FF6B6B",
        "accent": "#E53935",
        "warning_icon": "#FF6B6B"
    },
    "FORBIDDEN": {
        "header_start": "#FF5252",
        "header_end": "#FF7B7B",
        "card_bg": "#FFEBEE",
        "badge": "#FF5252",
        "accent": "#D32F2F",
        "warning_icon": "#FF5252"
    }
}

# ============================================================
# SLIDE CONTENT DEFINITIONS
# ============================================================
SLIDE_CONTENT = {
    "SAFE": {
        "03_Nutrition": {
            "title": "{음식명} 영양성분",
            "subtitle": "100g 기준 | 강아지에게 안전한 영양 간식",
            "items": [
                ("칼로리", "에너지원", "52kcal"),
                ("단백질", "근육 유지", "1.1g"),
                ("탄수화물", "활동 에너지", "12g"),
                ("식이섬유", "장 건강", "2.4g"),
                ("비타민C", "면역력 강화", "4.6mg")
            ]
        },
        "04_Feeding": {
            "title": "강아지가 먹어도 안전해요",
            "subtitle": None,
            "sections": [
                {
                    "header": "이렇게 급여하세요",
                    "header_color": "#4CAF50",
                    "bg_color": "#E8F6E8",
                    "items": ["생으로 아삭하게", "익혀서 부드럽게", "작게 썰어서"],
                    "icon": "V",
                    "icon_color": "#4CAF50"
                },
                {
                    "header": "이것만은 피해주세요",
                    "header_color": "#EF5350",
                    "bg_color": "#FDE8E8",
                    "items": ["큰 조각 그대로", "양념/버터 추가", "과다 급여"],
                    "icon": "X",
                    "icon_color": "#EF5350"
                }
            ],
            "bottom_text": "11살 노령견 햇살이도 안전하게 먹고 있어요"
        },
        "05_Amount": {
            "title": "체중별 급여량 가이드",
            "subtitle": "하루 기준 | 간식으로 급여 시",
            "table": {
                "headers": ["구분", "체중", "급여량"],
                "rows": [
                    ("소형견", "5kg 이하", "20~30g"),
                    ("중형견", "5~15kg", "30~50g"),
                    ("대형견", "15~30kg", "50~80g"),
                    ("초대형견", "30kg 이상", "80~100g")
                ]
            }
        },
        "06_Caution": {
            "title": "주의사항",
            "subtitle": "안전한 급여를 위해 꼭 확인하세요",
            "items": [
                ("첫 급여", "소량으로 시작하여 반응 확인"),
                ("알레르기", "구토/설사 시 급여 중단"),
                ("급여량", "하루 섭취량의 10% 이내"),
                ("신선도", "상온 2시간 이상 방치 금지"),
                ("씨/껍질", "제거 후 급여 권장")
            ],
            "bottom_text": "주의: 첫 급여 시 절반량으로 시작하세요"
        },
        "07_Cooking": {
            "title": "안전한 조리 방법",
            "subtitle": "STEP by STEP",
            "steps": [
                ("1", "깨끗이 씻어주세요"),
                ("2", "씨와 껍질을 제거하세요"),
                ("3", "한입 크기로 잘라주세요"),
                ("4", "살짝 익히거나 생으로 급여"),
                ("5", "급여량을 지켜주세요")
            ],
            "tip": "TIP: 냉동 보관 시 2주 이내 사용"
        }
    },
    "DANGER": {
        "03_Nutrition": {
            "title": "{음식명} 성분 분석",
            "subtitle": "100g 기준 | 위험 성분 포함 주의",
            "items": [
                ("칼로리", "에너지원", "67kcal"),
                ("당분", "과당 함유", "16g"),
                ("독성 성분", "주의 필요", "미량"),
                ("수분", "높은 수분", "81%"),
                ("산도", "위장 자극", "pH 3.5")
            ]
        },
        "04_Risk": {
            "title": "급여를 권장하지 않아요",
            "subtitle": None,
            "sections": [
                {
                    "header": "위험 요소",
                    "header_color": "#FF6B6B",
                    "bg_color": "#FDE8E8",
                    "items": ["신장 손상 유발 가능", "소화기 장애 발생", "급성 중독 위험"],
                    "icon": "!",
                    "icon_color": "#FF6B6B"
                },
                {
                    "header": "만약 섭취했다면",
                    "header_color": "#FF6B6B",
                    "bg_color": "#FDE8E8",
                    "items": ["즉시 수의사에게 연락", "구토 유도하지 말 것", "섭취량과 시간 기록"],
                    "icon_type": "number",
                    "icon_color": "#FF6B6B"
                }
            ],
            "bottom_text": "응급 상황 발생 시 즉시 동물병원으로"
        },
        "05_Symptoms": {
            "title": "섭취 시 나타나는 증상",
            "subtitle": "아래 증상 발견 시 즉시 병원 방문",
            "items": [
                ("구토", "섭취 후 1~2시간 이내"),
                ("설사", "소화 장애로 인한 증상"),
                ("기력 저하", "무기력함, 움직임 감소"),
                ("식욕 부진", "음식 거부 행동"),
                ("과호흡", "호흡이 빨라짐")
            ]
        },
        "06_Alternative": {
            "title": "안전한 대체 간식",
            "subtitle": "이 음식 대신 이것을 추천해요",
            "items": [
                ("당근", "비타민A 풍부, 저칼로리"),
                ("호박", "소화가 잘 되는 영양 간식"),
                ("사과", "씨 제거 후 급여 가능"),
                ("블루베리", "항산화 성분 풍부"),
                ("오이", "수분 보충에 좋음")
            ]
        },
        "07_Warning": {
            "title": "최종 경고",
            "subtitle": "반드시 기억하세요",
            "items": [
                ("절대 급여 금지", "건강에 심각한 위험"),
                ("실수로 섭취 시", "즉시 동물병원 방문"),
                ("증상 관찰", "최소 24시간 모니터링"),
                ("수의사 상담", "섭취량 관계없이 필수")
            ],
            "emergency": {
                "text": "응급 연락처: 동물병원 또는 119",
                "subtext": "섭취 후 2시간 이내 처치가 중요합니다"
            }
        }
    },
    "FORBIDDEN": {
        "03_Toxicity": {
            "title": "{음식명} 독성 성분",
            "subtitle": "강아지에게 치명적인 성분 경고",
            "items": [
                ("테오브로민", "심장/신경 독성", "치명적"),
                ("카페인", "중추신경 자극", "위험"),
                ("지방", "췌장염 유발", "고위험"),
                ("설탕", "당뇨/비만 위험", "주의"),
                ("치사량", "체중 kg당", "20mg")
            ]
        },
        "04_Symptoms": {
            "title": "절대 급여 금지",
            "subtitle": None,
            "sections": [
                {
                    "header": "독성 증상",
                    "header_color": "#FF5252",
                    "bg_color": "#FFEBEE",
                    "items": ["심장 박동 이상", "경련/발작", "호흡 곤란"],
                    "icon": "!",
                    "icon_color": "#FF5252"
                },
                {
                    "header": "섭취 시 즉시 조치",
                    "header_color": "#FF5252",
                    "bg_color": "#FFEBEE",
                    "items": ["즉시 수의사에게 연락", "구토 유도하지 말 것", "섭취량과 시간 기록"],
                    "icon_type": "number",
                    "icon_color": "#FF5252"
                }
            ],
            "bottom_text": "응급 상황 발생 시 즉시 동물병원으로"
        },
        "05_Emergency": {
            "title": "응급 대처 가이드",
            "subtitle": "시간별 행동 지침",
            "table": {
                "headers": ["시간", "상황", "행동"],
                "rows": [
                    ("즉시", "섭취 직후", "병원 연락"),
                    ("30분", "증상 발현", "이동 준비"),
                    ("1시간", "응급 상황", "즉시 이송"),
                    ("2시간+", "위험 구간", "집중 치료")
                ]
            }
        },
        "06_Alternative": {
            "title": "안전한 대체 간식",
            "subtitle": "이 음식 대신 이것을 추천해요",
            "items": [
                ("당근", "비타민A 풍부, 저칼로리"),
                ("호박", "소화가 잘 되는 영양 간식"),
                ("사과", "씨 제거 후 급여 가능"),
                ("블루베리", "항산화 성분 풍부"),
                ("고구마", "식이섬유 풍부")
            ]
        },
        "07_Warning": {
            "title": "최종 경고",
            "subtitle": "이 음식은 독입니다",
            "items": [
                ("절대 급여 금지", "소량도 치명적"),
                ("실수로 섭취 시", "즉시 응급실 이송"),
                ("2차 피해 주의", "포장지/쓰레기통 관리"),
                ("가족 교육", "모든 가족에게 알림")
            ],
            "emergency": {
                "text": "응급 연락처: 동물병원 또는 119",
                "subtext": "이 음식은 강아지에게 치명적입니다"
            }
        }
    }
}

# ============================================================
# FONT PATHS
# ============================================================
FONT_PATHS = {
    "bold": "/Users/al02399300/Library/Fonts/NanumGothic-ExtraBold.ttf",
    "regular": "/Users/al02399300/Library/Fonts/NanumGothic-Regular.ttf"
}

# ============================================================
# HELPER FUNCTIONS
# ============================================================

def hex_to_rgb(hex_color):
    """Convert hex color to RGB tuple"""
    hex_color = hex_color.lstrip('#')
    return tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))

def create_gradient(draw, width, height, start_color, end_color, direction="horizontal"):
    """Create a gradient rectangle"""
    start_rgb = hex_to_rgb(start_color)
    end_rgb = hex_to_rgb(end_color)

    if direction == "horizontal":
        for x in range(width):
            ratio = x / width
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
            draw.line([(x, 0), (x, height)], fill=(r, g, b))
    else:
        for y in range(height):
            ratio = y / height
            r = int(start_rgb[0] + (end_rgb[0] - start_rgb[0]) * ratio)
            g = int(start_rgb[1] + (end_rgb[1] - start_rgb[1]) * ratio)
            b = int(start_rgb[2] + (end_rgb[2] - start_rgb[2]) * ratio)
            draw.line([(0, y), (width, y)], fill=(r, g, b))

def draw_rounded_rect(draw, xy, radius, fill):
    """Draw a rounded rectangle"""
    x1, y1, x2, y2 = xy
    draw.rectangle([x1 + radius, y1, x2 - radius, y2], fill=fill)
    draw.rectangle([x1, y1 + radius, x2, y2 - radius], fill=fill)
    draw.ellipse([x1, y1, x1 + 2*radius, y1 + 2*radius], fill=fill)
    draw.ellipse([x2 - 2*radius, y1, x2, y1 + 2*radius], fill=fill)
    draw.ellipse([x1, y2 - 2*radius, x1 + 2*radius, y2], fill=fill)
    draw.ellipse([x2 - 2*radius, y2 - 2*radius, x2, y2], fill=fill)

def draw_circle(draw, center, radius, fill):
    """Draw a circle"""
    x, y = center
    draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=fill)

def get_text_width(draw, text, font):
    """Get text width"""
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0]

# ============================================================
# SLIDE GENERATORS
# ============================================================

def generate_03_nutrition(safety, content, colors, output_path):
    """Generate 03_Nutrition or 03_Toxicity slide"""
    img = Image.new('RGB', (1080, 1080), hex_to_rgb("#FFF8F0"))
    draw = ImageDraw.Draw(img)

    # Header gradient
    header_img = Image.new('RGB', (1080, 120), (255, 255, 255))
    header_draw = ImageDraw.Draw(header_img)
    create_gradient(header_draw, 1080, 120, colors["header_start"], colors["header_end"])
    img.paste(header_img, (0, 0))
    draw = ImageDraw.Draw(img)

    # Badge
    badge_x, badge_y = 980, 24
    badge_w, badge_h = 80, 36
    draw_rounded_rect(draw, (badge_x - badge_w, badge_y, badge_x, badge_y + badge_h), 18, hex_to_rgb(colors["badge"]))

    font_badge = ImageFont.truetype(FONT_PATHS["bold"], 14)
    badge_text = safety
    text_w = get_text_width(draw, badge_text, font_badge)
    draw.text((badge_x - badge_w/2 - text_w/2, badge_y + 10), badge_text, font=font_badge, fill=(255, 255, 255))

    # Title
    font_title = ImageFont.truetype(FONT_PATHS["bold"], 48)
    title = content["title"]
    title_w = get_text_width(draw, title, font_title)
    draw.text(((1080 - title_w) / 2, 30), title, font=font_title, fill=(255, 255, 255))

    # Subtitle
    font_subtitle = ImageFont.truetype(FONT_PATHS["regular"], 20)
    subtitle = content["subtitle"]
    subtitle_w = get_text_width(draw, subtitle, font_subtitle)
    draw.text(((1080 - subtitle_w) / 2, 85), subtitle, font=font_subtitle, fill=(255, 255, 255, 200))

    # Cards
    card_y = 152
    card_height = 90
    card_margin = 40
    card_gap = 16
    card_width = 1080 - 2 * card_margin

    icon_colors = ["#FFA726", "#66BB6A", "#EF5350", "#42A5F5", "#AB47BC"]

    for i, item in enumerate(content["items"]):
        name, desc, value = item
        y = card_y + i * (card_height + card_gap)

        # Card background
        draw_rounded_rect(draw, (card_margin, y, 1080 - card_margin, y + card_height), 12, hex_to_rgb(colors["card_bg"]))

        # Number circle
        circle_x = card_margin + 50
        circle_y = y + card_height / 2
        draw_circle(draw, (circle_x, circle_y), 20, hex_to_rgb(icon_colors[i % 5]))

        font_num = ImageFont.truetype(FONT_PATHS["bold"], 18)
        num_text = str(i + 1)
        num_w = get_text_width(draw, num_text, font_num)
        draw.text((circle_x - num_w/2, circle_y - 12), num_text, font=font_num, fill=(255, 255, 255))

        # Text
        font_name = ImageFont.truetype(FONT_PATHS["bold"], 28)
        font_desc = ImageFont.truetype(FONT_PATHS["regular"], 18)
        font_value = ImageFont.truetype(FONT_PATHS["bold"], 36)

        draw.text((circle_x + 40, y + 18), name, font=font_name, fill=hex_to_rgb("#333333"))
        draw.text((circle_x + 40, y + 52), desc, font=font_desc, fill=hex_to_rgb("#888888"))

        # Value (right side)
        value_w = get_text_width(draw, value, font_value)
        draw.text((1080 - card_margin - 24 - value_w, y + 25), value, font=font_value, fill=hex_to_rgb(colors["accent"]))

    img.save(output_path)
    print(f"Created: {output_path}")

def generate_04_feeding(safety, content, colors, output_path):
    """Generate 04_Feeding, 04_Risk, or 04_Symptoms slide"""
    img = Image.new('RGB', (1080, 1080), hex_to_rgb("#FFF8F0"))
    draw = ImageDraw.Draw(img)

    # Header gradient
    header_img = Image.new('RGB', (1080, 120), (255, 255, 255))
    header_draw = ImageDraw.Draw(header_img)
    create_gradient(header_draw, 1080, 120, colors["header_start"], colors["header_end"])
    img.paste(header_img, (0, 0))
    draw = ImageDraw.Draw(img)

    # Badge
    badge_x, badge_y = 980, 24
    badge_w, badge_h = 80, 36
    draw_rounded_rect(draw, (badge_x - badge_w, badge_y, badge_x, badge_y + badge_h), 18, hex_to_rgb(colors["badge"]))

    font_badge = ImageFont.truetype(FONT_PATHS["bold"], 14)
    badge_text = safety
    text_w = get_text_width(draw, badge_text, font_badge)
    draw.text((badge_x - badge_w/2 - text_w/2, badge_y + 10), badge_text, font=font_badge, fill=(255, 255, 255))

    # Title
    font_title = ImageFont.truetype(FONT_PATHS["bold"], 48)
    title = content["title"]
    title_w = get_text_width(draw, title, font_title)
    draw.text(((1080 - title_w) / 2, 35), title, font=font_title, fill=(255, 255, 255))

    # Sections
    section_y = 160
    section_margin = 40
    section_gap = 32

    for i, section in enumerate(content["sections"]):
        # Section header
        font_header = ImageFont.truetype(FONT_PATHS["bold"], 24)
        draw.text((section_margin, section_y), section["header"], font=font_header, fill=hex_to_rgb(section["header_color"]))

        section_y += 40

        # Section card
        card_height = len(section["items"]) * 55 + 20
        draw_rounded_rect(draw, (section_margin, section_y, 1080 - section_margin, section_y + card_height), 12, hex_to_rgb(section["bg_color"]))

        # Items
        item_y = section_y + 20
        for j, item_text in enumerate(section["items"]):
            # Icon
            icon_x = section_margin + 45
            icon_y = item_y + 15

            if section.get("icon_type") == "number":
                draw_circle(draw, (icon_x, icon_y), 16, hex_to_rgb(section["icon_color"]))
                font_icon = ImageFont.truetype(FONT_PATHS["bold"], 14)
                draw.text((icon_x - 4, icon_y - 10), str(j + 1), font=font_icon, fill=(255, 255, 255))
            else:
                draw_circle(draw, (icon_x, icon_y), 16, hex_to_rgb(section["icon_color"]))
                font_icon = ImageFont.truetype(FONT_PATHS["bold"], 16)
                icon_text = section.get("icon", "!")
                draw.text((icon_x - 5, icon_y - 10), icon_text, font=font_icon, fill=(255, 255, 255))

            # Text
            font_item = ImageFont.truetype(FONT_PATHS["regular"], 22)
            draw.text((icon_x + 35, item_y + 3), item_text, font=font_item, fill=hex_to_rgb("#333333"))

            item_y += 55

        section_y += card_height + section_gap

    # Bottom text
    if content.get("bottom_text"):
        font_bottom = ImageFont.truetype(FONT_PATHS["regular"], 20)
        bottom_w = get_text_width(draw, content["bottom_text"], font_bottom)

        # Background bar
        bar_height = 50
        bar_y = 1080 - bar_height - 20

        if safety == "SAFE":
            bar_color = "#E3F2FD"
            text_color = "#1976D2"
        else:
            bar_color = "#FDE8E8"
            text_color = "#E53935"

        draw_rounded_rect(draw, (section_margin, bar_y, 1080 - section_margin, bar_y + bar_height), 8, hex_to_rgb(bar_color))
        draw.text(((1080 - bottom_w) / 2, bar_y + 13), content["bottom_text"], font=font_bottom, fill=hex_to_rgb(text_color))

    img.save(output_path)
    print(f"Created: {output_path}")

def generate_05_amount(safety, content, colors, output_path):
    """Generate 05_Amount, 05_Symptoms, or 05_Emergency slide"""
    img = Image.new('RGB', (1080, 1080), hex_to_rgb("#FFF8F0"))
    draw = ImageDraw.Draw(img)

    # Header gradient
    header_img = Image.new('RGB', (1080, 120), (255, 255, 255))
    header_draw = ImageDraw.Draw(header_img)
    create_gradient(header_draw, 1080, 120, colors["header_start"], colors["header_end"])
    img.paste(header_img, (0, 0))
    draw = ImageDraw.Draw(img)

    # Badge
    badge_x, badge_y = 980, 24
    badge_w, badge_h = 80, 36
    draw_rounded_rect(draw, (badge_x - badge_w, badge_y, badge_x, badge_y + badge_h), 18, hex_to_rgb(colors["badge"]))

    font_badge = ImageFont.truetype(FONT_PATHS["bold"], 14)
    badge_text = safety
    text_w = get_text_width(draw, badge_text, font_badge)
    draw.text((badge_x - badge_w/2 - text_w/2, badge_y + 10), badge_text, font=font_badge, fill=(255, 255, 255))

    # Title
    font_title = ImageFont.truetype(FONT_PATHS["bold"], 48)
    title = content["title"]
    title_w = get_text_width(draw, title, font_title)
    draw.text(((1080 - title_w) / 2, 30), title, font=font_title, fill=(255, 255, 255))

    # Subtitle
    font_subtitle = ImageFont.truetype(FONT_PATHS["regular"], 20)
    subtitle = content["subtitle"]
    subtitle_w = get_text_width(draw, subtitle, font_subtitle)
    draw.text(((1080 - subtitle_w) / 2, 85), subtitle, font=font_subtitle, fill=(255, 255, 255, 200))

    if "table" in content:
        # Table layout
        table = content["table"]
        table_margin = 40
        table_y = 170
        col_width = (1080 - 2 * table_margin) // 3
        row_height = 100

        # Table header
        header_height = 60
        draw_rounded_rect(draw, (table_margin, table_y, 1080 - table_margin, table_y + header_height), 12, hex_to_rgb(colors["card_bg"]))

        font_header = ImageFont.truetype(FONT_PATHS["bold"], 22)
        for i, header in enumerate(table["headers"]):
            x = table_margin + col_width * i + col_width / 2
            hw = get_text_width(draw, header, font_header)
            draw.text((x - hw/2, table_y + 18), header, font=font_header, fill=hex_to_rgb(colors["accent"]))

        # Table rows
        row_y = table_y + header_height + 16
        font_col1 = ImageFont.truetype(FONT_PATHS["regular"], 22)
        font_col2 = ImageFont.truetype(FONT_PATHS["regular"], 22)
        font_col3 = ImageFont.truetype(FONT_PATHS["bold"], 28)

        for row_data in table["rows"]:
            # Row background
            draw_rounded_rect(draw, (table_margin, row_y, 1080 - table_margin, row_y + row_height - 8), 12, hex_to_rgb(colors["card_bg"]))

            # Column 1
            x1 = table_margin + col_width / 2
            w1 = get_text_width(draw, row_data[0], font_col1)
            draw.text((x1 - w1/2, row_y + 35), row_data[0], font=font_col1, fill=hex_to_rgb("#333333"))

            # Column 2
            x2 = table_margin + col_width + col_width / 2
            w2 = get_text_width(draw, row_data[1], font_col2)
            draw.text((x2 - w2/2, row_y + 35), row_data[1], font=font_col2, fill=hex_to_rgb("#666666"))

            # Column 3
            x3 = table_margin + col_width * 2 + col_width / 2
            w3 = get_text_width(draw, row_data[2], font_col3)
            draw.text((x3 - w3/2, row_y + 30), row_data[2], font=font_col3, fill=hex_to_rgb(colors["accent"]))

            row_y += row_height

    elif "items" in content:
        # Card layout for symptoms
        card_y = 170
        card_height = 90
        card_margin = 40
        card_gap = 16

        icon_colors = ["#FFA726", "#66BB6A", "#EF5350", "#42A5F5", "#AB47BC"]

        for i, item in enumerate(content["items"]):
            name, desc = item
            y = card_y + i * (card_height + card_gap)

            draw_rounded_rect(draw, (card_margin, y, 1080 - card_margin, y + card_height), 12, hex_to_rgb(colors["card_bg"]))

            circle_x = card_margin + 50
            circle_y = y + card_height / 2
            draw_circle(draw, (circle_x, circle_y), 20, hex_to_rgb(icon_colors[i % 5]))

            font_num = ImageFont.truetype(FONT_PATHS["bold"], 18)
            num_text = str(i + 1)
            num_w = get_text_width(draw, num_text, font_num)
            draw.text((circle_x - num_w/2, circle_y - 12), num_text, font=font_num, fill=(255, 255, 255))

            font_name = ImageFont.truetype(FONT_PATHS["bold"], 28)
            font_desc = ImageFont.truetype(FONT_PATHS["regular"], 18)

            draw.text((circle_x + 40, y + 18), name, font=font_name, fill=hex_to_rgb("#333333"))
            draw.text((circle_x + 40, y + 52), desc, font=font_desc, fill=hex_to_rgb("#888888"))

    img.save(output_path)
    print(f"Created: {output_path}")

def generate_06_caution(safety, content, colors, output_path):
    """Generate 06_Caution or 06_Alternative slide"""
    img = Image.new('RGB', (1080, 1080), hex_to_rgb("#FFF8F0"))
    draw = ImageDraw.Draw(img)

    # Header gradient
    header_img = Image.new('RGB', (1080, 120), (255, 255, 255))
    header_draw = ImageDraw.Draw(header_img)
    create_gradient(header_draw, 1080, 120, colors["header_start"], colors["header_end"])
    img.paste(header_img, (0, 0))
    draw = ImageDraw.Draw(img)

    # Badge
    badge_x, badge_y = 980, 24
    badge_w, badge_h = 80, 36
    draw_rounded_rect(draw, (badge_x - badge_w, badge_y, badge_x, badge_y + badge_h), 18, hex_to_rgb(colors["badge"]))

    font_badge = ImageFont.truetype(FONT_PATHS["bold"], 14)
    badge_text = safety
    text_w = get_text_width(draw, badge_text, font_badge)
    draw.text((badge_x - badge_w/2 - text_w/2, badge_y + 10), badge_text, font=font_badge, fill=(255, 255, 255))

    # Title
    font_title = ImageFont.truetype(FONT_PATHS["bold"], 48)
    title = content["title"]
    title_w = get_text_width(draw, title, font_title)
    draw.text(((1080 - title_w) / 2, 30), title, font=font_title, fill=(255, 255, 255))

    # Subtitle
    font_subtitle = ImageFont.truetype(FONT_PATHS["regular"], 20)
    subtitle = content["subtitle"]
    subtitle_w = get_text_width(draw, subtitle, font_subtitle)
    draw.text(((1080 - subtitle_w) / 2, 85), subtitle, font=font_subtitle, fill=(255, 255, 255, 200))

    # Cards
    card_y = 160
    card_height = 90
    card_margin = 40
    card_gap = 16

    icon_colors = ["#FFA726", "#66BB6A", "#EF5350", "#42A5F5", "#AB47BC"]

    for i, item in enumerate(content["items"]):
        name, desc = item
        y = card_y + i * (card_height + card_gap)

        draw_rounded_rect(draw, (card_margin, y, 1080 - card_margin, y + card_height), 12, hex_to_rgb(colors["card_bg"]))

        circle_x = card_margin + 50
        circle_y = y + card_height / 2
        draw_circle(draw, (circle_x, circle_y), 20, hex_to_rgb(icon_colors[i % 5]))

        font_num = ImageFont.truetype(FONT_PATHS["bold"], 18)
        num_text = str(i + 1)
        num_w = get_text_width(draw, num_text, font_num)
        draw.text((circle_x - num_w/2, circle_y - 12), num_text, font=font_num, fill=(255, 255, 255))

        font_name = ImageFont.truetype(FONT_PATHS["bold"], 28)
        font_desc = ImageFont.truetype(FONT_PATHS["regular"], 18)

        draw.text((circle_x + 40, y + 18), name, font=font_name, fill=hex_to_rgb("#333333"))
        draw.text((circle_x + 40, y + 52), desc, font=font_desc, fill=hex_to_rgb("#888888"))

    # Bottom text
    if content.get("bottom_text"):
        font_bottom = ImageFont.truetype(FONT_PATHS["bold"], 20)
        bar_height = 50
        bar_y = 1080 - bar_height - 20

        draw_rounded_rect(draw, (card_margin, bar_y, 1080 - card_margin, bar_y + bar_height), 8, hex_to_rgb(colors["card_bg"]))
        bottom_w = get_text_width(draw, content["bottom_text"], font_bottom)
        draw.text(((1080 - bottom_w) / 2, bar_y + 13), content["bottom_text"], font=font_bottom, fill=hex_to_rgb(colors["accent"]))

    img.save(output_path)
    print(f"Created: {output_path}")

def generate_07_cooking(safety, content, colors, output_path):
    """Generate 07_Cooking, 07_Alternative, or 07_Warning slide"""
    img = Image.new('RGB', (1080, 1080), hex_to_rgb("#FFF8F0"))
    draw = ImageDraw.Draw(img)

    # Header gradient
    header_img = Image.new('RGB', (1080, 120), (255, 255, 255))
    header_draw = ImageDraw.Draw(header_img)
    create_gradient(header_draw, 1080, 120, colors["header_start"], colors["header_end"])
    img.paste(header_img, (0, 0))
    draw = ImageDraw.Draw(img)

    # Badge
    badge_x, badge_y = 980, 24
    badge_w, badge_h = 80, 36
    draw_rounded_rect(draw, (badge_x - badge_w, badge_y, badge_x, badge_y + badge_h), 18, hex_to_rgb(colors["badge"]))

    font_badge = ImageFont.truetype(FONT_PATHS["bold"], 14)
    badge_text = safety
    text_w = get_text_width(draw, badge_text, font_badge)
    draw.text((badge_x - badge_w/2 - text_w/2, badge_y + 10), badge_text, font=font_badge, fill=(255, 255, 255))

    # Title
    font_title = ImageFont.truetype(FONT_PATHS["bold"], 48)
    title = content["title"]
    title_w = get_text_width(draw, title, font_title)
    draw.text(((1080 - title_w) / 2, 30), title, font=font_title, fill=(255, 255, 255))

    # Subtitle
    if content.get("subtitle"):
        font_subtitle = ImageFont.truetype(FONT_PATHS["regular"], 20)
        subtitle = content["subtitle"]
        subtitle_w = get_text_width(draw, subtitle, font_subtitle)
        draw.text(((1080 - subtitle_w) / 2, 85), subtitle, font=font_subtitle, fill=(255, 255, 255, 200))

    card_margin = 40

    if "steps" in content:
        # Steps layout (SAFE/CAUTION cooking)
        step_y = 160
        step_height = 75
        step_gap = 12

        step_colors = ["#FFA726", "#66BB6A", "#EF5350", "#42A5F5", "#AB47BC"]

        for i, step in enumerate(content["steps"]):
            num, text = step
            y = step_y + i * (step_height + step_gap)

            draw_rounded_rect(draw, (card_margin, y, 1080 - card_margin, y + step_height), 12, hex_to_rgb(colors["card_bg"]))

            # STEP badge
            badge_w_step = 80
            badge_h_step = 32
            draw_rounded_rect(draw, (card_margin + 20, y + (step_height - badge_h_step) / 2, card_margin + 20 + badge_w_step, y + (step_height + badge_h_step) / 2), 16, hex_to_rgb(step_colors[i % 5]))

            font_step = ImageFont.truetype(FONT_PATHS["bold"], 14)
            step_text = f"STEP {num}"
            step_w = get_text_width(draw, step_text, font_step)
            draw.text((card_margin + 20 + (badge_w_step - step_w) / 2, y + (step_height - 16) / 2), step_text, font=font_step, fill=(255, 255, 255))

            # Step text
            font_text = ImageFont.truetype(FONT_PATHS["regular"], 22)
            draw.text((card_margin + 120, y + (step_height - 24) / 2), text, font=font_text, fill=hex_to_rgb("#333333"))

        # TIP
        if content.get("tip"):
            tip_y = step_y + 5 * (step_height + step_gap) + 20
            tip_height = 50

            draw_rounded_rect(draw, (card_margin, tip_y, 1080 - card_margin, tip_y + tip_height), 8, hex_to_rgb("#FFF8E1"))

            # TIP icon
            tip_icon_x = card_margin + 35
            tip_icon_y = tip_y + tip_height / 2
            draw_circle(draw, (tip_icon_x, tip_icon_y), 14, hex_to_rgb("#FFD93D"))
            font_icon = ImageFont.truetype(FONT_PATHS["bold"], 16)
            draw.text((tip_icon_x - 3, tip_icon_y - 10), "!", font=font_icon, fill=(255, 255, 255))

            font_tip = ImageFont.truetype(FONT_PATHS["regular"], 18)
            draw.text((tip_icon_x + 25, tip_y + 14), content["tip"], font=font_tip, fill=hex_to_rgb("#333333"))

    elif "items" in content:
        # Warning layout (DANGER/FORBIDDEN)
        card_y = 160
        card_height = 90
        card_gap = 16

        icon_colors = ["#EF5350", "#EF5350", "#EF5350", "#EF5350"]

        for i, item in enumerate(content["items"]):
            name, desc = item
            y = card_y + i * (card_height + card_gap)

            draw_rounded_rect(draw, (card_margin, y, 1080 - card_margin, y + card_height), 12, hex_to_rgb(colors["card_bg"]))

            circle_x = card_margin + 50
            circle_y = y + card_height / 2
            draw_circle(draw, (circle_x, circle_y), 20, hex_to_rgb(icon_colors[i % 4]))

            font_num = ImageFont.truetype(FONT_PATHS["bold"], 18)
            draw.text((circle_x - 4, circle_y - 12), "!", font=font_num, fill=(255, 255, 255))

            font_name = ImageFont.truetype(FONT_PATHS["bold"], 28)
            font_desc = ImageFont.truetype(FONT_PATHS["regular"], 18)

            draw.text((circle_x + 40, y + 18), name, font=font_name, fill=hex_to_rgb("#333333"))
            draw.text((circle_x + 40, y + 52), desc, font=font_desc, fill=hex_to_rgb("#888888"))

        # Emergency box
        if content.get("emergency"):
            em = content["emergency"]
            em_y = card_y + 4 * (card_height + card_gap) + 20
            em_height = 90

            draw_rounded_rect(draw, (card_margin, em_y, 1080 - card_margin, em_y + em_height), 12, hex_to_rgb("#FDE8E8"))

            font_em = ImageFont.truetype(FONT_PATHS["bold"], 24)
            font_sub = ImageFont.truetype(FONT_PATHS["regular"], 16)

            em_w = get_text_width(draw, em["text"], font_em)
            sub_w = get_text_width(draw, em["subtext"], font_sub)

            draw.text(((1080 - em_w) / 2, em_y + 20), em["text"], font=font_em, fill=hex_to_rgb("#E53935"))
            draw.text(((1080 - sub_w) / 2, em_y + 55), em["subtext"], font=font_sub, fill=hex_to_rgb("#666666"))

    img.save(output_path)
    print(f"Created: {output_path}")

# ============================================================
# MAIN
# ============================================================

def main():
    base_path = "/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/00_rules/02_Image_rules/Blog_04-07"

    # Generate for each safety level
    for safety in ["SAFE", "DANGER", "FORBIDDEN"]:
        colors = COLORS[safety]
        content_dict = SLIDE_CONTENT[safety]
        output_folder = os.path.join(base_path, safety)

        print(f"\n=== Generating {safety} slides ===")

        # 03 - Nutrition/Toxicity
        if safety == "FORBIDDEN":
            slide_name = "03_Toxicity"
        else:
            slide_name = "03_Nutrition"
        output_path = os.path.join(output_folder, f"Golden_Blog_{safety}_{slide_name}.png")
        generate_03_nutrition(safety, content_dict[slide_name], colors, output_path)

        # 04 - Feeding/Risk/Symptoms
        if safety == "SAFE":
            slide_name = "04_Feeding"
        elif safety == "DANGER":
            slide_name = "04_Risk"
        else:
            slide_name = "04_Symptoms"
        output_path = os.path.join(output_folder, f"Golden_Blog_{safety}_{slide_name}.png")
        generate_04_feeding(safety, content_dict[slide_name], colors, output_path)

        # 05 - Amount/Symptoms/Emergency
        if safety == "SAFE":
            slide_name = "05_Amount"
        elif safety == "DANGER":
            slide_name = "05_Symptoms"
        else:
            slide_name = "05_Emergency"
        output_path = os.path.join(output_folder, f"Golden_Blog_{safety}_{slide_name}.png")
        generate_05_amount(safety, content_dict[slide_name], colors, output_path)

        # 06 - Caution/Alternative
        if safety == "SAFE":
            slide_name = "06_Caution"
        else:
            slide_name = "06_Alternative"
        output_path = os.path.join(output_folder, f"Golden_Blog_{safety}_{slide_name}.png")
        generate_06_caution(safety, content_dict[slide_name], colors, output_path)

        # 07 - Cooking/Alternative/Warning
        if safety == "SAFE":
            slide_name = "07_Cooking"
        elif safety == "DANGER":
            slide_name = "07_Warning"
        else:
            slide_name = "07_Warning"
        output_path = os.path.join(output_folder, f"Golden_Blog_{safety}_{slide_name}.png")
        generate_07_cooking(safety, content_dict[slide_name], colors, output_path)

    print("\n=== All slides generated ===")

if __name__ == "__main__":
    main()
