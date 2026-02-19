#!/usr/bin/env python3
"""
WO-RENAME-001 STEP 8: 최종 무결성 검증
"""

import json
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
BACKUP_DIR = PROJECT_ROOT / "backups" / "wo_rename_001_20260213_171742"


def main():
    print("━" * 70)
    print("WO-RENAME-001 STEP 8: 최종 무결성 검증")
    print("━" * 70)

    # food_data 로드
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    # 1. 폴더 수 확인
    folders = [f for f in CONTENTS_DIR.iterdir() if f.is_dir() and re.match(r'^\d{3}_', f.name)]
    print(f"\n[1] 폴더 수: {len(folders)}개")

    # 2. food_data 매핑 확인
    fd_nums = set(int(k) for k in food_data.keys())
    folder_nums = set(int(re.match(r'^(\d{3})_', f.name).group(1)) for f in folders)

    both = fd_nums & folder_nums
    fd_only = fd_nums - folder_nums
    folder_only = folder_nums - fd_nums

    print(f"\n[2] ID 매핑")
    print(f"  양쪽 일치: {len(both)}개")
    print(f"  food_data만: {len(fd_only)}개 {sorted(fd_only) if fd_only else ''}")
    print(f"  폴더만: {len(folder_only)}개 {sorted(folder_only) if folder_only else ''}")

    # 3. metadata.json 검증
    print(f"\n[3] metadata.json 검증")
    meta_ok = 0
    meta_missing = 0
    for folder in folders:
        meta_path = folder / "metadata.json"
        if meta_path.exists():
            meta_ok += 1
        else:
            meta_missing += 1

    print(f"  존재: {meta_ok}개")
    print(f"  누락: {meta_missing}개")

    # 4. PascalCase 검증
    print(f"\n[4] PascalCase 검증")
    pascal_ok = 0
    for folder in folders:
        if re.match(r'^\d{3}_[A-Z][A-Za-z0-9]*$', folder.name):
            pascal_ok += 1

    print(f"  준수: {pascal_ok}/{len(folders)}개")

    # 5. Safety 분포
    print(f"\n[5] Safety 분포")
    safety_dist = {}
    for folder in folders:
        num = int(re.match(r'^(\d{3})_', folder.name).group(1))
        fd = food_data.get(str(num), {})
        safety = fd.get("safety", "UNKNOWN")
        safety_dist[safety] = safety_dist.get(safety, 0) + 1

    for level, count in sorted(safety_dist.items()):
        print(f"  {level}: {count}개")

    # 6. 상태별 분포 (metadata 기준)
    print(f"\n[6] 상태별 분포 (이전 status)")
    status_dist = {}
    for folder in folders:
        meta_path = folder / "metadata.json"
        if meta_path.exists():
            with open(meta_path, "r", encoding="utf-8") as f:
                meta = json.load(f)
            status = meta.get("status", "unknown")
            status_dist[status] = status_dist.get(status, 0) + 1

    for status, count in sorted(status_dist.items()):
        print(f"  {status}: {count}개")

    # 결과 요약
    print("\n" + "━" * 70)
    print("WO-RENAME-001 최종 결과")
    print("━" * 70)

    all_pass = True

    checks = [
        ("폴더 수", len(folders) == 165, f"{len(folders)}/165"),
        ("ID 매핑", len(folder_only) <= 8, f"불일치 {len(folder_only)}개"),
        ("metadata.json", meta_ok == len(folders), f"{meta_ok}/{len(folders)}"),
        ("PascalCase", pascal_ok == len(folders), f"{pascal_ok}/{len(folders)}"),
    ]

    for name, passed, detail in checks:
        status = "✅" if passed else "❌"
        print(f"  {status} {name}: {detail}")
        if not passed:
            all_pass = False

    if all_pass:
        print(f"\n✅ WO-RENAME-001 완료")
    else:
        print(f"\n⚠️ 일부 항목 확인 필요")

    # 실행 로그 저장
    log = {
        "work_order": "WO-RENAME-001",
        "completed_at": datetime.now().isoformat(),
        "results": {
            "total_folders": len(folders),
            "id_mapping": {"both": len(both), "fd_only": len(fd_only), "folder_only": len(folder_only)},
            "metadata_ok": meta_ok,
            "pascal_ok": pascal_ok,
            "safety_distribution": safety_dist,
            "status_distribution": status_dist
        },
        "all_pass": all_pass
    }

    log_path = PROJECT_ROOT / "config" / "logs" / f"wo_rename_001_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(log_path, "w", encoding="utf-8") as f:
        json.dump(log, f, ensure_ascii=False, indent=2)

    print(f"\n[로그 저장] {log_path}")

    return all_pass


if __name__ == "__main__":
    main()
