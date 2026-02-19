#!/usr/bin/env python3
"""
블로그/인스타 이미지 정리
- 영어 네이밍 규칙이 아닌 이미지 → 백업
- 소문자 영어 → PascalCase로 리네이밍
"""

import re
import shutil
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
BACKUP_DIR = PROJECT_ROOT / "backups" / f"images_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"


def get_food_name(folder_name):
    """폴더명에서 음식명 추출"""
    match = re.match(r'^\d{3}_(.+)$', folder_name)
    return match.group(1) if match else None


def to_pascal_case(text):
    """snake_case → PascalCase"""
    parts = text.split('_')
    return ''.join(word.capitalize() for word in parts if word)


def is_english_naming(filename):
    """영어 네이밍인지 확인 (한글 없음)"""
    return not bool(re.search(r'[가-힣]', filename))


def is_pascal_case_naming(filename, food):
    """PascalCase 규칙 네이밍인지 확인"""
    # {Food}_Blog_0X_*.png 또는 {Food}_Insta_0X_*.png
    pattern = rf'^{re.escape(food)}_(Blog|Insta|Common)_\d{{2}}_[A-Z][a-zA-Z]*\.(png|jpg)$'
    return bool(re.match(pattern, filename))


def pascal_to_snake(text):
    """PascalCase → snake_case 변환"""
    # SweetPotato → sweet_potato
    return re.sub(r'(?<!^)(?=[A-Z])', '_', text).lower()


def rename_to_pascal(filename, food):
    """소문자 영어 파일을 PascalCase로 변환"""
    # pumpkin_blog_03_nutrition.png → Pumpkin_Blog_03_Nutrition.png
    # sweet_potato_blog_05_amount.png → SweetPotato_Blog_05_Amount.png

    # food를 snake_case로 변환
    food_snake = pascal_to_snake(food)  # SweetPotato → sweet_potato

    # 패턴 1: {food}_blog_0X_{name}.png
    match = re.match(rf'^{re.escape(food_snake)}_(blog|insta)_(\d{{2}})_([a-z_]+)\.(png|jpg)$', filename.lower())
    if match:
        folder_type = match.group(1).capitalize()
        num = match.group(2)
        name_part = match.group(3)
        ext = match.group(4)
        pascal_name = to_pascal_case(name_part)
        return f"{food}_{folder_type}_{num}_{pascal_name}.{ext}"

    # 패턴 2: {food}__blog_0X_{name}.png (더블 언더스코어)
    match = re.match(rf'^{re.escape(food_snake)}__(blog|insta)_(\d{{2}})_([a-z_]+)\.(png|jpg)$', filename.lower())
    if match:
        folder_type = match.group(1).capitalize()
        num = match.group(2)
        name_part = match.group(3)
        ext = match.group(4)
        pascal_name = to_pascal_case(name_part)
        return f"{food}_{folder_type}_{num}_{pascal_name}.{ext}"

    # 패턴 3: 단순 소문자 food (SweetPotato vs sweetpotato)
    food_lower = food.lower()  # SweetPotato → sweetpotato (no underscore)
    match = re.match(rf'^{re.escape(food_lower)}_(blog|insta)_(\d{{2}})_([a-z_]+)\.(png|jpg)$', filename.lower())
    if match:
        folder_type = match.group(1).capitalize()
        num = match.group(2)
        name_part = match.group(3)
        ext = match.group(4)
        pascal_name = to_pascal_case(name_part)
        return f"{food}_{folder_type}_{num}_{pascal_name}.{ext}"

    return None


