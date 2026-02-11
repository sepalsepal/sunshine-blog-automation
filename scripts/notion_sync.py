#!/usr/bin/env python3
"""
notion_sync.py - 콘텐츠 폴더 → 노션 DB 동기화
WO-039: Google Sheets → Notion 전환

사용법: python3 scripts/notion_sync.py [--init]
"""

import os
import sys
import re
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

# === 설정 ===
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_VERSION = "2022-06-28"
CONTENTS_DIR = PROJECT_ROOT / "contents"

# 폴더 → 상태 매핑
FOLDER_STATUS_MAP = {
    "1_cover_only": "표지완료",
    "2_body_ready": "본문완료",
    "3_approved": "승인완료",
    "4_posted": "게시완료",
    "5_archived": "아카이브",
}


def get_headers():
    """API 헤더 생성"""
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION
    }


def scan_local_contents():
    """로컬 콘텐츠 폴더 스캔"""
    contents = {}

    for folder_name, status in FOLDER_STATUS_MAP.items():
        folder_path = CONTENTS_DIR / folder_name
        if not folder_path.exists():
            continue

        for item in folder_path.iterdir():
            if not item.is_dir() or item.name.startswith('.'):
                continue

            # 폴더명에서 번호 추출 (예: 060_fried_chicken_후라이드치킨)
            match = re.match(r'^(\d{3})_', item.name)
            if not match:
                continue

            content_num = int(match.group(1))  # 정수로 변환

            # 게시 URL 확인
            permalink = ""
            permalink_file = item / "permalink.txt"
            if permalink_file.exists():
                permalink = permalink_file.read_text().strip()

            # Validator 상태 확인
            validator_pass = check_validator_status(item)

            # 캡션 파일 존재 여부 확인
            insta_dir = item / "insta"
            blog_dir = item / "blog"
            insta_caption = (insta_dir / "caption.txt").exists() if insta_dir.exists() else False
            blog_caption = (blog_dir / "caption.txt").exists() if blog_dir.exists() else False

            # 이미지 개수 확인
            insta_images = 0
            blog_images = 0
            if insta_dir.exists():
                insta_images = len([f for f in insta_dir.iterdir()
                                   if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']])
            if blog_dir.exists():
                blog_images = len([f for f in blog_dir.iterdir()
                                  if f.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']])

            contents[content_num] = {
                "번호": content_num,
                "상태": status,
                "폴더경로": str(item),
                "게시URL": permalink,
                "Validator": "PASS" if validator_pass else "FAIL",
                "insta_caption": insta_caption,
                "blog_caption": blog_caption,
                "insta_images": insta_images,
                "blog_images": blog_images,
            }

    return contents


def check_validator_status(content_path: Path) -> bool:
    """콘텐츠 폴더의 Validator 상태 확인"""
    blog_dir = content_path / "blog"
    if not blog_dir.exists():
        return False

    # 8장 이미지 확인
    image_count = len(list(blog_dir.glob("*.png")))
    if image_count < 8:
        return False

    # 캡션 파일 확인
    caption_file = content_path / "caption_instagram.txt"
    if not caption_file.exists():
        return False

    return True


def fetch_all_notion_pages():
    """Notion DB의 모든 페이지 가져오기"""
    pages = {}
    has_more = True
    start_cursor = None

    while has_more:
        url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
        body = {}
        if start_cursor:
            body["start_cursor"] = start_cursor

        response = requests.post(url, headers=get_headers(), json=body)
        if response.status_code != 200:
            print(f"   ⚠️ API 오류: {response.status_code}")
            break

        data = response.json()

        for page in data.get("results", []):
            props = page.get("properties", {})
            # "번호" 속성 (number 타입)
            num = props.get("번호", {}).get("number")
            if num is not None:
                pages[int(num)] = {
                    "id": page["id"],
                    "properties": props,
                }

        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return pages


def update_notion_page(page_id: str, local_data: dict, debug: bool = False):
    """Notion 페이지 업데이트"""
    # 상태 매핑: 폴더명 → 노션 인스타상태 값
    status_map = {
        "표지완료": "표지완료",
        "본문완료": "본문완료",
        "승인완료": "승인완료",
        "게시완료": "게시완료",
        "아카이브": "게시완료",  # 아카이브는 게시완료로 처리
    }

    notion_status = status_map.get(local_data["상태"], "표지완료")

    properties = {
        "인스타상태": {"select": {"name": notion_status}},
        "Validator": {"select": {"name": local_data["Validator"]}},
        "insta_caption": {"checkbox": local_data.get("insta_caption", False)},
        "blog_caption": {"checkbox": local_data.get("blog_caption", False)},
        "insta_images": {"number": local_data.get("insta_images", 0)},
        "blog_images": {"number": local_data.get("blog_images", 0)},
    }

    permalink = local_data.get("게시URL")
    if permalink:
        properties["인스타URL"] = {"url": permalink}

    url = f"https://api.notion.com/v1/pages/{page_id}"
    response = requests.patch(url, headers=get_headers(), json={"properties": properties})

    if debug and response.status_code != 200:
        print(f"      DEBUG: {response.status_code} - {response.text[:200]}")

    return response.status_code == 200


def sync_to_notion():
    """메인 동기화 함수"""
    if not NOTION_DATABASE_ID or not NOTION_API_KEY:
        print("❌ NOTION_API_KEY 또는 NOTION_DATABASE_ID가 설정되지 않음")
        return False

    print("━" * 50)
    print("📊 Notion 동기화 시작")
    print("━" * 50)

    # 1. 로컬 콘텐츠 스캔
    print("\n📁 로컬 콘텐츠 폴더 스캔 중...")
    local_contents = scan_local_contents()
    print(f"   발견: {len(local_contents)}개 콘텐츠")

    # 2. Notion 페이지 조회
    print("\n📋 Notion 페이지 조회 중...")
    notion_pages = fetch_all_notion_pages()
    print(f"   Notion: {len(notion_pages)}개 페이지")

    # 3. 동기화 실행
    updated = 0
    not_found = 0

    print("\n🔄 동기화 실행 중...")
    insta_cap_updated = 0
    blog_cap_updated = 0

    first_error = True
    for content_num, local_data in local_contents.items():
        if content_num in notion_pages:
            notion_page = notion_pages[content_num]
            success = update_notion_page(
                page_id=notion_page["id"],
                local_data=local_data,
                debug=first_error,
            )
            if success:
                updated += 1
                if local_data.get("insta_caption"):
                    insta_cap_updated += 1
                if local_data.get("blog_caption"):
                    blog_cap_updated += 1
                print(f"   ✅ {content_num:03d}: {local_data['상태']} | 인스타캡션:{local_data.get('insta_caption')} 블로그캡션:{local_data.get('blog_caption')}")
            else:
                print(f"   ❌ {content_num:03d}: 업데이트 실패")
                first_error = False  # Only show debug for first error
        else:
            not_found += 1
            print(f"   ⚠️ {content_num:03d}: Notion에 없음")

    # 4. 결과 보고
    print("\n" + "━" * 50)
    print("📊 Notion 동기화 완료")
    print("━" * 50)
    print(f"📁 로컬 콘텐츠: {len(local_contents)}개")
    print(f"📋 Notion 전체: {len(notion_pages)}개")
    print(f"✅ 업데이트: {updated}개")
    print(f"   ├─ 인스타캡션 ✅: {insta_cap_updated}개")
    print(f"   └─ 블로그캡션 ✅: {blog_cap_updated}개")
    print(f"⚠️ Notion에 없음: {not_found}개")
    print("━" * 50)

    return True


def main():
    success = sync_to_notion()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
