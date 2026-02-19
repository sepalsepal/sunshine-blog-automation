#!/usr/bin/env python3
"""
sync_folder_to_notion.py - 폴더 구조 스캔 → 노션 DB 업데이트
"""

import os
import sys
import requests
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_VERSION = "2022-06-28"

CONTENTS_DIR = PROJECT_ROOT / "01_contents"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["4_posted", "3_approved", "2_body_ready", "1_cover_only"]


def get_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION
    }


def add_properties_to_database():
    """노션 DB에 새 컬럼 추가"""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}"

    payload = {
        "properties": {
            "insta_images": {"number": {}},
            "blog_images": {"number": {}},
            "insta_caption": {"checkbox": {}},
            "blog_caption": {"checkbox": {}},
        }
    }

    response = requests.patch(url, headers=get_headers(), json=payload)
    if response.status_code == 200:
        print("✅ 노션 DB 컬럼 추가 완료")
        return True
    else:
        print(f"⚠️ 컬럼 추가 실패: {response.status_code}")
        print(f"   {response.text[:200]}")
        return False


def scan_folder(folder_path: Path) -> dict:
    """폴더 스캔해서 이미지 수와 캡션 존재 여부 확인"""
    result = {
        "insta_images": 0,
        "blog_images": 0,
        "insta_caption": False,
        "blog_caption": False,
    }

    if not folder_path.exists():
        return result

    # insta/ 폴더
    insta_dir = folder_path / "01_Insta&Thread"
    if insta_dir.exists():
        images = [f for f in insta_dir.iterdir()
                  if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
        result["insta_images"] = len(images)
        result["insta_caption"] = (insta_dir / "caption.txt").exists()

    # blog/ 폴더
    blog_dir = folder_path / "02_Blog"
    if blog_dir.exists():
        images = [f for f in blog_dir.iterdir()
                  if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
        result["blog_images"] = len(images)
        result["blog_caption"] = (blog_dir / "caption.txt").exists()

    return result


def find_content_folder(num: int) -> Path:
    """번호로 콘텐츠 폴더 찾기 - contents/ 직접 스캔"""
    num_str = f"{num:03d}"

    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    for item in CONTENTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith(num_str):
            return item

    return None


def fetch_notion_pages():
    """노션 DB에서 모든 페이지 가져오기"""
    pages = []
    has_more = True
    start_cursor = None

    while has_more:
        url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
        body = {"sorts": [{"property": "번호", "direction": "ascending"}]}
        if start_cursor:
            body["start_cursor"] = start_cursor

        response = requests.post(url, headers=get_headers(), json=body)
        if response.status_code != 200:
            print(f"❌ 노션 API 오류: {response.status_code}")
            break

        data = response.json()
        pages.extend(data.get("results", []))

        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return pages


def update_notion_page(page_id: str, data: dict):
    """노션 페이지 업데이트"""
    url = f"https://api.notion.com/v1/pages/{page_id}"

    payload = {
        "properties": {
            "insta_images": {"number": data["insta_images"]},
            "blog_images": {"number": data["blog_images"]},
            "insta_caption": {"checkbox": data["insta_caption"]},
            "blog_caption": {"checkbox": data["blog_caption"]},
        }
    }

    response = requests.patch(url, headers=get_headers(), json=payload)
    return response.status_code == 200


def main():
    print("━" * 60)
    print("📁 폴더 구조 → 노션 DB 동기화")
    print("━" * 60)

    # 1. 노션 DB 컬럼 추가
    print("\n📋 노션 DB 컬럼 추가 중...")
    add_properties_to_database()

    # 2. 노션 페이지 가져오기
    print("\n📋 노션 DB 조회 중...")
    pages = fetch_notion_pages()
    print(f"   {len(pages)}개 페이지")

    # 3. 각 페이지 업데이트
    print("\n🔄 폴더 스캔 및 업데이트 중...")
    updated = 0
    not_found = 0
    stats = {"insta_images": 0, "blog_images": 0, "insta_caption": 0, "blog_caption": 0}

    for page in pages:
        props = page.get("properties", {})
        num = props.get("번호", {}).get("number")

        if num is None:
            continue

        page_id = page["id"]

        # 폴더 찾기
        folder = find_content_folder(num)

        if folder:
            data = scan_folder(folder)
        else:
            data = {
                "insta_images": 0,
                "blog_images": 0,
                "insta_caption": False,
                "blog_caption": False,
            }
            not_found += 1

        # 통계
        stats["insta_images"] += data["insta_images"]
        stats["blog_images"] += data["blog_images"]
        if data["insta_caption"]:
            stats["insta_caption"] += 1
        if data["blog_caption"]:
            stats["blog_caption"] += 1

        # 업데이트
        if update_notion_page(page_id, data):
            updated += 1
            if (updated % 20) == 0:
                print(f"   진행: {updated}/{len(pages)}")

    # 4. 결과 보고
    print("\n" + "━" * 60)
    print("📊 동기화 완료")
    print("━" * 60)
    print(f"📋 노션 전체: {len(pages)}개")
    print(f"✅ 업데이트: {updated}개")
    print(f"❌ 폴더 없음: {not_found}개")
    print(f"\n📸 insta_images 총합: {stats['insta_images']}개")
    print(f"📝 blog_images 총합: {stats['blog_images']}개")
    print(f"✅ insta_caption 있음: {stats['insta_caption']}개")
    print(f"✅ blog_caption 있음: {stats['blog_caption']}개")
    print("━" * 60)


if __name__ == "__main__":
    main()
