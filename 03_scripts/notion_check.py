#!/usr/bin/env python3
"""
notion_check.py - 노션 vs 로컬 vs 인스타 3중 검증
모든 항목 "콘텐츠(폴더) 기준"으로 통일

§14.7 3중 검증 (Triple Check):
- 인스타 게시물 수 == 노션 게시완료 수 == 로컬 4_posted 수
"""

import os
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
IG_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
IG_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
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


def fetch_notion_pages():
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
            break

        data = response.json()
        pages.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return pages


def get_instagram_post_count():
    """인스타그램 게시물 수 가져오기"""
    posts = []
    url = f"https://graph.facebook.com/v18.0/{IG_ACCOUNT_ID}/media"
    params = {
        "fields": "id",
        "access_token": IG_ACCESS_TOKEN,
        "limit": 100
    }

    while url:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            break

        data = response.json()
        posts.extend(data.get("data", []))

        paging = data.get("paging", {})
        url = paging.get("next")
        params = {}

    return len(posts)


def get_notion_posted_count(pages):
    """노션에서 '게시완료' 상태인 항목 수"""
    count = 0
    posted_nums = []
    for page in pages:
        props = page.get("properties", {})
        status = props.get("인스타상태", {}).get("select", {})
        status_name = status.get("name", "") if status else ""
        if status_name == "게시완료":
            count += 1
            num = props.get("번호", {}).get("number")
            if num:
                posted_nums.append(num)
    return count, posted_nums


def count_local_4_posted():
    """로컬 4_posted 폴더의 콘텐츠 수"""
    posted_dir = CONTENTS_DIR / "4_posted"
    if not posted_dir.exists():
        return 0, []

    nums = []
    for folder in posted_dir.iterdir():
        if folder.is_dir() and not folder.name.startswith("."):
            try:
                num = int(folder.name[:3])
                nums.append(num)
            except ValueError:
                continue

    return len(nums), nums


def find_notion_without_insta(notion_posted_nums, insta_count):
    """노션 게시완료 중 인스타에 없는 항목 (orphan) 찾기"""
    # 이 함수는 인스타 API로 캡션을 스캔해야 정확하지만,
    # 간단히 개수 차이로 판단
    if len(notion_posted_nums) > insta_count:
        return notion_posted_nums[insta_count:]  # 추정 orphan
    return []


def find_content_folder(num: int) -> Path:
    """번호로 콘텐츠 폴더 찾기"""
    num_str = f"{num:03d}"
    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    for item in CONTENTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith(num_str):
            return item
    return None


def scan_local_folders():
    """로컬 폴더 스캔"""
    local_data = {}

    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    for folder in CONTENTS_DIR.iterdir():
            if not folder.is_dir() or folder.name.startswith("."):
                continue

            # 번호 추출
            try:
                num = int(folder.name[:3])
            except ValueError:
                continue

            # 2026-02-13: 플랫 구조
            insta_dir = folder / "01_Insta&Thread"
            blog_dir = folder / "02_Blog"

            # 이미지 개수 (콘텐츠당 있음/없음)
            insta_images = 0
            blog_images = 0
            insta_caption = False
            blog_caption = False

            if insta_dir.exists():
                images = [f for f in insta_dir.iterdir()
                          if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
                insta_images = len(images)
                insta_caption = (insta_dir / "caption.txt").exists()

            if blog_dir.exists():
                images = [f for f in blog_dir.iterdir()
                          if f.is_file() and f.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]]
                blog_images = len(images)
                blog_caption = (blog_dir / "caption.txt").exists()

            local_data[num] = {
                "insta_images": insta_images,
                "blog_images": blog_images,
                "insta_caption": insta_caption,
                "blog_caption": blog_caption,
            }

    return local_data


