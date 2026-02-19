#!/usr/bin/env python3
"""
이미지 재분류 스크립트 (김감독 지시)

상세 검토 결과를 바탕으로 회전 필요 이미지를 B등급 폴더로 이동
"""

import json
import shutil
from pathlib import Path

# 경로 설정
BASE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/content/images/sunshine/01_usable")
GRADE_B_DIR = BASE_DIR / "grade_B_80_89"
RESULTS_FILE = BASE_DIR / "detailed_review_results.json"

def reclassify_to_grade_b():
    """회전 필요 이미지를 B등급으로 재분류"""
    print("=" * 60)
    print("🔄 이미지 재분류 시작 (A → B)")
    print("=" * 60)

    # 결과 파일 로드
    with open(RESULTS_FILE, "r", encoding="utf-8") as f:
        results = json.load(f)

    reclassify_list = results["categories"]["reclassify_B"]
    print(f"\n재분류 대상: {len(reclassify_list)}개")

    # B등급 폴더 준비
    b_expression = GRADE_B_DIR / "expression_rotation"
    b_location = GRADE_B_DIR / "location_rotation"
    b_expression.mkdir(parents=True, exist_ok=True)
    b_location.mkdir(parents=True, exist_ok=True)

    moved_count = 0
    errors = []

    for item in reclassify_list:
        src_path = Path(item["path"])

        if not src_path.exists():
            errors.append(f"파일 없음: {src_path.name}")
            continue

        # 대상 폴더 결정
        if "outdoor" in item["filename"]:
            dest_dir = b_location
        else:
            dest_dir = b_expression

        dest_path = dest_dir / src_path.name

        try:
            shutil.move(str(src_path), str(dest_path))
            moved_count += 1
        except Exception as e:
            errors.append(f"{src_path.name}: {str(e)}")

    print(f"\n✅ 이동 완료: {moved_count}개")
    if errors:
        print(f"⚠️  오류: {len(errors)}건")
        for err in errors[:5]:
            print(f"   - {err}")

    return moved_count, errors


def count_remaining():
    """남은 A등급 이미지 수 확인"""
    expression_dir = BASE_DIR / "expression"
    location_dir = BASE_DIR / "location"

    exp_count = len(list(expression_dir.glob("*.jpg"))) if expression_dir.exists() else 0
    loc_count = len(list(location_dir.glob("*.jpg"))) if location_dir.exists() else 0

    print(f"\n📊 남은 A등급 이미지:")
    print(f"   expression: {exp_count}개")
    print(f"   location: {loc_count}개")
    print(f"   합계: {exp_count + loc_count}개")

    return exp_count + loc_count


if __name__ == "__main__":
    moved, errors = reclassify_to_grade_b()
    remaining = count_remaining()

    print("\n" + "=" * 60)
    print("📋 재분류 완료 요약")
    print("=" * 60)
    print(f"   B등급으로 이동: {moved}개")
    print(f"   A등급 유지: {remaining}개")
    print("=" * 60)
