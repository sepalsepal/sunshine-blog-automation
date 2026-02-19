#!/usr/bin/env python3
"""
notion_image_sync.py - 이미지_8, 햇살이실사_9 노션 동기화
WO-2026-0217: 김부장 지시 - 노션 싱크 작업
"""

import os
import sys
import re
import requests
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_VERSION = "2022-06-28"
CONTENTS_DIR = PROJECT_ROOT / "01_contents"


def get_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION
    }


def scan_image_status():
    """로컬 이미지 상태 스캔"""
    results = {}

    for folder in sorted(CONTENTS_DIR.iterdir()):
        if not folder.is_dir():
            continue

        match = re.match(r'^(\d{3})_', folder.name)
        if not match:
            continue

        num = int(match.group(1))
        if num == 0 or num == 999:
            continue

        # 블로그 폴더 확인
        blog_dir = folder / "blog"
        old_blog_dir = folder / "02_Blog"

        slide8_found = False
        slide9_found = False

        for blog_path in [blog_dir, old_blog_dir]:
            if blog_path.exists():
                for f in blog_path.iterdir():
                    if not f.is_file():
                        continue
                    fname = f.name.lower()
                    suffix = f.suffix.lower()

                    if suffix not in [".png", ".jpg", ".jpeg", ".webp"]:
                        continue

                    # 슬라이드 8: 08, _8_, cooking
                    if "_08_" in fname or "_8_" in fname or "08_" in fname or "cooking" in fname:
                        slide8_found = True

                    # 슬라이드 9: 09, _9_, cta, 마무리
                    if "_09_" in fname or "_9_" in fname or "09_" in fname or "cta" in fname:
                        slide9_found = True

        results[num] = {
            "slide8": slide8_found,
            "slide9": slide9_found
        }

    return results


def fetch_all_notion_pages():
    """Notion DB의 모든 페이지 가져오기"""
    pages = {}
    has_more = True
    start_cursor = None

    while has_more:
        url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
        payload = {"page_size": 100}
        if start_cursor:
            payload["start_cursor"] = start_cursor

        response = requests.post(url, headers=get_headers(), json=payload)

        if response.status_code != 200:
            print(f"❌ Notion API 오류: {response.status_code}")
            return pages

        data = response.json()

        for page in data.get("results", []):
            props = page.get("properties", {})
            num_prop = props.get("번호", {})
            num = num_prop.get("number")

            if num is not None:
                # 현재 이미지 상태 확인
                img8_prop = props.get("이미지_8", {})
                img9_prop = props.get("햇살이실사_9", {})

                img8_status = img8_prop.get("status", {}).get("name", "시작 전")
                img9_status = img9_prop.get("status", {}).get("name", "시작 전")

                pages[int(num)] = {
                    "id": page["id"],
                    "img8_current": img8_status,
                    "img9_current": img9_status
                }

        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return pages


def update_notion_image_status(page_id: str, slide8: bool, slide9: bool):
    """Notion 페이지 이미지 상태 업데이트"""
    properties = {
        "이미지_8": {
            "status": {"name": "완료" if slide8 else "시작 전"}
        },
        "햇살이실사_9": {
            "status": {"name": "완료" if slide9 else "시작 전"}
        }
    }

    url = f"https://api.notion.com/v1/pages/{page_id}"
    response = requests.patch(url, headers=get_headers(), json={"properties": properties})

    return response.status_code == 200


def main():
    print("━" * 60)
    print("📊 이미지_8 / 햇살이실사_9 노션 동기화")
    print("━" * 60)

    # 1. 로컬 이미지 상태 스캔
    print("\n📁 로컬 이미지 스캔 중...")
    local_status = scan_image_status()

    slide8_total = sum(1 for v in local_status.values() if v["slide8"])
    slide9_total = sum(1 for v in local_status.values() if v["slide9"])

    print(f"   슬라이드 8 완료: {slide8_total}건")
    print(f"   슬라이드 9 완료: {slide9_total}건")

    # 2. Notion 페이지 조회
    print("\n📋 Notion 페이지 조회 중...")
    notion_pages = fetch_all_notion_pages()
    print(f"   Notion: {len(notion_pages)}개 페이지")

    # 3. 변경 필요한 건 확인 및 업데이트
    print("\n🔄 동기화 실행 중...")

    changes_8 = []
    changes_9 = []
    updated = 0

    for num, local in sorted(local_status.items()):
        if num not in notion_pages:
            continue

        notion = notion_pages[num]

        # 현재 노션 상태
        notion_8 = notion["img8_current"] == "완료"
        notion_9 = notion["img9_current"] == "완료"

        # 로컬 상태
        local_8 = local["slide8"]
        local_9 = local["slide9"]

        # 변경 필요 여부
        need_update = (notion_8 != local_8) or (notion_9 != local_9)

        if need_update:
            success = update_notion_image_status(notion["id"], local_8, local_9)
            if success:
                updated += 1
                if notion_8 != local_8:
                    changes_8.append((num, "시작 전" if notion_8 else "완료", "완료" if local_8 else "시작 전"))
                if notion_9 != local_9:
                    changes_9.append((num, "시작 전" if notion_9 else "완료", "완료" if local_9 else "시작 전"))
                print(f"   ✅ {num:03d}: 8={('✅' if local_8 else '⬜')} 9={('✅' if local_9 else '⬜')}")

    # 4. 결과 보고
    print("\n" + "━" * 60)
    print("📊 이미지 상태 동기화 완료")
    print("━" * 60)
    print(f"✅ 업데이트: {updated}건")
    print(f"\n[이미지_8 변경]")
    if changes_8:
        for num, old, new in changes_8[:10]:
            print(f"   {num:03d}: {old} → {new}")
        if len(changes_8) > 10:
            print(f"   ... 외 {len(changes_8) - 10}건")
    else:
        print("   변경 없음")

    print(f"\n[햇살이실사_9 변경]")
    if changes_9:
        for num, old, new in changes_9[:10]:
            print(f"   {num:03d}: {old} → {new}")
        if len(changes_9) > 10:
            print(f"   ... 외 {len(changes_9) - 10}건")
    else:
        print("   변경 없음")

    # 미제작 목록
    missing_9 = [num for num, v in local_status.items() if not v["slide9"]]
    print(f"\n[햇살이실사_9 미제작] {len(missing_9)}건")
    print("   (전체 미제작 - 별도 제작 필요)")

    print("━" * 60)


if __name__ == "__main__":
    main()
