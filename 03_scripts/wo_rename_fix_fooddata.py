#!/usr/bin/env python3
"""
WO-RENAME-001: food_data.json 번호 체계 수정
기준: 로컬 폴더 번호
"""

import json
import re
import shutil
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]


def extract_food_name(folder_name):
    """폴더명에서 음식 영문명과 한글명 추출"""
    # 패턴: 123_food_name 또는 123_food_name_한글명
    match = re.match(r'^\d{3}_(.+)$', folder_name)
    if not match:
        return None, None

    name_part = match.group(1)

    # 한글이 포함된 경우 분리
    korean_match = re.search(r'_([가-힣]+)$', name_part)
    if korean_match:
        korean_name = korean_match.group(1)
        english_name = name_part[:korean_match.start()]
    else:
        korean_name = None
        english_name = name_part

    return english_name, korean_name


def normalize_name(name):
    """비교를 위한 이름 정규화"""
    if not name:
        return ""
    return name.lower().replace("_", "").replace(" ", "")


def main():
    print("━" * 70)
    print("WO-RENAME-001: food_data.json 번호 수정 (폴더 기준)")
    print("━" * 70)

    # 1. 백업 생성
    backup_path = FOOD_DATA_PATH.with_suffix(f'.json.backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}')
    shutil.copy(FOOD_DATA_PATH, backup_path)
    print(f"\n[백업 생성] {backup_path}")

    # 2. 기존 food_data 로드
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        old_food_data = json.load(f)

    # 음식 이름으로 인덱스 생성
    food_by_name = {}
    food_by_english = {}
    for key, value in old_food_data.items():
        name = value.get("name", "")
        english = value.get("english_name", "")
        food_by_name[name] = {"key": key, "data": value}
        # 영문명에서 한글 제거하고 저장
        eng_clean = re.sub(r'_[가-힣]+$', '', english).lower()
        food_by_english[eng_clean] = {"key": key, "data": value}

    # 3. 폴더 스캔 - 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    folder_foods = []
    for item in CONTENTS_DIR.iterdir():
        if not item.is_dir():
            continue
        match = re.match(r'^(\d{3})_(.+)', item.name)
        if match:
            num = int(match.group(1))
            food_part = match.group(2)

            # 한글명 분리
            korean_match = re.search(r'_([가-힣]+)$', food_part)
            if korean_match:
                korean_name = korean_match.group(1)
                english_name = food_part[:korean_match.start()]
            else:
                korean_name = None
                english_name = food_part

            folder_foods.append({
                "num": num,
                "folder_name": item.name,
                "english_name": english_name,
                "korean_name": korean_name,
                "status": "contents"  # flat structure
            })

    folder_foods.sort(key=lambda x: x["num"])
    print(f"\n[폴더 스캔] {len(folder_foods)}개 발견")

    # 4. 새 food_data 생성
    new_food_data = {}
    matched = []
    not_found = []

    for folder in folder_foods:
        num = folder["num"]
        eng_clean = folder["english_name"].lower()
        korean = folder["korean_name"]

        # 매칭 시도 (영문명 우선)
        found_data = None

        # 1) 영문명으로 찾기
        if eng_clean in food_by_english:
            found_data = food_by_english[eng_clean]["data"].copy()
            matched.append((num, folder["folder_name"], "영문명 매칭"))
        # 2) 한글명으로 찾기
        elif korean and korean in food_by_name:
            found_data = food_by_name[korean]["data"].copy()
            matched.append((num, folder["folder_name"], "한글명 매칭"))
        # 3) 기존 번호로 찾기 (1~136 범위에서)
        elif str(num) in old_food_data and num <= 136:
            # 기존 데이터 사용 (번호 유지된 항목)
            found_data = old_food_data[str(num)].copy()
            matched.append((num, folder["folder_name"], "번호 유지"))

        if found_data:
            # english_name 업데이트 (폴더명 형식으로)
            if korean:
                found_data["english_name"] = f"{folder['english_name']}_{korean}"
            else:
                found_data["english_name"] = folder["english_name"]
            new_food_data[str(num)] = found_data
        else:
            not_found.append(folder)

    # 5. 결과 출력
    print(f"\n[매칭 결과]")
    print(f"  성공: {len(matched)}건")
    print(f"  실패: {len(not_found)}건")

    if not_found:
        print(f"\n[⚠️ 매칭 실패 - 새 데이터 필요] ({len(not_found)}건)")
        for f in not_found:
            print(f"  #{f['num']:03d} {f['folder_name']}")

    # 6. 변경 사항 요약
    old_keys = set(old_food_data.keys())
    new_keys = set(new_food_data.keys())

    added = new_keys - old_keys
    removed = old_keys - new_keys

    print(f"\n[변경 요약]")
    print(f"  기존 항목: {len(old_keys)}개")
    print(f"  새 항목: {len(new_keys)}개")
    print(f"  추가된 번호: {len(added)}개")
    print(f"  제거된 번호: {len(removed)}개")

    # 7. 저장
    with open(FOOD_DATA_PATH, "w", encoding="utf-8") as f:
        json.dump(new_food_data, f, ensure_ascii=False, indent=2)

    print(f"\n[저장 완료] {FOOD_DATA_PATH}")
    print(f"[백업 위치] {backup_path}")

    # 8. 검증
    print("\n" + "━" * 70)
    print("검증: 번호 체계 정합성")
    print("━" * 70)

    # 다시 로드해서 검증
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        verify_data = json.load(f)

    verify_keys = set(int(k) for k in verify_data.keys())
    folder_nums = set(f["num"] for f in folder_foods)

    both = verify_keys & folder_nums
    data_only = verify_keys - folder_nums
    folder_only = folder_nums - verify_keys

    print(f"  양쪽 존재: {len(both)}개")
    print(f"  food_data만: {len(data_only)}개 {sorted(data_only) if data_only else ''}")
    print(f"  폴더만: {len(folder_only)}개")

    if folder_only:
        print(f"\n[폴더만 있는 항목 - food_data 추가 필요]")
        for num in sorted(folder_only):
            folder = next(f for f in folder_foods if f["num"] == num)
            print(f"  #{num:03d} {folder['folder_name']}")

    return {
        "matched": len(matched),
        "not_found": not_found,
        "backup": str(backup_path)
    }


if __name__ == "__main__":
    main()
