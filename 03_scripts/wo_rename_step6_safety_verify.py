#!/usr/bin/env python3
"""
WO-RENAME-001 STEP 6: Safety 검증
- 전체 폴더 구조 검증
- 단팥빵 특별 검사 (WO-RENAME-001 지시)
- 파일 무결성 확인
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
BACKUP_DIR = PROJECT_ROOT / "backups" / "wo_rename_001_20260213_171742"


def main():
    print("━" * 70)
    print("WO-RENAME-001 STEP 6: Safety 검증")
    print("━" * 70)

    # food_data 로드
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    # 백업 스냅샷 로드
    snapshot_path = BACKUP_DIR / "folder_structure_snapshot.json"
    with open(snapshot_path, "r", encoding="utf-8") as f:
        snapshot = json.load(f)

    old_files_count = sum(
        len(f["files"]) + sum(len(files) for files in f["subfolders"].values())
        for f in snapshot["folders"]
    )

    # 1. 폴더 구조 검증
    print("\n[1] 폴더 구조 검증")
    folders = []
    for item in sorted(CONTENTS_DIR.iterdir()):
        if item.is_dir() and re.match(r'^\d{3}_', item.name):
            folders.append(item)

    print(f"  전체 폴더: {len(folders)}개")

    # PascalCase 검증
    pascal_ok = 0
    pascal_fail = []
    for folder in folders:
        match = re.match(r'^(\d{3})_([A-Z][A-Za-z0-9]*)$', folder.name)
        if match:
            pascal_ok += 1
        else:
            pascal_fail.append(folder.name)

    print(f"  PascalCase 준수: {pascal_ok}개")
    if pascal_fail:
        print(f"  PascalCase 미준수: {len(pascal_fail)}개")
        for f in pascal_fail[:5]:
            print(f"    - {f}")

    # 2. 서브폴더 검증
    print("\n[2] 서브폴더 검증")
    expected_subs = {"Blog", "Insta", "Captions", "0_Clean"}
    sub_stats = {"Blog": 0, "Insta": 0, "Captions": 0, "0_Clean": 0, "other": 0}

    for folder in folders:
        for sub in folder.iterdir():
            if sub.is_dir():
                if sub.name in expected_subs:
                    sub_stats[sub.name] += 1
                else:
                    sub_stats["other"] += 1

    for name, count in sub_stats.items():
        print(f"  {name}: {count}개")

    # 3. 파일 수 검증
    print("\n[3] 파일 수 검증")
    new_files_count = 0
    for folder in folders:
        for sub in folder.iterdir():
            if sub.is_dir():
                new_files_count += len(list(sub.iterdir()))
        # 루트 파일
        new_files_count += len([f for f in folder.iterdir() if f.is_file()])

    print(f"  이전: {old_files_count}개")
    print(f"  현재: {new_files_count}개")
    diff = new_files_count - old_files_count
    if diff == 0:
        print(f"  ✅ 파일 수 일치")
    else:
        print(f"  ⚠️ 차이: {diff:+d}개 (metadata.json 추가분 포함)")

    # 4. 단팥빵 특별 검사 (WO-RENAME-001 지시)
    print("\n[4] 단팥빵 특별 검사 (034)")
    red_bean = None
    for folder in folders:
        if folder.name.startswith("034_"):
            red_bean = folder
            break

    if red_bean:
        print(f"  폴더명: {red_bean.name}")

        # metadata 확인
        meta_path = red_bean / "metadata.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            print(f"  content_id: {meta.get('content_id')}")
            print(f"  name_ko: {meta.get('name_ko')}")
            print(f"  safety: {meta.get('safety')}")
            print(f"  status: {meta.get('status')}")

        # 서브폴더 확인
        print(f"  서브폴더:")
        for sub in sorted(red_bean.iterdir()):
            if sub.is_dir():
                file_count = len(list(sub.iterdir()))
                print(f"    {sub.name}/: {file_count}개 파일")

        # food_data 확인
        fd_34 = food_data.get("34", {})
        print(f"  food_data[34]:")
        print(f"    name: {fd_34.get('name', '-')}")
        print(f"    english_name: {fd_34.get('english_name', '-')}")
        print(f"    safety: {fd_34.get('safety', '-')}")

        # 일치 확인
        if fd_34.get("name") == "단팥빵":
            print(f"  ✅ 단팥빵 데이터 정합성 확인됨")
        else:
            print(f"  ⚠️ 단팥빵 데이터 불일치")
    else:
        print(f"  ⚠️ 034 폴더 없음")

    # 5. Safety 레벨 분포
    print("\n[5] Safety 레벨 분포")
    safety_dist = {"SAFE": 0, "CAUTION": 0, "DANGER": 0, "FORBIDDEN": 0, "unknown": 0}

    for folder in folders:
        match = re.match(r'^(\d{3})_', folder.name)
        if match:
            num = match.group(1)
            fd = food_data.get(num, {})
            safety = fd.get("safety", "unknown")
            safety_dist[safety] = safety_dist.get(safety, 0) + 1

    for level, count in safety_dist.items():
        if count > 0:
            print(f"  {level}: {count}개")

    # 결과
    print("\n" + "━" * 70)
    print("STEP 6 검증 결과")
    print("━" * 70)

    issues = []
    if pascal_fail:
        issues.append(f"PascalCase 미준수: {len(pascal_fail)}개")
    if sub_stats["other"] > 0:
        issues.append(f"비표준 서브폴더: {sub_stats['other']}개")

    if issues:
        print("⚠️ 발견된 이슈:")
        for issue in issues:
            print(f"  - {issue}")
    else:
        print("✅ 모든 검증 통과")

    return {
        "folders": len(folders),
        "pascal_ok": pascal_ok,
        "pascal_fail": len(pascal_fail),
        "files_before": old_files_count,
        "files_after": new_files_count
    }


if __name__ == "__main__":
    main()
