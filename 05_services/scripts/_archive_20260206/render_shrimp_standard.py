#!/usr/bin/env python3
"""
shrimp 콘텐츠 표준 텍스트 오버레이 스크립트
potato/burdock과 동일한 스타일 적용

조건:
1. 자동 파이프라인 (PIL 표준 오버레이)
2. potato/burdock과 동일한 스타일
3. CAUTION 기준 샘플로 지정

담당: 박편집
검수: 김감독
승인: 최부장
"""

import json
import shutil
from datetime import datetime
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).parent.parent.parent
SHRIMP_DIR = ROOT / "content/images/140_shrimp_새우_published"
ARCHIVE_DIR = SHRIMP_DIR / "archive"
CONFIG_PATH = ROOT / "config/settings/shrimp_text.json"

# 폰트 경로 (macOS)
FONT_BOLD = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
FONT_REGULAR = "/System/Library/Fonts/Supplemental/Arial.ttf"
FONT_KOREAN = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

# 스타일 설정 (potato/burdock 기준)
STYLES = {
    "cover": {
        "title_font_size": 72,
        "title_color": (255, 255, 255),
        "title_y_ratio": 0.15,  # 상단에서 15% 위치
        "shadow": True,
        "shadow_offset": (4, 4),
        "shadow_color": (0, 0, 0, 180),
    },
    "content_bottom": {
        "title_font_size": 48,
        "title_color": (255, 217, 61),  # 노란색 (CAUTION)
        "subtitle_font_size": 24,
        "subtitle_color": (255, 255, 255),
        "bg_box": True,
        "bg_box_color": (0, 0, 0, 140),
        "title_y_ratio": 0.78,
        "subtitle_y_ratio": 0.88,
    },
    "cta": {
        "title_font_size": 48,
        "title_color": (255, 217, 61),  # 노란색
        "subtitle_font_size": 24,
        "subtitle_color": (255, 255, 255),
        "bg_box": True,
        "bg_box_color": (0, 0, 0, 140),
        "title_y_ratio": 0.78,
        "subtitle_y_ratio": 0.88,
    }
}


def load_font(path, size):
    """폰트 로드 (fallback 포함)"""
    try:
        return ImageFont.truetype(path, size)
    except:
        try:
            return ImageFont.truetype(FONT_KOREAN, size)
        except:
            return ImageFont.load_default()


def add_text_shadow(draw, position, text, font, fill, shadow_offset, shadow_color):
    """그림자가 있는 텍스트 그리기"""
    x, y = position
    sx, sy = shadow_offset

    # 그림자
    draw.text((x + sx, y + sy), text, font=font, fill=shadow_color, anchor="mm")
    # 메인 텍스트
    draw.text(position, text, font=font, fill=fill, anchor="mm")