def triple_check():
    """
    §14.7 3중 검증 (Triple Check)
    인스타 == 노션 게시완료 == 로컬 4_posted
    """
    print("\n" + "━" * 60)
    print("🔍 3중 검증 (Triple Check)")
    print("━" * 60)

    # 1. 인스타 게시물 수
    insta_count = get_instagram_post_count()
    print(f"📸 인스타그램 게시물: {insta_count}개")

    # 2. 노션 게시완료 수
    pages = fetch_notion_pages()
    notion_posted, notion_posted_nums = get_notion_posted_count(pages)
    print(f"📋 노션 '게시완료': {notion_posted}개")

    # 3. 로컬 4_posted 수
    local_posted, local_posted_nums = count_local_4_posted()
    print(f"📁 로컬 4_posted: {local_posted}개")

    # 4. 일치 확인
    print("\n┌─────────────────┬────────┬────────┐")
    print("│ 비교            │ 값     │ 결과   │")
    print("├─────────────────┼────────┼────────┤")

    # 인스타 vs 노션
    if insta_count == notion_posted:
        result1 = "✅ 일치"
    else:
        diff = abs(insta_count - notion_posted)
        result1 = f"❌ {diff}차이"
    print(f"│ 인스타 vs 노션  │ {insta_count} vs {notion_posted} │ {result1:<6} │")

    # 노션 vs 로컬
    if notion_posted == local_posted:
        result2 = "✅ 일치"
    else:
        diff = abs(notion_posted - local_posted)
        result2 = f"❌ {diff}차이"
    print(f"│ 노션 vs 로컬    │ {notion_posted} vs {local_posted} │ {result2:<6} │")

    # 인스타 vs 로컬
    if insta_count == local_posted:
        result3 = "✅ 일치"
    else:
        diff = abs(insta_count - local_posted)
        result3 = f"❌ {diff}차이"
    print(f"│ 인스타 vs 로컬  │ {insta_count} vs {local_posted} │ {result3:<6} │")

    print("└─────────────────┴────────┴────────┘")

    # 5. 전체 일치 여부
    all_match = (insta_count == notion_posted == local_posted)

    if all_match:
        print("\n✅ 3중 검증 PASS: 모든 소스가 일치합니다!")
    else:
        print("\n❌ 3중 검증 FAIL: 불일치가 발견되었습니다.")

        # 노션에만 있고 로컬에 없는 항목
        notion_only = set(notion_posted_nums) - set(local_posted_nums)
        if notion_only:
            print(f"\n   📋 노션에만 '게시완료' (로컬 4_posted 없음):")
            for num in sorted(notion_only)[:10]:
                print(f"      #{num:03d}")

        # 로컬에만 있고 노션에 없는 항목
        local_only = set(local_posted_nums) - set(notion_posted_nums)
        if local_only:
            print(f"\n   📁 로컬 4_posted만 (노션 '게시완료' 아님):")
            for num in sorted(local_only)[:10]:
                print(f"      #{num:03d}")

    return all_match


