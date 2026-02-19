#!/usr/bin/env python3
"""
Notion 게시 상태 업데이트
- 011 딸기: Thread 게시 완료
- 037 콜리플라워: Instagram + Thread 게시 완료
"""

import os
import requests
from dotenv import load_dotenv
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

headers = {
    "Authorization": f"Bearer {NOTION_API_KEY}",
    "Content-Type": "application/json",
    "Notion-Version": "2022-06-28"
}

def find_page(number: int):
    """번호로 페이지 찾기"""
    url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
    payload = {"filter": {"property": "번호", "number": {"equals": number}}}
    resp = requests.post(url, headers=headers, json=payload)
    data = resp.json()
    if data.get("results"):
        return data["results"][0]["id"]
    return None

def update_page(page_id: str, properties: dict):
    """페이지 업데이트"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    resp = requests.patch(url, headers=headers, json={"properties": properties})
    return resp.status_code == 200

def main():
    print("=" * 50)
    print("Notion 게시 상태 업데이트")
    print("=" * 50)

    # 011 딸기 - Thread 완료
    page_011 = find_page(11)
    if page_011:
        props_011 = {
            "쓰레드게시": {"status": {"name": "완료"}}
        }
        if update_page(page_011, props_011):
            print("✅ 011 딸기: Thread 게시 완료 업데이트")
        else:
            print("❌ 011 딸기: 업데이트 실패")
    else:
        print("⚠️ 011 딸기: 페이지 없음")

    # 037 콜리플라워 - Instagram + Thread 완료
    page_037 = find_page(37)
    if page_037:
        props_037 = {
            "인스타게시": {"status": {"name": "완료"}},
            "쓰레드게시": {"status": {"name": "완료"}}
        }
        if update_page(page_037, props_037):
            print("✅ 037 콜리플라워: Instagram + Thread 게시 완료 업데이트")
        else:
            print("❌ 037 콜리플라워: 업데이트 실패")
    else:
        print("⚠️ 037 콜리플라워: 페이지 없음")

    print("=" * 50)
    print("완료")

if __name__ == "__main__":
    main()
