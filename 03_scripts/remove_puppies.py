#!/usr/bin/env python3
"""
퍼피 이미지 제거 스크립트 (김부장 총괄)

확인된 퍼피 이미지를 puppy_removed 폴더로 이동
CLAUDE.md 위반: "10살 시니어 느낌 (puppy/young 절대 금지)"
"""

import shutil
from pathlib import Path
from datetime import datetime

# 경로 설정
BASE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/content/images/sunshine/01_usable")
EXPRESSION_DIR = BASE_DIR / "expression"
LOCATION_DIR = BASE_DIR / "location"
PUPPY_DIR = BASE_DIR / "puppy_removed"

# 확인된 퍼피 목록 (수동 검토 완료)
PUPPY_FILES_EXPRESSION = [
    # happy_lay_indoor 0092-0101 구간 (10개)
    "haetsali_happy_lay_indoor_0092.jpg",
    "haetsali_happy_lay_indoor_0093.jpg",
    "haetsali_happy_lay_indoor_0094.jpg",
    "haetsali_happy_lay_indoor_0095.jpg",
    "haetsali_happy_lay_indoor_0096.jpg",
    "haetsali_happy_lay_indoor_0097.jpg",
    "haetsali_happy_lay_indoor_0098.jpg",
    "haetsali_happy_lay_indoor_0099.jpg",
    "haetsali_happy_lay_indoor_0100.jpg",
    "haetsali_happy_lay_indoor_0101.jpg",
]

PUPPY_FILES_LOCATION = [
    "haetsali_happy_walk_outdoor_0091.jpg",
    "haetsali_happy_walk_outdoor_0115.jpg",
    "haetsali_happy_walk_outdoor_0120.jpg",
    "haetsali_happy_walk_outdoor_0130.jpg",
]


def remove_puppies():
    """퍼피 이미지를 별도 폴더로 이동"""
    print("=" * 60)
    print("👔 김부장 총괄 - 퍼피 이미지 제거")
    print("=" * 60)

    # 퍼피 폴더 생성
    PUPPY_DIR.mkdir(exist_ok=True)
    (PUPPY_DIR / "expression").mkdir(exist_ok=True)
    (PUPPY_DIR / "location").mkdir(exist_ok=True)

    removed_count = 0
    not_found = []

    # expression 폴더 퍼피 제거
    print(f"\n📁 expression 폴더에서 {len(PUPPY_FILES_EXPRESSION)}개 제거 중...")
    for filename in PUPPY_FILES_EXPRESSION:
        src = EXPRESSION_DIR / filename
        dst = PUPPY_DIR / "expression" / filename

        if src.exists():
            shutil.move(str(src), str(dst))
            removed_count += 1
            print(f"   ✓ {filename}")
        else:
            not_found.append(filename)

    # location 폴더 퍼피 제거
    print(f"\n📁 location 폴더에서 {len(PUPPY_FILES_LOCATION)}개 제거 중...")
    for filename in PUPPY_FILES_LOCATION:
        src = LOCATION_DIR / filename
        dst = PUPPY_DIR / "location" / filename

        if src.exists():
            shutil.move(str(src), str(dst))
            removed_count += 1
            print(f"   ✓ {filename}")
        else:
            not_found.append(filename)

    print(f"\n✅ 제거 완료: {removed_count}개")
    if not_found:
        print(f"⚠️  파일 없음: {len(not_found)}개")
        for f in not_found:
            print(f"   - {f}")

    # 남은 이미지 수 확인
    exp_remaining = len(list(EXPRESSION_DIR.glob("*.jpg")))
    loc_remaining = len(list(LOCATION_DIR.glob("*.jpg")))

    print(f"\n📊 남은 A등급 이미지:")
    print(f"   expression: {exp_remaining}개")
    print(f"   location: {loc_remaining}개")
    print(f"   합계: {exp_remaining + loc_remaining}개")

    # 결과 기록
    log_path = PUPPY_DIR / "removal_log.txt"
    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"퍼피 이미지 제거 로그\n")
        f.write(f"실행 시간: {datetime.now().isoformat()}\n")
        f.write(f"제거된 파일: {removed_count}개\n\n")
        f.write("expression 폴더:\n")
        for filename in PUPPY_FILES_EXPRESSION:
            f.write(f"  - {filename}\n")
        f.write("\nlocation 폴더:\n")
        for filename in PUPPY_FILES_LOCATION:
            f.write(f"  - {filename}\n")

    print(f"\n📄 로그 저장: {log_path}")

    return removed_count


if __name__ == "__main__":
    removed = remove_puppies()

    print("\n" + "=" * 60)
    print(f"✅ 총 {removed}개 퍼피 이미지 제거 완료")
    print("=" * 60)
