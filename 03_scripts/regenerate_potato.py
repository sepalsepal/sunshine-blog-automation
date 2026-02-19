#!/usr/bin/env python3
"""
🥔 Potato 텍스트 오버레이 재생성 (줄간격 수정 버전)

수정 사항:
- line-height: fontSize * 1.4 적용
- 제목-부제목 간격: 48px (기존 32px)
- 하단 여백: 12% 확보
"""

# ═══════════════════════════════════════════════════════════════
# 🔴 WO-FREEZE-001 동결
# ═══════════════════════════════════════════════════════════════
import sys
print("🔴 FROZEN: WO-FREEZE-001 동결 중. 실행 차단됨.")
print("   사유: 범위 초과 실행 방지")
print("   해제: PD 승인 + 김부장 동결해제 지시 필요")
sys.exit(1)
# ═══════════════════════════════════════════════════════════════

import os
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont
import subprocess

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"

# 폰트 경로
FONT_PATHS = [
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
    "/Library/Fonts/NotoSansKR-Bold.otf",
    str(PROJECT_ROOT / "content/fonts/NotoSansKR-Bold.ttf"),
]

def get_font(size, bold=True):
    """폰트 로드"""
    for font_path in FONT_PATHS:
        if os.path.exists(font_path):
            try:
                return ImageFont.truetype(font_path, size)
            except:
                continue
    return ImageFont.load_default()

def add_text_shadow(draw, position, text, font, fill, shadow_offset=3, shadow_color=(0, 0, 0, 200)):
    """텍스트에 그림자 추가"""
    x, y = position
    # 그림자
    draw.text((x + shadow_offset, y + shadow_offset), text, font=font, fill=shadow_color, anchor="mm")
    # 메인 텍스트
    draw.text((x, y), text, font=font, fill=fill, anchor="mm")

def add_text_overlay(input_path: Path, output_path: Path, title: str, subtitle: str, safety_color: str = "#4ECDC4"):
    """
    텍스트 오버레이 - 줄간격 적용 버전 (v1.1)
    """

    img = Image.open(input_path).convert("RGBA")
    canvas_width, canvas_height = img.size

    # 🔴 하단 25% 블러 + 어두운 오버레이 (CLAUDE.md 규칙)
    gradient = Image.new("RGBA", img.size, (0, 0, 0, 0))
    gradient_draw = ImageDraw.Draw(gradient)

    gradient_height = int(canvas_height * 0.25)  # 하단 25%
    for i in range(gradient_height):
        y = canvas_height - gradient_height + i
        progress = i / gradient_height
        alpha = int(220 * progress)  # 0 → 220 (85% opacity at bottom)
        gradient_draw.line([(0, y), (canvas_width, y)], fill=(0, 0, 0, alpha))

    img = Image.alpha_composite(img, gradient)
    draw = ImageDraw.Draw(img)

    # 폰트 설정 (v1.2 - 시금치/올리브 기준 CLAUDE.md)
    title_font_size = 48      # 🔴 48px (CLAUDE.md 규칙)
    subtitle_font_size = 24   # 🔴 24px (CLAUDE.md 규칙)

    title_font = get_font(title_font_size)
    subtitle_font = get_font(subtitle_font_size)

    # 줄간격 설정 (v1.2)
    title_line_height = int(title_font_size * 1.4)      # 67.2px
    subtitle_line_height = int(subtitle_font_size * 1.4)  # 33.6px
    title_sub_gap = int(title_font_size * 0.8)  # 38.4px

    # 텍스트 블록 높이 계산
    total_height = title_line_height + title_sub_gap + subtitle_line_height

    # 🔴 제목 위치: 하단에서 약 20% (CLAUDE.md 규칙)
    text_center_y = int(canvas_height * 0.80)  # 하단 20% = 상단 80%

    # 제목 위치
    title_y = text_center_y - (title_sub_gap // 2) - (title_line_height // 2)
    title_x = canvas_width // 2

    # 부제목 위치
    subtitle_y = text_center_y + (title_sub_gap // 2) + (subtitle_line_height // 2)
    subtitle_x = canvas_width // 2

    # 색상 설정
    title_color = safety_color
    subtitle_color = "#FFFFFF"

    # 제목 그리기
    add_text_shadow(draw, (title_x, title_y), title, title_font, title_color, shadow_offset=3)

    # 부제목 그리기
    add_text_shadow(draw, (subtitle_x, subtitle_y), subtitle, subtitle_font, subtitle_color, shadow_offset=2)

    # RGB로 변환하여 저장
    img_rgb = img.convert("RGB")
    img_rgb.save(output_path, "PNG", quality=95)

    print(f"  ✅ {output_path.name}")

def main():
    print("=" * 60)
    print("🥔 Potato 텍스트 오버레이 재생성")
    print("=" * 60)

    # potato 폴더 찾기
    potato_dir = None
    for folder in CONTENTS_DIR.iterdir():
        if folder.is_dir() and "potato" in folder.name.lower():
            potato_dir = folder
            break

    if not potato_dir:
        print("❌ potato 폴더 없음")
        sys.exit(1)

    print(f"📁 폴더: {potato_dir.name}")

    archive_dir = potato_dir / "archive"

    # 텍스트 데이터
    slides = [
        {"num": "01", "title": "✓ 먹어도 돼요!", "subtitle": "탄수화물과 비타민C 풍부 ✅", "color": "#4ECDC4"},
        {"num": "02", "title": "⚠️ 주의사항", "subtitle": "껍질/싹 제거, 익혀서만 ⚠️", "color": "#FFE066"},
        {"num": "03", "title": "💾 저장 & 공유", "subtitle": "주변 견주에게 알려주세요! 🐶", "color": "#FFD93D"},
    ]

    print()

    for slide in slides:
        num = slide["num"]

        # 배경 이미지 찾기
        bg_path = archive_dir / f"potato_{num}_bg.png"
        if not bg_path.exists():
            bg_path = archive_dir / f"potato_{num}.png"
        if not bg_path.exists():
            # 기존 이미지에서 추출 시도 (이미 텍스트가 있지만)
            bg_path = potato_dir / f"potato_{num}.png"
            if not bg_path.exists():
                print(f"  ⚠️ [{num}] 배경 이미지 없음 - 스킵")
                continue

        output_path = potato_dir / f"potato_{num}.png"

        print(f"[{num}] {slide['title']}")

        add_text_overlay(
            bg_path,
            output_path,
            slide["title"],
            slide["subtitle"],
            slide["color"]
        )

    print()
    print("=" * 60)
    print("✨ 완료!")
    print()
    print("📋 확인 명령어:")
    print(f"   open {potato_dir}")

if __name__ == "__main__":
    main()