def main():
    print("━" * 60)
    print(f"📊 노션 vs 로컬 vs 인스타 검증")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("━" * 60)

    # 1. 노션 데이터 가져오기
    print("\n📥 노션 데이터 로드 중...")
    pages = fetch_notion_pages()

    notion_data = {}
    for page in pages:
        props = page.get("properties", {})
        num = props.get("번호", {}).get("number")
        if num is None:
            continue

        insta_images = props.get("insta_images", {}).get("number", 0) or 0
        blog_images = props.get("blog_images", {}).get("number", 0) or 0
        insta_caption = props.get("insta_caption", {}).get("checkbox", False)
        blog_caption = props.get("blog_caption", {}).get("checkbox", False)

        notion_data[num] = {
            "insta_images": insta_images,
            "blog_images": blog_images,
            "insta_caption": insta_caption,
            "blog_caption": blog_caption,
        }

    # 2. 로컬 데이터 스캔
    print("📁 로컬 폴더 스캔 중...")
    local_data = scan_local_folders()

    # 3. 집계 (콘텐츠 기준)
    total_notion = len(notion_data)
    total_local = len(local_data)

    # 노션 기준 집계
    notion_insta_img = sum(1 for d in notion_data.values() if d["insta_images"] > 0)
    notion_blog_img = sum(1 for d in notion_data.values() if d["blog_images"] > 0)
    notion_insta_cap = sum(1 for d in notion_data.values() if d["insta_caption"])
    notion_blog_cap = sum(1 for d in notion_data.values() if d["blog_caption"])

    # 로컬 기준 집계
    local_insta_img = sum(1 for d in local_data.values() if d["insta_images"] > 0)
    local_blog_img = sum(1 for d in local_data.values() if d["blog_images"] > 0)
    local_insta_cap = sum(1 for d in local_data.values() if d["insta_caption"])
    local_blog_cap = sum(1 for d in local_data.values() if d["blog_caption"])

    # 4. 일치 여부 확인
    def check_match(notion_val, local_val, total):
        if notion_val == local_val:
            return f"✅ 100%"
        else:
            diff = abs(notion_val - local_val)
            return f"❌ {diff}개 차이"

    # 5. 결과 출력
    print("\n")
    print("┌──────────────┬────────┬────────┬─────────┐")
    print("│ 항목         │ 노션   │ 로컬   │ 일치    │")
    print("├──────────────┼────────┼────────┼─────────┤")

    # 전체 콘텐츠
    match_total = check_match(total_notion, total_local, total_notion)
    print(f"│ 전체 콘텐츠  │ {total_notion:>6} │ {total_local:>6} │ {match_total:<7} │")

    # 인스타 이미지
    notion_str = f"{notion_insta_img}/{total_notion}"
    local_str = f"{local_insta_img}/{total_local}"
    match_insta_img = check_match(notion_insta_img, local_insta_img, total_notion)
    print(f"│ 인스타 이미지│ {notion_str:>6} │ {local_str:>6} │ {match_insta_img:<7} │")

    # 블로그 이미지
    notion_str = f"{notion_blog_img}/{total_notion}"
    local_str = f"{local_blog_img}/{total_local}"
    match_blog_img = check_match(notion_blog_img, local_blog_img, total_notion)
    print(f"│ 블로그 이미지│ {notion_str:>6} │ {local_str:>6} │ {match_blog_img:<7} │")

    # 인스타 캡션
    notion_str = f"{notion_insta_cap}/{total_notion}"
    local_str = f"{local_insta_cap}/{total_local}"
    match_insta_cap = check_match(notion_insta_cap, local_insta_cap, total_notion)
    print(f"│ 인스타 캡션  │ {notion_str:>6} │ {local_str:>6} │ {match_insta_cap:<7} │")

    # 블로그 캡션
    notion_str = f"{notion_blog_cap}/{total_notion}"
    local_str = f"{local_blog_cap}/{total_local}"
    match_blog_cap = check_match(notion_blog_cap, local_blog_cap, total_notion)
    print(f"│ 블로그 캡션  │ {notion_str:>6} │ {local_str:>6} │ {match_blog_cap:<7} │")

    print("└──────────────┴────────┴────────┴─────────┘")

    # 6. 불일치 상세
    mismatches = []
    all_nums = set(notion_data.keys()) | set(local_data.keys())

    for num in sorted(all_nums):
        n = notion_data.get(num, {"insta_images": 0, "blog_images": 0, "insta_caption": False, "blog_caption": False})
        l = local_data.get(num, {"insta_images": 0, "blog_images": 0, "insta_caption": False, "blog_caption": False})

        # 이미지 개수가 0보다 큰지로 비교 (콘텐츠 유무 기준)
        n_insta_has = 1 if n["insta_images"] > 0 else 0
        l_insta_has = 1 if l["insta_images"] > 0 else 0
        n_blog_has = 1 if n["blog_images"] > 0 else 0
        l_blog_has = 1 if l["blog_images"] > 0 else 0

        if (n_insta_has != l_insta_has or
            n_blog_has != l_blog_has or
            n["insta_caption"] != l["insta_caption"] or
            n["blog_caption"] != l["blog_caption"]):
            mismatches.append((num, n, l))

    if mismatches:
        print(f"\n⚠️ 불일치 항목: {len(mismatches)}개")
        for num, n, l in mismatches[:10]:
            print(f"   #{num:03d}: 노션({n}) vs 로컬({l})")
        if len(mismatches) > 10:
            print(f"   ... 외 {len(mismatches) - 10}개")
    else:
        print("\n✅ 모든 항목 일치!")

    # 7. 3중 검증 실행
    triple_check()

    print("\n" + "━" * 60)


if __name__ == "__main__":
    main()
