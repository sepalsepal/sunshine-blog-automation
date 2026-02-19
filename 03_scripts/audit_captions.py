#!/usr/bin/env python3
"""
audit_captions.py - WO-FREEZE-001 조사 C
캡션 미생성 원인 분석
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]


def main():
    print("━" * 60)
    print("조사 C: 캡션 미생성 원인 분석")
    print("━" * 60)

    # food_data 로드
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    food_data_keys = set(food_data.keys())

    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    results = []
    for item in CONTENTS_DIR.iterdir():
        if not item.is_dir():
            continue
        match = re.match(r'^(\d{3})_([a-z_]+)', item.name)
        if not match:
            continue

        num = int(match.group(1))
        food_en = match.group(2)

        # 2026-02-13: 플랫 구조 - 캡션은 플랫폼 폴더 내로 이동
        insta_dir = item / "01_Insta&Thread"
        blog_dir = item / "02_Blog"
        insta_cap = insta_dir / "caption.txt"
        thread_cap = insta_dir / "thread_caption.txt"
        blog_cap = blog_dir / "caption.txt"

        results.append({
            "num": num,
            "folder": item.name,
            "food_en": food_en,
            "in_food_data": str(num) in food_data_keys,
            "insta": insta_cap.exists(),
            "thread": thread_cap.exists(),
            "blog": blog_cap.exists(),
            "status": "flat"  # 2026-02-13: 플랫 구조
        })

    results.sort(key=lambda x: x["num"])

    # 집계
    total = len(results)
    full_caption = [r for r in results if r["insta"] and r["thread"] and r["blog"]]
    no_caption = [r for r in results if not r["insta"] and not r["thread"] and not r["blog"]]
    partial = [r for r in results if r not in full_caption and r not in no_caption]

    # 미생성 원인 분류
    no_food_data = [r for r in no_caption if not r["in_food_data"]]
    has_food_data_but_no_caption = [r for r in no_caption if r["in_food_data"]]

    print(f"\n전체 폴더: {total}개")
    print(f"캡션 완료 (3종 모두): {len(full_caption)}개")
    print(f"캡션 미생성: {len(no_caption)}개")
    print(f"부분 생성: {len(partial)}개")

    print(f"\n[미생성 원인 분류]")
    print(f"  food_data 없음: {len(no_food_data)}건")
    print(f"  food_data 있으나 미생성: {len(has_food_data_but_no_caption)}건 (코드 문제)")

    if no_food_data:
        print(f"\n[food_data 없어서 미생성] ({len(no_food_data)}건)")
        for r in no_food_data:
            print(f"  #{r['num']:03d}_{r['food_en']} ({r['status']})")

    if has_food_data_but_no_caption:
        print(f"\n[⚠️ food_data 있으나 미생성] ({len(has_food_data_but_no_caption)}건)")
        for r in has_food_data_but_no_caption:
            print(f"  #{r['num']:03d}_{r['food_en']} ({r['status']})")

    # 전체 표
    print(f"\n[전수조사표 - 처음 30건]")
    print(f"| # | food_data | 인스타 | 쓰레드 | 블로그 | 사유 |")
    print(f"|---|-----------|--------|--------|--------|------|")
    for r in results[:30]:
        fd = "✅" if r["in_food_data"] else "❌"
        insta = "✅" if r["insta"] else "❌"
        thread = "✅" if r["thread"] else "❌"
        blog = "✅" if r["blog"] else "❌"
        reason = "" if r["insta"] else ("food_data 없음" if not r["in_food_data"] else "???")
        print(f"| {r['num']:03d} | {fd} | {insta} | {thread} | {blog} | {reason} |")


if __name__ == "__main__":
    main()
