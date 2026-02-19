#!/usr/bin/env python3
"""
중복/유사 항목 자동 감지 스크립트
실행: python services/scripts/check_duplicates.py
"""

import gspread
from google.oauth2.service_account import Credentials
from difflib import SequenceMatcher
from pathlib import Path

PROJECT = Path(__file__).parent.parent.parent
CREDS_PATH = PROJECT / 'config' / 'google-credentials.json'
SHEET_ID = '199IQPmPsOfydw73Yf3OhjVZJvdK1GnAd8C2hzy-2LcY'

def similar(a: str, b: str) -> float:
    """두 문자열의 유사도 계산 (0~1)"""
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()

def get_sheet_data():
    """시트 데이터 가져오기"""
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets']
    creds = Credentials.from_service_account_file(str(CREDS_PATH), scopes=SCOPES)
    gc = gspread.authorize(creds)
    sheet = gc.open_by_key(SHEET_ID).worksheet('게시콘텐츠')
    return sheet.get_all_values()

def check_exact_duplicates(data):
    """정확히 동일한 영문명 중복 체크"""
    from collections import Counter
    eng_names = [row[1].strip() for row in data[1:] if row[1].strip()]
    duplicates = {name: count for name, count in Counter(eng_names).items() if count > 1}

    if duplicates:
        print("🔴 정확히 동일한 영문명 중복:")
        for name, count in sorted(duplicates.items()):
            print(f"   - {name}: {count}회")
            for i, row in enumerate(data[1:], start=2):
                if row[1].strip() == name:
                    print(f"      Row {i}: {row[0]} | {row[2]} | {row[3]}")
        return True
    return False

def check_similar_items(data, threshold=0.8):
    """유사 항목 체크 (임계값 이상)"""
    items = []
    for i, row in enumerate(data[1:], start=2):
        if row[1].strip():
            items.append({
                'row': i,
                'num': row[0],
                'eng': row[1].strip(),
                'kr': row[2].strip() if len(row) > 2 else ''
            })

    similar_pairs = []
    for i, item1 in enumerate(items):
        for item2 in items[i+1:]:
            eng_sim = similar(item1['eng'], item2['eng'])
            kr_sim = similar(item1['kr'], item2['kr']) if item1['kr'] and item2['kr'] else 0

            # 한글명 100% 동일 = 진짜 중복 가능성 높음
            if kr_sim == 1.0 and item1['kr']:
                similar_pairs.append({
                    'item1': item1, 'item2': item2,
                    'eng_sim': eng_sim, 'kr_sim': kr_sim,
                    'priority': 'HIGH'
                })
            elif eng_sim >= threshold or kr_sim >= threshold:
                similar_pairs.append({
                    'item1': item1, 'item2': item2,
                    'eng_sim': eng_sim, 'kr_sim': kr_sim,
                    'priority': 'LOW'
                })

    return similar_pairs

def check_number_duplicates(data):
    """동일 번호 중복 체크"""
    from collections import Counter
    nums = [row[0].strip() for row in data[1:] if row[0].strip()]
    duplicates = {num: count for num, count in Counter(nums).items() if count > 1}

    if duplicates:
        print("🔴 동일 번호 중복:")
        for num, count in sorted(duplicates.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 0):
            print(f"   - {num}번: {count}회")
            for i, row in enumerate(data[1:], start=2):
                if row[0].strip() == num:
                    print(f"      Row {i}: {row[1]} | {row[2]}")
        return True
    return False

def main():
    print("=" * 60)
    print("        중복/유사 항목 자동 감지 보고서")
    print("=" * 60)

    data = get_sheet_data()
    print(f"\n총 항목: {len(data) - 1}개\n")

    # 1. 번호 중복
    print("-" * 40)
    has_num_dup = check_number_duplicates(data)
    if not has_num_dup:
        print("✅ 번호 중복 없음")

    # 2. 영문명 정확히 동일
    print("\n" + "-" * 40)
    has_eng_dup = check_exact_duplicates(data)
    if not has_eng_dup:
        print("✅ 영문명 정확히 동일한 중복 없음")

    # 3. 유사 항목
    print("\n" + "-" * 40)
    similar_pairs = check_similar_items(data)

    high_priority = [p for p in similar_pairs if p['priority'] == 'HIGH']
    low_priority = [p for p in similar_pairs if p['priority'] == 'LOW']

    if high_priority:
        print("🔴 높은 우선순위 (한글명 100% 동일 - 중복 가능성 높음):")
        for pair in high_priority:
            i1, i2 = pair['item1'], pair['item2']
            print(f"\n   [{i1['num']}] {i1['eng']} ({i1['kr']})")
            print(f"   [{i2['num']}] {i2['eng']} ({i2['kr']})")
            print(f"   → 확인 필요!")

    if low_priority:
        print(f"\n🟡 낮은 우선순위 (유사 항목 {len(low_priority)}쌍):")
        for pair in low_priority[:5]:  # 상위 5개만 표시
            i1, i2 = pair['item1'], pair['item2']
            print(f"   [{i1['num']}] {i1['eng']} ↔ [{i2['num']}] {i2['eng']} ({pair['eng_sim']:.0%})")
        if len(low_priority) > 5:
            print(f"   ... 외 {len(low_priority) - 5}쌍")

    if not similar_pairs:
        print("✅ 유사 항목 없음")

    print("\n" + "=" * 60)

    # 요약
    issues = sum([has_num_dup, has_eng_dup, len(high_priority) > 0])
    if issues == 0:
        print("✅ 모든 검사 통과!")
    else:
        print(f"⚠️  {issues}개 이슈 발견 - 확인 필요")

if __name__ == '__main__':
    main()
