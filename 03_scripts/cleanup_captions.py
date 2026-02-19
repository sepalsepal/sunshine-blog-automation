#!/usr/bin/env python3
"""
캡션 파일 정리
- 규칙 네이밍 ({Food}_{Safety}_*_Caption.txt) 만 유지
- 나머지 캡션 파일은 백업 폴더로 이동
"""

import re
import shutil
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
BACKUP_DIR = PROJECT_ROOT / "backups" / f"captions_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def get_food_name(folder_name):
    """폴더명에서 음식명 추출"""
    match = re.match(r'^\d{3}_(.+)$', folder_name)
    return match.group(1) if match else None


def is_valid_caption(filename, food):
    """규칙 네이밍 캡션인지 확인"""
    # 패턴: {Food}_{Safety}_Insta_Caption.txt, {Food}_{Safety}_Threads_Caption.txt, {Food}_{Safety}_Blog_Caption.txt
    pattern = rf'^{re.escape(food)}_[A-Z]+_(Insta|Threads|Thread|Blog)_Caption\.txt$'
    return bool(re.match(pattern, filename))


def main():
    print("━━━━━ 캡션 파일 정리 ━━━━━")

    # 백업 디렉토리 생성
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"백업 디렉토리: {BACKUP_DIR}")

    folders = sorted([f for f in CONTENTS_DIR.iterdir() if f.is_dir() and re.match(r'^\d{3}_', f.name)])

    stats = {
        "kept": 0,
        "moved": 0,
        "folders_processed": 0
    }

    moved_files = []

    for folder in folders:
        food = get_food_name(folder.name)
        if not food:
            continue

        # 01_Insta&Thread 처리
        insta_dir = folder / "01_Insta&Thread"
        if insta_dir.exists():
            for f in insta_dir.iterdir():
                if f.is_file() and f.suffix == ".txt":
                    if is_valid_caption(f.name, food):
                        stats["kept"] += 1
                    else:
                        # 백업으로 이동
                        backup_folder = BACKUP_DIR / folder.name / "01_Insta&Thread"
                        backup_folder.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(f), str(backup_folder / f.name))
                        stats["moved"] += 1
                        moved_files.append(f"{folder.name}/01_Insta&Thread/{f.name}")

        # 02_Blog 처리
        blog_dir = folder / "02_Blog"
        if blog_dir.exists():
            for f in blog_dir.iterdir():
                if f.is_file() and f.suffix == ".txt":
                    if is_valid_caption(f.name, food):
                        stats["kept"] += 1
                    else:
                        # 백업으로 이동
                        backup_folder = BACKUP_DIR / folder.name / "02_Blog"
                        backup_folder.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(f), str(backup_folder / f.name))
                        stats["moved"] += 1
                        moved_files.append(f"{folder.name}/02_Blog/{f.name}")

        stats["folders_processed"] += 1

    # 결과 출력
    print(f"\n[결과]")
    print(f"  처리 폴더: {stats['folders_processed']}개")
    print(f"  유지: {stats['kept']}개")
    print(f"  백업 이동: {stats['moved']}개")

    if moved_files:
        print(f"\n[이동된 파일] (처음 20개)")
        for f in moved_files[:20]:
            print(f"  → {f}")
        if len(moved_files) > 20:
            print(f"  ... 외 {len(moved_files) - 20}개")

    # 검증: 각 폴더의 캡션 확인
    print(f"\n[검증] 캡션 현황 (처음 5개 폴더)")
    for folder in folders[:5]:
        food = get_food_name(folder.name)
        print(f"  {folder.name}:")

        insta_dir = folder / "01_Insta&Thread"
        if insta_dir.exists():
            txt_files = [f.name for f in insta_dir.iterdir() if f.suffix == ".txt"]
            print(f"    01_Insta&Thread: {txt_files}")

        blog_dir = folder / "02_Blog"
        if blog_dir.exists():
            txt_files = [f.name for f in blog_dir.iterdir() if f.suffix == ".txt"]
            print(f"    02_Blog: {txt_files}")

    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"백업 위치: {BACKUP_DIR}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    return stats


if __name__ == "__main__":
    main()
