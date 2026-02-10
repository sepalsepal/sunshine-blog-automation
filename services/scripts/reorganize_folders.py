#!/usr/bin/env python3
"""
폴더 구조 개선 스크립트 (김부장 승인)

1. A/B/C 레벨 폴더 정리
2. expression 세부폴더 생성 (happy/curious/calm)
3. location 세부폴더 생성 (outdoor)
4. 빈 action 폴더 삭제
"""

import os
import shutil
from pathlib import Path
from collections import defaultdict

# 경로 설정
BASE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/content/images/sunshine/01_usable")

def create_new_structure():
    """새 폴더 구조 생성"""
    print("=" * 60)
    print("📁 폴더 구조 개선 시작")
    print("=" * 60)

    # 1. 새 폴더 구조 생성
    new_folders = [
        "grade_A/expression/happy",
        "grade_A/expression/curious",
        "grade_A/expression/calm",
        "grade_A/location/outdoor",
        "grade_B/needs_rotation",
        "grade_B/low_quality",
        "grade_C/eating_action",
        "grade_C/puppy",
        "grade_C/rejected",
        "_archive/work_files",
    ]

    print("\n📂 새 폴더 구조 생성 중...")
    for folder in new_folders:
        folder_path = BASE_DIR / folder
        folder_path.mkdir(parents=True, exist_ok=True)
        print(f"   ✓ {folder}")

    return True


def move_a_grade_images():
    """A등급 이미지를 세부 폴더로 이동"""
    print("\n" + "-" * 60)
    print("📦 A등급 이미지 세부 분류 중...")

    expression_dir = BASE_DIR / "expression"
    location_dir = BASE_DIR / "location"

    moved_count = defaultdict(int)

    # expression 폴더 이미지 분류
    if expression_dir.exists():
        for img in expression_dir.glob("*.jpg"):
            filename = img.name.lower()

            # 표정별 분류
            if "happy" in filename:
                dest = BASE_DIR / "grade_A/expression/happy" / img.name
                category = "happy"
            elif "curious" in filename:
                dest = BASE_DIR / "grade_A/expression/curious" / img.name
                category = "curious"
            elif "calm" in filename:
                dest = BASE_DIR / "grade_A/expression/calm" / img.name
                category = "calm"
            else:
                dest = BASE_DIR / "grade_A/expression/happy" / img.name  # 기본값
                category = "happy"

            shutil.move(str(img), str(dest))
            moved_count[f"expression/{category}"] += 1

    # location 폴더 이미지 분류
    if location_dir.exists():
        for img in location_dir.glob("*.jpg"):
            dest = BASE_DIR / "grade_A/location/outdoor" / img.name
            shutil.move(str(img), str(dest))
            moved_count["location/outdoor"] += 1

    print("   A등급 이동 완료:")
    for category, count in sorted(moved_count.items()):
        print(f"      {category}: {count}개")

    return sum(moved_count.values())


def move_b_grade_images():
    """B등급 이미지 정리"""
    print("\n" + "-" * 60)
    print("📦 B등급 이미지 정리 중...")

    old_b_dir = BASE_DIR / "grade_B_80_89"
    moved_count = 0

    if old_b_dir.exists():
        # needs_rotation 이동
        for subdir in ["expression_rotation", "location_rotation"]:
            src_dir = old_b_dir / subdir
            if src_dir.exists():
                for img in src_dir.glob("*.jpg"):
                    dest = BASE_DIR / "grade_B/needs_rotation" / img.name
                    shutil.move(str(img), str(dest))
                    moved_count += 1

        # low_quality 이동
        low_q_dir = old_b_dir / "low_quality"
        if low_q_dir.exists():
            for img in low_q_dir.glob("*.jpg"):
                dest = BASE_DIR / "grade_B/low_quality" / img.name
                shutil.move(str(img), str(dest))
                moved_count += 1

        # 기존 expression/location 이동
        for subdir in ["expression", "location"]:
            src_dir = old_b_dir / subdir
            if src_dir.exists():
                for img in src_dir.glob("*.jpg"):
                    dest = BASE_DIR / "grade_B/needs_rotation" / img.name
                    shutil.move(str(img), str(dest))
                    moved_count += 1

    print(f"   B등급 이동 완료: {moved_count}개")
    return moved_count


def move_c_grade_images():
    """C등급 이미지 정리"""
    print("\n" + "-" * 60)
    print("📦 C등급 이미지 정리 중...")

    old_c_dir = BASE_DIR / "grade_C_under_80"
    puppy_dir = BASE_DIR / "puppy_removed"
    moved_count = 0

    # 기존 C등급
    if old_c_dir.exists():
        # action (eating) 이동
        action_dir = old_c_dir / "action"
        if action_dir.exists():
            for img in action_dir.glob("*.jpg"):
                dest = BASE_DIR / "grade_C/eating_action" / img.name
                shutil.move(str(img), str(dest))
                moved_count += 1

        # 기타 C등급
        for subdir in ["expression", "location"]:
            src_dir = old_c_dir / subdir
            if src_dir.exists():
                for img in src_dir.glob("*.jpg"):
                    dest = BASE_DIR / "grade_C/rejected" / img.name
                    shutil.move(str(img), str(dest))
                    moved_count += 1

    # 퍼피 이동
    if puppy_dir.exists():
        for subdir in puppy_dir.iterdir():
            if subdir.is_dir():
                for img in subdir.glob("*.jpg"):
                    dest = BASE_DIR / "grade_C/puppy" / img.name
                    shutil.move(str(img), str(dest))
                    moved_count += 1

    print(f"   C등급 이동 완료: {moved_count}개")
    return moved_count


