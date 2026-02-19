#!/usr/bin/env python3
"""
caption_recovery.py - 인스타/블로그 캡션 복구 및 노션 구조화
"""

import os
import sys
import json
import re
import time
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_VERSION = "2022-06-28"

CONTENTS_DIR = PROJECT_ROOT / "01_contents"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["4_posted", "3_approved", "2_body_ready", "1_cover_only"]


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


def find_content_folder(num: int) -> Path:
    """번호로 콘텐츠 폴더 찾기"""
    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    num_str = f"{num:03d}"
    for item in CONTENTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith(num_str):
            return item
    return None


def get_property_value(props, prop_name, prop_type):
    """노션 프로퍼티 값 추출"""
    prop = props.get(prop_name, {})

    if prop_type == "url":
        return prop.get("url", "")
    elif prop_type == "number":
        return prop.get("number")
    elif prop_type == "title":
        title_arr = prop.get("title", [])
        return title_arr[0].get("plain_text", "") if title_arr else ""
    elif prop_type == "rich_text":
        text_arr = prop.get("rich_text", [])
        return text_arr[0].get("plain_text", "") if text_arr else ""

    return None


def scrape_instagram_caption(url: str) -> str:
    """인스타그램 캡션 스크래핑 (기본 방식)"""
    if not url or "instagram.com" not in url:
        return ""

    try:
        # 모바일 User-Agent 사용
        headers = {
            "User-Agent": "Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) AppleWebKit/605.1.15",
            "Accept": "text/html,application/xhtml+xml",
            "Accept-Language": "ko-KR,ko;q=0.9",
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return ""

        html = response.text

        # meta description에서 캡션 추출 시도
        # 패턴: <meta property="og:description" content="..."/>
        match = re.search(r'<meta property="og:description" content="([^"]*)"', html)
        if match:
            caption = match.group(1)
            # HTML 엔티티 디코딩
            caption = caption.replace("&amp;", "&")
            caption = caption.replace("&lt;", "<")
            caption = caption.replace("&gt;", ">")
            caption = caption.replace("&quot;", '"')
            caption = caption.replace("&#x27;", "'")
            return caption

        # 대체 패턴
        match = re.search(r'"caption":"([^"]*)"', html)
        if match:
            return match.group(1).encode().decode('unicode_escape')

    except Exception as e:
        print(f"      스크래핑 오류: {e}")

    return ""


def scrape_naver_blog_content(url: str) -> str:
    """네이버 블로그 본문 추출"""
    if not url or "blog.naver.com" not in url:
        return ""

    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36",
        }

        response = requests.get(url, headers=headers, timeout=10)

        if response.status_code != 200:
            return ""

        html = response.text

        # iframe src 추출
        match = re.search(r'src="(https://blog\.naver\.com/PostView\.naver[^"]*)"', html)
        if match:
            iframe_url = match.group(1)
            response = requests.get(iframe_url, headers=headers, timeout=10)
            html = response.text

        # 본문 추출 (se-main-container)
        match = re.search(r'<div class="se-main-container"[^>]*>(.*?)</div>\s*</div>\s*</div>', html, re.DOTALL)
        if match:
            content = match.group(1)
            # HTML 태그 제거
            content = re.sub(r'<[^>]+>', '', content)
            content = content.strip()
            return content[:2000]  # 최대 2000자

    except Exception as e:
        print(f"      블로그 스크래핑 오류: {e}")

    return ""


