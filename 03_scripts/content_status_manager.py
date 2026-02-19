#!/usr/bin/env python3
"""
📂 콘텐츠 상태 관리자 (v3 폴더 구조)
STEP 5: 상태 전환 함수

상태 흐름:
2026-02-13: 플랫 구조 - contents 직접 스캔

사용법:
    python scripts/content_status_manager.py promote <folder> - 다음 상태로 이동
    python scripts/content_status_manager.py demote <folder> - 이전 상태로 이동
    python scripts/content_status_manager.py move <folder> <status> - 특정 상태로 이동
    python scripts/content_status_manager.py status - 현황 출력
"""

import json
import shutil
from pathlib import Path
from datetime import datetime

# 프로젝트 루트
ROOT = Path(__file__).parent.parent
CONTENTS_DIR = ROOT / "01_contents"
POSTED_DIR = ROOT / "posted"

# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# 상태 폴더 (승격 순서)
# STATUS_ORDER = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]
# STATUS_DIRS = {status: CONTENTS_DIR / status for status in STATUS_ORDER}
STATUS_ORDER = []
STATUS_DIRS = {}


def find_content_by_name(name_pattern: str) -> tuple[Path, str] | tuple[None, None]:
    """폴더명 패턴으로 콘텐츠 찾기

    Args:
        name_pattern: 폴더명 일부 (예: "pasta", "028_pasta")

    Returns:
        (폴더 경로, 현재 상태) 또는 (None, None)
    """
    for status in STATUS_ORDER:
        status_dir = STATUS_DIRS[status]
        if not status_dir.exists():
            continue

        for folder in status_dir.iterdir():
            if folder.is_dir() and name_pattern in folder.name:
                return folder, status

    # v2 호환: contents/ 루트
    for folder in CONTENTS_DIR.iterdir():
        if folder.is_dir() and folder.name not in STATUS_ORDER:
            if name_pattern in folder.name:
                return folder, "root"

    return None, None


def promote_content(folder_path: Path, current_status: str) -> bool:
    """콘텐츠를 다음 상태로 승격

    Args:
        folder_path: 폴더 경로
        current_status: 현재 상태

    Returns:
        성공 여부
    """
    if current_status not in STATUS_ORDER:
        print(f"⚠️ 알 수 없는 상태: {current_status}")
        return False

    current_idx = STATUS_ORDER.index(current_status)
    if current_idx >= len(STATUS_ORDER) - 1:
        print(f"⚠️ 이미 최상위 상태: {current_status}")
        print("   → 게시 후 POSTED_DIR로 이동됩니다")
        return False

    next_status = STATUS_ORDER[current_idx + 1]
    return move_content(folder_path, next_status)


def demote_content(folder_path: Path, current_status: str) -> bool:
    """콘텐츠를 이전 상태로 강등

    Args:
        folder_path: 폴더 경로
        current_status: 현재 상태

    Returns:
        성공 여부
    """
    if current_status not in STATUS_ORDER:
        print(f"⚠️ 알 수 없는 상태: {current_status}")
        return False

    current_idx = STATUS_ORDER.index(current_status)
    if current_idx <= 0:
        print(f"⚠️ 이미 최하위 상태: {current_status}")
        return False

    prev_status = STATUS_ORDER[current_idx - 1]
    return move_content(folder_path, prev_status)


def move_content(folder_path: Path, target_status: str) -> bool:
    """콘텐츠를 특정 상태로 이동

    Args:
        folder_path: 폴더 경로
        target_status: 대상 상태

    Returns:
        성공 여부
    """
    if target_status not in STATUS_ORDER:
        print(f"❌ 유효하지 않은 상태: {target_status}")
        print(f"   가능한 상태: {', '.join(STATUS_ORDER)}")
        return False

    target_dir = STATUS_DIRS[target_status]
    target_dir.mkdir(exist_ok=True)

    dest_path = target_dir / folder_path.name

    if dest_path.exists():
        print(f"❌ 이미 존재: {dest_path}")
        return False

    try:
        shutil.move(str(folder_path), str(dest_path))
        print(f"✅ 이동: {folder_path.name}")
        print(f"   {folder_path.parent.name}/ → {target_status}/")

        # 메타데이터 업데이트
        update_metadata(dest_path, target_status)

        return True
    except Exception as e:
        print(f"❌ 이동 실패: {e}")
        return False


