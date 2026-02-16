#!/usr/bin/env python3
"""
notion_food_photo_sync.py - 음식사진_2 (Common_02_Food) 상태 노션 동기화
WO-2026-0216: 사진이미지 규칙
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


def scan_food_photos():
    """로컬 Common_02_Food 이미지 스캔"""
    results = {}
    
    for item in CONTENTS_DIR.iterdir():
        if not item.is_dir() or item.name.startswith('.'):
            continue
        
        match = re.match(r'^(\d{3})_([A-Za-z]+)', item.name)
        if not match:
            continue
        
        content_num = int(match.group(1))
        
        # Common_02_Food 파일 존재 여부
        food_photos = list(item.glob("*_Common_02_Food.png"))
        results[content_num] = len(food_photos) > 0
    
    return results


def fetch_notion_pages():
    """노션 페이지 가져오기"""
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
            break
        
        data = response.json()
        
        for page in data.get("results", []):
            props = page.get("properties", {})
            num = props.get("번호", {}).get("number")
            if num is not None:
                pages[int(num)] = page["id"]
        
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")
    
    return pages


def update_food_photo_status(page_id: str, has_photo: bool):
    """음식사진_2 상태 업데이트"""
    properties = {
        "음식사진_2": {
            "status": {"name": "완료" if has_photo else "PENDING"}
        }
    }
    
    url = f"https://api.notion.com/v1/pages/{page_id}"
    response = requests.patch(url, headers=get_headers(), json={"properties": properties})
    return response.status_code == 200


def main():
    print("━" * 50)
    print("📷 음식사진_2 노션 동기화")
    print("━" * 50)
    
    # 스캔
    print("\n📁 로컬 Common_02_Food 스캔 중...")
    food_photos = scan_food_photos()
    has_photo_count = sum(1 for v in food_photos.values() if v)
    print(f"   발견: {len(food_photos)}개 폴더 중 {has_photo_count}개 음식사진 보유")
    
    # 노션 조회
    print("\n📋 노션 페이지 조회 중...")
    notion_pages = fetch_notion_pages()
    print(f"   노션: {len(notion_pages)}개 페이지")
    
    # 동기화
    print("\n🔄 음식사진_2 상태 동기화 중...")
    updated = 0
    for num, has_photo in sorted(food_photos.items()):
        if num in notion_pages:
            success = update_food_photo_status(notion_pages[num], has_photo)
            if success:
                updated += 1
                status = "✅" if has_photo else "⬜"
                print(f"   {status} {num:03d}")
    
    print("\n" + "━" * 50)
    print(f"✅ 동기화 완료: {updated}개")
    print("━" * 50)


if __name__ == "__main__":
    main()