def create_toggle_structure(page_id: str, food_name: str, insta_data: dict, blog_data: dict):
    """노션 페이지에 토글 구조 생성"""

    children = []

    # 인스타 토글
    insta_children = []
    if insta_data.get("caption"):
        insta_children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": insta_data["caption"][:2000]}}]
            }
        })
    if insta_data.get("images"):
        for img_path in insta_data["images"][:10]:
            insta_children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"📷 {img_path}"}}]
                }
            })

    if insta_children:
        children.append({
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": "📸 인스타"}}],
                "children": insta_children[:100]
            }
        })

    # 블로그 토글
    blog_children = []
    if blog_data.get("caption"):
        blog_children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": blog_data["caption"][:2000]}}]
            }
        })
    if blog_data.get("images"):
        for img_path in blog_data["images"][:10]:
            blog_children.append({
                "object": "block",
                "type": "paragraph",
                "paragraph": {
                    "rich_text": [{"type": "text", "text": {"content": f"📷 {img_path}"}}]
                }
            })

    if blog_children:
        children.append({
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": "📝 블로그"}}],
                "children": blog_children[:100]
            }
        })

    if not children:
        return False

    # 기존 블록 가져오기
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    response = requests.get(url, headers=get_headers())

    if response.status_code == 200:
        existing_blocks = response.json().get("results", [])

        # 기존 토글 삭제 (📸 인스타, 📝 블로그)
        for block in existing_blocks:
            if block.get("type") == "toggle":
                toggle_text = ""
                rich_text = block.get("toggle", {}).get("rich_text", [])
                if rich_text:
                    toggle_text = rich_text[0].get("plain_text", "")

                if toggle_text in ["📸 인스타", "📝 블로그"]:
                    delete_url = f"https://api.notion.com/v1/blocks/{block['id']}"
                    requests.delete(delete_url, headers=get_headers())

    # 새 토글 추가
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    payload = {"children": children}

    response = requests.patch(url, headers=get_headers(), json=payload)
    return response.status_code == 200


