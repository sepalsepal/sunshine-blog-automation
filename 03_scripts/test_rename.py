#!/usr/bin/env python3
"""테스트: rename_to_pascal 함수"""

import re


def to_pascal_case(text):
    """snake_case → PascalCase"""
    parts = text.split('_')
    return ''.join(word.capitalize() for word in parts if word)


def pascal_to_snake(text):
    """PascalCase → snake_case 변환"""
    # SweetPotato → sweet_potato
    return re.sub(r'(?<!^)(?=[A-Z])', '_', text).lower()


def rename_to_pascal(filename, food):
    """소문자 영어 파일을 PascalCase로 변환"""
    food_snake = pascal_to_snake(food)
    food_lower = food.lower()

    # 패턴 1: {food_snake}_(blog|insta)_XX_name.ext
    match = re.match(rf'^{re.escape(food_snake)}_(blog|insta)_(\d{{2}})_([a-z_]+)\.(png|jpg)$', filename.lower())
    if match:
        folder_type = match.group(1).capitalize()
        num = match.group(2)
        name_part = match.group(3)
        ext = match.group(4)
        pascal_name = to_pascal_case(name_part)
        return f"{food}_{folder_type}_{num}_{pascal_name}.{ext}"

    # 패턴 2: {food_lower}_(blog|insta)_XX_name.ext (no underscore)
    match = re.match(rf'^{re.escape(food_lower)}_(blog|insta)_(\d{{2}})_([a-z_]+)\.(png|jpg)$', filename.lower())
    if match:
        folder_type = match.group(1).capitalize()
        num = match.group(2)
        name_part = match.group(3)
        ext = match.group(4)
        pascal_name = to_pascal_case(name_part)
        return f"{food}_{folder_type}_{num}_{pascal_name}.{ext}"

    return None


if __name__ == "__main__":
    tests = [
        ("pumpkin_blog_03_nutrition.png", "Pumpkin"),
        ("sweet_potato_blog_03_nutrition.png", "SweetPotato"),
        ("sweetpotato_blog_03_nutrition.png", "SweetPotato"),
        ("pumpkin_blog_04_feeding.png", "Pumpkin"),
        ("pumpkin_blog_05_amount.png", "Pumpkin"),
    ]

    print("Testing rename_to_pascal:")
    for fn, food in tests:
        result = rename_to_pascal(fn, food)
        print(f"  {fn} + {food} => {result}")
