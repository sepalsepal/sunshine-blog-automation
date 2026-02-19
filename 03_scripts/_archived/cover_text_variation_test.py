#!/usr/bin/env python3
"""
부제 베리에이션 테스트
- 제목: 고정 (Arial Black 170px, 위치 150px)
- 부제: 다양한 스타일 테스트
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

# 폰트 경로
ARIAL_BLACK = "/Library/Fonts/Arial Black.ttf"
NOTO_BLACK = "/Users/al02399300/Library/Fonts/NotoSansKR-Black.ttf"
NOTO_BOLD = "/Users/al02399300/Library/Fonts/NotoSansKR-Bold.ttf"

def get_font(path, size):
    try:
        return ImageFont.truetype(path, size)
    except:
        return ImageFont.load_default()

def add_text_with_stroke(draw, position, text, font, fill, stroke_color, stroke_width):
    """텍스트에 외곽선 효과"""
    x, y = position
    # 외곽선
    for dx in range(-stroke_width, stroke_width + 1):
        for dy in range(-stroke_width, stroke_width + 1):
            if dx != 0 or dy != 0:
                draw.text((x + dx, y + dy), text, font=font, fill=stroke_color)
    # 본문
    draw.text(position, text, font=font, fill=fill)

def add_text_shadow(draw, position, text, font, fill, shadow_color=(0, 0, 0, 200), offset=4):
    """텍스트에 그림자 효과"""
    x, y = position
    draw.text((x + offset, y + offset), text, font=font, fill=shadow_color)
    draw.text(position, text, font=font, fill=fill)

def create_gradient_banner(width, height, banner_height, max_alpha=220):
    """상단 그라데이션 배너"""
    banner = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    for y in range(banner_height):
        alpha = int(max_alpha * (1 - y / banner_height) ** 1.5)
        for x in range(width):
            banner.putpixel((x, y), (0, 0, 0, alpha))
    return banner

def generate_variation(input_path, output_path, variation_name, subtitle_config):
    """베리에이션 생성"""
    img = Image.open(input_path).convert("RGBA")
    width, height = img.size

    # 그라데이션 배너
    banner_height = int(height * 0.22)  # 22%로 확대
    banner = create_gradient_banner(width, height, banner_height, max_alpha=230)
    img = Image.alpha_composite(img, banner)

    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 제목 (고정)
    font_title = get_font(ARIAL_BLACK, 170)
    title = "ONION"
    title_bbox = draw.textbbox((0, 0), title, font=font_title)
    title_width = title_bbox[2] - title_bbox[0]
    title_height = title_bbox[3] - title_bbox[1]
    title_x = (width - title_width) // 2
    title_y = 150

    add_text_shadow(draw, (title_x, title_y), title, font_title, (255, 255, 255, 255), offset=5)

    # 부제 (베리에이션)
    subtitle = "11살 노령견 기준"
    font_subtitle = get_font(subtitle_config['font'], subtitle_config['size'])

    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=font_subtitle)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (width - subtitle_width) // 2
    subtitle_y = title_y + title_height + 70

    if subtitle_config.get('stroke'):
        add_text_with_stroke(
            draw, (subtitle_x, subtitle_y), subtitle, font_subtitle,
            subtitle_config['color'], subtitle_config['stroke_color'], subtitle_config['stroke_width']
        )
    else:
        add_text_shadow(
            draw, (subtitle_x, subtitle_y), subtitle, font_subtitle,
            subtitle_config['color'], subtitle_config.get('shadow_color', (0, 0, 0, 200)),
            offset=subtitle_config.get('shadow_offset', 3)
        )

    result = Image.alpha_composite(img, overlay)
    result = result.convert("RGB")
    result.save(output_path, quality=95)
    print(f"✅ {variation_name}: {output_path}")

# 입력 이미지
INPUT = "content/images/000_cover/02_ready/cover_55_양파_onion_DANGER.png"
OUTPUT_DIR = "content/images/039_onion_양파"

# 베리에이션 정의
variations = {
    "A_white_bold_shadow": {
        "font": NOTO_BLACK,
        "size": 90,
        "color": (255, 255, 255, 255),
        "shadow_color": (0, 0, 0, 220),
        "shadow_offset": 5
    },
    "B_yellow_gold": {
        "font": NOTO_BLACK,
        "size": 90,
        "color": (255, 220, 100, 255),  # 골드
        "shadow_color": (0, 0, 0, 200),
        "shadow_offset": 4
    },
    "C_white_stroke": {
        "font": NOTO_BLACK,
        "size": 90,
        "color": (255, 255, 255, 255),
        "stroke": True,
        "stroke_color": (0, 0, 0, 255),
        "stroke_width": 3
    },
    "D_larger_100px": {
        "font": NOTO_BLACK,
        "size": 100,
        "color": (255, 255, 255, 255),
        "shadow_color": (0, 0, 0, 220),
        "shadow_offset": 5
    },
}

if __name__ == "__main__":
    for name, config in variations.items():
        output = f"{OUTPUT_DIR}/test_{name}.png"
        generate_variation(INPUT, output, name, config)

    print("\n모든 베리에이션 생성 완료!")
