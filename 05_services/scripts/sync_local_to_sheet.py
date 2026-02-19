#!/usr/bin/env python3
"""
로컬 폴더 → 구글시트 동기화 스크립트

사용법:
    python sync_local_to_sheet.py           # 전체 동기화
    python sync_local_to_sheet.py --dry-run # 변경사항만 출력 (실제 업데이트 안함)
    python sync_local_to_sheet.py --watch   # 폴더 감시 모드 (자동 동기화)

동기화 대상:
    - contents/2_body_ready/ 폴더의 상태
    - 커버(00), CTA(03), 클린소스 존재 여부
"""

import os
import sys
import time
from pathlib import Path
from datetime import datetime

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import gspread
from google.oauth2.service_account import Credentials


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


def get_local_status():
    """로컬 폴더 상태 확인"""
    body_ready = PROJECT_ROOT / "contents" / "2_body_ready"
    status = {}

    for folder in body_ready.iterdir():
        if not folder.is_dir() or folder.name.startswith('.'):
            continue

        parts = folder.name.split('_')
        num = parts[0]
        eng_name = parts[1] if len(parts) > 1 else ""

        # 파일 존재 확인
        cover_files = list(folder.glob("*_00.png"))
        cta_files = list(folder.glob("*_03.png"))
        clean_folder = folder / "clean"
        source_files = list(clean_folder.glob("*_00_source.png")) if clean_folder.exists() else []

        status[num] = {
            'eng_name': eng_name,
            'folder': folder.name,
            'has_cover': len(cover_files) > 0,
            'has_cta': len(cta_files) > 0,
            'has_source': len(source_files) > 0,
            'cover_file': cover_files[0].name if cover_files else None,
            'cta_file': cta_files[0].name if cta_files else None,
        }

    return status


def sync_to_sheet(dry_run=False):
    """로컬 상태를 구글시트에 동기화"""
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 동기화 시작...")

    local_status = get_local_status()
    sheet = get_sheet()
    all_data = sheet.get_all_values()

    updates = []

    for idx, row in enumerate(all_data[1:], start=2):
        if len(row) == 0:
            continue

        num = row[0]
        if num not in local_status:
            continue

        local = local_status[num]

        # O열(15): 상태 - 커버+CTA 있으면 "완료", 아니면 "진행중"
        current_status = row[14] if len(row) > 14 else ""
        new_status = "완료" if (local['has_cover'] and local['has_cta']) else "진행중"

        if current_status != new_status:
            updates.append({
                'row': idx,
                'col': 15,  # O열
                'old': current_status,
                'new': new_status,
                'field': '상태',
                'num': num
            })

    # 결과 출력
    if updates:
        print(f"\n변경 필요: {len(updates)}건")
        print("-" * 50)
        for u in updates:
            print(f"  [{u['num']}] {u['field']}: '{u['old']}' → '{u['new']}'")

        if not dry_run:
            # 배치 업데이트
            cells = []
            for u in updates:
                cells.append(gspread.Cell(u['row'], u['col'], u['new']))

            sheet.update_cells(cells)
            print(f"\n✅ {len(updates)}건 업데이트 완료")
        else:
            print("\n(--dry-run 모드: 실제 업데이트 안함)")
    else:
        print("✅ 변경사항 없음 - 이미 동기화됨")

    return updates


def watch_mode():
    """폴더 감시 모드 (변경 감지 시 자동 동기화)"""
    print("👁️ 폴더 감시 모드 시작 (Ctrl+C로 종료)")
    print(f"   감시 대상: contents/2_body_ready/")
    print("-" * 50)

    last_status = get_local_status()

    try:
        while True:
            time.sleep(5)  # 5초마다 체크

            current_status = get_local_status()

            # 변경 감지
            changed = False
            for num, local in current_status.items():
                if num not in last_status:
                    print(f"[NEW] {num} 폴더 추가됨")
                    changed = True
                elif local != last_status[num]:
                    print(f"[CHG] {num} 변경 감지")
                    changed = True

            if changed:
                sync_to_sheet(dry_run=False)
                last_status = current_status

    except KeyboardInterrupt:
        print("\n감시 모드 종료")


def main():
    args = sys.argv[1:]

    if '--watch' in args:
        watch_mode()
    elif '--dry-run' in args:
        sync_to_sheet(dry_run=True)
    else:
        sync_to_sheet(dry_run=False)


if __name__ == "__main__":
    main()
