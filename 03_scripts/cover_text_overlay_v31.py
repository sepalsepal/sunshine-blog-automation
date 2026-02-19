#!/usr/bin/env python3
"""
v3.1 표지 텍스트 오버레이 (RULES.md 준수)

규칙:
- 폰트: NotoSansCJK-Black (없으면 Arial Black)
- 크기: 114px
- 색상: #FFFFFF
- Y위치: 100px 고정
- 효과: 2단 그림자
- 제목만 (부제 없음)

레퍼런스: reference/cover_reference_pasta.png, cover_reference_burdock.png
"""

from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).parent.parent.parent

# v3.1 고정 설정
FONT_SIZE = 114
Y_POSITION = 100
TEXT_COLOR = (255, 255, 255, 255)  # #FFFFFF

# 폰트 경로 (우선순위: NotoSansCJK-Black > Arial Black)
FONT_PATHS = [
    "/Library/Fonts/NotoSansCJK-Black.ttf",
    "/Library/Fonts/NotoSansCJKkr-Black.otf",
    "/System/Library/Fonts/NotoSansCJK-Black.ttc",
    "/Library/Fonts/Arial Black.ttf",
    "/System/Library/Fonts/Supplemental/Arial Black.ttf",
]


def get_font(size: int = FONT_SIZE):
    """v3.1 규칙 폰트 로드"""
    for path in FONT_PATHS:
        if Path(path).exists():
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    print("⚠️ 지정 폰트 없음, 기본 폰트 사용")
    return ImageFont.load_default()


def add_double_shadow(draw, position, text, font, fill):
    """2단 그림자 효과 (v3.1 규칙)"""
    x, y = position
    # 1단 그림자 (멀리, 진하게)
    draw.text((x + 4, y + 4), text, font=font, fill=(0, 0, 0, 200))
    # 2단 그림자 (가깝게, 연하게)
    draw.text((x + 2, y + 2), text, font=font, fill=(0, 0, 0, 120))
    # 본문
    draw.text(position, text, font=font, fill=fill)


def apply_cover_text_v31(
    input_image: str,
    output_image: str,
    title_en: str,
    font_size: int = None
):
    """
    v3.1 표지 텍스트 오버레이

    RULES.md 기준:
    - 폰트: NotoSansCJK-Black (114px)
    - Y위치: 100px 고정
    - 제목만 (부제 없음)
    - 2단 그림자

    Args:
        input_image: 원본 이미지 경로
        output_image: 출력 이미지 경로
        title_en: 영문 제목 (예: PASTA)
        font_size: 폰트 크기 (기본 114px, 긴 제목용 조정 가능)
    """
    # 이미지 로드
    img = Image.open(input_image).convert("RGBA")
    width, height = img.size

    # 드로우 객체
    overlay = Image.new("RGBA", img.size, (0, 0, 0, 0))
    draw = ImageDraw.Draw(overlay)

    # 폰트 (긴 제목은 크기 조정 가능)
    actual_size = font_size if font_size else FONT_SIZE
    font = get_font(actual_size)

    # 텍스트 위치 계산 (중앙 정렬, Y=100px 고정)
    title_bbox = draw.textbbox((0, 0), title_en, font=font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    title_y = Y_POSITION  # v3.1 규칙: 100px 고정

    # 텍스트 그리기 (2단 그림자)
    add_double_shadow(draw, (title_x, title_y), title_en, font, TEXT_COLOR)

    # 합성
    result = Image.alpha_composite(img, overlay)

    # RGB로 변환 후 저장
    result = result.convert("RGB")
    result.save(output_image, quality=95)

    print(f"✅ v3.1 표지 생성: {output_image}")
    print(f"   - 제목: '{title_en}'")
    print(f"   - 위치: ({title_x}, {title_y})")
    print(f"   - 크기: {actual_size}px")

    return True


if __name__ == "__main__":
    if len(sys.argv) < 4:
        print("Usage: python cover_text_overlay_v31.py <input> <output> <title_en> [font_size]")
        print("Example: python cover_text_overlay_v31.py cover.png output.png PASTA")
        print("         python cover_text_overlay_v31.py cover.png output.png 'GREEN BEANS' 90")
        sys.exit(1)

    input_img = sys.argv[1]
    output_img = sys.argv[2]
    title = sys.argv[3]
    size = int(sys.argv[4]) if len(sys.argv) > 4 else None

    apply_cover_text_v31(input_img, output_img, title, size)
