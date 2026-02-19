#!/usr/bin/env python3
"""
sample_test.py - WO-SCHEMA-001 STEP 3
랜덤 5건 샘플 테스트
"""

import os
import sys
import json
import random
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.infographic_generator import generate_precautions

FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
TEST_OUTPUT_DIR = PROJECT_ROOT / "debug" / "step3_sample_test"


def main():
    print("━" * 50)
    print("STEP 3: 샘플 테스트 (랜덤 5건)")
    print("━" * 50)

    TEST_OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    # 랜덤 5건 선택
    keys = list(food_data.keys())
    sample_keys = random.sample(keys, min(5, len(keys)))

    print(f"테스트 대상: {sample_keys}")
    print()

    passed = 0
    failed = 0

    for key in sample_keys:
        food_info = food_data[key]
        food_ko = food_info.get("name", f"#{key}")
        safety = food_info.get("safety", "SAFE")
        precautions = food_info.get("precautions", [])

        output_path = TEST_OUTPUT_DIR / f"test_{key}_{food_ko}_slide06.png"

        try:
            generate_precautions(food_ko, precautions, "", safety, output_path)
            print(f"  #{key} {food_ko:<10} ✅ PASS")
            passed += 1
        except Exception as e:
            print(f"  #{key} {food_ko:<10} ❌ FAIL: {e}")
            failed += 1

    print()
    print("━" * 50)
    print("샘플 테스트 결과")
    print("━" * 50)
    print(f"PASS: {passed}건")
    print(f"FAIL: {failed}건")
    print(f"출력 경로: {TEST_OUTPUT_DIR}")

    return failed == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
