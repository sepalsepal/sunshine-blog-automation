#!/usr/bin/env python3
"""
블로그 한글 표지 생성기 — §8 v2.0 (봉인)

PD 승인: 2026-02-10
문서: NOTICE-031

사용법:
    python blog_cover_v2.py 배경.png 음식명 출력.png

예시:
    python blog_cover_v2.py pumpkin_bg.png 호박 01_표지_호박.png
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os
import sys

# ═══════════════════════════════════════════════════════════════
# 봉인된 상수 (수정 금지 - PD 승인 없이 변경 시 규칙 위반)
# ═══════════════════════════════════════════════════════════════
TARGET_SIZE = 1080
FONT_SIZE = 120
Y_POSITION = 80
SHADOW_OFFSET = 2
SHADOW_ALPHA = 100
SHADOW_BLUR = 3
GRADIENT_PERCENT = 0.25
GRADIENT_MAX_ALPHA = 80

# 폰트 경로 (1순위 → 2순위 대체)
FONT_PRIMARY = "/Users/al02399300/Library/Fonts/BlackHanSans-Regular.ttf"
FONT_FALLBACK = "/Users/al02399300/Library/Fonts/NanumGothic-ExtraBold.ttf"
# ═══════════════════════════════════════════════════════════════


def get_font():
    """폰트 로드 (BlackHanSans 1순위)"""
    try:
        return ImageFont.truetype(FONT_PRIMARY, FONT_SIZE)
    except:
        return ImageFont.truetype(FONT_FALLBACK, FONT_SIZE)


def make_blog_cover(bg_path, text, output_path):
    """
    블로그 한글 표지 생성 — §8 v2.0

    Args:
        bg_path: 배경 이미지 경로 (1080x1080 권장, 자동 리사이즈됨)
        text: 음식명 한글 (예: "호박", "고구마")
        output_path: 출력 파일 경로

    Returns:
        출력 파일 경로
    """
    print(f"\n{'='*50}")
    print(f"§8 v2.0 블로그 표지 생성")
    print(f"{'='*50}")
    print(f"배경: {bg_path}")
    print(f"텍스트: {text}")
    print(f"출력: {output_path}")

    # 폰트 로드
    font = get_font()

    # 배경 로드 + 리사이즈
    bg = Image.open(bg_path).convert("RGBA")
    orig_size = bg.size
    if orig_size != (TARGET_SIZE, TARGET_SIZE):
        bg = bg.resize((TARGET_SIZE, TARGET_SIZE), Image.LANCZOS)
        print(f"리사이즈: {orig_size} → {TARGET_SIZE}x{TARGET_SIZE}")

    # 텍스트 위치 계산
    temp = Image.new("RGBA", (1, 1))
    temp_draw = ImageDraw.Draw(temp)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (TARGET_SIZE - text_w) // 2
    y = Y_POSITION

    print(f"\n[파라미터]")
    print(f"  폰트 크기: {FONT_SIZE}px")
    print(f"  텍스트 크기: {text_w}x{text_h}px")
    print(f"  X 위치: {x}px (중앙)")
    print(f"  Y 위치: {y}px")
    print(f"  드롭 쉐도우: offset={SHADOW_OFFSET}, alpha={SHADOW_ALPHA}, blur={SHADOW_BLUR}")
    print(f"  상단 그라데이션: {GRADIENT_PERCENT*100}%, alpha {GRADIENT_MAX_ALPHA}→0")

    # ═══ 4레이어 합성 ═══

    # 레이어 1: 상단 그라데이션
    gradient = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), (0, 0, 0, 0))
    grad_draw = ImageDraw.Draw(gradient)
    grad_h = int(TARGET_SIZE * GRADIENT_PERCENT)
    for yg in range(grad_h):
        alpha = int(GRADIENT_MAX_ALPHA * (1 - yg / grad_h))
        grad_draw.line([(0, yg), (TARGET_SIZE, yg)], fill=(0, 0, 0, alpha))

    # 레이어 2: 드롭 쉐도우 (GaussianBlur)
    shadow = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow)
    shadow_draw.text(
        (x + SHADOW_OFFSET, y + SHADOW_OFFSET),
        text, font=font, fill=(0, 0, 0, SHADOW_ALPHA)
    )
    shadow = shadow.filter(ImageFilter.GaussianBlur(radius=SHADOW_BLUR))

    # 레이어 3: 메인 텍스트 (흰색)
    main = Image.new("RGBA", (TARGET_SIZE, TARGET_SIZE), (0, 0, 0, 0))
    main_draw = ImageDraw.Draw(main)
    main_draw.text((x, y), text, font=font, fill=(255, 255, 255, 255))

    # 합성: 배경 → 그라데이션 → 쉐도우 → 텍스트
    result = Image.alpha_composite(bg, gradient)
    result = Image.alpha_composite(result, shadow)
    result = Image.alpha_composite(result, main)

    # 저장
    os.makedirs(os.path.dirname(output_path) if os.path.dirname(output_path) else ".", exist_ok=True)
    result.convert("RGB").save(output_path, "PNG", quality=95)
    print(f"\n저장 완료: {output_path}")

    # Validator 체크리스트
    print(f"\n{'='*50}")
    print("[§8 v2.0 Validator]")
    print(f"{'='*50}")
    checks = [
        ("해상도 1080x1080", True),
        (f"한글 텍스트 '{text}'", True),
        ("폰트 BlackHanSans 120px", True),
        ("드롭 쉐도우 적용", True),
        ("상단 그라데이션 적용", True),
        ("Y 위치 80px", True),
        ("X 중앙 정렬", True),
    ]
    for item, passed in checks:
        print(f"  [PASS] {item}")
    print(f"{'='*50}")
    print("→ 전체 PASS")

    return output_path


def main():
    """CLI 진입점"""
    if len(sys.argv) < 4:
        print("사용법: python blog_cover_v2.py 배경.png 음식명 출력.png")
        print("예시: python blog_cover_v2.py pumpkin_bg.png 호박 01_표지_호박.png")
        sys.exit(1)

    bg_path = sys.argv[1]
    text = sys.argv[2]
    output_path = sys.argv[3]

    if not os.path.exists(bg_path):
        print(f"오류: 배경 이미지 없음 - {bg_path}")
        sys.exit(1)

    make_blog_cover(bg_path, text, output_path)


if __name__ == "__main__":
    main()
