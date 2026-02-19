#!/usr/bin/env python3
"""
00_Best 폴더 정리 + 스마트 크롭 스크립트
1. 중복 삭제 (_cta_source.jpg, _01_usable.jpg)
2. 원본 이미지 스마트 크롭 (1080x1080, 햇살이 얼굴 보존)
3. 크롭된 이미지 저장 (00_Best_cropped/)
"""

import os
from pathlib import Path
from PIL import Image

# 경로
BEST_FOLDER = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/contents/sunshine photos/00_Best")
CROPPED_FOLDER = BEST_FOLDER.parent / "00_Best_cropped"

# 출력 크기
OUTPUT_SIZE = (1080, 1080)


def get_aspect_ratio_type(width: int, height: int) -> str:
    """이미지 비율 타입 감지"""
    ratio = width / height
    
    if 0.95 <= ratio <= 1.05:
        return "square"
    elif ratio < 0.95:
        if ratio < 0.65:
            return "vertical_long"
        else:
            return "vertical"
    else:
        return "horizontal"


def get_y_offset_percent(ratio_type: str) -> float:
    """비율별 y_offset 반환 (Sunshine Photo Crop Spec v1.0)"""
    offsets = {
        "square": 0,
        "horizontal": 0,
        "vertical": -0.15,
        "vertical_long": -0.20,
    }
    return offsets.get(ratio_type, 0)


def smart_crop(img: Image.Image) -> Image.Image:
    """스마트 정사각형 크롭 (햇살이 얼굴 보존)"""
    width, height = img.size

    if width == height:
        return img.resize(OUTPUT_SIZE, Image.Resampling.LANCZOS)

    ratio_type = get_aspect_ratio_type(width, height)
    y_offset_percent = get_y_offset_percent(ratio_type)

    if width > height:
        # 가로 이미지: 중앙 크롭
        left = (width - height) // 2
        cropped = img.crop((left, 0, left + height, height))
    else:
        # 세로 이미지: 상단 우선 크롭
        crop_size = width
        max_top = height - crop_size
        center_top = (height - crop_size) // 2
        offset_pixels = int(max_top * y_offset_percent)
        top = max(0, min(max_top, center_top + offset_pixels))
        cropped = img.crop((0, top, width, top + crop_size))

    return cropped.resize(OUTPUT_SIZE, Image.Resampling.LANCZOS)


def cleanup_duplicates():
    """중복 파일 삭제"""
    delete_patterns = ['_cta_source.jpg', '_01_usable.jpg']
    
    deleted_count = 0
    deleted_size = 0
    
    print("\n[1/3] 중복 파일 삭제 중...")
    
    for file in sorted(BEST_FOLDER.glob("*.jpg")):
        filename = file.name
        should_delete = any(pattern in filename for pattern in delete_patterns)
        
        if should_delete:
            size = file.stat().st_size
            file.unlink()
            deleted_count += 1
            deleted_size += size
    
    print(f"     삭제 완료: {deleted_count}개 ({deleted_size/1024/1024:.1f}MB)")
    return deleted_count


def crop_all_images():
    """모든 원본 이미지 스마트 크롭"""
    CROPPED_FOLDER.mkdir(exist_ok=True)
    
    images = list(BEST_FOLDER.glob("*.jpg")) + list(BEST_FOLDER.glob("*.jpeg"))
    total = len(images)
    
    print(f"\n[2/3] 스마트 크롭 중... ({total}개)")
    
    success = 0
    for idx, img_path in enumerate(sorted(images), 1):
        try:
            img = Image.open(img_path).convert('RGB')
            orig_w, orig_h = img.size
            ratio_type = get_aspect_ratio_type(orig_w, orig_h)
            
            cropped = smart_crop(img)
            
            # 저장 (PNG로 고품질)
            output_name = img_path.stem + "_cropped.png"
            output_path = CROPPED_FOLDER / output_name
            cropped.save(output_path, "PNG", optimize=True)
            
            success += 1
            
            if idx % 50 == 0:
                print(f"     진행: {idx}/{total}")
                
        except Exception as e:
            print(f"     ❌ {img_path.name}: {e}")
    
    print(f"     크롭 완료: {success}/{total}개")
    return success


def main():
    print("=" * 60)
    print("00_Best 폴더 정리 + 스마트 크롭")
    print("Sunshine Photo Crop Spec v1.0 적용")
    print("=" * 60)
    
    # 1. 중복 삭제
    deleted = cleanup_duplicates()
    
    # 2. 스마트 크롭
    cropped = crop_all_images()
    
    # 3. 결과 요약
    remaining = len(list(BEST_FOLDER.glob("*.jpg")))
    
    print("\n[3/3] 완료!")
    print("=" * 60)
    print(f"  삭제: {deleted}개 중복 파일")
    print(f"  원본: {remaining}개 (00_Best/)")
    print(f"  크롭: {cropped}개 (00_Best_cropped/)")
    print("=" * 60)
    print(f"\n📁 크롭 폴더: {CROPPED_FOLDER}")


if __name__ == "__main__":
    main()
