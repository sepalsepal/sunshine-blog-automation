#!/usr/bin/env python3
"""
WO-2026-0206-016: 시트 검증 스크립트

검증 항목:
1. U열 이상값 (O/X 외)
2. approved 불완전 (P/Q/R/S 중 "-")
3. posted 불완전 (T열 비어있음)
4. 안전도 이상값 (SAFE/CAUTION/DANGER/FORBIDDEN 외)
5. 폴더 불일치 (U열 vs 실제 폴더)

사용법:
    python sheet_validator.py           # 검증만
    python sheet_validator.py --fix     # 검증 + 자동 수정
"""

import sys
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import gspread
from google.oauth2.service_account import Credentials

# 열 인덱스 (1-based)
COL_NUM = 1          # A열: 번호
COL_ENG_NAME = 2     # B열: 영문명
COL_SAFETY = 5       # E열: 안전도
COL_STATUS = 6       # F열: 게시상태
COL_CAPTION_INSTA = 16   # P열
COL_CAPTION_THREADS = 17 # Q열
COL_METADATA = 18    # R열
COL_CLOUDINARY = 19  # S열
COL_PUBLISH = 20     # T열: 게시
COL_FOLDER = 21      # U열: 폴더유무

# 유효한 값들
VALID_SAFETY = ['SAFE', 'CAUTION', 'DANGER', 'FORBIDDEN']
VALID_FOLDER = ['O', 'X']


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


def get_folder_map():
    """로컬 폴더 맵 생성"""
    SEARCH_PATHS = [
        PROJECT_ROOT / 'contents' / '1_cover_only',
        PROJECT_ROOT / 'contents' / '2_body_ready',
        PROJECT_ROOT / 'contents' / '3_approved',
        PROJECT_ROOT / 'contents' / '4_posted',
    ]

    folder_map = {}
    for search_path in SEARCH_PATHS:
        if search_path.exists():
            for folder in search_path.iterdir():
                if folder.is_dir() and not folder.name.startswith('.'):
                    parts = folder.name.split('_')
                    num = parts[0]
                    folder_map[num] = search_path.name

    return folder_map


