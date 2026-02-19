#!/usr/bin/env python3
"""
부제 베리에이션 테스트 - 3차
Apple SD Gothic Neo Bold 사용
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

ARIAL_BLACK = "/Library/Fonts/Arial Black.ttf"
# Apple SD Gothic Neo (macOS 기본 한글 폰트)
KOREAN_FONT = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except Exception as e:
        print(f"폰트 로드 실패: {path} - {e}")
        return ImageFont.load_default()

def add_text_shadow(draw, position, text, font, fill, shadow_color=(0, 0, 0, 220), offset=4):
    x, y = position
    # 더 진한 그림자 (여러 레이어)
    for i in range(3):
        draw.text((x + offset + i, y + offset + i), text, font=font, fill=shadow_color)
    draw.text(position, text, font=font, fill=fill)

def create_gradient_banner(width, height, banner_height, max_alpha=240):
    banner = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for y in range(banner_height):
        alpha = int(max_alpha * (1 - y / banner_height) ** 1.2)
        for x in range(width):
            banner.putpixel((x, y), (0, 0, 0, alpha))
    return banner

def generate_variation(input_path, output_path, name, title_size, subtitle_size, gap, top_offset, banner_pct):
    img = Image.open(input_path).convert("RGBA")
    width, height = img.size

    banner_height = int(height * banner_pct)
    banner = create_gradient_banner(width, height, banner_height, max_alpha=250)
    img = Image.alpha_composite(img, banner)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 제목 (Arial Black)
    font_title = get_font(ARIAL_BLACK, title_size)
    title = "ONION"
    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]
    title_x = (width - title_width) // 2
    title_y = top_offset

    add_text_shadow(draw, (title_x, title_y), title, font_title, (255, 255, 255, 255), offset=5)

    # 부제 (Apple SD Gothic Neo)
    subtitle = "11살 노령견 기준"
    font_subtitle = get_font(KOREAN_FONT, subtitle_size)
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_height = subtitle_bbox[3] - subtitle_bbox[1]
    subtitle_x = (width - subtitle_width) // 2
    subtitle_y = title_y + title_height + gap

    add_text_shadow(draw, (subtitle_x, subtitle_y), subtitle, font_subtitle, (255, 255, 255, 255), offset=4)

    text_end = subtitle_y + subtitle_height

    result = Image.alpha_composite(img, overlay)
    result = result.convert("RGB")
    result.save(output_path, quality=95)

    print(f"✅ {name}")
    print(f"   제목: {title_size}px @ {title_y}px")
    print(f"   부제: {subtitle_size}px @ {subtitle_y}px (끝: {text_end}px)")
    print(f"   배너: {banner_height}px ({int(banner_pct*100)}%)")
    print(f"   여유: {banner_height - text_end}px")
    print()

INPUT = "content/images/000_cover/02_ready/cover_55_양파_onion_DANGER.png"
OUTPUT_DIR = "content/images/039_onion_양파"

if __name__ == "__main__":
    # H안: 제목 170px @ 80px, 부제 80px, 간격 15px
    generate_variation(INPUT, f"{OUTPUT_DIR}/test_H_apple80.png",
                       "H안 (Apple 80px)", 170, 80, 15, 80, 0.28)

    # I안: 제목 170px @ 60px, 부제 70px, 간격 20px
    generate_variation(INPUT, f"{OUTPUT_DIR}/test_I_higher.png",
                       "I안 (더 위로 60px)", 170, 70, 20, 60, 0.30)

    # J안: 제목 150px @ 50px, 부제 65px, 간격 15px (전체 작게)
    generate_variation(INPUT, f"{OUTPUT_DIR}/test_J_smaller.png",
                       "J안 (전체 작게)", 150, 65, 15, 50, 0.26)

    print("3차 베리에이션 생성 완료!")