def update_metadata(folder_path: Path, status: str):
    """메타데이터 상태 업데이트"""
    metadata_path = folder_path / "metadata.json"

    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    else:
        metadata = {}

    # 상태 매핑
    status_map = {
        "1_cover_only": "cover_only",
        "2_body_ready": "body_ready",
        "3_approved": "approved",
        "4_posted": "posted"
    }

    metadata["status"] = status_map.get(status, status)
    metadata["status_updated_at"] = datetime.now().isoformat()

    # 3_approved로 이동 시 pd_approved = True
    if status == "3_approved":
        metadata["pd_approved"] = True
        metadata["approved_at"] = datetime.now().isoformat()

    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def get_status_summary() -> dict:
    """상태별 콘텐츠 현황"""
    summary = {}

    for status in STATUS_ORDER:
        status_dir = STATUS_DIRS[status]
        if status_dir.exists():
            folders = [f.name for f in status_dir.iterdir() if f.is_dir()]
            summary[status] = folders
        else:
            summary[status] = []

    return summary


def print_status():
    """현황 출력"""
    print("=" * 60)
    print("📊 콘텐츠 상태 현황 (v3)")
    print("=" * 60)

    summary = get_status_summary()

    for status in STATUS_ORDER:
        folders = summary[status]
        emoji = {"1_cover_only": "🔵", "2_body_ready": "🟡", "3_approved": "🟢"}
        print(f"\n{emoji.get(status, '⚪')} [{status}] ({len(folders)}개)")

        for name in folders[:5]:
            print(f"   - {name}")
        if len(folders) > 5:
            print(f"   ... 외 {len(folders) - 5}개")


def main():
    import sys

    if len(sys.argv) < 2:
        print("사용법:")
        print("  python content_status_manager.py status          - 현황 출력")
        print("  python content_status_manager.py promote <name>  - 다음 상태로 승격")
        print("  python content_status_manager.py demote <name>   - 이전 상태로 강등")
        print("  python content_status_manager.py move <name> <status> - 특정 상태로 이동")
        print("")
        print("상태 종류: 1_cover_only, 2_body_ready, 3_approved")
        return

    cmd = sys.argv[1]

    if cmd == "status":
        print_status()

    elif cmd == "promote":
        if len(sys.argv) < 3:
            print("사용법: python content_status_manager.py promote <folder_name>")
            return

        name = sys.argv[2]
        folder, status = find_content_by_name(name)
        if folder:
            promote_content(folder, status)
        else:
            print(f"❌ 폴더를 찾을 수 없음: {name}")

    elif cmd == "demote":
        if len(sys.argv) < 3:
            print("사용법: python content_status_manager.py demote <folder_name>")
            return

        name = sys.argv[2]
        folder, status = find_content_by_name(name)
        if folder:
            demote_content(folder, status)
        else:
            print(f"❌ 폴더를 찾을 수 없음: {name}")

    elif cmd == "move":
        if len(sys.argv) < 4:
            print("사용법: python content_status_manager.py move <folder_name> <status>")
            return

        name = sys.argv[2]
        target_status = sys.argv[3]
        folder, status = find_content_by_name(name)
        if folder:
            move_content(folder, target_status)
        else:
            print(f"❌ 폴더를 찾을 수 없음: {name}")

    else:
        print(f"❌ 알 수 없는 명령: {cmd}")


if __name__ == "__main__":
    main()