def validate_sheet(fix=False):
    """시트 검증 실행"""
    print("=" * 70)
    print(f"🔍 시트 검증 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"   모드: {'검증 + 자동 수정' if fix else '검증만'}")
    print("=" * 70)

    sheet = get_sheet()
    all_data = sheet.get_all_values()
    folder_map = get_folder_map()

    errors = {
        'u_abnormal': [],      # U열 이상값
        'approved_incomplete': [],  # approved 불완전
        'posted_incomplete': [],    # posted 불완전
        'safety_abnormal': [],      # 안전도 이상값
        'folder_mismatch': [],      # 폴더 불일치
    }

    fixes = []

    for idx, row in enumerate(all_data[1:], start=2):
        if len(row) < 6:
            continue

        num = row[0] if len(row) > 0 else ''
        eng_name = row[1] if len(row) > 1 else ''
        safety = row[COL_SAFETY - 1] if len(row) >= COL_SAFETY else ''
        status = row[COL_STATUS - 1] if len(row) >= COL_STATUS else ''
        p = row[COL_CAPTION_INSTA - 1] if len(row) >= COL_CAPTION_INSTA else ''
        q = row[COL_CAPTION_THREADS - 1] if len(row) >= COL_CAPTION_THREADS else ''
        r = row[COL_METADATA - 1] if len(row) >= COL_METADATA else ''
        s = row[COL_CLOUDINARY - 1] if len(row) >= COL_CLOUDINARY else ''
        t = row[COL_PUBLISH - 1] if len(row) >= COL_PUBLISH else ''
        u = row[COL_FOLDER - 1] if len(row) >= COL_FOLDER else ''

        # 번호 형식 체크 (3자리 숫자)
        if not (num.isdigit() and len(num) == 3):
            continue

        # 1. U열 이상값
        if u and u not in VALID_FOLDER:
            has_folder = num in folder_map
            correct_val = 'O' if has_folder else 'X'
            errors['u_abnormal'].append({
                'row': idx, 'num': num, 'current': u, 'correct': correct_val
            })
            if fix:
                fixes.append(gspread.Cell(idx, COL_FOLDER, correct_val))

        # 2. approved 불완전
        if status.lower() == 'approved':
            missing = []
            if p in ['-', '']:
                missing.append('P')
            if q in ['-', '']:
                missing.append('Q')
            if r in ['-', '']:
                missing.append('R')
            if s in ['-', '']:
                missing.append('S')

            if missing:
                errors['approved_incomplete'].append({
                    'row': idx, 'num': num, 'eng_name': eng_name, 'missing': missing
                })

        # 3. posted 불완전
        if status.lower() == 'posted':
            if t in ['-', '']:
                errors['posted_incomplete'].append({
                    'row': idx, 'num': num, 'eng_name': eng_name
                })
                if fix:
                    fixes.append(gspread.Cell(idx, COL_PUBLISH, '완료'))

        # 4. 안전도 이상값
        if safety and safety.upper() not in VALID_SAFETY:
            errors['safety_abnormal'].append({
                'row': idx, 'num': num, 'eng_name': eng_name, 'current': safety
            })

        # 5. 폴더 불일치
        has_folder = num in folder_map
        if u == 'O' and not has_folder:
            errors['folder_mismatch'].append({
                'row': idx, 'num': num, 'u_val': 'O', 'actual': 'X (없음)'
            })
            if fix:
                fixes.append(gspread.Cell(idx, COL_FOLDER, 'X'))
        elif u == 'X' and has_folder:
            errors['folder_mismatch'].append({
                'row': idx, 'num': num, 'u_val': 'X', 'actual': f'O ({folder_map[num]})'
            })
            if fix:
                fixes.append(gspread.Cell(idx, COL_FOLDER, 'O'))

    # 결과 출력
    print()
    total_errors = sum(len(v) for v in errors.values())

    # 1. U열 이상값
    print(f"[1] U열 이상값: {len(errors['u_abnormal'])}건")
    for e in errors['u_abnormal'][:5]:
        print(f"    행{e['row']} | {e['num']} | '{e['current']}' → '{e['correct']}'")
    if len(errors['u_abnormal']) > 5:
        print(f"    ... 외 {len(errors['u_abnormal']) - 5}건")

    # 2. approved 불완전
    print(f"\n[2] approved 불완전: {len(errors['approved_incomplete'])}건")
    for e in errors['approved_incomplete'][:5]:
        print(f"    행{e['row']} | {e['num']} {e['eng_name']} | 누락: {', '.join(e['missing'])}")
    if len(errors['approved_incomplete']) > 5:
        print(f"    ... 외 {len(errors['approved_incomplete']) - 5}건")

    # 3. posted 불완전
    print(f"\n[3] posted 불완전: {len(errors['posted_incomplete'])}건")
    for e in errors['posted_incomplete'][:5]:
        print(f"    행{e['row']} | {e['num']} {e['eng_name']} | T열 비어있음")
    if len(errors['posted_incomplete']) > 5:
        print(f"    ... 외 {len(errors['posted_incomplete']) - 5}건")

    # 4. 안전도 이상값
    print(f"\n[4] 안전도 이상값: {len(errors['safety_abnormal'])}건")
    for e in errors['safety_abnormal'][:5]:
        print(f"    행{e['row']} | {e['num']} {e['eng_name']} | '{e['current']}'")
    if len(errors['safety_abnormal']) > 5:
        print(f"    ... 외 {len(errors['safety_abnormal']) - 5}건")

    # 5. 폴더 불일치
    print(f"\n[5] 폴더 불일치: {len(errors['folder_mismatch'])}건")
    for e in errors['folder_mismatch'][:5]:
        print(f"    행{e['row']} | {e['num']} | U열={e['u_val']} → 실제={e['actual']}")
    if len(errors['folder_mismatch']) > 5:
        print(f"    ... 외 {len(errors['folder_mismatch']) - 5}건")

    # 자동 수정
    if fix and fixes:
        print(f"\n{'='*70}")
        print(f"🔧 자동 수정 실행: {len(fixes)}건")
        sheet.update_cells(fixes)
        print(f"✅ 수정 완료")

    # 요약
    print(f"\n{'='*70}")
    print(f"📋 검증 요약")
    print(f"{'='*70}")
    print(f"   총 에러: {total_errors}건")
    print(f"   - U열 이상값: {len(errors['u_abnormal'])}건")
    print(f"   - approved 불완전: {len(errors['approved_incomplete'])}건")
    print(f"   - posted 불완전: {len(errors['posted_incomplete'])}건")
    print(f"   - 안전도 이상값: {len(errors['safety_abnormal'])}건")
    print(f"   - 폴더 불일치: {len(errors['folder_mismatch'])}건")

    if fix:
        print(f"\n   자동 수정: {len(fixes)}건 완료")

    return errors


def main():
    args = sys.argv[1:]
    fix = '--fix' in args
    validate_sheet(fix=fix)


if __name__ == "__main__":
    main()
