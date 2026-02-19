#!/usr/bin/env python3
"""
🧹 콘텐츠 폴더 내부 정리 스크립트
STEP 3: 폴더 내부 정리

정리 항목:
1. archive/ 폴더 내 파일 정리 (이미 archive에 있으면 유지)
2. temp/ 폴더 존재 시 archive/로 이동
3. _bg.png, *_metadata.json 등 부수 파일 정리
4. 표준 파일명 확인 ({name}_00.png ~ {name}_03.png)
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

# 프로젝트 루트
ROOT = Path(__file__).parent.parent
CONTENTS_DIR = ROOT / "01_contents"

# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# 상태 폴더
# STATUS_DIRS = [
#     CONTENTS_DIR / "1_cover_only",
#     CONTENTS_DIR / "2_body_ready",
#     CONTENTS_DIR / "3_approved",
# ]


def cleanup_folder(folder: Path, dry_run: bool = True) -> dict:
    """개별 폴더 정리"""
    result = {
        "folder": folder.name,
        "temp_moved": 0,
        "bg_archived": 0,
        "meta_archived": 0,
        "errors": [],
    }

    # archive 폴더 확인/생성
    archive_dir = folder / "archive"
    if not dry_run:
        archive_dir.mkdir(exist_ok=True)

    # 1. temp/ 폴더 내용을 archive/로 이동
    temp_dir = folder / "temp"
    if temp_dir.exists() and temp_dir.is_dir():
        for f in temp_dir.iterdir():
            if dry_run:
                print(f"    [DRY] temp→archive: {f.name}")
            else:
                try:
                    dst = archive_dir / f.name
                    if dst.exists():
                        dst = archive_dir / f"{f.stem}_{datetime.now().strftime('%H%M%S')}{f.suffix}"
                    shutil.move(str(f), str(dst))
                    print(f"    ✅ temp→archive: {f.name}")
                except Exception as e:
                    result["errors"].append(str(e))
            result["temp_moved"] += 1

        # temp 폴더 삭제 (비어있을 때)
        if not dry_run:
            try:
                temp_dir.rmdir()
                print(f"    🗑️ temp/ 폴더 삭제")
            except OSError:
                pass  # 폴더가 비어있지 않음

    # 2. *_bg.png 파일 → archive/
    for f in folder.glob("*_bg.png"):
        if f.parent == folder:  # 최상위에 있는 경우만
            if dry_run:
                print(f"    [DRY] bg→archive: {f.name}")
            else:
                try:
                    dst = archive_dir / f.name
                    shutil.move(str(f), str(dst))
                    print(f"    ✅ bg→archive: {f.name}")
                except Exception as e:
                    result["errors"].append(str(e))
            result["bg_archived"] += 1

    # 3. *_metadata.json 파일 (metadata.json 제외) → archive/
    for f in folder.glob("*_metadata.json"):
        if f.name != "metadata.json" and f.parent == folder:
            if dry_run:
                print(f"    [DRY] meta→archive: {f.name}")
            else:
                try:
                    dst = archive_dir / f.name
                    shutil.move(str(f), str(dst))
                    print(f"    ✅ meta→archive: {f.name}")
                except Exception as e:
                    result["errors"].append(str(e))
            result["meta_archived"] += 1

    return result


def cleanup_all(dry_run: bool = True) -> dict:
    """모든 폴더 정리"""
    total = {
        "folders_processed": 0,
        "temp_moved": 0,
        "bg_archived": 0,
        "meta_archived": 0,
        "errors": [],
    }

    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    print(f"\n📁 contents/")

    for folder in sorted(CONTENTS_DIR.iterdir()):
            if not folder.is_dir() or folder.name.startswith("."):
                continue

            # 정리 필요 여부 확인
            needs_cleanup = False
            if (folder / "temp").exists():
                needs_cleanup = True
            if list(folder.glob("*_bg.png")):
                needs_cleanup = True
            if [f for f in folder.glob("*_metadata.json") if f.name != "metadata.json"]:
                needs_cleanup = True

            if needs_cleanup:
                print(f"  🧹 {folder.name}")
                result = cleanup_folder(folder, dry_run)
                total["folders_processed"] += 1
                total["temp_moved"] += result["temp_moved"]
                total["bg_archived"] += result["bg_archived"]
                total["meta_archived"] += result["meta_archived"]
                total["errors"].extend(result["errors"])

    return total


def main():
    print("=" * 60)
    print("🧹 CONTENTS 폴더 내부 정리")
    print("=" * 60)

    # 1. 드라이런 먼저
    print("\n🧪 DRY RUN (정리 미리보기)")
    print("-" * 60)
    total = cleanup_all(dry_run=True)

    print("\n" + "-" * 60)
    print(f"📊 요약:")
    print(f"  - 정리 대상 폴더: {total['folders_processed']}개")
    print(f"  - temp → archive: {total['temp_moved']}개 파일")
    print(f"  - *_bg.png → archive: {total['bg_archived']}개 파일")
    print(f"  - *_metadata.json → archive: {total['meta_archived']}개 파일")

    if total["folders_processed"] == 0:
        print("\n✅ 정리할 항목이 없습니다!")
        return

    # 2. 사용자 확인
    print("\n" + "=" * 60)
    response = input("🔄 실제로 정리하시겠습니까? (y/N): ").strip().lower()

    if response == "y":
        print("\n🧹 정리 실행 중...")
        total = cleanup_all(dry_run=False)
        print(f"\n✅ 완료!")
        print(f"  - 폴더: {total['folders_processed']}개")
        print(f"  - 이동된 파일: {total['temp_moved'] + total['bg_archived'] + total['meta_archived']}개")
        if total["errors"]:
            print(f"  - 오류: {len(total['errors'])}개")
    else:
        print("❌ 취소됨")


if __name__ == "__main__":
    main()
