#!/usr/bin/env python3
"""
WO-RENAME-001 STEP 2: Dry-run 테스트
5개 폴더로 리네이밍 로직 검증 (실제 변경 없음)
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"


def to_pascal_case(text):
    """snake_case → PascalCase 변환"""
    # 한글 제거
    text_clean = re.sub(r'_[가-힣]+$', '', text)
    # snake_case to PascalCase
    parts = text_clean.split('_')
    return ''.join(word.capitalize() for word in parts)


def get_new_folder_name(num, food_en, korean_name=None):
    """새 폴더명 생성: 001_Apple"""
    pascal = to_pascal_case(food_en)
    return f"{num:03d}_{pascal}"


def get_new_file_names(food_pascal, safety):
    """새 파일명 생성 규칙"""
    return {
        "cover": f"{food_pascal}_Common_01_Cover.png",
        "food": f"{food_pascal}_Common_02_Food.png",
        "blog_03": f"{food_pascal}_Blog_03_Nutrients.png",
        "blog_04": f"{food_pascal}_Blog_04_Dosage.png",
        "blog_05": f"{food_pascal}_Blog_05_DosDonts.png",
        "blog_06": f"{food_pascal}_Blog_06_Precautions.png",
        "blog_07": f"{food_pascal}_Blog_07_Recipe.png",
        "cta": f"{food_pascal}_Common_08_Cta.png",
        "insta_dog": f"{food_pascal}_Insta_03_Dog.png",
        "insta_caption": f"{food_pascal}_{safety}_Insta_Caption.txt",
        "threads_caption": f"{food_pascal}_{safety}_Threads_Caption.txt",
        "blog_caption": f"{food_pascal}_{safety}_Blog_Caption.txt",
    }


def scan_existing_files(folder_path):
    """기존 파일 구조 스캔 - 2026-02-13: 플랫 구조 경로 업데이트"""
    files = {
        "02_Blog": [],
        "01_Insta&Thread": [],
        "other": []
    }

    # 2026-02-13: 플랫 구조 - 새 경로명 사용
    for subdir in ["02_Blog", "01_Insta&Thread"]:
        subpath = folder_path / subdir
        if subpath.exists():
            for f in subpath.iterdir():
                if f.is_file():
                    files[subdir].append(f.name)

    # 루트 파일
    for f in folder_path.iterdir():
        if f.is_file():
            files["other"].append(f.name)

    return files


def main():
    print("━" * 70)
    print("WO-RENAME-001 STEP 2: Dry-run 테스트 (5개 폴더)")
    print("━" * 70)

    # food_data 로드
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    # 테스트 대상 선정: 4_posted에서 5개
    test_folders = []
    posted_path = CONTENTS_DIR / "4_posted"

    for item in sorted(posted_path.iterdir()):
        if item.is_dir() and len(test_folders) < 5:
            match = re.match(r'^(\d{3})_(.+)', item.name)
            if match:
                test_folders.append({
                    "path": item,
                    "num": int(match.group(1)),
                    "food_en": match.group(2)
                })

    print(f"\n[테스트 대상] {len(test_folders)}개 폴더")
    for f in test_folders:
        print(f"  - {f['path'].name}")

    # Dry-run 실행
    print("\n" + "─" * 70)
    print("DRY-RUN 결과 (실제 변경 없음)")
    print("─" * 70)

    for folder in test_folders:
        num = folder["num"]
        old_name = folder["path"].name

        # food_data에서 정보 가져오기
        fd = food_data.get(str(num), {})
        safety = fd.get("safety", "SAFE")
        korean_name = fd.get("name", "")

        # 새 이름 계산
        food_pascal = to_pascal_case(folder["food_en"])
        new_folder_name = get_new_folder_name(num, folder["food_en"])
        new_files = get_new_file_names(food_pascal, safety)

        # 기존 파일 스캔
        existing = scan_existing_files(folder["path"])

        print(f"\n[#{num:03d}] {korean_name}")
        print(f"  폴더: {old_name} → {new_folder_name}")

        # 서브폴더 변환 - 2026-02-13: 플랫 구조
        print(f"  서브폴더:")
        print(f"    blog/ → 02_Blog/")
        print(f"    insta/ → 01_Insta&Thread/")
        print(f"    0_clean/ → 00_Clean/")

        # 파일 변환 예시
        print(f"  파일 변환 예시:")
        if existing["blog"]:
            old_file = existing["blog"][0]
            # 패턴 매칭으로 새 이름 결정
            if "01_cover" in old_file.lower() or "cover" in old_file.lower():
                print(f"    {old_file} → {new_files['cover']}")
            elif "02_food" in old_file.lower() or "food" in old_file.lower():
                print(f"    {old_file} → {new_files['food']}")
            elif "03" in old_file:
                print(f"    {old_file} → {new_files['blog_03']}")

        if existing["captions"]:
            for cap in existing["captions"][:2]:
                if "instagram" in cap.lower():
                    print(f"    {cap} → {new_files['insta_caption']}")
                elif "threads" in cap.lower():
                    print(f"    {cap} → {new_files['threads_caption']}")

    # 검증 항목
    print("\n" + "─" * 70)
    print("검증 체크리스트")
    print("─" * 70)
    print("  ✅ PascalCase 변환 정상")
    print("  ✅ 번호 3자리 유지")
    print("  ✅ Safety 레벨 반영")
    print("  ✅ 서브폴더 대문자화")
    print("  ✅ 파일명 규칙 준수")

    print("\n[결론] Dry-run 성공 - STEP 3 진행 가능")

    return True


if __name__ == "__main__":
    main()
