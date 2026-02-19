#!/usr/bin/env python3
"""단일 폴더 테스트: 001_Pumpkin/02_Blog 처리"""

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
    result = bool(re.match(pattern, filename))
    print(f"  is_pascal_case_naming({filename}, {food}) => {result}")
    return result


def is_english_naming(filename):
    result = not bool(re.search(r'[가-힣]', filename))
    print(f"  is_english_naming({filename}) => {result}")
    return result


def rename_to_pascal(filename, food):
    food_snake = pascal_to_snake(food)
    food_lower = food.lower()

    print(f"  rename_to_pascal({filename}, {food})")
    print(f"    food_snake: {food_snake}, food_lower: {food_lower}")

    # 패턴 1
    pattern1 = rf'^{re.escape(food_snake)}_(blog|insta)_(\d{{2}})_([a-z_]+)\.(png|jpg)$'
    match = re.match(pattern1, filename.lower())
    print(f"    pattern1 match: {match is not None}")
    if match:
        folder_type = match.group(1).capitalize()
        num = match.group(2)
        name_part = match.group(3)
        ext = match.group(4)
        pascal_name = to_pascal_case(name_part)
        result = f"{food}_{folder_type}_{num}_{pascal_name}.{ext}"
        print(f"    => {result}")
        return result

    # 패턴 2
    pattern2 = rf'^{re.escape(food_lower)}_(blog|insta)_(\d{{2}})_([a-z_]+)\.(png|jpg)$'
    match = re.match(pattern2, filename.lower())
    print(f"    pattern2 match: {match is not None}")
    if match:
        folder_type = match.group(1).capitalize()
        num = match.group(2)
        name_part = match.group(3)
        ext = match.group(4)
        pascal_name = to_pascal_case(name_part)
        result = f"{food}_{folder_type}_{num}_{pascal_name}.{ext}"
        print(f"    => {result}")
        return result

    print(f"    => None")
    return None


def main():
    folder = CONTENTS_DIR / "001_Pumpkin"
    food = "Pumpkin"
    blog_dir = folder / "02_Blog"

    print(f"Processing: {folder.name}/02_Blog")
    print(f"Food: {food}")
    print("-" * 50)

    for f in sorted(blog_dir.iterdir()):
        if f.is_file() and f.suffix.lower() in [".png", ".jpg"]:
            print(f"\nFile: {f.name}")

            if is_pascal_case_naming(f.name, food):
                print(f"  => KEEP (already PascalCase)")
            elif not is_english_naming(f.name):
                print(f"  => BACKUP (Korean)")
            else:
                new_name = rename_to_pascal(f.name, food)
                if new_name:
                    new_path = blog_dir / new_name
                    if new_path.exists():
                        print(f"  => BACKUP (destination exists: {new_name})")
                    else:
                        print(f"  => RENAME to: {new_name}")
                        # Actually rename
                        f.rename(new_path)
                        print(f"  => DONE")
                else:
                    print(f"  => BACKUP (can't determine new name)")


if __name__ == "__main__":
    main()
