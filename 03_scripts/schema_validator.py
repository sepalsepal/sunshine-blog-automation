#!/usr/bin/env python3
"""
schema_validator.py - WO-SCHEMA-001 STEP 1
food_data.json 전체 스키마 검증

검증 항목:
- 필수 필드: name (name_ko), precautions
- 타입 검증: precautions가 str이면 위반
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"

def validate_schema():
    """food_data.json 스키마 검증"""
    print("━" * 50)
    print("STEP 1: 스키마 검증")
    print("━" * 50)

    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    total = len(food_data)
    valid_count = 0
    invalid_items = []

    for idx, (key, item) in enumerate(sorted(food_data.items(), key=lambda x: int(x[0]) if x[0].isdigit() else 999), 1):
        food_name = item.get("name", item.get("name_ko", f"#{key}"))
        errors = []

        # 1. 필수 필드 확인
        if not item.get("name") and not item.get("name_ko"):
            errors.append("name 필드 없음")

        # 2. precautions 타입 검증
        precautions = item.get("precautions")
        if precautions is None:
            # precautions 없음 - 경고
            errors.append("precautions 필드 없음")
        elif isinstance(precautions, str):
            # str 형태 - 위반
            errors.append(f"precautions: str (위반) → \"{precautions[:30]}...\"" if len(str(precautions)) > 30 else f"precautions: str (위반) → \"{precautions}\"")
        elif isinstance(precautions, list):
            # list 형태 - 내부 검증
            if len(precautions) == 0:
                pass  # 빈 리스트는 허용
            elif all(isinstance(p, dict) for p in precautions):
                pass  # list of dict - 정상
            elif all(isinstance(p, str) for p in precautions):
                pass  # list of str - 정상
            else:
                errors.append(f"precautions: 혼합 타입 (확인 필요)")
        elif isinstance(precautions, dict):
            errors.append("precautions: dict (확인 필요)")

        # 결과 출력
        if errors:
            status = "❌"
            invalid_items.append({
                "key": key,
                "name": food_name,
                "errors": errors
            })
        else:
            status = "✅"
            valid_count += 1

        print(f"[{idx:03d}/{total}] {food_name[:15]:<15} {status} {', '.join(errors) if errors else ''}")

    # 요약
    print()
    print("━" * 50)
    print("검증 결과 요약")
    print("━" * 50)
    print(f"전체: {total}건")
    print(f"정상: {valid_count}건")
    print(f"위반: {len(invalid_items)}건")

    if invalid_items:
        print()
        print("━" * 50)
        print("위반 항목 상세")
        print("━" * 50)
        for item in invalid_items:
            print(f"  #{item['key']} {item['name']}")
            for error in item['errors']:
                print(f"    → {error}")

    return {
        "total": total,
        "valid": valid_count,
        "invalid": len(invalid_items),
        "invalid_items": invalid_items
    }


if __name__ == "__main__":
    validate_schema()
