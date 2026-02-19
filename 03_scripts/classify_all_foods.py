#!/usr/bin/env python3
"""
구글 시트 전체 안전도 분류 스크립트
- safety_classification.json 기반 + 수의학 자료 기반 추가 분류
- 로컬 CSV 업데이트 + Google Sheets 배치 업데이트

분류 기준:
  SAFE: 적정량 급여 안전
  CAUTION: 조건부 급여 가능 (주의사항 있음)
  DANGER: 건강 위험 가능성 높음
  FORBIDDEN: 절대 급여 금지 (치명적)

주요 위험 요인:
  - 양파/마늘 함유 → FORBIDDEN/DANGER
  - 알코올 → FORBIDDEN
  - 카페인 → FORBIDDEN
  - 초콜릿(테오브로민) → FORBIDDEN
  - 고염분/고당분 가공식품 → DANGER
  - 탄산음료 → DANGER
  - 견과류/뼈/씨앗 주의 → CAUTION
  - 반려견 전용 사료/간식 → SAFE
"""

import csv
import json
import os
import sys
import time
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

# ============================================================
# 전체 안전도 매핑 (영문명 기준)
# 출처: AKC, ASPCA, PetMD, safety_classification.json
# ============================================================

SAFETY_MAP = {
    # === safety_classification.json topics (27개) ===
    "grape": "FORBIDDEN",      # 급성 신부전, 소량도 치명적
    "cherry": "CAUTION",       # 씨/줄기 시안화물, 과육만 안전
    "mango": "CAUTION",        # 씨 제거 필수, 당분 높음
    "orange": "CAUTION",       # 과다 시 위장장애, 껍질 제거
    "peach": "CAUTION",        # 씨에 시안화물, 과육만 안전
    "kiwi": "CAUTION",         # 소량 안전, 과다 시 위장장애
    "papaya": "CAUTION",       # 씨/껍질 제거 필수, 당분 높음
    "broccoli": "CAUTION",     # 과다 시 가스 (이소티오시아네이트)
    "shrimp": "CAUTION",       # 반드시 익혀야, 껍질 제거
    "apple": "SAFE",           # 씨 제거, 비타민 A·C 풍부
    "banana": "SAFE",          # 소량 급여, 칼륨 풍부
    "blueberry": "SAFE",       # 항산화제 풍부
    "carrot": "SAFE",          # 저칼로리, 비타민 A
    "cucumber": "SAFE",        # 저칼로리, 수분 보충
    "pear": "SAFE",            # 씨 제거, 비타민 C
    "spinach": "SAFE",         # 소량 안전, 옥살산 주의
    "egg": "SAFE",             # 익혀서, 단백질 풍부
    "salmon": "SAFE",          # 반드시 익혀야, 오메가3
    "yogurt": "SAFE",          # 무설탕/무감미료만

    # === completed_external (6개) ===
    # onion, garlic: 시트에 없음
    "naengmyeon": "CAUTION",   # 면류, 조미료 주의
    "sandwich": "CAUTION",     # 가공식품, 재료에 따라 다름
    "cheetos": "DANGER",       # 고염분, 양파분말, 인공첨가물
    # potato: 시트에 없음

    # === 과일류 추가 ===
    "pumpkin": "SAFE",         # 식이섬유, 소화 도움 (수의사 권장)
    "sweet_potato": "SAFE",    # 비타민A, 식이섬유 (수의사 권장)
    "watermelon": "SAFE",      # 수분 보충, 씨/껍질 제거
    "strawberry": "SAFE",      # 비타민C, 항산화, 소량 안전
    "pineapple": "CAUTION",    # 산성, 고당분, 심/껍질 제거 필수
    "melon2": "SAFE",          # 멜론, 씨/껍질 제거 시 안전
    "pomegranate2": "CAUTION", # 석류, 씨앗 장폐색 위험, 타닌 함유
    "blackberry2": "SAFE",     # 블랙베리, 항산화 풍부

    # === 채소류 추가 ===
    "celery": "SAFE",          # 저칼로리, 비타민K
    "olive": "CAUTION",        # 소량 안전, 고나트륨 주의
    "rice": "SAFE",            # 쌀밥, 소화 좋음
    "tofu2": "SAFE",           # 두부, 소량 안전
    "root": "CAUTION",         # 연근, 소화 어려울 수 있음
    "root2": "CAUTION",        # 연근 (중복)
    "burdock": "CAUTION",      # 우엉, 고섬유 소화주의
    "burdock2": "CAUTION",     # 우엉 (중복)
    "sprouts": "SAFE",         # 숙주나물, 안전
    "sprouts2": "SAFE",
    "sprouts3": "SAFE",
    "sprouts4": "SAFE",
    "mushroom": "CAUTION",     # 마트 버섯 안전, 야생 독버섯 위험
    "beans": "SAFE",           # 그린빈, 저칼로리 안전
    "kimchi2": "DANGER",       # 김치: 마늘/양파/고춧가루 함유
    "nuts": "CAUTION",         # 견과류: 마카다미아 독성, 대부분 고지방
    "almonds": "CAUTION",      # 아몬드: 소화 어려움, 고지방

    # === 달걀류 ===
    "poached_egg": "SAFE",     # 수란, 익힌 달걀 안전
    "boiled_egg": "SAFE",      # 삶은달걀 안전
    "yolk": "SAFE",            # 달걀노른자 안전
    "egg2": "SAFE",            # 메추리알, 익힌 것 안전

    # === 육류/해산물 ===
    "breast": "SAFE",          # 닭가슴살, 무양념 안전
    "samgyeopsal": "CAUTION",  # 삼겹살: 고지방, 반드시 익혀야
    "tuna2": "CAUTION",        # 참치: 수은 축적 위험
    "mackerel2": "CAUTION",    # 고등어: 뼈/히스타민 주의, 익혀야
    "salmon2": "SAFE",         # 연어: 익힌 것 안전, 오메가3
    "fish": "SAFE",            # 흰살생선: 익힌 것 안전
    "dried_pollack": "SAFE",   # 황태: 건조 생선 안전

    # === 육류 가공식품 (양념/조리) ===
    "bulgogi": "DANGER",       # 불고기: 마늘/양파/간장/설탕 양념
    "chicken2": "DANGER",      # 후라이드치킨: 튀김, 고지방/고염분
    "dakgangjeong": "DANGER",  # 닭강정: 튀김+마늘소스
    "skewer": "DANGER",        # 닭꼬치: 양념+꼬치 위험
    "yangnyeom_chicken": "FORBIDDEN",  # 양념치킨: 마늘/양파 양념
    "sausage": "CAUTION",      # 소시지: 가공육, 고나트륨
    "meatball": "CAUTION",     # 미트볼: 양념 주의, 양파 가능
    "stick": "SAFE",           # 닭고기스틱: 반려견 간식 (143번, 반려견용)

    # === 면류/밥류 ===
    "udon": "CAUTION",         # 우동: 면+국물 나트륨 높음
    "kalguksu": "CAUTION",     # 칼국수: 면+국물 나트륨
    "jjajangmyeon": "DANGER",  # 짜장면: 양파 다량 함유
    "kimbap": "CAUTION",       # 김밥: 혼합 재료, 당근무해/단무지 고염분
    "bibimbap": "DANGER",      # 비빔밥: 고추장+참기름+마늘
    "tteokguk": "CAUTION",     # 떡국: 떡 질식위험, 국물 나트륨
    "tteokguk2": "CAUTION",    # 떡국 (중복)
    "toast": "CAUTION",        # 토스트: 소량 안전, 버터/잼 주의
    "baguette": "CAUTION",     # 바게트: 밀가루, 소량 안전
    "croissant": "CAUTION",    # 크루아상: 버터 고지방
    "pancake": "CAUTION",      # 팬케이크: 설탕/버터
    "waffle": "CAUTION",       # 와플: 설탕/버터

    # === 과자/사탕/초콜릿 ===
    "chocolate": "FORBIDDEN",  # 초콜릿: 테오브로민 독성 (치명적)
    "brownie": "FORBIDDEN",    # 브라우니: 초콜릿 함유
    "reeses": "FORBIDDEN",     # 리세스: 초콜릿 함유
    "kitkat": "FORBIDDEN",     # 킷캣: 초콜릿 함유
    "skittles": "DANGER",      # 스키틀즈: 고당분, 인공색소/향료
    "starburst": "DANGER",     # 스타버스트: 고당분, 인공첨가물
    "doritos": "DANGER",       # 도리토스: 양파/마늘분말, 고염분
    "pringles": "DANGER",      # 프링글스: 양파분말, 고염분
    "lays": "DANGER",          # 레이즈: 고염분, 양파/마늘분말 가능
    "ritz": "CAUTION",         # 리츠: 크래커, 고염분
    "poptarts": "DANGER",      # 팝타르트: 고당분, 인공첨가물
    "tarts": "DANGER",         # 팝타르트 (중복)
    "muffin": "CAUTION",       # 머핀: 설탕/버터, 초콜릿칩 가능
    "granola": "CAUTION",      # 그래놀라: 건포도/견과류/설탕 주의
    "cereal": "CAUTION",       # 시리얼: 설탕, 가공식품
    "cake": "DANGER",          # 케이크: 고당분, 초콜릿/자일리톨 가능
    "icecream": "DANGER",      # 아이스크림: 유당/설탕/자일리톨
    "icecream2": "DANGER",     # 아이스크림 (중복)

    # === 음료 ===
    "coca_cola": "DANGER",     # 코카콜라: 카페인, 탄산, 고당분
    "cola": "DANGER",          # 코카콜라 (중복)
    "fanta": "DANGER",         # 환타: 탄산, 고당분, 인공색소
    "sprite": "DANGER",        # 스프라이트: 탄산, 고당분
    "milkis": "DANGER",        # 밀키스: 탄산+유제품+설탕
    "milk": "DANGER",          # 바나나우유: 유당+설탕+인공향
    "coffee": "FORBIDDEN",     # 커피: 카페인 독성 (치명적)
    "beer": "FORBIDDEN",       # 맥주(카스): 알코올 독성
    "budweiser": "FORBIDDEN",  # 맥주(버드와이저): 알코올 독성
    "soju": "FORBIDDEN",       # 소주: 알코올 독성
    "perrier": "CAUTION",      # 페리에: 탄산수, 무해하나 가스 유발

    # === 반려견 전용 사료/간식 (브랜드) ===
    "hills": "SAFE",           # 힐스 사이언스 다이어트
    "diet": "SAFE",            # 힐스 사료
    "nutricore": "SAFE",       # 닥터뉴트리코어
    "iskhan": "SAFE",          # 이스칸
    "canin": "SAFE",           # 로얄캐닌
    "food": "SAFE",            # 시니어사료
    "food2": "SAFE",           # 사료
    "treat": "SAFE",           # 데이스포 (반려견 간식)
    "lid": "SAFE",             # 헬시트릿 LID
    "v2": "SAFE",              # 딸기 (v2 리메이크)

    # === 기타 ===
    "avocado": "CAUTION",      # 아보카도: 퍼신 독소(껍질/씨), 과육 소량 가능
}


