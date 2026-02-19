#!/usr/bin/env python3
"""
B등급 이미지 자동 회전 스크립트 (김감독 승인)

세로 이미지를 가로로 자동 회전하여 A등급으로 승격 가능하게 처리
"""

import os
from pathlib import Path
from PIL import Image, ExifTags
import json
from datetime import datetime

# 경로 설정
BASE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/content/images/sunshine/01_usable")
GRADE_B_DIR = BASE_DIR / "grade_B_80_89"
EXPRESSION_ROTATION = GRADE_B_DIR / "expression_rotation"
LOCATION_ROTATION = GRADE_B_DIR / "location_rotation"

# 회전 후 저장할 폴더
OUTPUT_DIR = BASE_DIR / "rotated_to_A"

# 결과 추적
results = {
    "rotated": [],
    "skipped": [],
    "errors": [],
    "timestamp": datetime.now().isoformat()
}


def get_exif_orientation(img):
    """EXIF에서 회전 정보 추출"""
    try:
        exif = img._getexif()
        if exif:
            for tag_id, value in exif.items():
                tag = ExifTags.TAGS.get(tag_id, tag_id)
                if tag == 'Orientation':
                    return value
    except:
        pass
    return None


def auto_rotate_image(img_path: Path, output_dir: Path) -> dict:
    """이미지 자동 회전"""
    try:
        img = Image.open(img_path)
        width, height = img.size
        original_size = (width, height)

        rotated = False
        rotation_angle = 0

        # EXIF 기반 회전
        orientation = get_exif_orientation(img)
        if orientation:
            if orientation == 3:
                img = img.rotate(180, expand=True)
                rotated = True
                rotation_angle = 180
            elif orientation == 6:
                img = img.rotate(270, expand=True)
                rotated = True
                rotation_angle = 270
            elif orientation == 8:
                img = img.rotate(90, expand=True)
                rotated = True
                rotation_angle = 90

        # EXIF 없으면 비율로 판단 (세로가 가로보다 길면 회전)
        if not rotated:
            current_w, current_h = img.size
            if current_h > current_w * 1.2:
                # 시계방향 90도 회전 (270도 = -90도)
                img = img.rotate(270, expand=True)
                rotated = True
                rotation_angle = 270

        if rotated:
            # 출력 폴더 생성
            output_dir.mkdir(parents=True, exist_ok=True)

            # 저장 (EXIF 제거하고 저장)
            output_path = output_dir / img_path.name

            # RGB 모드로 변환 (RGBA인 경우)
            if img.mode in ('RGBA', 'P'):
                img = img.convert('RGB')

            img.save(output_path, "JPEG", quality=95)

            new_w, new_h = img.size
            return {
                "filename": img_path.name,
                "original_size": original_size,
                "new_size": (new_w, new_h),
                "rotation": rotation_angle,
                "status": "rotated"
            }
        else:
            return {
                "filename": img_path.name,
                "original_size": original_size,
                "status": "skipped",
                "reason": "회전 불필요"
            }

    except Exception as e:
        return {
            "filename": img_path.name,
            "status": "error",
            "error": str(e)
        }


def process_all_rotation_images():
    """모든 회전 필요 이미지 처리"""
    print("=" * 60)
    print("🔄 B등급 이미지 자동 회전 처리")
    print("=" * 60)

    # 처리할 폴더들
    folders = [
        (EXPRESSION_ROTATION, OUTPUT_DIR / "expression"),
        (LOCATION_ROTATION, OUTPUT_DIR / "location")
    ]

    total_processed = 0
    total_rotated = 0

    for src_dir, out_dir in folders:
        if not src_dir.exists():
            continue

        images = list(src_dir.glob("*.jpg")) + list(src_dir.glob("*.png"))
        print(f"\n📁 {src_dir.name}: {len(images)}개 처리 중...")

        for i, img_path in enumerate(images, 1):
            result = auto_rotate_image(img_path, out_dir)

            if result["status"] == "rotated":
                results["rotated"].append(result)
                total_rotated += 1
            elif result["status"] == "skipped":
                results["skipped"].append(result)
            else:
                results["errors"].append(result)

            total_processed += 1

            if i % 50 == 0:
                print(f"   처리 중... {i}/{len(images)}")

    print(f"\n✅ 처리 완료: {total_processed}개")
    print(f"   회전됨: {total_rotated}개")
    print(f"   스킵: {len(results['skipped'])}개")
    print(f"   오류: {len(results['errors'])}개")

    return total_rotated


def print_summary():
    """결과 요약 출력"""
    print("\n" + "=" * 60)
    print("📊 회전 처리 결과")
    print("=" * 60)

    # 회전된 이미지 분포
    if results["rotated"]:
        rotation_counts = {}
        for item in results["rotated"]:
            angle = item.get("rotation", 0)
            rotation_counts[angle] = rotation_counts.get(angle, 0) + 1

        print("\n회전 각도별 분포:")
        for angle, count in sorted(rotation_counts.items()):
            print(f"   {angle}도: {count}개")

    # 출력 폴더 확인
    print(f"\n📁 회전된 이미지 저장 위치:")
    print(f"   {OUTPUT_DIR}")

    # 각 폴더별 개수
    for subdir in OUTPUT_DIR.iterdir():
        if subdir.is_dir():
            count = len(list(subdir.glob("*.jpg")))
            print(f"   └─ {subdir.name}/: {count}개")


def save_results():
    """결과 저장"""
    results_path = OUTPUT_DIR / "rotation_results.json"
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(results_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n📄 결과 저장: {results_path}")


if __name__ == "__main__":
    rotated_count = process_all_rotation_images()
    print_summary()
    save_results()

    print("\n" + "=" * 60)
    print(f"✅ 총 {rotated_count}개 이미지 회전 완료")
    print("=" * 60)
    print("\n💡 다음 단계: 회전된 이미지 검토 후 A등급 폴더로 이동")
