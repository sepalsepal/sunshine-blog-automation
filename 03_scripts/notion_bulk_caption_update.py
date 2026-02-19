#!/usr/bin/env python3
"""
notion_bulk_caption_update.py - 블로그 캡션 상태 일괄 업데이트
사용법: python3 scripts/notion_bulk_caption_update.py
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


def get_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION
    }


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
            print(f"❌ API 오류: {response.status_code}")
            break

        data = response.json()
        pages.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return pages


def update_blog_caption_status(page_id: str, status: str):
    """블로그 캡션 상태 업데이트 (P2_블로그본문 속성 사용)"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "P2_블로그본문": {"select": {"name": status}}
        }
    }
    response = requests.patch(url, headers=get_headers(), json=payload)
    if response.status_code != 200:
        # 디버깅용 에러 출력
        print(f"      Error: {response.json().get('message', 'Unknown')[:50]}")
    return response.status_code == 200


def main():
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("🔄 노션 블로그 캡션 상태 일괄 업데이트")
    print("   1~20: 완료")
    print("   21+: 제작없음")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    pages = fetch_all_pages()
    print(f"📋 총 페이지: {len(pages)}개")

    completed = 0
    not_created = 0
    errors = 0

    for page in pages:
        props = page.get("properties", {})
        num = props.get("번호", {}).get("number")

        if num is None:
            continue

        # 1~20: 완료, 21+: 제작없음
        if 1 <= num <= 20:
            status = "완료"
            if update_blog_caption_status(page["id"], status):
                completed += 1
                print(f"   ✅ #{num:03d}: {status}")
            else:
                errors += 1
                print(f"   ❌ #{num:03d}: 업데이트 실패")
        else:
            status = "제작없음"
            if update_blog_caption_status(page["id"], status):
                not_created += 1
                if num <= 30 or num % 10 == 0:  # 처음 몇 개와 10단위만 출력
                    print(f"   ✅ #{num:03d}: {status}")
            else:
                errors += 1
                print(f"   ❌ #{num:03d}: 업데이트 실패")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"✅ 완료: {completed}개 (1~20)")
    print(f"📝 제작없음: {not_created}개 (21+)")
    if errors:
        print(f"❌ 오류: {errors}개")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


if __name__ == "__main__":
    main()
