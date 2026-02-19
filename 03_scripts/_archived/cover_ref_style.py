#!/usr/bin/env python3
"""
PD 레퍼런스 스타일 기반 베리에이션
- 제목 + 부제 (겹침 없이 분리)
"""

from PIL import Image, ImageDraw, ImageFont
import sys

ARIAL_BLACK = "/Library/Fonts/Arial Black.ttf"
KOREAN_FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def add_text_with_outline(draw, pos, text, font, fill, outline_color, outline_width=3):
    x, y = pos
    for dx in range(-outline_width, outline_width + 1):
        for dy in range(-outline_width, outline_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=outline_color)
    draw.text(pos, text, font=font, fill=fill)

def generate(input_path, output_path, title, title_size, subtitle_size, title_y, gap):
    img = Image.open(input_path).convert("RGBA")
    width, height = img.size

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 제목
    font_title = get_font(ARIAL_BLACK, title_size)
    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_w = title_bbox[2] - title_bbox[0]
    title_h = title_bbox[3] - title_bbox[1]
    title_x = (width - title_w) // 2

    add_text_with_outline(draw, (title_x, title_y), title, font_title,
                          (255, 255, 255, 255), (0, 0, 0, 180), 4)

    # 부제
    subtitle = "11살 노령견 기준"
    font_sub = get_font(KOREAN_FONT, subtitle_size)
    sub_bbox = draw.textbbox((0, 0), subtitle, font=font_sub)
    sub_w = sub_bbox[2] - sub_bbox[0]
    sub_h = sub_bbox[3] - sub_bbox[1]
    sub_x = (width - sub_w) // 2
    sub_y = title_y + title_h + gap

    add_text_with_outline(draw, (sub_x, sub_y), subtitle, font_sub,
                          (255, 255, 255, 255), (0, 0, 0, 150), 2)

    result = Image.alpha_composite(img, overlay)
    result.convert("RGB").save(output_path, quality=95)

    print(f"✅ {output_path}")
    print(f"   제목: {title_size}px @ {title_y}, 부제: {subtitle_size}px @ {sub_y}, 끝: {sub_y + sub_h}px")

INPUT = "content/images/000_cover/02_ready/cover_55_양파_onion_DANGER.png"
OUT = "content/images/039_onion_양파"

if __name__ == "__main__":
    # A: 간격 50px
    generate(INPUT, f"{OUT}/var_A.png", "ONION", 170, 55, 50, 50)

    # B: 간격 60px
    generate(INPUT, f"{OUT}/var_B.png", "ONION", 170, 55, 50, 60)

    # C: 간격 70px
    generate(INPUT, f"{OUT}/var_C.png", "ONION", 170, 55, 50, 70)
