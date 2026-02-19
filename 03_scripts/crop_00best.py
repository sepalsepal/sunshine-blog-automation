#!/usr/bin/env python3
"""
00_Best 폴더 이미지 크롭 스크립트
- 원본 → originals/ 폴더로 백업
- 크롭본 → crop/ 폴더에 저장
- 1080x1080 PNG, 비율별 스마트 오프셋 적용
"""

import os
import shutil
from pathlib import Path
from PIL import Image, ImageOps

# 경로 설정
BASE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/contents/sunshine photos/00_Best")
CROP_DIR = BASE_DIR / "crop"
ORIGINALS_DIR = BASE_DIR / "originals"

# 크롭 설정
OUTPUT_SIZE = (1080, 1080)
OUTPUT_FORMAT = "PNG"
OUTPUT_QUALITY = 95

def get_aspect_ratio_type(width, height):
    """이미지 비율 타입 판별"""
    ratio = width / height

    if 0.95 <= ratio <= 1.05:
        return "square", 0  # 1:1
    elif ratio < 0.95:
        if ratio <= 0.6:
            return "vertical_9_16", -20  # 9:16 (세로 긴 이미지)
        else:
            return "vertical_3_4", -15   # 3:4 (일반 세로)
    else:
        return "horizontal_4_3", 0       # 4:3 (가로)

def smart_crop(img, target_size=(1080, 1080)):
    """
    스마트 크롭: 비율별 y_offset 적용
    - 세로 이미지: 상단 우선 (얼굴 보존)
    - 가로/정사각: 중앙 크롭
    """
    width, height = img.size
    ratio_type, y_offset_percent = get_aspect_ratio_type(width, height)

    # 크롭할 영역 크기 계산 (정사각형)
    crop_size = min(width, height)

    # 중앙 좌표
    center_x = width // 2
    center_y = height // 2

    # y_offset 적용 (음수 = 위로 이동)
    y_offset = int(height * y_offset_percent / 100)

    # 크롭 영역 계산
    left = center_x - crop_size // 2
    top = center_y - crop_size // 2 + y_offset
    right = left + crop_size
    bottom = top + crop_size

    # 경계 보정
    if top < 0:
        bottom -= top
        top = 0
    if bottom > height:
        top -= (bottom - height)
        bottom = height
    if left < 0:
        right -= left
        left = 0
    if right > width:
        left -= (right - width)
        right = width

    # 크롭 및 리사이즈
    cropped = img.crop((left, top, right, bottom))
    resized = cropped.resize(target_size, Image.LANCZOS)

    return resized, ratio_type

def main():
    print("=" * 60)
    print("00_Best 스마트 크롭 v1.0")
    print("=" * 60)

    # 폴더 생성
    CROP_DIR.mkdir(exist_ok=True)
    ORIGINALS_DIR.mkdir(exist_ok=True)

    print(f"\n원본 폴더: {BASE_DIR}")
    print(f"크롭 저장: {CROP_DIR}")
    print(f"원본 백업: {ORIGINALS_DIR}")

    # 이미지 파일 목록 (하위 폴더 제외)
    image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
    images = [f for f in BASE_DIR.iterdir()
              if f.is_file() and f.suffix.lower() in image_extensions]

    print(f"\n처리 대상: {len(images)}개 이미지")
    print("-" * 60)

    success_count = 0
    error_count = 0
    stats = {"square": 0, "vertical_3_4": 0, "vertical_9_16": 0, "horizontal_4_3": 0}

    for img_path in sorted(images):
        try:
            # 원본 백업
            backup_path = ORIGINALS_DIR / img_path.name
            if not backup_path.exists():
                shutil.copy2(img_path, backup_path)

            # 이미지 열기
            with Image.open(img_path) as img:
                # EXIF 방향 정보 적용 (회전/뒤집힘 보정)
                img = ImageOps.exif_transpose(img)

                # RGB 변환 (PNG 저장용)
                if img.mode in ('RGBA', 'P'):
                    img = img.convert('RGB')
                elif img.mode != 'RGB':
                    img = img.convert('RGB')

                # 스마트 크롭
                cropped_img, ratio_type = smart_crop(img, OUTPUT_SIZE)
                stats[ratio_type] += 1

                # 저장 (PNG)
                output_name = img_path.stem + ".png"
                output_path = CROP_DIR / output_name
                cropped_img.save(output_path, OUTPUT_FORMAT, quality=OUTPUT_QUALITY)

            print(f"✅ {img_path.name} → {output_name} ({ratio_type})")
            success_count += 1

        except Exception as e:
            print(f"❌ {img_path.name}: {e}")
            error_count += 1

    # 결과 요약
    print("\n" + "=" * 60)
    print("크롭 완료")
    print("=" * 60)
    print(f"성공: {success_count}개")
    print(f"실패: {error_count}개")
    print(f"\n비율별 통계:")
    for ratio_type, count in stats.items():
        if count > 0:
            print(f"  - {ratio_type}: {count}개")

    # 용량 확인
    crop_size = sum(f.stat().st_size for f in CROP_DIR.iterdir() if f.is_file())
    orig_size = sum(f.stat().st_size for f in ORIGINALS_DIR.iterdir() if f.is_file())
    print(f"\n원본 백업 용량: {orig_size / 1024 / 1024:.1f} MB")
    print(f"크롭 이미지 용량: {crop_size / 1024 / 1024:.1f} MB")

if __name__ == "__main__":
    main()
