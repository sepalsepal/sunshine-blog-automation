#!/usr/bin/env python3
"""
WO-2026-0206-012 작업 2: P~R열 자동 체크 시스템

각 콘텐츠 폴더에서 파일 존재 여부 확인 → 구글시트 자동 업데이트

| 열 | 항목 | 확인 파일 | 값 |
|----|------|-----------|-----|
| P | 인스타 캡션 | caption_instagram.txt 또는 metadata 내 | 있으면 "완료", 없으면 "-" |
| Q | 쓰레드 캡션 | caption_threads.txt 또는 metadata 내 | 있으면 "완료", 없으면 "-" |
| R | 메타데이터 | metadata.json | 있으면 "완료", 없으면 "-" |

사용법:
    python check_folder_contents.py           # 전체 동기화
    python check_folder_contents.py --dry-run # 변경사항만 출력
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import gspread
from google.oauth2.service_account import Credentials


# 열 인덱스 (1-based)
COL_P_INSTAGRAM = 16  # P열: 인스타 캡션
COL_Q_THREADS = 17    # Q열: 쓰레드 캡션
COL_R_METADATA = 18   # R열: 메타데이터


def get_sheet():
    """구글시트 연결"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_path = PROJECT_ROOT / "config" / "google-credentials.json"
    creds = Credentials.from_service_account_file(str(creds_path), scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("Sunshine").worksheet("게시콘텐츠")


def check_instagram_caption(folder: Path) -> bool:
    """인스타 캡션 존재 여부 확인"""
    # 1. caption_instagram.txt 파일 확인
    if (folder / "caption_instagram.txt").exists():
        return True

    # 2. metadata.json 내 caption_instagram 필드 확인
    metadata_path = folder / "metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('caption_instagram'):
                    return True
        except (json.JSONDecodeError, KeyError):
            pass

    return False


def check_threads_caption(folder: Path) -> bool:
    """쓰레드 캡션 존재 여부 확인"""
    # 1. caption_threads.txt 파일 확인
    if (folder / "caption_threads.txt").exists():
        return True

    # 2. metadata.json 내 caption_threads 필드 확인
    metadata_path = folder / "metadata.json"
    if metadata_path.exists():
        try:
            with open(metadata_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if data.get('caption_threads'):
                    return True
        except (json.JSONDecodeError, KeyError):
            pass

    return False


def check_metadata(folder: Path) -> bool:
    """metadata.json 존재 여부 확인"""
    return (folder / "metadata.json").exists()


def get_folder_status():
    """모든 콘텐츠 폴더의 P~R열 상태 확인"""
    body_ready = PROJECT_ROOT / "contents" / "2_body_ready"
    status = {}

    for folder in body_ready.iterdir():
        if not folder.is_dir() or folder.name.startswith('.'):
            continue

        parts = folder.name.split('_')
        num = parts[0]

        status[num] = {
            'folder_name': folder.name,
            'has_instagram': check_instagram_caption(folder),
            'has_threads': check_threads_caption(folder),
            'has_metadata': check_metadata(folder),
        }

    return status


def sync_pqr_columns(dry_run=False):
    """P~R열을 구글시트에 동기화"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] P~R열 체크 시작...")

    folder_status = get_folder_status()
    sheet = get_sheet()
    all_data = sheet.get_all_values()

    updates = []

    for idx, row in enumerate(all_data[1:], start=2):
        if len(row) == 0:
            continue

        num = row[0]
        if num not in folder_status:
            continue

        local = folder_status[num]

        # P열: 인스타 캡션
        current_p = row[COL_P_INSTAGRAM - 1] if len(row) >= COL_P_INSTAGRAM else ""
        new_p = "완료" if local['has_instagram'] else "-"
        if current_p != new_p:
            updates.append({
                'row': idx,
                'col': COL_P_INSTAGRAM,
                'old': current_p,
                'new': new_p,
                'field': 'P열(인스타캡션)',
                'num': num
            })

        # Q열: 쓰레드 캡션
        current_q = row[COL_Q_THREADS - 1] if len(row) >= COL_Q_THREADS else ""
        new_q = "완료" if local['has_threads'] else "-"
        if current_q != new_q:
            updates.append({
                'row': idx,
                'col': COL_Q_THREADS,
                'old': current_q,
                'new': new_q,
                'field': 'Q열(쓰레드캡션)',
                'num': num
            })

        # R열: 메타데이터
        current_r = row[COL_R_METADATA - 1] if len(row) >= COL_R_METADATA else ""
        new_r = "완료" if local['has_metadata'] else "-"
        if current_r != new_r:
            updates.append({
                'row': idx,
                'col': COL_R_METADATA,
                'old': current_r,
                'new': new_r,
                'field': 'R열(메타데이터)',
                'num': num
            })

    # 결과 출력
    if updates:
        print(f"\n변경 필요: {len(updates)}건")
        print("-" * 60)
        for u in updates:
            print(f"  [{u['num']}] {u['field']}: '{u['old']}' → '{u['new']}'")

        if not dry_run:
            cells = []
            for u in updates:
                cells.append(gspread.Cell(u['row'], u['col'], u['new']))

            sheet.update_cells(cells)
            print(f"\n✅ {len(updates)}건 업데이트 완료")
        else:
            print("\n(--dry-run 모드: 실제 업데이트 안함)")
    else:
        print("✅ 변경사항 없음 - P~R열 이미 동기화됨")

    return updates


def main():
    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    sync_pqr_columns(dry_run=dry_run)


if __name__ == "__main__":
    main()
