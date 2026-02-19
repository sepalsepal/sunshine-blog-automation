#!/usr/bin/env python3
"""
notion_update.py - 단일 콘텐츠 노션 상태 업데이트
WO-039: Validator 실행 후 Hook에서 자동 호출

사용법: python3 scripts/notion_update.py <콘텐츠번호> <상태> [--validator PASS|FAIL]
예시: python3 scripts/notion_update.py 060 게시완료 --validator PASS
"""

import os
import sys
import argparse
import requests
from pathlib import Path
from dotenv import load_dotenv

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

load_dotenv(PROJECT_ROOT / ".env")

# === 설정 ===
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_VERSION = "2022-06-28"

# 유효한 상태 값
VALID_STATUSES = ["표지완료", "본문완료", "승인완료", "게시완료", "아카이브"]
VALID_VALIDATORS = ["PASS", "FAIL"]


def get_headers():
    """API 헤더 생성"""
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION
    }


def find_page_by_number(database_id: str, content_num: str):
    """콘텐츠 번호로 페이지 찾기 (Direct HTTP API)"""
    url = f"https://api.notion.com/v1/databases/{database_id}/query"
    body = {
        "filter": {
            "property": "이름",
            "title": {"equals": content_num}
        }
    }

    response = requests.post(url, headers=get_headers(), json=body)
    if response.status_code != 200:
        return None

    data = response.json()
    if data.get("results"):
        return data["results"][0]
    return None


def update_content_status(
    content_num: str,
    status: str = None,
    validator: str = None,
    permalink: str = None
):
    """콘텐츠 상태 업데이트"""
    if not NOTION_DATABASE_ID:
        print("❌ NOTION_DATABASE_ID가 .env에 설정되지 않음")
        return False

    if not NOTION_API_KEY:
        print("❌ NOTION_API_KEY가 .env에 설정되지 않음")
        return False

    # 페이지 찾기
    page = find_page_by_number(NOTION_DATABASE_ID, content_num)

    if not page:
        print(f"❌ 콘텐츠 {content_num}을 Notion에서 찾을 수 없음")
        print("   먼저 notion_sync.py를 실행하세요")
        return False

    # 업데이트할 속성
    properties = {}

    if status:
        if status not in VALID_STATUSES:
            print(f"❌ 유효하지 않은 상태: {status}")
            print(f"   가능한 값: {', '.join(VALID_STATUSES)}")
            return False
        properties["상태"] = {"select": {"name": status}}

    if validator:
        if validator not in VALID_VALIDATORS:
            print(f"❌ 유효하지 않은 Validator 상태: {validator}")
            print(f"   가능한 값: {', '.join(VALID_VALIDATORS)}")
            return False
        properties["Validator"] = {"select": {"name": validator}}

    if permalink:
        properties["게시URL"] = {"url": permalink}

    if not properties:
        print("⚠️ 업데이트할 항목이 없습니다")
        return True

    # 업데이트 실행 (Direct HTTP API)
    url = f"https://api.notion.com/v1/pages/{page['id']}"
    response = requests.patch(url, headers=get_headers(), json={"properties": properties})

    if response.status_code != 200:
        print(f"❌ 업데이트 실패: {response.status_code}")
        return False

    print(f"✅ 노션 업데이트 완료: {content_num}")
    if status:
        print(f"   상태: {status}")
    if validator:
        print(f"   Validator: {validator}")
    if permalink:
        print(f"   URL: {permalink}")

    return True


def main():
    parser = argparse.ArgumentParser(description="노션 콘텐츠 상태 업데이트")
    parser.add_argument("content_num", help="콘텐츠 번호 (예: 060)")
    parser.add_argument("status", nargs="?", help="상태 (예: 게시완료)")
    parser.add_argument("--validator", choices=["PASS", "FAIL"], help="Validator 결과")
    parser.add_argument("--permalink", help="게시 URL")
    parser.add_argument("--quiet", "-q", action="store_true", help="조용히 실행")

    args = parser.parse_args()

    # 콘텐츠 번호 정규화 (60 → 060)
    content_num = args.content_num.zfill(3)

    success = update_content_status(
        content_num=content_num,
        status=args.status,
        validator=args.validator,
        permalink=args.permalink,
    )

    if not args.quiet:
        if success:
            print("━" * 40)
        else:
            sys.exit(1)


if __name__ == "__main__":
    main()
