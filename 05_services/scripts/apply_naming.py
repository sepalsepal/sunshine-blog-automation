#!/usr/bin/env python3
"""
A등급 이미지 네이밍 변경 스크립트 (김감독 승인)

naming_map.json 기반으로 파일명 일괄 변경
"""

import json
import shutil
from pathlib import Path

# 경로 설정
BASE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/content/images/sunshine/01_usable")
EXPRESSION_DIR = BASE_DIR / "expression"
LOCATION_DIR = BASE_DIR / "location"
NAMING_MAP_FILE = BASE_DIR / "naming_map.json"

def apply_naming():
    """네이밍 변경 적용"""
    print("=" * 60)
    print("🏷️ A등급 이미지 네이밍 변경 시작")
    print("=" * 60)

    # 네이밍 맵 로드
    with open(NAMING_MAP_FILE, "r", encoding="utf-8") as f:
        naming_map = json.load(f)

    print(f"\n변경 대상: {len(naming_map)}개 파일")

    renamed_count = 0
    errors = []

    for old_name, new_name in naming_map.items():
        # 파일 찾기 (expression 또는 location)
        old_path = None
        if (EXPRESSION_DIR / old_name).exists():
            old_path = EXPRESSION_DIR / old_name
            new_path = EXPRESSION_DIR / new_name
        elif (LOCATION_DIR / old_name).exists():
            old_path = LOCATION_DIR / old_name
            new_path = LOCATION_DIR / new_name

        if old_path is None:
            errors.append(f"파일 없음: {old_name}")
            continue

        try:
            old_path.rename(new_path)
            renamed_count += 1

            if renamed_count <= 10 or renamed_count % 100 == 0:
                print(f"   ✓ {old_name} → {new_name}")
        except Exception as e:
            errors.append(f"{old_name}: {str(e)}")

    print(f"\n✅ 변경 완료: {renamed_count}개")

    if errors:
        print(f"⚠️  오류: {len(errors)}건")
        for err in errors[:5]:
            print(f"   - {err}")

    return renamed_count, errors


def verify_result():
    """변경 결과 확인"""
    print("\n" + "-" * 60)
    print("📊 변경 결과 확인")
    print("-" * 60)

    # expression 폴더
    exp_files = list(EXPRESSION_DIR.glob("*.jpg"))
    exp_new_format = [f for f in exp_files if f.name.count("_") >= 4]

    # location 폴더
    loc_files = list(LOCATION_DIR.glob("*.jpg"))
    loc_new_format = [f for f in loc_files if f.name.count("_") >= 4]

    print(f"\nexpression 폴더:")
    print(f"   전체: {len(exp_files)}개")
    print(f"   신규 네이밍: {len(exp_new_format)}개")

    print(f"\nlocation 폴더:")
    print(f"   전체: {len(loc_files)}개")
    print(f"   신규 네이밍: {len(loc_new_format)}개")

    # 샘플 출력
    print("\n📝 샘플 파일명 (처음 5개):")
    for f in sorted(exp_files)[:5]:
        print(f"   {f.name}")


if __name__ == "__main__":
    renamed, errors = apply_naming()
    verify_result()

    print("\n" + "=" * 60)
    print("✅ 네이밍 변경 완료")
    print("=" * 60)
