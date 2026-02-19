#!/usr/bin/env python3
"""
중복 콘텐츠 폴더 정리 실행
- 게시된 폴더가 있으면 미게시 버전 archive로 이동
- 미게시만 있으면 최신 번호만 유지, 나머지 archive로 이동
"""

import os
import re
import shutil
from pathlib import Path
from collections import defaultdict

BASE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine")
CONTENT_DIR = BASE_DIR / "content/images"
ARCHIVE_DIR = CONTENT_DIR / "archive" / "duplicates_20260131"

SKIP_FOLDERS = {'000_cover', 'archive', 'reference', 'sunshine', 'temp'}

def cleanup_duplicates(dry_run=True):
    """중복 폴더 정리"""
    print("=" * 70)
    print(f"🧹 중복 콘텐츠 폴더 정리 {'(DRY RUN)' if dry_run else '(실행)'}")
    print("=" * 70)

    # 영문명별 폴더 그룹핑
    food_folders = defaultdict(list)

    for folder in sorted(CONTENT_DIR.iterdir()):
        if not folder.is_dir() or folder.name in SKIP_FOLDERS:
            continue

        match = re.match(r'(\d+)_([a-z_]+)', folder.name)
        if match:
            num, english = match.groups()
            english = english.rstrip('_')
            food_folders[english].append({
                'num': int(num),
                'name': folder.name,
                'path': folder,
                'published': 'published' in folder.name
            })

    # 중복 찾기
    duplicates = {k: v for k, v in food_folders.items() if len(v) > 1}

    if not dry_run:
        ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

    moved_count = 0
    kept_count = 0

    for food, folders in sorted(duplicates.items()):
        published = [f for f in folders if f['published']]
        unpublished = [f for f in folders if not f['published']]

        # 유지할 폴더 결정
        if published:
            keep = published[0]  # 게시된 것 유지
            to_move = unpublished
        else:
            # 가장 최신 번호 유지
            sorted_folders = sorted(unpublished, key=lambda x: x['num'], reverse=True)
            keep = sorted_folders[0]
            to_move = sorted_folders[1:]

        kept_count += 1
        print(f"\n📌 {food}:")
        print(f"    ✅ 유지: {keep['name']}")

        for f in to_move:
            if dry_run:
                print(f"    🗑️ 이동 예정: {f['name']} → archive/")
            else:
                dest = ARCHIVE_DIR / f['name']
                shutil.move(str(f['path']), str(dest))
                print(f"    🗑️ 이동 완료: {f['name']} → archive/")
            moved_count += 1

    print("\n" + "=" * 70)
    print(f"📊 결과: {kept_count}개 유지, {moved_count}개 {'이동 예정' if dry_run else '이동 완료'}")
    print("=" * 70)

    if dry_run:
        print("\n⚠️ 실제 실행하려면: python cleanup_duplicates.py --execute")

    return moved_count

if __name__ == "__main__":
    import sys
    dry_run = "--execute" not in sys.argv
    cleanup_duplicates(dry_run=dry_run)