def render_cover(img, title, style):
    """표지 렌더링 (상단 타이틀)"""
    draw = ImageDraw.Draw(img)
    w, h = img.size

    font = load_font(FONT_BOLD, style["title_font_size"])
    y = int(h * style["title_y_ratio"])

    if style.get("shadow"):
        add_text_shadow(
            draw, (w // 2, y), title, font,
            style["title_color"],
            style["shadow_offset"],
            style["shadow_color"]
        )
    else:
        draw.text((w // 2, y), title, font=font, fill=style["title_color"], anchor="mm")

    return img


def render_content_bottom(img, title, subtitle, style):
    """본문 렌더링 (하단 텍스트 박스)"""
    # RGBA로 변환
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    w, h = img.size

    # 반투명 배경 박스
    if style.get("bg_box"):
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        overlay_draw = ImageDraw.Draw(overlay)

        box_top = int(h * 0.72)
        box_bottom = h
        overlay_draw.rectangle(
            [(0, box_top), (w, box_bottom)],
            fill=style["bg_box_color"]
        )

        img = Image.alpha_composite(img, overlay)

    draw = ImageDraw.Draw(img)

    # 제목
    title_font = load_font(FONT_KOREAN, style["title_font_size"])
    title_y = int(h * style["title_y_ratio"])
    draw.text((w // 2, title_y), title, font=title_font, fill=style["title_color"], anchor="mm")

    # 부제목
    if subtitle:
        subtitle_font = load_font(FONT_KOREAN, style["subtitle_font_size"])
        subtitle_y = int(h * style["subtitle_y_ratio"])
        draw.text((w // 2, subtitle_y), subtitle, font=subtitle_font, fill=style["subtitle_color"], anchor="mm")

    return img


def render_slide(bg_path, title, subtitle, slide_type, output_path):
    """슬라이드 렌더링"""
    print(f"   렌더링: {Path(bg_path).name} → {Path(output_path).name}")

    img = Image.open(bg_path)

    # 1080x1080 확인
    if img.size != (1080, 1080):
        img = img.resize((1080, 1080), Image.LANCZOS)

    style = STYLES.get(slide_type, STYLES["content_bottom"])

    if slide_type == "cover":
        img = render_cover(img, title, style)
    else:
        img = render_content_bottom(img, title, subtitle, style)

    # RGB로 변환 후 저장
    if img.mode == 'RGBA':
        # 흰색 배경과 합성
        background = Image.new('RGB', img.size, (255, 255, 255))
        background.paste(img, mask=img.split()[3])
        img = background

    img.save(output_path, quality=95)
    print(f"   ✅ 저장 완료: {Path(output_path).name}")
    return True


def backup_current_images():
    """현재 이미지 백업"""
    print("=" * 60)
    print("📦 박편집입니다. 기존 이미지 백업합니다.")
    print("=" * 60)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = ARCHIVE_DIR / f"before_standard_{timestamp}"
    backup_dir.mkdir(parents=True, exist_ok=True)

    for i in range(4):
        src = SHRIMP_DIR / f"shrimp_0{i}.png"
        if src.exists():
            dst = backup_dir / f"shrimp_0{i}.png"
            shutil.copy(src, dst)
            print(f"   백업: {src.name}")

    print(f"   위치: {backup_dir}")
    return backup_dir


def main():
    """메인 실행"""
    print("=" * 60)
    print("🦐 SHRIMP 재제작 (표준 PIL 오버레이)")
    print("   potato/burdock과 동일한 스타일 적용")
    print("=" * 60)

    # 1. 백업
    backup_dir = backup_current_images()

    # 2. 텍스트 설정 로드
    with open(CONFIG_PATH, encoding='utf-8') as f:
        text_config = json.load(f)

    print(f"\n📋 텍스트 설정 ({len(text_config)}개)")
    for slide in text_config:
        print(f"   [{slide['slide']}] {slide['type']}: {slide['title']}")

    # 3. 렌더링
    print("\n" + "=" * 60)
    print("📝 렌더링 시작")
    print("=" * 60)

    success_count = 0
    for slide in text_config:
        slide_num = slide["slide"]
        slide_type = slide["type"]
        title = slide["title"]
        subtitle = slide.get("subtitle", "")

        # 백업에서 원본 가져오기 (이미 오버레이된 이미지 사용 방지)
        src = backup_dir / f"shrimp_0{slide_num}.png"
        dst = SHRIMP_DIR / f"shrimp_0{slide_num}.png"

        if not src.exists():
            print(f"   ⚠️ 소스 없음: {src}")
            continue

        try:
            render_slide(str(src), title, subtitle, slide_type, str(dst))
            success_count += 1
        except Exception as e:
            print(f"   ❌ 실패: {e}")

    # 4. 결과
    print("\n" + "=" * 60)
    if success_count == len(text_config):
        print(f"✅ 완료! {success_count}/{len(text_config)}개 슬라이드")
        print("   김감독님 검수 부탁드립니다.")
    else:
        print(f"⚠️ 부분 완료: {success_count}/{len(text_config)}개")
    print("=" * 60)

    return success_count == len(text_config)


if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