FULL_FIELDNAMES = ['번호', '영문명', '한글명', '폴더명', '안전도', '게시상태', '게시일', '인스타URL']


def load_csv(csv_path: Path) -> list:
    """CSV 로드 (헤더에 누락된 열 보완)"""
    rows = []
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f, fieldnames=FULL_FIELDNAMES)
        header_skipped = False
        for row in reader:
            if not header_skipped:
                header_skipped = True
                continue  # 실제 헤더 행 스킵
            # None 키 제거
            clean = {k: v for k, v in row.items() if k is not None}
            rows.append(clean)
    return rows


def save_csv(csv_path: Path, rows: list, fieldnames: list = None):
    """CSV 저장"""
    fnames = fieldnames or FULL_FIELDNAMES
    with open(csv_path, 'w', encoding='utf-8', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=fnames, extrasaction='ignore')
        writer.writeheader()
        writer.writerows(rows)


def classify_local_csv():
    """로컬 CSV 안전도 업데이트"""
    csv_path = PROJECT_ROOT / 'config' / 'data' / 'published_contents.csv'

    if not csv_path.exists():
        print("❌ published_contents.csv 없음")
        return 0

    rows = load_csv(csv_path)
    print(f"📋 CSV 로드: {len(rows)}행")

    changed = 0
    unclassified = []

    for row in rows:
        topic_en = row.get('영문명', '').strip()
        current_safety = row.get('안전도', '').strip()

        if topic_en in SAFETY_MAP:
            new_safety = SAFETY_MAP[topic_en]
            if current_safety != new_safety:
                print(f"  ✏️  {topic_en} ({row.get('한글명','')}): {current_safety} → {new_safety}")
                row['안전도'] = new_safety
                changed += 1
        else:
            unclassified.append(f"{topic_en} ({row.get('한글명','')})")

    # 저장
    save_csv(csv_path, rows)

    print(f"\n✅ 로컬 CSV 업데이트: {changed}건 변경")

    if unclassified:
        print(f"\n⚠️  미분류 항목 ({len(unclassified)}건):")
        for item in unclassified:
            print(f"    - {item}")

    return changed


