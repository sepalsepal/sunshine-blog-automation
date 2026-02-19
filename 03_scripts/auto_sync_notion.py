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

CONTENTS_DIR = PROJECT_ROOT / "01_contents"
# 2026-02-13: 플랫 구조로 변경 - STATUS_DIRS 제거
# 이제 contents/ 직접 스캔


def get_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION
    }


def find_content_folder(num: int) -> Path:
    """번호로 콘텐츠 폴더 찾기 (플랫 구조)"""
    num_str = f"{num:03d}"
    # 2026-02-13: contents/ 직접 스캔 (플랫 구조)
    for item in CONTENTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith(num_str):
            return item
    return None


def scan_folder(folder_path: Path) -> dict:
    """폴더 스캔 (새 구조)"""
    result = {
        "insta_images": 0,
        "blog_images": 0,
        "insta_caption": False,
        "blog_caption": False,
        "thread_caption": False,
    }

    if not folder_path or not folder_path.exists():
        return result

    # 01_Insta&Thread/ (2026-02-13: 새 구조)
    insta_dir = folder_path / "01_Insta&Thread"
    if insta_dir.exists():
        images = [f for f in insta_dir.iterdir()
                  if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
        result["insta_images"] = len(images)
        result["insta_caption"] = any(insta_dir.glob("*_Insta_Caption.txt"))
        result["thread_caption"] = any(insta_dir.glob("*_Threads_Caption.txt"))

    # 02_Blog/ (2026-02-13: 새 구조)
    blog_dir = folder_path / "02_Blog"
    if blog_dir.exists():
        images = [f for f in blog_dir.iterdir()
                  if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
        result["blog_images"] = len(images)
        result["blog_caption"] = any(blog_dir.glob("*_Blog_Caption.txt"))

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
            "Thread_caption": {"checkbox": data["thread_caption"]},
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
        print(f"   thread: caption: {'O' if data['thread_caption'] else 'X'}")
        return True
    else:
        print(f"❌ #{content_num} 업데이트 실패")
        return False


def fetch_all_pages():
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
            break

        data = response.json()
        pages.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return pages


def sync_all():
    """전체 동기화"""
    from datetime import datetime
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"🔄 전체 동기화 시작: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    pages = fetch_all_pages()
    print(f"📋 노션 페이지: {len(pages)}개")

    updated = 0
    stats = {"insta_images": 0, "blog_images": 0, "insta_caption": 0, "blog_caption": 0, "thread_caption": 0}

    for page in pages:
        props = page.get("properties", {})
        num = props.get("번호", {}).get("number")
        if num is None:
            continue

        folder = find_content_folder(num)
        data = scan_folder(folder)

        # 통계
        stats["insta_images"] += data["insta_images"]
        stats["blog_images"] += data["blog_images"]
        if data["insta_caption"]:
            stats["insta_caption"] += 1
        if data["blog_caption"]:
            stats["blog_caption"] += 1
        if data["thread_caption"]:
            stats["thread_caption"] += 1

        if update_notion_page(page["id"], data):
            updated += 1
            if updated % 50 == 0:
                print(f"   진행: {updated}/{len(pages)}")

    print(f"\n✅ 동기화 완료: {updated}/{len(pages)}")
    print(f"📸 insta_images: {stats['insta_images']}개")
    print(f"📝 blog_images: {stats['blog_images']}개")
    print(f"✏️ insta_caption: {stats['insta_caption']}개")
    print(f"✏️ blog_caption: {stats['blog_caption']}개")
    print(f"🧵 thread_caption: {stats['thread_caption']}개")
    print(f"━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


def main():
    if len(sys.argv) < 2:
        print("사용법:")
        print("  python auto_sync_notion.py <번호>  - 단일 콘텐츠")
        print("  python auto_sync_notion.py --all   - 전체 동기화")
        return

    if sys.argv[1] == "--all":
        sync_all()
    else:
        try:
            content_num = int(sys.argv[1])
            sync_single(content_num)
        except ValueError:
            print("❌ 유효한 콘텐츠 번호를 입력하세요")


if __name__ == "__main__":
    main()
