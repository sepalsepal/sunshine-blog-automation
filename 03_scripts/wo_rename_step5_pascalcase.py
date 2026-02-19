#!/usr/bin/env python3
"""
WO-RENAME-001 STEP 5: PascalCase 리네이밍
- 폴더명: 001_pumpkin → 001_Pumpkin
- 서브폴더: blog/ → Blog/
- 파일명: PascalCase 적용
"""

import json
import re
import shutil
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"


def to_pascal_case(text):
    """snake_case → PascalCase 변환"""
    # 한글 제거 (나중에 다시 붙임)
    text_clean = re.sub(r'_[가-힣()]+$', '', text)
    # snake_case to PascalCase
    parts = text_clean.split('_')
    return ''.join(word.capitalize() for word in parts if word)


def rename_file_to_pascal(file_path, food_pascal, safety):
    """파일명을 PascalCase로 변환"""
    old_name = file_path.name
    new_name = None

    # 패턴 매칭
    patterns = {
        # 이미지 파일
        r'.*01[_-]?cover.*\.png$': f"{food_pascal}_Common_01_Cover.png",
        r'.*02[_-]?food.*\.png$': f"{food_pascal}_Common_02_Food.png",
        r'.*03[_-]?nutrient.*\.png$': f"{food_pascal}_Blog_03_Nutrients.png",
        r'.*04[_-]?dosage.*\.png$': f"{food_pascal}_Blog_04_Dosage.png",
        r'.*05[_-]?dos.*dont.*\.png$': f"{food_pascal}_Blog_05_DosDonts.png",
        r'.*06[_-]?precaution.*\.png$': f"{food_pascal}_Blog_06_Precautions.png",
        r'.*07[_-]?recipe.*\.png$': f"{food_pascal}_Blog_07_Recipe.png",
        r'.*08[_-]?cta.*\.png$': f"{food_pascal}_Common_08_Cta.png",
        r'.*03[_-]?dog.*\.png$': f"{food_pascal}_Insta_03_Dog.png",
        # 캡션 파일
        r'instagram[_-]?caption\.txt$': f"{food_pascal}_{safety}_Insta_Caption.txt",
        r'threads[_-]?caption\.txt$': f"{food_pascal}_{safety}_Threads_Caption.txt",
        r'blog[_-]?caption\.txt$': f"{food_pascal}_{safety}_Blog_Caption.txt",
    }

    for pattern, replacement in patterns.items():
        if re.match(pattern, old_name, re.IGNORECASE):
            new_name = replacement
            break

    return new_name


def main():
    print("━" * 70)
    print("WO-RENAME-001 STEP 5: PascalCase 리네이밍")
    print("━" * 70)

    # food_data 로드
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    # 통계
    folders_renamed = 0
    subfolders_renamed = 0
    files_renamed = 0
    errors = []

    # 콘텐츠 폴더 스캔
    for item in sorted(CONTENTS_DIR.iterdir()):
        if not item.is_dir():
            continue
        match = re.match(r'^(\d{3})_(.+)', item.name)
        if not match:
            continue

        num = int(match.group(1))
        old_food_name = match.group(2)

        # food_data에서 정보
        fd = food_data.get(str(num), {})
        safety = fd.get("safety", "SAFE")

        # PascalCase 변환
        food_pascal = to_pascal_case(old_food_name)
        new_folder_name = f"{num:03d}_{food_pascal}"

        try:
            # 1. 서브폴더 리네이밍 (blog → Blog, insta → Insta, captions → Captions)
            for old_sub, new_sub in [("blog", "Blog"), ("insta", "Insta"), ("captions", "Captions"), ("0_clean", "0_Clean")]:
                old_sub_path = item / old_sub
                new_sub_path = item / new_sub
                if old_sub_path.exists() and old_sub_path.name != new_sub:
                    # 파일 리네이밍 먼저
                    for f in old_sub_path.iterdir():
                        if f.is_file():
                            new_file_name = rename_file_to_pascal(f, food_pascal, safety)
                            if new_file_name and new_file_name != f.name:
                                new_file_path = old_sub_path / new_file_name
                                f.rename(new_file_path)
                                files_renamed += 1

                    # 서브폴더 리네이밍
                    old_sub_path.rename(new_sub_path)
                    subfolders_renamed += 1

            # 2. 폴더 리네이밍
            if item.name != new_folder_name:
                new_path = CONTENTS_DIR / new_folder_name
                item.rename(new_path)
                folders_renamed += 1

        except Exception as e:
            errors.append({"folder": item.name, "error": str(e)})

    # 결과 출력
    print(f"\n[리네이밍 완료]")
    print(f"  폴더: {folders_renamed}개")
    print(f"  서브폴더: {subfolders_renamed}개")
    print(f"  파일: {files_renamed}개")
    print(f"  오류: {len(errors)}개")

    if errors:
        print(f"\n[오류 목록]")
        for e in errors[:10]:
            print(f"  {e['folder']}: {e['error']}")

    # 샘플 확인
    print(f"\n[샘플 확인 - 처음 5개 폴더]")
    for item in sorted(CONTENTS_DIR.iterdir())[:5]:
        if item.is_dir() and re.match(r'^\d{3}_', item.name):
            print(f"  {item.name}/")
            for sub in sorted(item.iterdir()):
                if sub.is_dir():
                    print(f"    {sub.name}/")
                    for f in sorted(sub.iterdir())[:2]:
                        print(f"      {f.name}")

    print("\n" + "━" * 70)
    print("STEP 5 완료")
    print("━" * 70)

    return {
        "folders_renamed": folders_renamed,
        "subfolders_renamed": subfolders_renamed,
        "files_renamed": files_renamed,
        "errors": errors
    }


if __name__ == "__main__":
    main()
