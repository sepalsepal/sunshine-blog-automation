#!/usr/bin/env python3
"""
🔐 PD 봉인 운영 원칙 (2026-02-03 확정)

1. 로컬 폴더 = 상태의 결과
   - 상태의 "원인"은 metadata / Sheets / API
   - 폴더는 결과물일 뿐 판단 근거 아님

2. posted 이동은 단방향
   - posted → contents 되돌림 ❌
   - 재작업 시 새 food_id 생성

3. 동기화 우선순위
   Instagram API > Sheets > Local metadata > Folder
"""

import os
import shutil
import json
import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "contents"  # v2: content/images → contents
POSTED_DIR = CONTENTS_DIR / "4_posted"    # v3: posted → contents/4_posted

# v3 상태 폴더
STATUS_FOLDERS = ["3_approved", "2_body_ready", "1_cover_only"]


def move_to_posted(food_id: str, source_folder: str) -> str:
    """
    게시 완료 콘텐츠를 posted/ 폴더로 이동

    Args:
        food_id: 콘텐츠 ID (예: "celery")
        source_folder: 원본 폴더 경로 (예: "content/images/027_celery_셀러리")

    Returns:
        이동된 폴더 경로
    """
    source_path = Path(source_folder)

    if not source_path.exists():
        print(f"❌ 원본 폴더 없음: {source_folder}")
        return ""

    # 1. 현재 월 폴더 결정
    current_month = datetime.now().strftime("%Y-%m")
    posted_month_dir = POSTED_DIR / current_month
    posted_month_dir.mkdir(parents=True, exist_ok=True)

    # 2. 대상 폴더명 생성 (번호 제거)
    # "027_celery_셀러리" → "celery_셀러리"
    folder_name = source_path.name
    parts = folder_name.split("_", 1)
    if len(parts) > 1 and parts[0].isdigit():
        new_folder_name = parts[1]
    else:
        new_folder_name = folder_name

    destination = posted_month_dir / new_folder_name

    # 3. archive/ 폴더 제거 (작업 파일 불필요)
    archive_path = source_path / "archive"
    if archive_path.exists():
        shutil.rmtree(archive_path)
        print(f"📦 archive/ 삭제: {archive_path}")

    # 4. 중복 방지
    if destination.exists():
        print(f"⚠️ 이미 존재: {destination}")
        # 타임스탬프 추가
        timestamp = datetime.now().strftime("%H%M%S")
        destination = posted_month_dir / f"{new_folder_name}_{timestamp}"

    # 5. 폴더 이동
    shutil.move(str(source_path), str(destination))
    print(f"✅ 이동 완료: {source_path} → {destination}")

    # 6. 메타데이터 업데이트 (v2: metadata.json)
    metadata_path = destination / "metadata.json"
    # v1 호환
    if not metadata_path.exists():
        v1_path = destination / f"{food_id}_00_metadata.json"
        if v1_path.exists():
            metadata_path = v1_path

    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)

        metadata.update({
            "status": "published",
            "posted_at": datetime.now().isoformat(),
            "folder_path": str(destination)
        })

        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)

    return str(destination)


def find_content_folder(food_id: str, status_filter: str = None) -> Path | None:
    """food_id로 콘텐츠 폴더 찾기 (v3 구조 지원)

    Args:
        food_id: 콘텐츠 ID (예: "pasta")
        status_filter: 특정 상태만 검색 ("3_approved" 등)
    """
    if not CONTENTS_DIR.exists():
        return None

    pattern = re.compile(rf'^\d{{3}}_{food_id}_')

    # v3: 상태 폴더 내 검색
    search_folders = [status_filter] if status_filter else STATUS_FOLDERS
    for status in search_folders:
        status_dir = CONTENTS_DIR / status
        if status_dir.exists():
            for folder in status_dir.iterdir():
                if folder.is_dir() and pattern.match(folder.name):
                    return folder

    # v2 호환: contents/ 루트 검색
    for folder in CONTENTS_DIR.iterdir():
        if folder.is_dir() and pattern.match(folder.name):
            return folder

    return None


def cleanup_posted_in_contents():
    """
    contents/ 내 게시 완료 콘텐츠 정리 (v3 구조 지원)
    (동기화 지연으로 남아있는 경우 처리)
    """

    if not CONTENTS_DIR.exists():
        print("❌ contents 폴더 없음")
        return 0

    moved_count = 0

    # v3: 상태 폴더 내 검색 + 루트 검색
    search_dirs = []
    for status in STATUS_FOLDERS:
        status_dir = CONTENTS_DIR / status
        if status_dir.exists():
            search_dirs.append(status_dir)
    search_dirs.append(CONTENTS_DIR)  # v2 호환

    for search_dir in search_dirs:
        for folder in search_dir.iterdir():
            if not folder.is_dir():
                continue

            # 특수 폴더 제외
            if folder.name.startswith("000_") or "archive" in folder.name.lower():
                continue
            # 상태 폴더 자체는 제외
            if folder.name in STATUS_FOLDERS or folder.name.startswith("🔒"):
                continue

            # 폴더명 파싱
            parts = folder.name.split("_")
            if len(parts) < 2:
                continue

            food_id = parts[1]

            # 메타데이터 확인 (v2: metadata.json)
            metadata_path = folder / "metadata.json"
            # v1 호환
            if not metadata_path.exists():
                v1_path = folder / f"{food_id}_00_metadata.json"
                if v1_path.exists():
                    metadata_path = v1_path

            if not metadata_path.exists():
                continue

            with open(metadata_path, 'r', encoding='utf-8') as f:
                metadata = json.load(f)

            if metadata.get("status") == "published":
                move_to_posted(food_id, str(folder))
                moved_count += 1

    print(f"📊 정리 완료: {moved_count}개 이동됨")
    return moved_count


def get_posted_contents() -> list:
    """posted/ 폴더의 모든 콘텐츠 목록"""
    result = []

    if not POSTED_DIR.exists():
        return result

    for month_dir in sorted(POSTED_DIR.iterdir()):
        if not month_dir.is_dir():
            continue

        for content_dir in month_dir.iterdir():
            if content_dir.is_dir():
                result.append({
                    "month": month_dir.name,
                    "folder": content_dir.name,
                    "path": str(content_dir)
                })

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "cleanup":
            cleanup_posted_in_contents()

        elif cmd == "list":
            contents = get_posted_contents()
            print(f"📂 게시 완료 콘텐츠: {len(contents)}개")
            for c in contents:
                print(f"  {c['month']}/{c['folder']}")

        elif cmd == "move":
            if len(sys.argv) < 3:
                print("사용법: python move_to_posted.py move <food_id>")
            else:
                food_id = sys.argv[2]
                folder = find_content_folder(food_id)
                if folder:
                    move_to_posted(food_id, str(folder))
                else:
                    print(f"❌ 폴더 없음: {food_id}")
    else:
        print("사용법:")
        print("  python move_to_posted.py cleanup  - 게시완료 콘텐츠 정리")
        print("  python move_to_posted.py list     - 게시완료 목록")
        print("  python move_to_posted.py move <food_id> - 특정 콘텐츠 이동")
