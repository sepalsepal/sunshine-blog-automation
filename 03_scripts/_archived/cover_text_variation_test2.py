#!/usr/bin/env python3
"""
부제 베리에이션 테스트 - 2차
E안: 간격 20px (부제를 제목 바로 아래)
F안: 부제 60px + 간격 15px (컴팩트)
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

ARIAL_BLACK = "/Library/Fonts/Arial Black.ttf"
NOTO_BLACK = "/Users/al02399300/Library/Fonts/NotoSansKR-Black.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def add_text_shadow(draw, position, text, font, fill, shadow_color=(0, 0, 0, 220), offset=4):
    x, y = position
    draw.text((x + offset, y + offset), text, font=font, fill=shadow_color)
    draw.text(position, text, font=font, fill=fill)

def create_gradient_banner(width, height, banner_height, max_alpha=240):
    banner = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for y in range(banner_height):
        alpha = int(max_alpha * (1 - y / banner_height) ** 1.3)
        for x in range(width):
            banner.putpixel((x, y), (0, 0, 0, alpha))
    return banner

def generate_variation(input_path, output_path, name, title_size, subtitle_size, gap, top_offset, banner_pct):
    img = Image.open(input_path).convert("RGBA")
    width, height = img.size

    # 그라데이션 배너
    banner_height = int(height * banner_pct)
    banner = create_gradient_banner(width, height, banner_height, max_alpha=240)
    img = Image.alpha_composite(img, banner)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 제목
    font_title = get_font(ARIAL_BLACK, title_size)
    title = "ONION"
    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]
    title_x = (width - title_width) // 2
    title_y = top_offset

    add_text_shadow(draw, (title_x, title_y), title, font_title, (255, 255, 255, 255), offset=5)

    # 부제
    subtitle = "11살 노령견 기준"
    font_subtitle = get_font(NOTO_BLACK, subtitle_size)
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]
    subtitle_x = (width - subtitle_width) // 2
    subtitle_y = title_y + title_height + gap

    add_text_shadow(draw, (subtitle_x, subtitle_y), subtitle, font_subtitle, (255, 255, 255, 255), offset=3)

    text_end = subtitle_y + subtitle_height

    result = Image.alpha_composite(img, overlay)
    result = result.convert("RGB")
    result.save(output_path, quality=95)

    print(f"✅ {name}")
    print(f"   제목: {title_size}px @ {title_y}px")
    print(f"   부제: {subtitle_size}px @ {subtitle_y}px")
    print(f"   텍스트 끝: {text_end}px / 배너: {banner_height}px")
    print(f"   여유: {banner_height - text_end}px")
    print()

INPUT = "content/images/000_cover/02_ready/cover_55_양파_onion_DANGER.png"
OUTPUT_DIR = "content/images/039_onion_양파"

if __name__ == "__main__":
    # E안: 제목 170px, 부제 90px, 간격 20px, 상단 100px, 배너 30%
    generate_variation(INPUT, f"{OUTPUT_DIR}/test_E_gap20.png",
                       "E안 (간격 20px)", 170, 90, 20, 100, 0.30)

    # F안: 제목 170px, 부제 60px, 간격 15px, 상단 120px, 배너 28%
    generate_variation(INPUT, f"{OUTPUT_DIR}/test_F_compact.png",
                       "F안 (컴팩트 60px)", 170, 60, 15, 120, 0.28)

    # G안: 제목 170px, 부제 70px, 간격 10px, 상단 80px, 배너 32%
    generate_variation(INPUT, f"{OUTPUT_DIR}/test_G_tight.png",
                       "G안 (타이트 배치)", 170, 70, 10, 80, 0.32)

    print("2차 베리에이션 생성 완료!")
