#!/usr/bin/env python3
"""
instagram_api_recovery.py - Instagram Graph API로 캡션/URL 복구
"""

import os
import re
import json
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

# Instagram API
IG_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
IG_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")

# Notion API
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_VERSION = "2022-06-28"

CONTENTS_DIR = PROJECT_ROOT / "01_contents"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["4_posted", "3_approved", "2_body_ready", "1_cover_only"]


def get_notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION
    }


def fetch_instagram_posts():
    """Instagram Graph API로 모든 게시물 가져오기"""
    posts = []
    url = f"https://graph.facebook.com/v18.0/{IG_ACCOUNT_ID}/media"
    params = {
        "fields": "id,caption,permalink,timestamp,media_type,media_url",
        "access_token": IG_ACCESS_TOKEN,
        "limit": 100
    }

    while url:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"❌ Instagram API 오류: {response.status_code}")
            print(f"   {response.text[:200]}")
            break

        data = response.json()
        posts.extend(data.get("data", []))

        # 다음 페이지
        paging = data.get("paging", {})
        url = paging.get("next")
        params = {}  # next URL에 이미 params 포함됨

    return posts


def extract_food_name_from_caption(caption: str) -> str:
    """캡션에서 음식 이름 추출"""
    if not caption:
        return ""

    # 패턴들
    patterns = [
        r"#(\w+)_for_dogs",  # #pumpkin_for_dogs
        r"강아지\s*(.+?)\s*(간식|급여|먹|주)",  # 강아지 호박 급여
        r"반려견\s*(.+?)\s*(간식|급여|먹|주)",
        r"🐕.*?(\w+)",  # 이모지 뒤 단어
    ]

    for pattern in patterns:
        match = re.search(pattern, caption, re.IGNORECASE)
        if match:
            return match.group(1).lower().strip()

    # 첫 줄에서 추출
    first_line = caption.split("\n")[0]
    # 한글 음식명 (급여, 간식 등 제외)
    match = re.search(r"([\w가-힣]+)", first_line)
    if match:
        name = match.group(1)
        if name not in ["강아지", "반려견", "급여", "간식", "먹이", "주기"]:
            return name.lower()

    return ""


def find_content_folder(num: int) -> Path:
    """번호로 콘텐츠 폴더 찾기"""
    num_str = f"{num:03d}"
    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    for item in CONTENTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith(num_str):
            return item
    return None


def fetch_notion_pages():
    """노션 페이지 가져오기"""
    pages = []
    has_more = True
    start_cursor = None

    while has_more:
        url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
        body = {"sorts": [{"property": "번호", "direction": "ascending"}]}
        if start_cursor:
            body["start_cursor"] = start_cursor

        response = requests.post(url, headers=get_notion_headers(), json=body)
        if response.status_code != 200:
            break

        data = response.json()
        pages.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return pages


