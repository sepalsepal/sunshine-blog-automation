#!/usr/bin/env python3
"""
WO-2026-0206-013: approved 정합성 복구 스크립트

작업 태그: reconciled_after_definition_fix
사유: approved 정의 확정 이전 상태 불일치 보정

실행:
    python reconcile_approved.py           # 실제 실행
    python reconcile_approved.py --dry-run # 테스트 모드
"""

import os
import sys
import json
import shutil
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import gspread
from google.oauth2.service_account import Credentials

# 열 인덱스 (1-based)
COL_NUM = 1
COL_ENG_NAME = 2
COL_KR_NAME = 3
COL_FOLDER_NAME = 4
COL_STATUS = 6        # F열: 게시상태
COL_CAPTION_INSTA = 16   # P열
COL_CAPTION_THREADS = 17  # Q열
COL_METADATA = 18     # R열
COL_CLOUDINARY = 19   # S열
COL_FOLDER_STATUS = 21  # U열

# 대상 콘텐츠 (2_body_ready → 3_approved 이동 대상)
TARGET_NUMS = ['060', '066', '071', '076', '093', '096', '102', '118', '121', '124', '126']


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


def fix_metadata(folder: Path, dry_run=False) -> dict:
    """메타데이터 보완

    - food_name_kr 추가 (폴더명에서 추출)
    - status → approved
    - safety_level 대문자 표준화
    - reconciled_at 추가
    """
    metadata_path = folder / "metadata.json"
    if not metadata_path.exists():
        return {'error': 'metadata.json not found'}

    with open(metadata_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    # 폴더명에서 한글명 추출 (e.g., 060_fried_chicken_후라이드치킨 → 후라이드치킨)
    parts = folder.name.split('_')
    kr_name = parts[-1] if len(parts) >= 3 else parts[1] if len(parts) >= 2 else ""

    changes = []

    # food_name_kr 추가
    if not data.get('food_name_kr'):
        data['food_name_kr'] = kr_name
        changes.append(f"food_name_kr: {kr_name}")

    # status → approved
    if data.get('status') != 'approved':
        old_status = data.get('status', 'unknown')
        data['status'] = 'approved'
        changes.append(f"status: {old_status} → approved")

    # safety_level 대문자 표준화
    safety = data.get('safety_level', data.get('safety', ''))
    if safety:
        std_safety = safety.upper()
        if std_safety != safety:
            data['safety_level'] = std_safety
            if 'safety' in data:
                del data['safety']
            changes.append(f"safety_level: {safety} → {std_safety}")

    # 정합성 복구 태그 추가
    data['reconciled_at'] = datetime.now().isoformat()
    data['reconcile_tag'] = 'reconciled_after_definition_fix'

    if changes and not dry_run:
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    return {'changes': changes, 'data': data}


def move_folder(src_base: Path, dst_base: Path, folder_name: str, dry_run=False) -> dict:
    """폴더 이동: body_ready → approved"""
    src = src_base / folder_name
    dst = dst_base / folder_name

    if not src.exists():
        return {'error': f'Source not found: {src}'}

    if dst.exists():
        return {'skipped': f'Already exists: {dst}'}

    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

    return {'moved': f'{src} → {dst}'}


def reconcile_all(dry_run=False):
    """전체 정합성 복구 실행"""
    print("=" * 70)
    print(f"🔧 WO-2026-0206-013: approved 정합성 복구")
    print(f"   태그: reconciled_after_definition_fix")
    print(f"   시각: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 70)

    body_ready = PROJECT_ROOT / "contents" / "2_body_ready"
    approved_dir = PROJECT_ROOT / "contents" / "3_approved"

    sheet = get_sheet()
    all_data = sheet.get_all_values()

    # 대상 폴더 매핑
    folder_map = {}
    for folder in body_ready.iterdir():
        if folder.is_dir() and not folder.name.startswith('.'):
            num = folder.name.split('_')[0]
            if num in TARGET_NUMS:
                folder_map[num] = folder

    updates = []
    results = []

    for num in TARGET_NUMS:
        print(f"\n{'─'*60}")
        print(f"[{num}] 처리 시작")

        folder = folder_map.get(num)
        if not folder:
            print(f"  ⚠️ 폴더 없음 - 건너뜀")
            continue

        result = {'num': num, 'folder': folder.name}

        # 1. 메타데이터 보완
        print(f"  📝 메타데이터 보완...")
        meta_result = fix_metadata(folder, dry_run=dry_run)
        if meta_result.get('changes'):
            for c in meta_result['changes']:
                print(f"     - {c}")
            result['metadata_changes'] = meta_result['changes']
        else:
            print(f"     - 변경 없음")

        # 2. 폴더 이동
        print(f"  📁 폴더 이동...")
        move_result = move_folder(body_ready, approved_dir, folder.name, dry_run=dry_run)
        if move_result.get('moved'):
            print(f"     - {move_result['moved']}")
            result['folder_moved'] = True
        elif move_result.get('skipped'):
            print(f"     - 건너뜀: {move_result['skipped']}")
            result['folder_moved'] = False
        elif move_result.get('error'):
            print(f"     - 에러: {move_result['error']}")
            result['folder_error'] = move_result['error']

        # 3. 시트 행 찾기
        for idx, row in enumerate(all_data[1:], start=2):
            if len(row) > 0 and row[0] == num:
                # P/Q/R/S 확인
                p = row[COL_CAPTION_INSTA - 1] if len(row) >= COL_CAPTION_INSTA else ""
                q = row[COL_CAPTION_THREADS - 1] if len(row) >= COL_CAPTION_THREADS else ""
                r = row[COL_METADATA - 1] if len(row) >= COL_METADATA else ""
                s = row[COL_CLOUDINARY - 1] if len(row) >= COL_CLOUDINARY else ""
                f = row[COL_STATUS - 1] if len(row) >= COL_STATUS else ""
                u = row[COL_FOLDER_STATUS - 1] if len(row) >= COL_FOLDER_STATUS else ""

                print(f"  📊 시트 상태: P={p}, Q={q}, R={r}, S={s}, F={f}, U={u}")

                # 필요한 업데이트 수집
                if p != "완료":
                    updates.append({'row': idx, 'col': COL_CAPTION_INSTA, 'val': '완료'})
                if q != "완료":
                    updates.append({'row': idx, 'col': COL_CAPTION_THREADS, 'val': '완료'})
                if r != "완료":
                    updates.append({'row': idx, 'col': COL_METADATA, 'val': '완료'})
                # S열은 이미 완료인 경우 건드리지 않음
                if u != "approved":
                    updates.append({'row': idx, 'col': COL_FOLDER_STATUS, 'val': 'approved'})

                break

        results.append(result)

    # 시트 업데이트 실행
    if updates:
        print(f"\n{'─'*60}")
        print(f"📊 구글시트 업데이트: {len(updates)}건")

        if not dry_run:
            cells = [gspread.Cell(u['row'], u['col'], u['val']) for u in updates]
            sheet.update_cells(cells)
            print("  ✅ 업데이트 완료")
        else:
            for u in updates:
                print(f"  - Row {u['row']}, Col {u['col']} → {u['val']}")
            print("  (dry-run 모드)")

    # 결과 요약
    print(f"\n{'='*70}")
    print("📋 결과 요약")
    print(f"{'='*70}")
    print(f"  처리 대상: {len(TARGET_NUMS)}건")
    print(f"  폴더 이동: {sum(1 for r in results if r.get('folder_moved'))}건")
    print(f"  메타데이터 수정: {sum(1 for r in results if r.get('metadata_changes'))}건")
    print(f"  시트 업데이트: {len(updates)}건")

    if dry_run:
        print("\n  ⚠️ dry-run 모드: 실제 변경 없음")

    return results


def main():
    args = sys.argv[1:]
    dry_run = '--dry-run' in args
    reconcile_all(dry_run=dry_run)


if __name__ == "__main__":
    main()
