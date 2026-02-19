#!/usr/bin/env python3
"""
표지 텍스트 오버레이 - 최종

규칙:
1. 제목과 부제 겹침 금지
2. 텍스트와 개 얼굴/음식 겹침 금지
"""

from PIL import Image, ImageDraw, ImageFont
import sys

ARIAL_BLACK = "/Library/Fonts/Arial Black.ttf"
KOREAN_FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

# 고정 스펙
# 규칙: 제목-부제 겹침 금지, 눈 가림 금지 (머리 끝 닿음 허용)
TITLE_SIZE = 170
SUBTITLE_SIZE = 65
TITLE_Y = 150
GAP = 80  # 제목-부제 간격 (겹침 방지)

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def add_text_with_outline(draw, pos, text, font, fill, outline_color, outline_width):
    x, y = pos
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text(pos, text, font=font, fill=fill)

def apply_cover_text(input_path, output_path, title):
    img = Image.open(input_path).convert("RGBA")
    width, height = img.size

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 제목
    font_title = get_font(ARIAL_BLACK, TITLE_SIZE)
    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    title_h = title_bbox[3] - title_bbox[1]
    title_x = (width - title_w) // 2

    add_text_with_outline(draw, (title_x, TITLE_Y), title, font_title,
                          (255, 255, 255, 255), (0, 0, 0, 180), 4)

    # 부제
    subtitle = "11살 노령견 기준"
    font_sub = get_font(KOREAN_FONT, SUBTITLE_SIZE)
    sub_bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
    sub_w = sub_bbox[2] - sub_bbox[0]
    sub_h = sub_bbox[3] - sub_bbox[1]
    sub_x = (width - sub_w) // 2
    sub_y = TITLE_Y + title_h + GAP

    add_text_with_outline(draw, (sub_x, sub_y), subtitle, font_sub,
                          (255, 255, 255, 255), (0, 0, 0, 200), 3)

    result = Image.alpha_composite(img, overlay)
    result.convert("RGB").save(output_path, quality=95)

    print(f"✅ {output_path}")

if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python cover_text_final.py <input> <output> <title>")
        sys.exit(1)

    apply_cover_text(sys.argv[1], sys.argv[2], sys.argv[3])
