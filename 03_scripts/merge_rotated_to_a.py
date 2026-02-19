#!/usr/bin/env python3
"""
회전된 이미지를 A등급 폴더로 병합 및 네이밍 적용
"""

import shutil
from pathlib import Path
from PIL import Image
from collections import defaultdict

# 경로 설정
BASE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/content/images/sunshine/01_usable")
ROTATED_DIR = BASE_DIR / "rotated_to_A"
EXPRESSION_DIR = BASE_DIR / "expression"
LOCATION_DIR = BASE_DIR / "location"


def infer_category(filename: str, width: int, height: int) -> dict:
    """파일명과 크기로 카테고리 추론"""
    lower = filename.lower()

    # 표정
    if "happy" in lower:
        expression = "happy"
    elif "curious" in lower:
        expression = "curious"
    elif "profile" in lower:
        expression = "calm"
    elif "outdoor" in lower:
        expression = "happy"
    else:
        expression = "calm"

    # 포즈
    if "outdoor" in lower:
        pose = "walk"
    elif "profile" in lower:
        pose = "lay"
    elif height > width * 0.9:
        pose = "sit"
    else:
        pose = "lay"

    # 배경
    if "outdoor" in lower:
        background = "outdoor"
    elif "profile" in lower:
        background = "bed"
    else:
        background = "indoor"

    return {
        "expression": expression,
        "pose": pose,
        "background": background
    }


def get_next_number(target_dir: Path, prefix: str) -> int:
    """다음 번호 찾기"""
    existing = list(target_dir.glob(f"{prefix}*.jpg"))
    if not existing:
        return 1

    max_num = 0
    for f in existing:
        try:
            # haetsali_happy_lay_indoor_0001.jpg에서 번호 추출
            num_str = f.stem.split("_")[-1]
            num = int(num_str)
            max_num = max(max_num, num)
        except:
            pass

    return max_num + 1


def merge_rotated_images():
    """회전된 이미지를 A등급으로 병합"""
    print("=" * 60)
    print("🔄 회전 이미지 A등급 병합 시작")
    print("=" * 60)

    # 각 카테고리별 카운터
    counters = defaultdict(int)

    # 기존 A등급 이미지에서 최대 번호 파악
    for img in EXPRESSION_DIR.glob("*.jpg"):
        parts = img.stem.split("_")
        if len(parts) >= 5:
            key = "_".join(parts[1:4])  # happy_lay_indoor
            try:
                num = int(parts[-1])
                counters[key] = max(counters[key], num)
            except:
                pass

    for img in LOCATION_DIR.glob("*.jpg"):
        parts = img.stem.split("_")
        if len(parts) >= 5:
            key = "_".join(parts[1:4])
            try:
                num = int(parts[-1])
                counters[key] = max(counters[key], num)
            except:
                pass

    print(f"\n기존 카테고리 최대 번호: {dict(counters)}")

    merged_count = 0
    errors = []

    # 회전된 expression 이미지 처리
    rotated_exp = ROTATED_DIR / "expression"
    if rotated_exp.exists():
        for img_path in sorted(rotated_exp.glob("*.jpg")):
            try:
                img = Image.open(img_path)
                width, height = img.size
                img.close()

                cat = infer_category(img_path.name, width, height)
                key = f"{cat['expression']}_{cat['pose']}_{cat['background']}"

                counters[key] += 1
                new_name = f"haetsali_{key}_{counters[key]:04d}.jpg"
                dest_path = EXPRESSION_DIR / new_name

                shutil.copy2(img_path, dest_path)
                merged_count += 1

                if merged_count <= 5 or merged_count % 100 == 0:
                    print(f"   ✓ {img_path.name} → {new_name}")

            except Exception as e:
                errors.append(f"{img_path.name}: {str(e)}")

    # 회전된 location 이미지 처리
    rotated_loc = ROTATED_DIR / "location"
    if rotated_loc.exists():
        for img_path in sorted(rotated_loc.glob("*.jpg")):
            try:
                img = Image.open(img_path)
                width, height = img.size
                img.close()

                cat = infer_category(img_path.name, width, height)
                key = f"{cat['expression']}_{cat['pose']}_{cat['background']}"

                counters[key] += 1
                new_name = f"haetsali_{key}_{counters[key]:04d}.jpg"
                dest_path = LOCATION_DIR / new_name

                shutil.copy2(img_path, dest_path)
                merged_count += 1

            except Exception as e:
                errors.append(f"{img_path.name}: {str(e)}")

    print(f"\n✅ 병합 완료: {merged_count}개")
    if errors:
        print(f"⚠️  오류: {len(errors)}건")

    return merged_count


def count_final():
    """최종 A등급 개수"""
    exp_count = len(list(EXPRESSION_DIR.glob("*.jpg")))
    loc_count = len(list(LOCATION_DIR.glob("*.jpg")))

    print("\n" + "=" * 60)
    print("📊 최종 A등급 이미지 현황")
    print("=" * 60)
    print(f"\n   expression: {exp_count}개")
    print(f"   location: {loc_count}개")
    print(f"   합계: {exp_count + loc_count}개")


if __name__ == "__main__":
    merged = merge_rotated_images()
    count_final()

    print("\n" + "=" * 60)
    print("✅ A등급 병합 완료")
    print("=" * 60)
