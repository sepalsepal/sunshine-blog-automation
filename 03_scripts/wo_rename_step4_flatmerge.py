#!/usr/bin/env python3
"""
WO-RENAME-001 STEP 4: Flat Merge
상태 폴더(1_cover_only, 2_body_ready 등) → contents/ 루트로 병합
기존 상태는 metadata.json에 기록
"""

import json
import shutil
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]

# 2026-02-13: 플랫 구조 - STATUS_MAP 제거
# STATUS_MAP = {
#     "1_cover_only": "cover_only",
#     "2_body_ready": "body_ready",
#     "3_approved": "approved",
#     "4_posted": "posted"
# }


def scan_all_folders():
    """모든 콘텐츠 폴더 스캔 - 2026-02-13: 플랫 구조 - contents/ 직접 스캔"""
    folders = []
    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    for item in sorted(CONTENTS_DIR.iterdir()):
        if item.is_dir():
            match = re.match(r'^(\d{3})_(.+)', item.name)
            if match:
                folders.append({
                    "path": item,
                    "name": item.name,
                    "num": int(match.group(1)),
                    "status_dir": "contents",
                    "status": "flat"  # flat structure
                })
    return folders


def main():
    print("━" * 70)
    print("WO-RENAME-001 STEP 4: Flat Merge (상태 폴더 병합)")
    print("━" * 70)

    # 1. 폴더 스캔
    folders = scan_all_folders()
    print(f"\n[스캔 결과] {len(folders)}개 폴더")

    # 상태별 집계
    by_status = {}
    for f in folders:
        status = f["status_dir"]
        by_status[status] = by_status.get(status, 0) + 1

    for status, count in by_status.items():
        print(f"  {status}: {count}개")

    # 2. 번호 충돌 검사
    nums = [f["num"] for f in folders]
    if len(nums) != len(set(nums)):
        duplicates = [n for n in nums if nums.count(n) > 1]
        print(f"\n⚠️ 번호 충돌 발견: {set(duplicates)}")
        print("  병합 중단 - 충돌 해결 필요")
        return False

    print(f"\n✅ 번호 충돌 없음")

    # 3. Dry-run 결과 표시
    print(f"\n[Dry-run] 이동 계획 (처음 10건)")
    print(f"  현재 위치 → 이동 후 위치")
    print(f"  " + "─" * 60)
    for f in folders[:10]:
        old_path = f["path"].relative_to(PROJECT_ROOT)
        new_path = f"contents/{f['name']}"
        print(f"  {old_path}")
        print(f"    → {new_path}")
        print(f"    (status: {f['status']})")

    # 4. 실제 이동 실행
    print(f"\n[실행] 폴더 이동 중...")
    moved = 0
    errors = []

    for f in folders:
        try:
            # 새 위치
            new_path = CONTENTS_DIR / f["name"]

            # 이미 존재하면 스킵
            if new_path.exists():
                print(f"  ⚠️ 이미 존재: {f['name']}")
                continue

            # 이동 (실제로는 복사 후 원본 삭제)
            shutil.move(str(f["path"]), str(new_path))

            # metadata.json 생성/업데이트
            metadata_path = new_path / "metadata.json"
            metadata = {}
            if metadata_path.exists():
                with open(metadata_path, "r", encoding="utf-8") as mf:
                    metadata = json.load(mf)

            metadata["content_id"] = f["num"]
            metadata["previous_status_dir"] = f["status_dir"]
            metadata["status"] = f["status"]
            metadata["migrated_at"] = datetime.now().isoformat()
            metadata["work_order"] = "WO-RENAME-001"

            with open(metadata_path, "w", encoding="utf-8") as mf:
                json.dump(metadata, mf, ensure_ascii=False, indent=2)

            moved += 1

        except Exception as e:
            errors.append({"folder": f["name"], "error": str(e)})

    # 5. 빈 상태 폴더 정리 (선택적)
    print(f"\n[정리] 빈 상태 폴더 확인")
    for status_dir in STATUS_DIRS:
        status_path = CONTENTS_DIR / status_dir
        if status_path.exists():
            remaining = list(status_path.iterdir())
            if not remaining:
                print(f"  {status_dir}: 비어있음 (삭제 가능)")
            else:
                print(f"  {status_dir}: {len(remaining)}개 남음")

    # 6. 결과 출력
    print("\n" + "━" * 70)
    print("STEP 4 완료")
    print("━" * 70)
    print(f"  이동 완료: {moved}개")
    print(f"  오류: {len(errors)}개")

    if errors:
        print(f"\n[오류 목록]")
        for e in errors:
            print(f"  {e['folder']}: {e['error']}")

    return {
        "moved": moved,
        "errors": errors
    }


if __name__ == "__main__":
    main()
