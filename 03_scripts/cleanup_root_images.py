#!/usr/bin/env python3
"""
루트 이미지 정리
- 영어+한국어 커버 (PascalCase: {Food}_Common_0X_*.png) 만 유지
- 나머지 이미지는 백업 폴더로 이동
- 결과: 각 폴더에 01, 02, 08 이미지 각 1개씩만
"""

import re
import shutil
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
BACKUP_DIR = PROJECT_ROOT / "backups" / f"root_images_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def get_food_name(folder_name):
    """폴더명에서 음식명 추출"""
    match = re.match(r'^\d{3}_(.+)$', folder_name)
    return match.group(1) if match else None


def main():
    print("━━━━━ 루트 이미지 정리 ━━━━━")

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

        # 루트의 PNG 파일들
        root_pngs = [f for f in folder.iterdir() if f.is_file() and f.suffix == ".png"]

        if not root_pngs:
            continue

        # 유지할 패턴: {Food}_Common_01_Cover.png, {Food}_Common_02_Food.png, {Food}_Common_08_Cta.png
        keep_patterns = [
            f"{food}_Common_01_Cover.png",
            f"{food}_Common_02_Food.png",
            f"{food}_Common_08_Cta.png",
        ]

        for png in root_pngs:
            if png.name in keep_patterns:
                stats["kept"] += 1
            else:
                # 백업으로 이동
                backup_folder = BACKUP_DIR / folder.name
                backup_folder.mkdir(exist_ok=True)
                dst = backup_folder / png.name
                shutil.move(str(png), str(dst))
                stats["moved"] += 1
                moved_files.append(f"{folder.name}/{png.name}")

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

    # 검증: 각 폴더에 01, 02, 08 이미지 확인
    print(f"\n[검증] 루트 이미지 현황")
    sample_folders = folders[:5]
    for folder in sample_folders:
        food = get_food_name(folder.name)
        root_pngs = [f.name for f in folder.iterdir() if f.is_file() and f.suffix == ".png"]
        print(f"  {folder.name}: {root_pngs}")

    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"백업 위치: {BACKUP_DIR}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    return stats


if __name__ == "__main__":
    main()
