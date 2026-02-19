#!/usr/bin/env python3
"""단일 폴더 테스트: 001_Pumpkin/02_Blog - 수정된 로직"""

import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"


def to_pascal_case(text):
    parts = text.split('_')
    return ''.join(word.capitalize() for word in parts if word)


def pascal_to_snake(text):
    return re.sub(r'(?<!^)(?=[A-Z])', '_', text).lower()


def is_pascal_case_naming(filename, food):
    pattern = rf'^{re.escape(food)}_(Blog|Insta|Common)_\d{{2}}_[A-Z][a-zA-Z]*\.(png|jpg)$'
    return bool(re.match(pattern, filename))


def rename_to_pascal(filename, food):
    food_snake = pascal_to_snake(food)
    food_lower = food.lower()

    # 패턴 1
    match = re.match(rf'^{re.escape(food_snake)}_(blog|insta)_(\d{{2}})_([a-z_]+)\.(png|jpg)$', filename.lower())
    if match:
        folder_type = match.group(1).capitalize()
        num = match.group(2)
        name_part = match.group(3)
        ext = match.group(4)
        pascal_name = to_pascal_case(name_part)
        return f"{food}_{folder_type}_{num}_{pascal_name}.{ext}"

    # 패턴 2
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
    folder = CONTENTS_DIR / "001_Pumpkin"
    food = "Pumpkin"
    blog_dir = folder / "02_Blog"

    print(f"Processing: {folder.name}/02_Blog")
    print(f"Food: {food}")
    print("-" * 50)

    renamed_count = 0

    for f in sorted(blog_dir.iterdir()):
        if f.is_file() and f.suffix.lower() in [".png", ".jpg"]:
            print(f"\nFile: {f.name}")

            if is_pascal_case_naming(f.name, food):
                print(f"  => KEEP (already PascalCase)")
            else:
                new_name = rename_to_pascal(f.name, food)
                if new_name:
                    if f.name == new_name:
                        print(f"  => KEEP (same name)")
                    else:
                        # 2단계 리네이밍
                        temp_path = blog_dir / f"_temp_{f.name}"
                        new_path = blog_dir / new_name
                        print(f"  => RENAME: {f.name} → {new_name}")
                        f.rename(temp_path)
                        temp_path.rename(new_path)
                        print(f"  => DONE")
                        renamed_count += 1
                else:
                    print(f"  => Would BACKUP (no pattern match)")

    print(f"\n{'='*50}")
    print(f"Renamed: {renamed_count} files")

    print(f"\n최종 파일 목록:")
    for f in sorted(blog_dir.iterdir()):
        if f.suffix.lower() in [".png", ".jpg"]:
            print(f"  {f.name}")


if __name__ == "__main__":
    main()