def update_notion_page(page_id: str, insta_url: str, has_caption: bool):
    """노션 페이지 업데이트 (인스타URL, 체크박스)"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "인스타URL": {"url": insta_url},
            "insta_caption": {"checkbox": has_caption},
        }
    }
    response = requests.patch(url, headers=get_notion_headers(), json=payload)
    return response.status_code == 200


def create_toggle_in_page(page_id: str, caption: str, images: list):
    """노션 페이지에 인스타 토글 추가"""
    children = []

    # 캡션
    if caption:
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": caption[:2000]}}]
            }
        })

    # 이미지 목록
    for img in images[:10]:
        children.append({
            "object": "block",
            "type": "paragraph",
            "paragraph": {
                "rich_text": [{"type": "text", "text": {"content": f"📷 {img}"}}]
            }
        })

    if not children:
        return False

    # 토글 블록 추가
    url = f"https://api.notion.com/v1/blocks/{page_id}/children"
    payload = {
        "children": [{
            "object": "block",
            "type": "toggle",
            "toggle": {
                "rich_text": [{"type": "text", "text": {"content": "📸 인스타"}}],
                "children": children
            }
        }]
    }

    response = requests.patch(url, headers=get_notion_headers(), json=payload)
    return response.status_code == 200


def main():
    print("━" * 60)
    print("📸 Instagram API 캡션/URL 복구")
    print(f"   시작: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("━" * 60)

    # 1. Instagram 게시물 가져오기
    print("\n📥 Instagram 게시물 로드 중...")
    posts = fetch_instagram_posts()
    print(f"   총 {len(posts)}개 게시물")

    if not posts:
        print("❌ Instagram 게시물을 가져올 수 없습니다.")
        return

    # 2. 노션 페이지 가져오기
    print("\n📥 노션 페이지 로드 중...")
    notion_pages = fetch_notion_pages()
    print(f"   총 {len(notion_pages)}개 페이지")

    # 3. 노션 페이지를 폴더명/영어명으로 매핑
    notion_map = {}  # 영어명 -> page 정보
    for page in notion_pages:
        props = page.get("properties", {})
        num = props.get("번호", {}).get("number")
        title_arr = props.get("이름", {}).get("title", [])
        name = title_arr[0].get("plain_text", "").lower() if title_arr else ""
        folder_arr = props.get("폴더명", {}).get("rich_text", [])
        folder_name = folder_arr[0].get("plain_text", "").lower() if folder_arr else ""
        korean_arr = props.get("한글명", {}).get("rich_text", [])
        korean_name = korean_arr[0].get("plain_text", "").lower() if korean_arr else ""

        if num is not None:
            notion_map[name] = {"page_id": page["id"], "num": num, "name": name, "korean": korean_name}
            if folder_name:
                notion_map[folder_name] = {"page_id": page["id"], "num": num, "name": name, "korean": korean_name}
            if korean_name:
                notion_map[korean_name] = {"page_id": page["id"], "num": num, "name": name, "korean": korean_name}

    # 4. 매칭 및 저장
    print("\n" + "━" * 60)
    print("🔄 캡션 매칭 및 저장")
    print("━" * 60)

    matched = 0
    saved_captions = 0
    unmatched = []

    for i, post in enumerate(posts):
        caption = post.get("caption", "")
        permalink = post.get("permalink", "")
        media_type = post.get("media_type", "")
        timestamp = post.get("timestamp", "")

        # 음식 이름 추출
        food_name = extract_food_name_from_caption(caption)

        if not food_name:
            unmatched.append({"caption": caption[:50], "url": permalink})
            continue

        # 노션에서 찾기
        page_info = notion_map.get(food_name.lower())

        if not page_info:
            # 부분 매칭 시도
            for key, info in notion_map.items():
                if food_name in key or key in food_name:
                    page_info = info
                    break

        if not page_info:
            unmatched.append({"food": food_name, "caption": caption[:50], "url": permalink})
            continue

        matched += 1
        num = page_info["num"]
        page_id = page_info["page_id"]
        name = page_info["name"]

        print(f"\n[{matched}] #{num} {name}")
        print(f"   URL: {permalink}")

        # 폴더 찾기 및 캡션 저장
        folder = find_content_folder(num)
        if folder:
            insta_dir = folder / "01_Insta&Thread"
            insta_dir.mkdir(exist_ok=True)
            caption_file = insta_dir / "caption.txt"

            if caption:
                caption_file.write_text(caption)
                print(f"   ✅ 캡션 저장 ({len(caption)}자)")
                saved_captions += 1

                # 이미지 목록
                images = [f.name for f in insta_dir.iterdir()
                          if f.is_file() and f.suffix.lower() in [".jpg", ".png", ".webp", ".jpeg"]]

                # 노션 업데이트
                update_notion_page(page_id, permalink, True)
                create_toggle_in_page(page_id, caption, images)
            else:
                update_notion_page(page_id, permalink, False)
        else:
            print(f"   ⚠️ 폴더 없음")
            update_notion_page(page_id, permalink, bool(caption))

    # 5. 결과 리포트
    print("\n" + "━" * 60)
    print("📊 완료 리포트")
    print("━" * 60)
    print(f"📸 Instagram 게시물: {len(posts)}개")
    print(f"✅ 매칭 성공: {matched}개")
    print(f"📝 캡션 저장: {saved_captions}개")
    print(f"❌ 매칭 실패: {len(unmatched)}개")

    if unmatched[:5]:
        print("\n⚠️ 매칭 실패 샘플:")
        for item in unmatched[:5]:
            print(f"   - {item}")

    print("━" * 60)

    # 매칭 결과 저장
    result_file = PROJECT_ROOT / "scripts" / "instagram_recovery_result.json"
    with open(result_file, "w") as f:
        json.dump({
            "timestamp": datetime.now().isoformat(),
            "total_posts": len(posts),
            "matched": matched,
            "saved_captions": saved_captions,
            "unmatched": unmatched
        }, f, ensure_ascii=False, indent=2)
    print(f"\n📄 결과 저장: {result_file}")


if __name__ == "__main__":
    main()
