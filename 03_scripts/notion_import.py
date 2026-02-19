#!/usr/bin/env python3
"""
notion_import.py - CSV에서 Notion DB로 전체 가져오기
기존 데이터 삭제 후 새로 입력
"""

import os
import sys
import csv
import requests
import time
from pathlib import Path
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_VERSION = "2022-06-28"

CSV_PATH = "/Users/al02399300/Downloads/Sunshine - 게시콘텐츠 (6).csv"


def get_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION
    }


def read_csv_data():
    """CSV 파일에서 데이터 읽기"""
    data = []
    with open(CSV_PATH, 'r', encoding='utf-8') as f:
        reader = csv.reader(f)
        rows = list(reader)

    # 데이터 추출 (3행부터, 번호가 있는 행만)
    for row in rows[3:]:
        if row and row[0] and row[0].isdigit():
            data.append({
                '번호': int(row[0]),
                '영문명': row[1] if len(row) > 1 else '',
                '한글명': row[2] if len(row) > 2 else '',
                '폴더명': row[3] if len(row) > 3 else '',
                '안전도': row[4] if len(row) > 4 else '',
                '인스타상태': row[5] if len(row) > 5 else '',
                '쓰레드상태': row[6] if len(row) > 6 else '',
                '블로그상태': row[7] if len(row) > 7 else '',
            })
    return data


def get_all_page_ids():
    """기존 모든 페이지 ID 가져오기"""
    page_ids = []
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
            page_ids.append(page["id"])

        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return page_ids


def delete_page(page_id):
    """페이지 삭제 (아카이브)"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    response = requests.patch(url, headers=get_headers(), json={"archived": True})
    return response.status_code == 200


def create_page(item):
    """새 페이지 생성"""
    # 상태 매핑
    status_map = {
        'posted': '게시완료',
        'approved': '승인완료',
        'body_ready': '본문완료',
        'cover_only': '표지완료',
        '': '',
    }

    insta_status = status_map.get(item['인스타상태'], item['인스타상태'])
    threads_status = status_map.get(item['쓰레드상태'], item['쓰레드상태'])
    blog_status = status_map.get(item['블로그상태'], item['블로그상태'])

    properties = {
        "이름": {"title": [{"text": {"content": item['영문명']}}]},
        "번호": {"number": item['번호']},
        "한글명": {"rich_text": [{"text": {"content": item['한글명']}}]},
        "폴더명": {"rich_text": [{"text": {"content": item['폴더명']}}]},
    }

    # 안전도 (있는 경우만)
    if item['안전도']:
        properties["안전도"] = {"select": {"name": item['안전도']}}

    # 상태들 (있는 경우만)
    if insta_status:
        properties["인스타상태"] = {"select": {"name": insta_status}}
    if threads_status:
        properties["쓰레드상태"] = {"select": {"name": threads_status}}
    if blog_status:
        properties["블로그상태"] = {"select": {"name": blog_status}}

    url = "https://api.notion.com/v1/pages"
    response = requests.post(url, headers=get_headers(), json={
        "parent": {"database_id": NOTION_DATABASE_ID},
        "properties": properties
    })

    return response.status_code == 200


def main():
    print("━" * 50)
    print("📥 CSV → Notion 전체 가져오기")
    print("━" * 50)

    # 1. CSV 읽기
    print("\n📄 CSV 파일 읽는 중...")
    data = read_csv_data()
    print(f"   {len(data)}개 데이터 로드")

    # 2. 기존 페이지 삭제
    print("\n🗑️ 기존 Notion 페이지 삭제 중...")
    page_ids = get_all_page_ids()
    print(f"   {len(page_ids)}개 페이지 발견")

    deleted = 0
    for i, page_id in enumerate(page_ids):
        if delete_page(page_id):
            deleted += 1
        if (i + 1) % 20 == 0:
            print(f"   삭제 중... {i + 1}/{len(page_ids)}")
            time.sleep(0.5)  # Rate limit 방지

    print(f"   ✅ {deleted}개 삭제 완료")

    # 3. 새 페이지 생성
    print("\n📝 새 페이지 생성 중...")
    created = 0
    failed = 0

    for i, item in enumerate(data):
        if create_page(item):
            created += 1
        else:
            failed += 1
            print(f"   ❌ 실패: {item['번호']:03d} {item['한글명']}")

        if (i + 1) % 20 == 0:
            print(f"   생성 중... {i + 1}/{len(data)}")
            time.sleep(0.5)  # Rate limit 방지

    # 4. 결과 보고
    print("\n" + "━" * 50)
    print("📊 가져오기 완료")
    print("━" * 50)
    print(f"📄 CSV 데이터: {len(data)}개")
    print(f"🗑️ 삭제: {deleted}개")
    print(f"✅ 생성: {created}개")
    if failed:
        print(f"❌ 실패: {failed}개")
    print("━" * 50)


if __name__ == "__main__":
    main()