def archive_work_files():
    """작업 파일 아카이브"""
    print("\n" + "-" * 60)
    print("📦 작업 파일 아카이브 중...")

    work_files = [
        "a_grade_categories.json",
        "a_plus_images.txt",
        "classification_report.json",
        "detailed_review_results.json",
        "naming_map.json",
        "puppy_removal_list.txt",
        "review_batches.json",
        "final_team_evaluation.md",
    ]

    archive_dir = BASE_DIR / "_archive/work_files"
    moved_count = 0

    for filename in work_files:
        src = BASE_DIR / filename
        if src.exists():
            dest = archive_dir / filename
            shutil.move(str(src), str(dest))
            moved_count += 1
            print(f"   ✓ {filename}")

    print(f"   아카이브 완료: {moved_count}개 파일")
    return moved_count


def cleanup_empty_folders():
    """빈 폴더 정리"""
    print("\n" + "-" * 60)
    print("🗑️ 빈 폴더 정리 중...")

    folders_to_remove = [
        "action",
        "expression",
        "location",
        "grade_B_80_89",
        "grade_C_under_80",
        "puppy_removed",
        "puppy_suspect",
        "rotated_to_A",
        "temp",
    ]

    removed_count = 0
    for folder in folders_to_remove:
        folder_path = BASE_DIR / folder
        if folder_path.exists():
            try:
                shutil.rmtree(folder_path)
                print(f"   ✓ 삭제: {folder}/")
                removed_count += 1
            except Exception as e:
                print(f"   ⚠️ 삭제 실패: {folder}/ - {e}")

    print(f"   정리 완료: {removed_count}개 폴더 삭제")
    return removed_count


def print_final_structure():
    """최종 구조 출력"""
    print("\n" + "=" * 60)
    print("📊 최종 폴더 구조")
    print("=" * 60)

    def count_images(path):
        if path.exists():
            return len(list(path.glob("*.jpg")))
        return 0

    structure = {
        "grade_A/expression/happy": count_images(BASE_DIR / "grade_A/expression/happy"),
        "grade_A/expression/curious": count_images(BASE_DIR / "grade_A/expression/curious"),
        "grade_A/expression/calm": count_images(BASE_DIR / "grade_A/expression/calm"),
        "grade_A/location/outdoor": count_images(BASE_DIR / "grade_A/location/outdoor"),
        "grade_B/needs_rotation": count_images(BASE_DIR / "grade_B/needs_rotation"),
        "grade_B/low_quality": count_images(BASE_DIR / "grade_B/low_quality"),
        "grade_C/eating_action": count_images(BASE_DIR / "grade_C/eating_action"),
        "grade_C/puppy": count_images(BASE_DIR / "grade_C/puppy"),
        "grade_C/rejected": count_images(BASE_DIR / "grade_C/rejected"),
    }

    total_a = 0
    total_b = 0
    total_c = 0

    print("\n📁 grade_A/ (캐러셀 본문 사용 가능)")
    for path, count in structure.items():
        if path.startswith("grade_A"):
            print(f"   └─ {path.replace('grade_A/', '')}: {count}개")
            total_a += count
    print(f"   소계: {total_a}개")

    print("\n📁 grade_B/ (수정 후 사용)")
    for path, count in structure.items():
        if path.startswith("grade_B"):
            print(f"   └─ {path.replace('grade_B/', '')}: {count}개")
            total_b += count
    print(f"   소계: {total_b}개")

    print("\n📁 grade_C/ (사용 불가)")
    for path, count in structure.items():
        if path.startswith("grade_C"):
            print(f"   └─ {path.replace('grade_C/', '')}: {count}개")
            total_c += count
    print(f"   소계: {total_c}개")

    print(f"\n📊 총계: {total_a + total_b + total_c}개")
    print(f"   A등급: {total_a}개 ({total_a*100/(total_a+total_b+total_c):.1f}%)")
    print(f"   B등급: {total_b}개 ({total_b*100/(total_a+total_b+total_c):.1f}%)")
    print(f"   C등급: {total_c}개 ({total_c*100/(total_a+total_b+total_c):.1f}%)")


if __name__ == "__main__":
    create_new_structure()
    move_a_grade_images()
    move_b_grade_images()
    move_c_grade_images()
    archive_work_files()
    cleanup_empty_folders()
    print_final_structure()

    print("\n" + "=" * 60)
    print("✅ 폴더 구조 개선 완료!")
    print("=" * 60)