def update_checkboxes(page_id: str, insta_caption: bool, blog_caption: bool):
    """체크박스 업데이트"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "insta_caption": {"checkbox": insta_caption},
            "blog_caption": {"checkbox": blog_caption},
        }
    }
    response = requests.patch(url, headers=get_headers(), json=payload)
    return response.status_code == 200


def main():
    print("━" * 60)
    print("📋 캡션 복구 및 노션 구조화")
    print(f"   시작: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("━" * 60)

    # 1. 노션 페이지 가져오기
    print("\n📥 노션 페이지 로드 중...")
    pages = fetch_all_pages()
    print(f"   총 {len(pages)}개 페이지")

    # 2. 분류
    insta_pages = []
    blog_pages = []

    for page in pages:
        props = page.get("properties", {})
        num = get_property_value(props, "번호", "number")
        name = get_property_value(props, "제목", "title") or get_property_value(props, "Name", "title")
        insta_url = get_property_value(props, "인스타URL", "url") or get_property_value(props, "insta_url", "url")
        blog_url = get_property_value(props, "블로그URL", "url") or get_property_value(props, "blog_url", "url")

        if insta_url:
            insta_pages.append({
                "page_id": page["id"],
                "num": num,
                "name": name,
                "url": insta_url
            })

        if blog_url:
            blog_pages.append({
                "page_id": page["id"],
                "num": num,
                "name": name,
                "url": blog_url
            })

    print(f"   인스타 URL 있음: {len(insta_pages)}개")
    print(f"   블로그 URL 있음: {len(blog_pages)}개")

    # 3. 인스타 캡션 복구
    print("\n" + "━" * 60)
    print("📸 인스타 캡션 복구")
    print("━" * 60)

    insta_success = 0
    insta_fail = 0

    for i, item in enumerate(insta_pages):
        num = item["num"]
        name = item["name"]
        url = item["url"]
        page_id = item["page_id"]

        print(f"\n[{i+1}/{len(insta_pages)}] #{num} {name}")
        print(f"   URL: {url[:50]}...")

        # 폴더 찾기
        folder = find_content_folder(num)
        if not folder:
            print(f"   ⚠️ 폴더 없음")
            insta_fail += 1
            continue

        # 2026-02-13: 플랫 구조 반영
        insta_dir = folder / "01_Insta&Thread"
        insta_dir.mkdir(exist_ok=True)
        caption_file = insta_dir / "caption.txt"

        # 이미 캡션 있으면 스킵
        if caption_file.exists() and caption_file.stat().st_size > 10:
            print(f"   ✅ 캡션 이미 존재 ({caption_file.stat().st_size}자)")
            insta_success += 1

            # 노션 업데이트
            caption = caption_file.read_text()
            images = [f.name for f in insta_dir.iterdir() if f.suffix.lower() in [".jpg", ".png", ".webp"]]
            create_toggle_structure(page_id, name, {"caption": caption, "images": images}, {})
            update_checkboxes(page_id, True, False)
            continue

        # 스크래핑
        caption = scrape_instagram_caption(url)

        if caption and len(caption) > 10:
            caption_file.write_text(caption)
            print(f"   ✅ 캡션 저장 ({len(caption)}자)")
            insta_success += 1

            # 노션 업데이트
            images = [f.name for f in insta_dir.iterdir() if f.suffix.lower() in [".jpg", ".png", ".webp"]]
            create_toggle_structure(page_id, name, {"caption": caption, "images": images}, {})
            update_checkboxes(page_id, True, False)
        else:
            print(f"   ❌ 캡션 추출 실패")
            insta_fail += 1

        # Rate limiting
        time.sleep(1)

    # 4. 블로그 캡션 복구
    print("\n" + "━" * 60)
    print("📝 블로그 캡션 복구")
    print("━" * 60)

    blog_success = 0
    blog_fail = 0

    for i, item in enumerate(blog_pages):
        num = item["num"]
        name = item["name"]
        url = item["url"]
        page_id = item["page_id"]

        print(f"\n[{i+1}/{len(blog_pages)}] #{num} {name}")
        print(f"   URL: {url[:50]}...")

        folder = find_content_folder(num)
        if not folder:
            print(f"   ⚠️ 폴더 없음")
            blog_fail += 1
            continue

        # 2026-02-13: 플랫 구조 반영
        blog_dir = folder / "02_Blog"
        blog_dir.mkdir(exist_ok=True)
        caption_file = blog_dir / "caption.txt"

        # 이미 캡션 있으면 스킵
        if caption_file.exists() and caption_file.stat().st_size > 10:
            print(f"   ✅ 캡션 이미 존재 ({caption_file.stat().st_size}자)")
            blog_success += 1
            update_checkboxes(page_id, False, True)
            continue

        # 스크래핑
        caption = scrape_naver_blog_content(url)

        if caption and len(caption) > 10:
            caption_file.write_text(caption)
            print(f"   ✅ 캡션 저장 ({len(caption)}자)")
            blog_success += 1
            update_checkboxes(page_id, False, True)
        else:
            print(f"   ❌ 캡션 추출 실패")
            blog_fail += 1

        time.sleep(1)

    # 5. 전체 페이지 노션 구조 업데이트 (캡션 없는 것도)
    print("\n" + "━" * 60)
    print("🔄 노션 페이지 구조 업데이트")
    print("━" * 60)

    structure_updated = 0

    for i, page in enumerate(pages):
        props = page.get("properties", {})
        num = get_property_value(props, "번호", "number")
        name = get_property_value(props, "제목", "title") or get_property_value(props, "Name", "title")
        page_id = page["id"]

        if num is None:
            continue

        folder = find_content_folder(num)
        if not folder:
            continue

        # 2026-02-13: 플랫 구조 반영
        insta_dir = folder / "01_Insta&Thread"
        blog_dir = folder / "02_Blog"

        insta_data = {"caption": "", "images": []}
        blog_data = {"caption": "", "images": []}

        if insta_dir.exists():
            caption_file = insta_dir / "caption.txt"
            if caption_file.exists():
                insta_data["caption"] = caption_file.read_text()
            insta_data["images"] = [f.name for f in insta_dir.iterdir()
                                    if f.is_file() and f.suffix.lower() in [".jpg", ".png", ".webp", ".jpeg"]]

        if blog_dir.exists():
            caption_file = blog_dir / "caption.txt"
            if caption_file.exists():
                blog_data["caption"] = caption_file.read_text()
            blog_data["images"] = [f.name for f in blog_dir.iterdir()
                                   if f.is_file() and f.suffix.lower() in [".jpg", ".png", ".webp", ".jpeg"]]

        # 데이터가 있으면 토글 구조 생성
        if insta_data["caption"] or insta_data["images"] or blog_data["caption"] or blog_data["images"]:
            if create_toggle_structure(page_id, name, insta_data, blog_data):
                structure_updated += 1
                update_checkboxes(page_id, bool(insta_data["caption"]), bool(blog_data["caption"]))

        if (i + 1) % 20 == 0:
            print(f"   진행: {i+1}/{len(pages)}")

    # 6. 결과 리포트
    print("\n" + "━" * 60)
    print("📊 완료 리포트")
    print("━" * 60)
    print(f"📸 인스타 캡션:")
    print(f"   - 대상: {len(insta_pages)}개")
    print(f"   - 성공: {insta_success}개")
    print(f"   - 실패: {insta_fail}개")
    print(f"\n📝 블로그 캡션:")
    print(f"   - 대상: {len(blog_pages)}개")
    print(f"   - 성공: {blog_success}개")
    print(f"   - 실패: {blog_fail}개")
    print(f"\n🔄 노션 구조 업데이트: {structure_updated}개")
    print("━" * 60)


if __name__ == "__main__":
    main()
