#!/usr/bin/env python3
"""
구글 시트 중복 항목 분석 및 정리 스크립트
- 한글명 기준 중복 탐지
- 게시완료 항목 우선 보존
- 중복 행 삭제 (시트 + 로컬 CSV)
"""

import csv
import os
import sys
import time
from pathlib import Path
from collections import defaultdict

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

import gspread
from google.oauth2.service_account import Credentials


def connect():
    """Google Sheets 연결"""
    sheet_id = os.environ.get('GOOGLE_SHEET_ID')
    creds_path = os.environ.get('GOOGLE_CREDENTIALS_PATH')
    worksheet_name = os.environ.get('GOOGLE_WORKSHEET_NAME', '게시콘텐츠')

    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]
    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.worksheet(worksheet_name)
    print(f"✅ 연결: {sheet.title} / {worksheet_name}")
    return worksheet


def analyze_duplicates(all_values, header):
    """중복 분석 - 한글명 기준"""
    ko_col = header.index('한글명') if '한글명' in header else 2
    en_col = header.index('영문명') if '영문명' in header else 1
    no_col = header.index('번호') if '번호' in header else 0
    status_col = header.index('게시상태') if '게시상태' in header else 5
    safety_col = header.index('안전도') if '안전도' in header else 4

    # 한글명별 행 그룹핑
    groups = defaultdict(list)
    for row_idx, row in enumerate(all_values[1:], start=2):  # 2행부터 (1-indexed)
        if len(row) <= ko_col:
            continue
        ko_name = row[ko_col].strip()
        if not ko_name:
            continue
        groups[ko_name].append({
            'row_idx': row_idx,
            'no': row[no_col] if len(row) > no_col else '',
            'en': row[en_col] if len(row) > en_col else '',
            'ko': ko_name,
            'status': row[status_col].strip() if len(row) > status_col else '',
            'safety': row[safety_col].strip() if len(row) > safety_col else '',
            'full_row': row
        })

    # 중복 그룹만 필터
    duplicates = {k: v for k, v in groups.items() if len(v) > 1}
    return duplicates


def decide_keep_delete(items):
    """
    보존/삭제 결정:
    1. 게시완료 항목 우선
    2. 인스타URL 있는 항목 우선
    3. 그 외 첫 번째 항목 보존
    """
    # 게시완료 있으면 그것 보존
    published = [i for i in items if i['status'] == '게시완료']
    if published:
        keep = published[0]
    else:
        keep = items[0]

    delete = [i for i in items if i['row_idx'] != keep['row_idx']]
    return keep, delete


def main():
    print("=" * 60)
    print("🔍 구글 시트 중복 항목 분석 및 정리")
    print("=" * 60)

    # 1. 연결
    worksheet = connect()
    all_values = worksheet.get_all_values()
    header = all_values[0] if all_values else []
    total_rows = len(all_values) - 1  # 헤더 제외

    print(f"📊 시트 총 {total_rows}행")

    # 2. 중복 분석
    print("\n[1/3] 중복 분석 중...")
    duplicates = analyze_duplicates(all_values, header)

    if not duplicates:
        print("✅ 중복 없음!")
        return

    print(f"\n🔴 중복 그룹 {len(duplicates)}건 발견:\n")

    total_delete = 0
    delete_rows = []

    for ko_name, items in sorted(duplicates.items()):
        keep, to_delete = decide_keep_delete(items)
        total_delete += len(to_delete)

        print(f"  [{ko_name}] ({len(items)}건)")
        print(f"    ✅ 보존: 행{keep['row_idx']:>4} | {keep['no']:>3} | {keep['en']:<20} | {keep['status']:<8} | {keep['safety']}")
        for d in to_delete:
            print(f"    ❌ 삭제: 행{d['row_idx']:>4} | {d['no']:>3} | {d['en']:<20} | {d['status']:<8} | {d['safety']}")
            delete_rows.append(d['row_idx'])

    print(f"\n📊 요약: {len(duplicates)} 그룹, 총 {total_delete}건 삭제 예정")

    # 3. 삭제 실행 (뒤에서부터 삭제해야 행 번호 안 밀림)
    print("\n[2/3] Google Sheets에서 중복 행 삭제 중...")
    delete_rows.sort(reverse=True)  # 역순 정렬

    for i, row_idx in enumerate(delete_rows):
        worksheet.delete_rows(row_idx)
        print(f"  🗑️  행 {row_idx} 삭제 ({i+1}/{len(delete_rows)})")
        time.sleep(1)  # API 제한 방지

    print(f"✅ {len(delete_rows)}건 삭제 완료")

    # 4. 로컬 CSV도 정리
    print("\n[3/3] 로컬 CSV 중복 정리...")
    csv_path = PROJECT_ROOT / 'config' / 'data' / 'published_contents.csv'

    if csv_path.exists():
        fieldnames = ['번호', '영문명', '한글명', '폴더명', '안전도', '게시상태', '게시일', '인스타URL']
        rows = []
        with open(csv_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f, fieldnames=fieldnames)
            next(reader)  # 헤더 스킵
            for row in reader:
                rows.append({k: v for k, v in row.items() if k is not None})

        # 한글명 기준 중복 제거 (게시완료 우선)
        seen = {}
        deduped = []
        csv_removed = 0

        for row in rows:
            ko = row.get('한글명', '').strip()
            status = row.get('게시상태', '').strip()

            if ko not in seen:
                seen[ko] = len(deduped)
                deduped.append(row)
            else:
                existing_idx = seen[ko]
                existing_status = deduped[existing_idx].get('게시상태', '')

                # 게시완료가 우선
                if status == '게시완료' and existing_status != '게시완료':
                    deduped[existing_idx] = row
                    csv_removed += 1
                else:
                    csv_removed += 1

        with open(csv_path, 'w', encoding='utf-8', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction='ignore')
            writer.writeheader()
            writer.writerows(deduped)

        print(f"✅ CSV: {csv_removed}건 중복 제거 ({len(rows)} → {len(deduped)}행)")

    # 최종 확인
    print("\n" + "=" * 60)
    final_values = worksheet.get_all_values()
    print(f"📊 정리 완료: {len(final_values) - 1}행 (이전 {total_rows}행)")
    print("=" * 60)


if __name__ == '__main__':
    main()
