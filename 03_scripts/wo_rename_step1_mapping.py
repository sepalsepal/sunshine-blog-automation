#!/usr/bin/env python3
"""
WO-RENAME-001 STEP 1: 3-way ID 매핑 테이블 생성
- food_data.json 키
- 폴더 번호
- (Notion ID는 별도 확인 필요)
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
    print("━" * 70)
    print("WO-RENAME-001 STEP 1: 3-way ID 매핑 테이블")
    print("━" * 70)

    # 1. food_data.json 로드
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    food_data_map = {}
    for key, value in food_data.items():
        food_data_map[int(key)] = {
            "name": value.get("name", ""),
            "english_name": value.get("english_name", ""),
            "safety": value.get("safety", "")
        }

    # 2. 폴더 스캔 - 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    folder_map = {}
    for item in CONTENTS_DIR.iterdir():
        if not item.is_dir():
            continue
        match = re.match(r'^(\d{3})_(.+)', item.name)
        if match:
            num = int(match.group(1))
            food_en = match.group(2)
            folder_map[num] = {
                "folder_name": item.name,
                "food_en": food_en,
                "status": "contents",  # flat structure
                "path": str(item)
            }

    # 3. 매핑 테이블 생성
    all_nums = sorted(set(food_data_map.keys()) | set(folder_map.keys()))

    mapping_results = []
    inconsistencies = []

    for num in all_nums:
        fd = food_data_map.get(num)
        folder = folder_map.get(num)

        row = {
            "num": num,
            "food_data_name": fd["name"] if fd else "-",
            "food_data_en": fd["english_name"] if fd else "-",
            "safety": fd["safety"] if fd else "-",
            "folder_name": folder["folder_name"] if folder else "-",
            "folder_food_en": folder["food_en"] if folder else "-",
            "status": folder["status"] if folder else "-",
            "in_food_data": fd is not None,
            "in_folder": folder is not None,
        }

        # 영문명 비교 (불일치 감지)
        if fd and folder:
            fd_en = fd["english_name"].lower().replace("_", "")
            # 폴더명에서 한글 제거하고 비교
            folder_en = re.sub(r'_[가-힣]+$', '', folder["food_en"]).lower().replace("_", "")
            if fd_en != folder_en and not folder_en.startswith(fd_en.split("_")[0]):
                row["mismatch"] = True
                inconsistencies.append(row)
            else:
                row["mismatch"] = False
        else:
            row["mismatch"] = None

        mapping_results.append(row)

    # 4. 통계 출력
    total = len(mapping_results)
    both = [r for r in mapping_results if r["in_food_data"] and r["in_folder"]]
    food_only = [r for r in mapping_results if r["in_food_data"] and not r["in_folder"]]
    folder_only = [r for r in mapping_results if not r["in_food_data"] and r["in_folder"]]

    print(f"\n[통계]")
    print(f"  전체 고유 번호: {total}개")
    print(f"  양쪽 존재: {len(both)}개")
    print(f"  food_data만: {len(food_only)}개")
    print(f"  폴더만: {len(folder_only)}개")

    # 5. 불일치 항목 (영문명 mismatch)
    mismatched = [r for r in mapping_results if r.get("mismatch") is True]
    print(f"  영문명 불일치: {len(mismatched)}개")

    # 6. food_data만 있는 항목 (폴더 생성 필요)
    if food_only:
        print(f"\n[food_data만 있는 항목 - 폴더 없음] ({len(food_only)}건)")
        for r in food_only:
            print(f"  #{r['num']:03d} {r['food_data_name']} ({r['food_data_en']})")

    # 7. 폴더만 있는 항목 (food_data 추가 필요)
    if folder_only:
        print(f"\n[폴더만 있는 항목 - food_data 없음] ({len(folder_only)}건)")
        for r in folder_only:
            print(f"  #{r['num']:03d} {r['folder_food_en']} ({r['status']})")

    # 8. 영문명 불일치 항목
    if mismatched:
        print(f"\n[⚠️ 영문명 불일치 항목] ({len(mismatched)}건)")
        for r in mismatched:
            print(f"  #{r['num']:03d}: food_data='{r['food_data_en']}' vs folder='{r['folder_food_en']}'")

    # 9. 매핑 테이블 CSV 저장
    csv_path = PROJECT_ROOT / "config" / "id_mapping_table.csv"
    with open(csv_path, "w", encoding="utf-8") as f:
        f.write("num,food_data_name,food_data_en,safety,folder_name,status,in_food_data,in_folder,mismatch\n")
        for r in mapping_results:
            f.write(f"{r['num']},{r['food_data_name']},{r['food_data_en']},{r['safety']},{r['folder_name']},{r['status']},{r['in_food_data']},{r['in_folder']},{r.get('mismatch', '')}\n")

    print(f"\n[CSV 저장됨] {csv_path}")

    # 10. 결과 요약
    print("\n" + "━" * 70)
    print("STEP 1 결과 요약")
    print("━" * 70)
    if food_only or folder_only or mismatched:
        print("⚠️ 불일치 발견됨 - PD님 확인 필요")
        print(f"  - food_data만 있는 항목: {len(food_only)}건")
        print(f"  - 폴더만 있는 항목: {len(folder_only)}건")
        print(f"  - 영문명 불일치: {len(mismatched)}건")
    else:
        print("✅ 모든 항목 정상 매핑됨")

    # 11. JSON 저장 (다음 단계용)
    json_path = PROJECT_ROOT / "config" / "id_mapping_table.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(mapping_results, f, ensure_ascii=False, indent=2)
    print(f"[JSON 저장됨] {json_path}")

    return {
        "total": total,
        "both": len(both),
        "food_only": len(food_only),
        "folder_only": len(folder_only),
        "mismatched": len(mismatched),
        "food_only_list": food_only,
        "folder_only_list": folder_only,
        "mismatched_list": mismatched
    }


if __name__ == "__main__":
    main()