def main():
    print("━━━━━ 블로그/인스타 이미지 정리 ━━━━━")

    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    print(f"백업 디렉토리: {BACKUP_DIR}")

    folders = sorted([f for f in CONTENTS_DIR.iterdir() if f.is_dir() and re.match(r'^\d{3}_', f.name)])

    stats = {
        "kept": 0,
        "renamed": 0,
        "moved": 0,
        "folders_processed": 0
    }

    moved_files = []
    renamed_files = []

    for folder in folders:
        food = get_food_name(folder.name)
        if not food:
            continue

        # 02_Blog 처리
        blog_dir = folder / "02_Blog"
        if blog_dir.exists():
            for f in list(blog_dir.iterdir()):
                if f.is_file() and f.suffix.lower() in [".png", ".jpg"]:
                    # 1. 이미 PascalCase 규칙이면 유지
                    if is_pascal_case_naming(f.name, food):
                        stats["kept"] += 1
                    # 2. 한글이 포함되면 백업
                    elif not is_english_naming(f.name):
                        backup_folder = BACKUP_DIR / folder.name / "02_Blog"
                        backup_folder.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(f), str(backup_folder / f.name))
                        stats["moved"] += 1
                        moved_files.append(f"{folder.name}/02_Blog/{f.name}")
                    # 3. 소문자 영어면 리네이밍 시도
                    else:
                        new_name = rename_to_pascal(f.name, food)
                        if new_name:
                            # macOS case-insensitive 파일시스템 대응:
                            # 이미 같은 이름이면 스킵 (case-sensitive 비교)
                            if f.name == new_name:
                                stats["kept"] += 1
                            else:
                                # 2단계 리네이밍 (case-insensitive 파일시스템에서 대소문자 변경)
                                temp_path = blog_dir / f"_temp_{f.name}"
                                new_path = blog_dir / new_name
                                f.rename(temp_path)
                                temp_path.rename(new_path)
                                stats["renamed"] += 1
                                renamed_files.append(f"{f.name} → {new_name}")
                        else:
                            # 리네이밍 불가면 백업
                            backup_folder = BACKUP_DIR / folder.name / "02_Blog"
                            backup_folder.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(f), str(backup_folder / f.name))
                            stats["moved"] += 1
                            moved_files.append(f"{folder.name}/02_Blog/{f.name}")

        # 01_Insta&Thread 처리
        insta_dir = folder / "01_Insta&Thread"
        if insta_dir.exists():
            for f in list(insta_dir.iterdir()):
                if f.is_file() and f.suffix.lower() in [".png", ".jpg"]:
                    # 1. 이미 PascalCase 규칙이면 유지
                    if is_pascal_case_naming(f.name, food):
                        stats["kept"] += 1
                    # 2. 한글이 포함되면 백업
                    elif not is_english_naming(f.name):
                        backup_folder = BACKUP_DIR / folder.name / "01_Insta&Thread"
                        backup_folder.mkdir(parents=True, exist_ok=True)
                        shutil.move(str(f), str(backup_folder / f.name))
                        stats["moved"] += 1
                        moved_files.append(f"{folder.name}/01_Insta&Thread/{f.name}")
                    # 3. 소문자 영어면 리네이밍 시도
                    else:
                        new_name = rename_to_pascal(f.name, food)
                        if new_name:
                            # macOS case-insensitive 파일시스템 대응
                            if f.name == new_name:
                                stats["kept"] += 1
                            else:
                                # 2단계 리네이밍 (case-insensitive 파일시스템에서 대소문자 변경)
                                temp_path = insta_dir / f"_temp_{f.name}"
                                new_path = insta_dir / new_name
                                f.rename(temp_path)
                                temp_path.rename(new_path)
                                stats["renamed"] += 1
                                renamed_files.append(f"{f.name} → {new_name}")
                        else:
                            # slide_XX.jpg 같은 레거시는 백업
                            backup_folder = BACKUP_DIR / folder.name / "01_Insta&Thread"
                            backup_folder.mkdir(parents=True, exist_ok=True)
                            shutil.move(str(f), str(backup_folder / f.name))
                            stats["moved"] += 1
                            moved_files.append(f"{folder.name}/01_Insta&Thread/{f.name}")

        stats["folders_processed"] += 1

    # 결과 출력
    print(f"\n[결과]")
    print(f"  처리 폴더: {stats['folders_processed']}개")
    print(f"  유지: {stats['kept']}개")
    print(f"  리네이밍: {stats['renamed']}개")
    print(f"  백업 이동: {stats['moved']}개")

    if renamed_files:
        print(f"\n[리네이밍된 파일] (처음 10개)")
        for f in renamed_files[:10]:
            print(f"  {f}")
        if len(renamed_files) > 10:
            print(f"  ... 외 {len(renamed_files) - 10}개")

    if moved_files:
        print(f"\n[백업 이동된 파일] (처음 20개)")
        for f in moved_files[:20]:
            print(f"  → {f}")
        if len(moved_files) > 20:
            print(f"  ... 외 {len(moved_files) - 20}개")

    # 검증
    print(f"\n[검증] 이미지 현황 (처음 3개 폴더)")
    for folder in folders[:3]:
        food = get_food_name(folder.name)
        print(f"  {folder.name}:")

        blog_dir = folder / "02_Blog"
        if blog_dir.exists():
            img_files = [f.name for f in blog_dir.iterdir() if f.suffix.lower() in [".png", ".jpg"]]
            print(f"    02_Blog: {img_files[:5]}{'...' if len(img_files) > 5 else ''}")

        insta_dir = folder / "01_Insta&Thread"
        if insta_dir.exists():
            img_files = [f.name for f in insta_dir.iterdir() if f.suffix.lower() in [".png", ".jpg"]]
            print(f"    01_Insta&Thread: {img_files[:5]}{'...' if len(img_files) > 5 else ''}")

    print(f"\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"백업 위치: {BACKUP_DIR}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    return stats


if __name__ == "__main__":
    main()
