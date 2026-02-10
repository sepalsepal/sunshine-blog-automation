#!/usr/bin/env python3
"""
auto_sync_notion.py - 폴더 변경 시 노션 자동 동기화
단일 콘텐츠 또는 전체 동기화 지원
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

CONTENTS_DIR = PROJECT_ROOT / "contents"
STATUS_DIRS = ["4_posted", "3_approved", "2_body_ready", "1_cover_only"]


def get_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION
    }


def find_content_folder(num: int) -> Path:
    """번호로 콘텐츠 폴더 찾기"""
    num_str = f"{num:03d}"
    for status_dir in STATUS_DIRS:
        status_path = CONTENTS_DIR / status_dir
        if not status_path.exists():
            continue
        for item in status_path.iterdir():
            if item.is_dir() and item.name.startswith(num_str):
                return item
    return None


def scan_folder(folder_path: Path) -> dict:
    """폴더 스캔"""
    result = {
        "insta_images": 0,
        "blog_images": 0,
        "insta_caption": False,
        "blog_caption": False,
    }

    if not folder_path or not folder_path.exists():
        return result

    # insta/
    insta_dir = folder_path / "insta"
    if insta_dir.exists():
        images = [f for f in insta_dir.iterdir()
                  if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
        result["insta_images"] = len(images)
        result["insta_caption"] = (insta_dir / "caption.txt").exists()

    # blog/
    blog_dir = folder_path / "blog"
    if blog_dir.exists():
        images = [f for f in blog_dir.iterdir()
                  if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
        result["blog_images"] = len(images)
        result["blog_caption"] = (blog_dir / "caption.txt").exists()

    return result


def find_notion_page(content_num: int):
    """노션에서 해당 번호의 페이지 찾기"""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    body = {
        "filter": {
            "property": "번호",
            "number": {"equals": content_num}
        }
    }
    response = requests.post(url, headers=get_headers(), json=body)
    if response.status_code == 200:
        results = response.json().get("results", [])
        if results:
            return results[0]
    return None


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


def sync_single(content_num: int):
    """단일 콘텐츠 동기화"""
    print(f"🔄 콘텐츠 #{content_num} 동기화 중...")

    # 폴더 찾기
    folder = find_content_folder(content_num)
    data = scan_folder(folder)

    # 노션 페이지 찾기
    page = find_notion_page(content_num)
    if not page:
        print(f"❌ 노션에서 #{content_num} 페이지를 찾을 수 없습니다")
        return False

    # 업데이트
    if update_notion_page(page["id"], data):
        print(f"✅ #{content_num} 동기화 완료")
        print(f"   insta: {data['insta_images']}장, caption: {'O' if data['insta_caption'] else 'X'}")
        print(f"   blog: {data['blog_images']}장, caption: {'O' if data['blog_caption'] else 'X'}")
        return True
    else:
        print(f"❌ #{content_num} 업데이트 실패")
        return False


def main():
    if len(sys.argv) < 2:
        print("사용법: python auto_sync_notion.py <콘텐츠번호>")
        print("예시: python auto_sync_notion.py 42")
        print("전체 동기화: python sync_folder_to_notion.py")
        return

    try:
        content_num = int(sys.argv[1])
        sync_single(content_num)
    except ValueError:
        print("❌ 유효한 콘텐츠 번호를 입력하세요")


if __name__ == "__main__":
    main()
