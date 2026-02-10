#!/usr/bin/env python3
"""
실사진 CTA 오버레이 스크립트 (A안 구현)
- 햇살이 실사진을 CTA 슬라이드(03번)에 적용
- 1080x1080 크로핑 + 하단 블러 + 텍스트 오버레이

Author: 김부장
Version: 1.0
"""

import os
import sys
import random
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# 프로젝트 루트
ROOT = Path(__file__).parent.parent.parent

# 실사진 폴더 경로
REAL_PHOTO_PATHS = {
    "happy": ROOT / "content/images/sunshine/01_usable/grade_A/expression/happy",
    "cuddle": ROOT / "content/images/sunshine/02_with_human/cuddle",
    "daily": ROOT / "content/images/sunshine/02_with_human/daily",
}

# 폰트 경로
FONT_PATH = ROOT / "content/fonts/Pretendard-ExtraBold.otf"
FONT_PATH_FALLBACK = "/System/Library/Fonts/AppleSDGothicNeo.ttc"

# 출력 크기
OUTPUT_SIZE = (1080, 1080)

# 텍스트 설정
CTA_TEXTS = {
    "default": {"title": "공유 필수!", "subtitle": "다른 견주에게도 알려주세요"},
    "save": {"title": "저장하세요!", "subtitle": "나중에 다시 확인하세요"},
    "follow": {"title": "팔로우하세요!", "subtitle": "더 많은 정보를 받아보세요"},
}


def get_random_photo(mood: str = "happy") -> Path:
    """지정된 분위기의 랜덤 실사진 선택"""
    folder = REAL_PHOTO_PATHS.get(mood, REAL_PHOTO_PATHS["happy"])

    if not folder.exists():
        raise FileNotFoundError(f"폴더를 찾을 수 없습니다: {folder}")

    photos = list(folder.glob("*.jpg")) + list(folder.glob("*.png")) + list(folder.glob("*.jpeg"))

    if not photos:
        raise FileNotFoundError(f"사진을 찾을 수 없습니다: {folder}")

    return random.choice(photos)


def crop_to_square(img: Image.Image) -> Image.Image:
    """이미지를 정사각형으로 크롭 (중앙 기준)"""
    width, height = img.size

    if width == height:
        return img

    # 짧은 쪽 기준으로 중앙 크롭
    if width > height:
        left = (width - height) // 2
        return img.crop((left, 0, left + height, height))
    else:
        top = (height - width) // 2
        return img.crop((0, top, width, top + width))


def apply_bottom_blur(img: Image.Image, blur_height_ratio: float = 0.35) -> Image.Image:
    """하단 영역에 블러 + 다크 오버레이 적용"""
    width, height = img.size
    blur_start = int(height * (1 - blur_height_ratio))

    # 원본 복사
    result = img.copy()

    # 하단 영역 추출
    bottom_region = img.crop((0, blur_start, width, height))

    # 블러 적용
    blurred = bottom_region.filter(ImageFilter.GaussianBlur(radius=30))

    # 다크 오버레이 (15% 어둡게)
    dark_overlay = Image.new('RGBA', blurred.size, (0, 0, 0, int(255 * 0.15)))
    blurred = Image.alpha_composite(blurred.convert('RGBA'), dark_overlay)

    # 그라데이션 마스크 생성 (부드러운 전환)
    gradient_height = int(height * 0.1)  # 10% 그라데이션 영역

    mask = Image.new('L', (width, height - blur_start), 0)
    mask_draw = ImageDraw.Draw(mask)

    for y in range(gradient_height):
        alpha = int(255 * (y / gradient_height))
        mask_draw.line([(0, y), (width, y)], fill=alpha)

    # 나머지는 완전 불투명
    mask_draw.rectangle([(0, gradient_height), (width, height - blur_start)], fill=255)

    # 블러 영역 합성
    result.paste(blurred.convert('RGB'), (0, blur_start), mask)

    return result