def update_google_sheet():
    """Google Sheets 안전도 배치 업데이트"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials
    except ImportError:
        print("❌ gspread 미설치. 로컬 CSV만 업데이트됨.")
        return False

    sheet_id = os.environ.get('GOOGLE_SHEET_ID')
    creds_path = os.environ.get('GOOGLE_CREDENTIALS_PATH')
    worksheet_name = os.environ.get('GOOGLE_WORKSHEET_NAME', '게시콘텐츠')

    if not sheet_id or not creds_path:
        print("❌ Google Sheets 환경변수 미설정. 로컬 CSV만 업데이트됨.")
        return False

    scopes = [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ]

    creds = Credentials.from_service_account_file(creds_path, scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open_by_key(sheet_id)
    worksheet = sheet.worksheet(worksheet_name)

    print(f"\n✅ Google Sheets 연결: {sheet.title} / {worksheet_name}")

    # 전체 데이터 읽기
    all_values = worksheet.get_all_values()
    if len(all_values) <= 1:
        print("⚠️ 시트에 데이터 없음")
        return False

    header = all_values[0]
    safety_col_idx = None
    en_col_idx = None

    for i, col in enumerate(header):
        if col.strip() == '안전도':
            safety_col_idx = i
        elif col.strip() == '영문명':
            en_col_idx = i

    if safety_col_idx is None or en_col_idx is None:
        print("❌ '안전도' 또는 '영문명' 컬럼을 찾을 수 없음")
        return False

    # 배치 업데이트 수집
    updates = []
    changed_count = 0

    for row_idx, row in enumerate(all_values[1:], start=2):  # 2행부터 (1-indexed)
        if len(row) <= max(safety_col_idx, en_col_idx):
            continue

        topic_en = row[en_col_idx].strip()
        current_safety = row[safety_col_idx].strip()

        if topic_en in SAFETY_MAP:
            new_safety = SAFETY_MAP[topic_en]
            if current_safety != new_safety:
                # gspread cell notation: column letter + row number
                col_letter = chr(ord('A') + safety_col_idx)
                cell = f"{col_letter}{row_idx}"
                updates.append({
                    'range': cell,
                    'values': [[new_safety]]
                })
                changed_count += 1

    if not updates:
        print("✅ Google Sheets: 변경 사항 없음 (이미 최신)")
        return True

    # 배치 업데이트 실행
    print(f"📝 Google Sheets: {changed_count}건 업데이트 중...")

    # gspread batch_update 사용
    worksheet.batch_update(updates)
    print(f"✅ Google Sheets 배치 업데이트 완료: {changed_count}건")

    return True


def apply_formatting():
    """포맷팅 적용 (format_google_sheets.py 호출)"""
    format_script = PROJECT_ROOT / 'services' / 'scripts' / 'format_google_sheets.py'
    if format_script.exists():
        print("\n🎨 포맷팅 적용 중...")
        os.system(f'cd "{PROJECT_ROOT}" && python "{format_script}"')
    else:
        print("⚠️ format_google_sheets.py 없음, 포맷팅 스킵")


def print_summary(rows: list):
    """분류 결과 요약"""
    from collections import Counter

    safety_count = Counter()
    for row in rows:
        safety = row.get('안전도', 'UNKNOWN')
        safety_count[safety] += 1

    print("\n" + "=" * 60)
    print("📊 전체 안전도 분류 결과")
    print("=" * 60)
    print(f"  총 항목: {len(rows)}건")
    print(f"  ✅ SAFE:      {safety_count.get('SAFE', 0)}건")
    print(f"  ⚠️  CAUTION:   {safety_count.get('CAUTION', 0)}건")
    print(f"  🔴 DANGER:    {safety_count.get('DANGER', 0)}건")
    print(f"  ⛔ FORBIDDEN: {safety_count.get('FORBIDDEN', 0)}건")

    # 등급별 상세 출력
    for grade in ['FORBIDDEN', 'DANGER', 'CAUTION']:
        items = [r for r in rows if r.get('안전도') == grade]
        if items:
            print(f"\n  --- {grade} ({len(items)}건) ---")
            for item in items:
                print(f"    {item.get('번호','?'):>3}. {item.get('한글명','')} ({item.get('영문명','')})")

    print("=" * 60)


def main():
    print("=" * 60)
    print("🏷️  구글 시트 전체 안전도 분류")
    print(f"   분류 기준: safety_classification.json + 수의학 자료")
    print(f"   총 매핑 수: {len(SAFETY_MAP)}개")
    print(f"   실행일: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 60)

    # 1. 로컬 CSV 업데이트
    print("\n[1/3] 로컬 CSV 분류 업데이트...")
    changed = classify_local_csv()

    # 2. 요약 출력
    csv_path = PROJECT_ROOT / 'config' / 'data' / 'published_contents.csv'
    rows = load_csv(csv_path)
    print_summary(rows)

    # 3. Google Sheets 업데이트
    print("\n[2/3] Google Sheets 업데이트...")
    sheet_updated = update_google_sheet()

    # 4. 포맷팅
    if sheet_updated:
        print("\n[3/3] 포맷팅 적용...")
        apply_formatting()
    else:
        print("\n[3/3] Google Sheets 미연결, 포맷팅 스킵")

    print("\n" + "=" * 60)
    print("✅ 분류 작업 완료")
    print("=" * 60)


if __name__ == '__main__':
    main()
