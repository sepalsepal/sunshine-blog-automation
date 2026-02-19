#!/usr/bin/env python3
"""
audit_number_system.py - WO-FREEZE-001 조사 A
번호 체계 정합성 검사
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]


def main():
    print("━" * 60)
    print("조사 A: 번호 체계 정합성")
    print("━" * 60)

    # 1. food_data.json 로드
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    food_data_nums = {}
    for key, value in food_data.items():
        food_data_nums[int(key)] = value.get("name", "")

    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    # 2. 폴더 스캔
    folder_nums = {}
    for item in CONTENTS_DIR.iterdir():
        if not item.is_dir():
            continue
        match = re.match(r'^(\d{3})_([a-z_]+)', item.name)
        if match:
            num = int(match.group(1))
            food_en = match.group(2)
            folder_nums[num] = {"food_en": food_en, "path": item.name, "status": "flat"}

    # 3. 비교
    all_nums = sorted(set(food_data_nums.keys()) | set(folder_nums.keys()))

    matched = []
    mismatched = []
    food_data_only = []
    folder_only = []

    for num in all_nums:
        in_food = num in food_data_nums
        in_folder = num in folder_nums

        if in_food and in_folder:
            matched.append(num)
        elif in_food and not in_folder:
            food_data_only.append(num)
        elif not in_food and in_folder:
            folder_only.append(num)

    # 4. 결과 출력
    print(f"\n전체 번호: {len(all_nums)}개")
    print(f"정상 일치: {len(matched)}건")
    print(f"불일치: {len(mismatched)}건")
    print(f"food_data에만 있음: {len(food_data_only)}건")
    print(f"폴더에만 있음: {len(folder_only)}건")

    if food_data_only:
        print(f"\n[food_data에만 있는 항목] ({len(food_data_only)}건)")
        for num in food_data_only[:20]:
            print(f"  #{num:03d} {food_data_nums[num]}")
        if len(food_data_only) > 20:
            print(f"  ... 외 {len(food_data_only)-20}건")

    if folder_only:
        print(f"\n[폴더에만 있는 항목] ({len(folder_only)}건)")
        for num in folder_only:
            info = folder_nums[num]
            print(f"  #{num:03d} {info['food_en']} ({info['status']})")

    # 5. 상세 비교표 (처음 30개)
    print(f"\n[비교표 샘플 (처음 30건)]")
    print(f"| # | food_data | 폴더 | 일치 |")
    print(f"|---|-----------|------|------|")
    for num in sorted(all_nums)[:30]:
        fd_name = food_data_nums.get(num, "-")
        folder_name = folder_nums.get(num, {}).get("food_en", "-")
        match_status = "✅" if num in matched else "❌"
        print(f"| {num:03d} | {fd_name[:10]:<10} | {folder_name[:10]:<10} | {match_status} |")

    return {
        "matched": len(matched),
        "food_data_only": food_data_only,
        "folder_only": folder_only
    }


if __name__ == "__main__":
    main()
