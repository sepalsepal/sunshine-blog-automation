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
CONTENTS_DIR = PROJECT_ROOT / "01_contents"

# 2026-02-13: 플랫 구조 - 상태는 폴더명이 아닌 별도 로직으로 판단
# FOLDER_STATUS_MAP 제거됨


def get_headers():
    """API 헤더 생성"""
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION
    }


def scan_local_contents():
    """로컬 콘텐츠 폴더 스캔 (플랫 구조)"""
    contents = {}

    # 2026-02-13: contents/ 직접 스캔 (플랫 구조)
    for item in CONTENTS_DIR.iterdir():
        if not item.is_dir() or item.name.startswith('.'):
            continue

        # 폴더명에서 번호 추출 (예: 001_Pumpkin)
        match = re.match(r'^(\d{3})_([A-Za-z]+)', item.name)
        if not match:
            continue

        content_num = int(match.group(1))  # 정수로 변환

        # 캡션 파일 존재 여부 확인 (새 폴더 구조)
        insta_dir = item / "01_Insta&Thread"
        blog_dir = item / "02_Blog"

        # PascalCase 캡션 파일 찾기
        insta_caption = any(insta_dir.glob("*_Insta_Caption.txt")) if insta_dir.exists() else False
        blog_caption = any(blog_dir.glob("*_Blog_Caption.txt")) if blog_dir.exists() else False
        thread_caption = any(insta_dir.glob("*_Threads_Caption.txt")) if insta_dir.exists() else False

        contents[content_num] = {
            "번호": content_num,
            "insta_caption": insta_caption,
            "blog_caption": blog_caption,
            "thread_caption": thread_caption,
        }

    return contents


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
    """Notion 페이지 업데이트

    WO-2026-0216-NOTION-SYNC: 스키마 싱크 수정
    - 삭제된 속성 제거: 인스타상태, Validator, insta_images, blog_images, 인스타URL
    - 타입 변경: insta_caption, blog_caption (checkbox → status)
    - 신규 추가: Thread_caption
    """
    properties = {
        "insta_caption": {
            "status": {"name": "완료" if local_data.get("insta_caption") else "시작 전"}
        },
        "blog_caption": {
            "status": {"name": "완료" if local_data.get("blog_caption") else "시작 전"}
        },
        "Thread_caption": {
            "status": {"name": "완료" if local_data.get("thread_caption") else "시작 전"}
        },
    }

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
    insta_cap_count = 0
    blog_cap_count = 0
    thread_cap_count = 0

    first_error = True
    for content_num, local_data in sorted(local_contents.items()):
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
                    insta_cap_count += 1
                if local_data.get("blog_caption"):
                    blog_cap_count += 1
                if local_data.get("thread_caption"):
                    thread_cap_count += 1

                # 캡션 상태 표시
                i_stat = "✅" if local_data.get("insta_caption") else "⬜"
                b_stat = "✅" if local_data.get("blog_caption") else "⬜"
                t_stat = "✅" if local_data.get("thread_caption") else "⬜"
                print(f"   ✅ {content_num:03d}: I{i_stat} B{b_stat} T{t_stat}")
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
    print(f"✅ 업데이트 성공: {updated}개")
    print(f"   ├─ 인스타캡션 완료: {insta_cap_count}개")
    print(f"   ├─ 블로그캡션 완료: {blog_cap_count}개")
    print(f"   └─ 쓰레드캡션 완료: {thread_cap_count}개")
    if not_found > 0:
        print(f"⚠️ Notion에 없음: {not_found}개")
    print("━" * 50)

    return True


def main():
    success = sync_to_notion()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
