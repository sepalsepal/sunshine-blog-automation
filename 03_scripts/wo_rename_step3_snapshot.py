#!/usr/bin/env python3
"""
WO-RENAME-001 STEP 3: 스냅샷 + 백업 생성
- 전체 폴더 구조 스냅샷 (JSON)
- config 폴더 백업
"""

import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
CONFIG_DIR = PROJECT_ROOT / "config"
BACKUP_DIR = PROJECT_ROOT / "backups"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]


def get_file_hash(filepath):
    """파일 MD5 해시 (처음 1KB만)"""
    try:
        with open(filepath, "rb") as f:
            return hashlib.md5(f.read(1024)).hexdigest()[:8]
    except:
        return "-"


def scan_folder_structure():
    """전체 폴더 구조 스캔 - 2026-02-13: 플랫 구조 - contents/ 직접 스캔"""
    import re
    structure = {
        "timestamp": datetime.now().isoformat(),
        "folders": []
    }

    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    for item in sorted(CONTENTS_DIR.iterdir()):
        if not item.is_dir():
            continue
        # 콘텐츠 폴더 패턴 확인 (001_xxx)
        if not re.match(r'^\d{3}_', item.name):
            continue

        folder_info = {
            "path": str(item.relative_to(PROJECT_ROOT)),
            "name": item.name,
            "status": "contents",  # flat structure
            "files": [],
            "subfolders": {}
        }

        # 루트 파일
        for f in item.iterdir():
            if f.is_file():
                folder_info["files"].append({
                    "name": f.name,
                    "size": f.stat().st_size,
                    "hash": get_file_hash(f)
                })

        # 서브폴더 - 2026-02-13: 플랫 구조 경로
        for subdir in ["02_Blog", "01_Insta&Thread", "00_Clean"]:
            subpath = item / subdir
            if subpath.exists():
                folder_info["subfolders"][subdir] = []
                for f in subpath.iterdir():
                    if f.is_file():
                        folder_info["subfolders"][subdir].append({
                            "name": f.name,
                            "size": f.stat().st_size,
                            "hash": get_file_hash(f)
                        })

        structure["folders"].append(folder_info)

    return structure


def main():
    print("━" * 70)
    print("WO-RENAME-001 STEP 3: 스냅샷 + 백업 생성")
    print("━" * 70)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # 백업 디렉토리 생성
    backup_path = BACKUP_DIR / f"wo_rename_001_{timestamp}"
    backup_path.mkdir(parents=True, exist_ok=True)
    print(f"\n[백업 디렉토리] {backup_path}")

    # 1. 폴더 구조 스냅샷
    print("\n[1/3] 폴더 구조 스냅샷 생성 중...")
    structure = scan_folder_structure()

    snapshot_path = backup_path / "folder_structure_snapshot.json"
    with open(snapshot_path, "w", encoding="utf-8") as f:
        json.dump(structure, f, ensure_ascii=False, indent=2)

    total_folders = len(structure["folders"])
    total_files = sum(
        len(f["files"]) + sum(len(files) for files in f["subfolders"].values())
        for f in structure["folders"]
    )
    print(f"  폴더: {total_folders}개")
    print(f"  파일: {total_files}개")
    print(f"  저장: {snapshot_path}")

    # 2. config 폴더 백업
    print("\n[2/3] config 폴더 백업 중...")
    config_backup = backup_path / "config"
    shutil.copytree(CONFIG_DIR, config_backup)

    config_files = list(config_backup.rglob("*"))
    print(f"  파일: {len([f for f in config_files if f.is_file()])}개")
    print(f"  저장: {config_backup}")

    # 3. id_mapping_table 복사
    print("\n[3/3] ID 매핑 테이블 백업 중...")
    mapping_src = CONFIG_DIR / "id_mapping_table.json"
    if mapping_src.exists():
        shutil.copy(mapping_src, backup_path / "id_mapping_table.json")
        print(f"  저장: {backup_path / 'id_mapping_table.json'}")

    # 4. 백업 매니페스트 생성
    manifest = {
        "work_order": "WO-RENAME-001",
        "step": "STEP 3 - Snapshot & Backup",
        "timestamp": timestamp,
        "contents": {
            "folder_structure_snapshot.json": "전체 폴더 구조 (파일명, 크기, 해시)",
            "config/": "config 폴더 전체 백업",
            "id_mapping_table.json": "3-way ID 매핑 테이블"
        },
        "stats": {
            "total_folders": total_folders,
            "total_files": total_files
        }
    }

    manifest_path = backup_path / "MANIFEST.json"
    with open(manifest_path, "w", encoding="utf-8") as f:
        json.dump(manifest, f, ensure_ascii=False, indent=2)

    # 결과 출력
    print("\n" + "━" * 70)
    print("STEP 3 완료")
    print("━" * 70)
    print(f"  백업 위치: {backup_path}")
    print(f"  폴더 수: {total_folders}개")
    print(f"  파일 수: {total_files}개")
    print(f"\n  ✅ 스냅샷 생성 완료")
    print(f"  ✅ config 백업 완료")
    print(f"  ✅ 매니페스트 생성 완료")

    return {
        "backup_path": str(backup_path),
        "total_folders": total_folders,
        "total_files": total_files
    }


if __name__ == "__main__":
    main()
