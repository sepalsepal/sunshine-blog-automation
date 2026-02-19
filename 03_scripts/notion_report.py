#!/usr/bin/env python3
"""
notion_report.py - 노션 DB 기반 콘텐츠 현황 리포트
"""

import os
import sys
import json
import argparse
import requests
from pathlib import Path
from datetime import datetime
from collections import Counter
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


def fetch_all_contents():
    """모든 콘텐츠 가져오기"""
    contents = []
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

        for page in data.get("results", []):
            props = page.get("properties", {})

            num = props.get("번호", {}).get("number")
            num_str = f"{num:03d}" if num is not None else ""

            kr_name = ""
            if props.get("한글명", {}).get("rich_text"):
                kr_name = props["한글명"]["rich_text"][0]["plain_text"] if props["한글명"]["rich_text"] else ""

            en_name = ""
            if props.get("이름", {}).get("title"):
                en_name = props["이름"]["title"][0]["plain_text"] if props["이름"]["title"] else ""

            # 각 플랫폼 상태
            insta = ""
            if props.get("인스타상태", {}).get("select"):
                insta = props["인스타상태"]["select"]["name"]

            threads = ""
            if props.get("쓰레드상태", {}).get("select"):
                threads = props["쓰레드상태"]["select"]["name"]

            blog = ""
            if props.get("블로그상태", {}).get("select"):
                blog = props["블로그상태"]["select"]["name"]

            safety = ""
            if props.get("안전도", {}).get("select"):
                safety = props["안전도"]["select"]["name"]

            contents.append({
                "번호": num_str,
                "한글명": kr_name,
                "영문명": en_name,
                "인스타상태": insta,
                "쓰레드상태": threads,
                "블로그상태": blog,
                "안전도": safety,
            })

        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return contents


def generate_report(output_format: str = "table"):
    """리포트 생성"""
    if not NOTION_DATABASE_ID or not NOTION_API_KEY:
        print("❌ NOTION API 설정이 없습니다")
        return None

    contents = fetch_all_contents()

    if output_format == "json":
        return json.dumps(contents, ensure_ascii=False, indent=2)

    # 테이블 형식 리포트
    report = []
    report.append("━" * 60)
    report.append("📊 Project Sunshine 콘텐츠 현황 (Notion)")
    report.append(f"   조회: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    report.append("━" * 60)

    # 인스타 상태별 집계
    insta_counts = Counter(c["인스타상태"] for c in contents if c["인스타상태"])
    threads_counts = Counter(c["쓰레드상태"] for c in contents if c["쓰레드상태"])
    blog_counts = Counter(c["블로그상태"] for c in contents if c["블로그상태"])
    safety_counts = Counter(c["안전도"] for c in contents if c["안전도"])

    report.append(f"\n📊 전체: {len(contents)}개")

    report.append("\n📸 인스타그램")
    for status in ["게시완료", "승인완료", "본문완료", "표지완료"]:
        count = insta_counts.get(status, 0)
        if count > 0:
            report.append(f"   {status}: {count}개")

    report.append("\n🧵 쓰레드")
    for status in ["게시완료", "승인완료", "본문완료", "표지완료"]:
        count = threads_counts.get(status, 0)
        if count > 0:
            report.append(f"   {status}: {count}개")

    report.append("\n📝 블로그")
    for status in ["게시완료", "승인완료", "본문완료", "표지완료"]:
        count = blog_counts.get(status, 0)
        if count > 0:
            report.append(f"   {status}: {count}개")

    report.append("\n🛡️ 안전도")
    for safety in ["SAFE", "CAUTION", "DANGER"]:
        count = safety_counts.get(safety, 0)
        if count > 0:
            emoji = "🟢" if safety == "SAFE" else "🟡" if safety == "CAUTION" else "🔴"
            report.append(f"   {emoji} {safety}: {count}개")

    # 게시완료 목록
    posted = [c for c in contents if c["인스타상태"] == "게시완료"]
    if posted:
        report.append(f"\n🚀 인스타 게시완료 ({len(posted)}개)")
        for c in posted[:10]:
            report.append(f"   {c['번호']}: {c['한글명']}")
        if len(posted) > 10:
            report.append(f"   ... 외 {len(posted) - 10}개")

    report.append("\n" + "━" * 60)

    return "\n".join(report)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--format", "-f", choices=["table", "json"], default="table")
    args = parser.parse_args()

    report = generate_report(args.format)
    if report:
        print(report)


if __name__ == "__main__":
    main()
