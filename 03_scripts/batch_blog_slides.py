#!/usr/bin/env python3
"""
batch_blog_slides.py - 블로그 슬라이드 3-7 일괄 생성
사용법: python3 scripts/batch_blog_slides.py [시작번호] [끝번호]
예: python3 scripts/batch_blog_slides.py 6 10
"""

import os
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT / "scripts"))

from infographic_generator import (
    generate_nutrition_info,
    generate_do_dont,
    generate_dosage_table,
    generate_precautions,
    generate_cooking_method
)

# 콘텐츠 폴더 매핑
CONTENT_FOLDERS = {
    6: "006_Apple",
    7: "007_Pineapple",
    8: "008_Banana",
    9: "009_Broccoli",
    10: "010_Watermelon",
}


def load_food_data(food_id: int) -> dict:
    """food_data.json에서 특정 음식 데이터 로드"""
    json_path = PROJECT_ROOT / "config" / "food_data.json"
    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get(str(food_id), {})


def generate_slides_for_food(food_id: int, food_data: dict, output_dir: Path):
    """특정 음식에 대해 슬라이드 3-7 생성"""
    name = food_data.get("name", "")
    english_name = food_data.get("english_name", "")
    safety = food_data.get("safety", "SAFE")

    print(f"\n{'='*60}")
    print(f"[{food_id:03d}] {name} ({english_name}) - {safety}")
    print(f"{'='*60}")

    # 출력 디렉토리 확인
    blog_dir = output_dir / "02_Blog"
    blog_dir.mkdir(parents=True, exist_ok=True)

    # 파일명 접두사 (소문자)
    prefix = english_name.lower().replace(" ", "_")

    # === 슬라이드 3: 영양정보 ===
    print("   [3] 영양정보 생성...")
    nutrients = food_data.get("nutrients", [])
    footnote = food_data.get("nutrition_footnote", f"{name}은 개체별 차이가 있으므로 반응을 보며 조절하세요")
    output_path = blog_dir / f"{prefix}_blog_03_nutrition.png"
    generate_nutrition_info(name, nutrients, safety, footnote, output_path)

    # === 슬라이드 4: DO/DON'T ===
    print("   [4] 급여 DO/DON'T 생성...")
    do_items = food_data.get("do_items", [])[:3]
    dont_items = food_data.get("dont_items", [])[:3]
    output_path = blog_dir / f"{prefix}_blog_04_feeding.png"
    generate_do_dont(name, do_items, dont_items, safety, output_path)

    # === 슬라이드 5: 급여량표 ===
    print("   [5] 급여량표 생성...")
    dosages = food_data.get("dosages", {})
    warning_text = food_data.get("dosage_warning", [])
    dosage_footnote = food_data.get("dosage_footnote", "개체별 차이가 있으므로 반응을 보며 조절하세요")
    output_path = blog_dir / f"{prefix}_blog_05_amount.png"
    generate_dosage_table(dosages, warning_text, dosage_footnote, safety, output_path)

    # === 슬라이드 6: 주의사항 ===
    print("   [6] 주의사항 생성...")
    precautions = food_data.get("precautions", [])
    emergency = food_data.get("precaution_emergency", "이상 증상 발견 시 즉시 수의사와 상담하세요")
    output_path = blog_dir / f"{prefix}_blog_06_caution.png"
    generate_precautions(name, precautions, emergency, safety, output_path)

    # === 슬라이드 7: 조리방법 ===
    print("   [7] 조리방법 생성...")
    cooking_steps = food_data.get("cooking_steps", [])
    cooking_tip = food_data.get("cooking_tip", f"{name}은 신선한 것으로 간단하게 준비해주세요")
    output_path = blog_dir / f"{prefix}_blog_07_cooking.png"
    generate_cooking_method(name, cooking_steps, cooking_tip, safety, output_path)

    print(f"   [OK] {name} 슬라이드 5개 생성 완료")


def main():
    print("=" * 60)
    print("블로그 슬라이드 일괄 생성기 v1.0")
    print("=" * 60)

    # 인자 파싱
    if len(sys.argv) >= 3:
        start_id = int(sys.argv[1])
        end_id = int(sys.argv[2])
    else:
        start_id = 6
        end_id = 10

    print(f"대상: {start_id}~{end_id}번")

    # 콘텐츠 폴더 베이스
    contents_dir = PROJECT_ROOT / "01_contents"

    success_count = 0
    error_count = 0

    for food_id in range(start_id, end_id + 1):
        folder_name = CONTENT_FOLDERS.get(food_id)
        if not folder_name:
            print(f"\n[SKIP] {food_id}번: 폴더 매핑 없음")
            continue

        output_dir = contents_dir / folder_name
        if not output_dir.exists():
            print(f"\n[SKIP] {food_id}번: 폴더 없음 ({output_dir})")
            continue

        food_data = load_food_data(food_id)
        if not food_data:
            print(f"\n[SKIP] {food_id}번: food_data.json에 데이터 없음")
            continue

        try:
            generate_slides_for_food(food_id, food_data, output_dir)
            success_count += 1
        except Exception as e:
            print(f"\n[ERROR] {food_id}번 생성 실패: {e}")
            error_count += 1

    print("\n" + "=" * 60)
    print(f"생성 완료: {success_count}개 성공, {error_count}개 실패")
    print("=" * 60)


if __name__ == "__main__":
    main()
