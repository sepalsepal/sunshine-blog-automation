#!/usr/bin/env python3
"""
regenerate_slide06.py - WO-SCHEMA-001 STEP 4
슬라이드06 재생성 (버그 수정 후)
"""

# ═══════════════════════════════════════════════════════════════
# 🔴 WO-FREEZE-001 동결
# ═══════════════════════════════════════════════════════════════
import sys
print("🔴 FROZEN: WO-FREEZE-001 동결 중. 실행 차단됨.")
print("   사유: 범위 초과 실행 방지")
print("   해제: PD 승인 + 김부장 동결해제 지시 필요")
sys.exit(1)
# ═══════════════════════════════════════════════════════════════

import os
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.infographic_generator import generate_precautions

CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]


def load_food_data():
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_all_folders():
    folders = []
    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    for item in CONTENTS_DIR.iterdir():
        if not item.is_dir():
            continue
        match = re.match(r'^(\d{3})_([a-z_]+)', item.name)
        if match:
            folders.append({
                "num": int(match.group(1)),
                "food_en": match.group(2),
                "path": item,
            })
    return sorted(folders, key=lambda x: x["num"])


def main():
    print("━" * 50)
    print("STEP 4: 슬라이드06 재생성")
    print("━" * 50)

    food_data = load_food_data()
    folders = get_all_folders()

    regenerated = 0
    skipped = 0
    errors = []

    for folder in folders:
        num = folder["num"]
        food_en = folder["food_en"]
        path = folder["path"]

        food_info = food_data.get(str(num))
        if not food_info:
            continue

        food_ko = food_info.get("name", "")
        safety = food_info.get("safety", "SAFE")
        precautions = food_info.get("precautions", [])

        # 2026-02-13: 플랫 구조 - blog → 02_Blog
        blog_dir = path / "02_Blog"
        if not blog_dir.exists():
            continue

        slide_06 = blog_dir / f"{food_en}_blog_06_caution.png"

        # 기존 파일 삭제 후 재생성
        if slide_06.exists():
            slide_06.unlink()

        try:
            generate_precautions(food_ko, precautions, "", safety, slide_06)
            print(f"[{num:03d}] {food_ko:<10} ✅ 재생성 완료")
            regenerated += 1
        except Exception as e:
            print(f"[{num:03d}] {food_ko:<10} ❌ {e}")
            errors.append(f"#{num} {food_ko}: {str(e)[:50]}")

    print()
    print("━" * 50)
    print("재생성 결과")
    print("━" * 50)
    print(f"재생성: {regenerated}건")
    print(f"에러: {len(errors)}건")

    if errors:
        print()
        print("에러 목록:")
        for e in errors[:10]:
            print(f"  ❌ {e}")


if __name__ == "__main__":
    main()
