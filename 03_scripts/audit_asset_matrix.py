#!/usr/bin/env python3
"""
audit_asset_matrix.py - WO-FREEZE-001 조사 D
전체 어셋 현황 매트릭스
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]


def check_asset(folder_path, pattern):
    """어셋 존재 여부 확인"""
    for p in pattern:
        if list(folder_path.glob(p)):
            return True
    return False


def main():
    print("━" * 60)
    print("조사 D: 전체 어셋 현황 매트릭스")
    print("━" * 60)

    results = []
    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    for item in CONTENTS_DIR.iterdir():
        if not item.is_dir():
            continue
        match = re.match(r'^(\d{3})_([a-z_]+)', item.name)
        if not match:
            continue

        num = int(match.group(1))
        food_en = match.group(2)
        blog_dir = item / "02_Blog"
        insta_dir = item / "01_Insta&Thread"
        # 2026-02-13: captions 폴더는 플랫폼 폴더 내로 이동
        # captions_dir = item / "captions"

        assets = {
            "num": num,
            "folder": item.name,
            "status": "flat",  # 2026-02-13: 플랫 구조
            # 이미지 어셋
            "cover": check_asset(blog_dir, ["*_common_01_cover.png", "*01_cover*.png"]) if blog_dir.exists() else False,
            "food": check_asset(blog_dir, ["*_common_02_food.png", "*02_food*.png"]) if blog_dir.exists() else False,
            "slide_03": check_asset(blog_dir, ["*_blog_03_*.png", "*03*.png"]) if blog_dir.exists() else False,
            "slide_04": check_asset(blog_dir, ["*_blog_04_*.png", "*04*.png"]) if blog_dir.exists() else False,
            "slide_05": check_asset(blog_dir, ["*_blog_05_*.png", "*05*.png"]) if blog_dir.exists() else False,
            "slide_06": check_asset(blog_dir, ["*_blog_06_*.png", "*06*.png"]) if blog_dir.exists() else False,
            "slide_07": check_asset(blog_dir, ["*_blog_07_*.png", "*07*.png"]) if blog_dir.exists() else False,
            "cta": check_asset(blog_dir, ["*_common_08_cta.png", "*08_cta*.png"]) if blog_dir.exists() else False,
            "dog": check_asset(insta_dir, ["*_insta_03_dog.png", "*03_dog*.png"]) if insta_dir.exists() else False,
            # 캡션 - 2026-02-13: 플랫폼 폴더 내 caption.txt로 변경
            "insta_cap": (insta_dir / "caption.txt").exists() if insta_dir.exists() else False,
            "thread_cap": (insta_dir / "thread_caption.txt").exists() if insta_dir.exists() else False,
            "blog_cap": (blog_dir / "caption.txt").exists() if blog_dir.exists() else False,
        }

        # 어셋 카운트
        ai_assets = [assets["cover"], assets["slide_03"], assets["slide_04"],
                     assets["slide_05"], assets["slide_06"], assets["slide_07"],
                     assets["cta"], assets["insta_cap"], assets["thread_cap"], assets["blog_cap"]]
        pd_assets = [assets["food"], assets["dog"]]

        assets["ai_count"] = sum(ai_assets)
        assets["pd_count"] = sum(pd_assets)
        assets["total_count"] = assets["ai_count"] + assets["pd_count"]

        results.append(assets)

    results.sort(key=lambda x: x["num"])

    # 집계
    total = len(results)
    complete = [r for r in results if r["total_count"] == 12]
    ai_complete = [r for r in results if r["ai_count"] == 10]  # AI팀 10개
    partial = [r for r in results if 0 < r["total_count"] < 12]
    none = [r for r in results if r["total_count"] == 0]

    print(f"\n전체 폴더: {total}개")
    print(f"완전 완료 (12/12): {len(complete)}개")
    print(f"AI팀 완료 (10/10, PD 대기): {len(ai_complete)}개")
    print(f"부분 완료: {len(partial)}개")
    print(f"미착수: {len(none)}개")

    # 표 출력
    print(f"\n[어셋 매트릭스 - 처음 30건]")
    print(f"| # | cover | food | 03-07 | cta | dog | cap3 | AI | PD | 합계 |")
    print(f"|---|-------|------|-------|-----|-----|------|----|----|------|")
    for r in results[:30]:
        cover = "✅" if r["cover"] else "❌"
        food = "✅" if r["food"] else "❌"
        slides = "".join(["✅" if r[f"slide_{i:02d}"] else "❌" for i in range(3, 8)])
        cta = "✅" if r["cta"] else "❌"
        dog = "✅" if r["dog"] else "❌"
        caps = "".join(["✅" if r[c] else "❌" for c in ["insta_cap", "thread_cap", "blog_cap"]])
        print(f"| {r['num']:03d} | {cover} | {food} | {slides} | {cta} | {dog} | {caps} | {r['ai_count']:02d} | {r['pd_count']:02d} | {r['total_count']:02d} |")

    # AI팀 완료, PD 대기 목록
    pd_waiting = [r for r in results if r["ai_count"] >= 8 and r["pd_count"] < 2]
    print(f"\n[AI팀 완료, PD 대기] ({len(pd_waiting)}건)")
    print(f"  → food(02), dog(03) 이미지 필요")


if __name__ == "__main__":
    main()