def add_text_overlay(img: Image.Image, title: str, subtitle: str) -> Image.Image:
    """CTA 텍스트 오버레이 추가"""
    draw = ImageDraw.Draw(img)
    width, height = img.size

    # 폰트 로드
    try:
        title_font = ImageFont.truetype(str(FONT_PATH), 72)
        subtitle_font = ImageFont.truetype(str(FONT_PATH), 32)
    except:
        title_font = ImageFont.truetype(FONT_PATH_FALLBACK, 72)
        subtitle_font = ImageFont.truetype(FONT_PATH_FALLBACK, 32)

    # 텍스트 위치 계산 (하단 25% 영역 중앙)
    text_area_top = int(height * 0.75)
    text_area_center = text_area_top + int(height * 0.125)

    # 제목 그리기
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_width = title_bbox[2] - title_bbox[0]
    title_x = (width - title_width) // 2
    title_y = text_area_center - 50

    # 그림자 효과
    shadow_offset = 3
    draw.text((title_x + shadow_offset, title_y + shadow_offset), title,
              font=title_font, fill=(0, 0, 0, 180))
    draw.text((title_x, title_y), title, font=title_font, fill="white")

    # 부제목 그리기
    subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
    subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
    subtitle_x = (width - subtitle_width) // 2
    subtitle_y = title_y + 80

    draw.text((subtitle_x + 2, subtitle_y + 2), subtitle,
              font=subtitle_font, fill=(0, 0, 0, 150))
    draw.text((subtitle_x, subtitle_y), subtitle, font=subtitle_font, fill="white")

    return img


def create_cta_slide(
    output_path: str,
    mood: str = "happy",
    cta_type: str = "default",
    specific_photo: str = None
) -> str:
    """
    CTA 슬라이드 생성

    Args:
        output_path: 출력 파일 경로
        mood: 사진 분위기 (happy, cuddle, daily)
        cta_type: CTA 유형 (default, save, follow)
        specific_photo: 특정 사진 경로 (선택)

    Returns:
        생성된 파일 경로
    """
    # 사진 선택
    if specific_photo:
        photo_path = Path(specific_photo)
    else:
        photo_path = get_random_photo(mood)

    print(f"📸 선택된 실사진: {photo_path.name}")

    # 이미지 로드
    img = Image.open(photo_path).convert('RGB')

    # 정사각형 크롭
    img = crop_to_square(img)

    # 1080x1080 리사이즈
    img = img.resize(OUTPUT_SIZE, Image.Resampling.LANCZOS)

    # 하단 블러 적용
    img = apply_bottom_blur(img)

    # 텍스트 가져오기
    cta_text = CTA_TEXTS.get(cta_type, CTA_TEXTS["default"])

    # 텍스트 오버레이
    img = add_text_overlay(img, cta_text["title"], cta_text["subtitle"])

    # 저장
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output, "PNG", quality=95)

    print(f"✅ CTA 슬라이드 생성 완료: {output}")
    return str(output)


def apply_to_content(content_folder: str, topic: str, mood: str = "happy"):
    """
    콘텐츠 폴더에 실사진 CTA 적용

    Args:
        content_folder: 콘텐츠 폴더 경로
        topic: 주제 (영문)
        mood: 사진 분위기
    """
    folder = Path(content_folder)
    output_path = folder / f"{topic}_03.png"

    # 기존 03번 백업
    if output_path.exists():
        backup_path = folder / "archive" / f"{topic}_03_ai_backup.png"
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.rename(backup_path)
        print(f"📦 기존 AI 이미지 백업: {backup_path.name}")

    # 실사진 CTA 생성
    create_cta_slide(str(output_path), mood=mood)

    print(f"🎉 {topic} CTA 슬라이드를 실사진으로 교체 완료!")


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python apply_real_photo_cta.py <output_path> [mood] [cta_type]")
        print("       python apply_real_photo_cta.py --apply <content_folder> <topic> [mood]")
        print("")
        print("Examples:")
        print("  python apply_real_photo_cta.py test_cta.png happy default")
        print("  python apply_real_photo_cta.py --apply content/images/023_코카콜라 coca_cola happy")
        print("")
        print("Moods: happy, cuddle, daily")
        print("CTA types: default, save, follow")
        sys.exit(1)

    if sys.argv[1] == "--apply":
        content_folder = sys.argv[2]
        topic = sys.argv[3]
        mood = sys.argv[4] if len(sys.argv) > 4 else "happy"
        apply_to_content(content_folder, topic, mood)
    else:
        output_path = sys.argv[1]
        mood = sys.argv[2] if len(sys.argv) > 2 else "happy"
        cta_type = sys.argv[3] if len(sys.argv) > 3 else "default"
        create_cta_slide(output_path, mood, cta_type)
