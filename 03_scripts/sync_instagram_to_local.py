#!/usr/bin/env python3
"""
sync_instagram_to_local.py - 인스타그램 → 로컬/노션 역동기화
Instagram Graph API로 게시물 스캔 → 상태 불일치 자동 수정

§14 원칙: 인스타 게시 여부가 Source of Truth
- 인스타에 게시됨 = 무조건 4_posted + 게시완료
- 원자적 트랜잭션: 전부 성공하거나 전부 실패
"""

import os
import re
import json
import shutil
import time
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

IG_ACCOUNT_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")
IG_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

CONTENTS_DIR = PROJECT_ROOT / "01_contents"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["4_posted", "3_approved", "2_body_ready", "1_cover_only"]
POSTED_DIR = CONTENTS_DIR  # 2026-02-13: 플랫 구조
SYNC_LOG_DIR = PROJECT_ROOT / "config" / "logs"


class RateLimitError(Exception):
    """Notion API Rate Limit 에러"""
    pass


def get_notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }


def save_sync_log(log: dict):
    """동기화 로그 저장"""
    SYNC_LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = SYNC_LOG_DIR / f"sync_{datetime.now().strftime('%Y%m%d')}.jsonl"
    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(log, ensure_ascii=False) + "\n")


def fetch_notion_mapping():
    """노션에서 음식명 → 번호 매핑 생성"""
    pages = []
    has_more = True
    start_cursor = None

    while has_more:
        url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
        body = {}
        if start_cursor:
            body["start_cursor"] = start_cursor

        response = requests.post(url, headers=get_notion_headers(), json=body)
        data = response.json()
        pages.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    mapping = {}
    num_to_info = {}

    for page in pages:
        props = page.get("properties", {})
        num = props.get("번호", {}).get("number")
        if num is None:
            continue

        title_arr = props.get("이름", {}).get("title", [])
        name = title_arr[0].get("plain_text", "").lower() if title_arr else ""

        korean_arr = props.get("한글명", {}).get("rich_text", [])
        korean = korean_arr[0].get("plain_text", "") if korean_arr else ""

        status_obj = props.get("인스타상태", {}).get("select", {})
        status = status_obj.get("name", "") if status_obj else ""

        # 다양한 키로 매핑
        if name:
            mapping[name] = num
            mapping[name.replace("_", "")] = num
            mapping[name.replace("_", " ")] = num
        if korean:
            mapping[korean] = num
            mapping[korean.lower()] = num

        num_to_info[num] = {
            "name": name,
            "korean": korean,
            "page_id": page["id"],
            "status": status
        }

    return mapping, num_to_info


def find_content_folder_with_status(num: int):
    """번호로 콘텐츠 폴더 찾기 (상태 정보 포함) - contents/ 직접 스캔"""
    num_str = f"{num:03d}"
    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    for item in CONTENTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith(num_str):
            return item, "contents"  # flat structure
    return None, None


def extract_food_from_caption(caption: str, mapping: dict) -> int:
    """캡션에서 음식명 추출하여 번호 반환"""
    if not caption:
        return None

    caption_lower = caption.lower()

    # 1. 한글 음식명 직접 검색 (가장 정확)
    for key, num in mapping.items():
        if len(key) >= 2 and key in caption_lower:
            return num

    # 2. 해시태그에서 추출
    hashtags = re.findall(r"#(\w+)", caption)
    for tag in hashtags:
        tag_lower = tag.lower()
        if tag_lower in mapping:
            return mapping[tag_lower]
        if tag_lower.startswith("강아지"):
            food = tag_lower[3:]
            if food in mapping:
                return mapping[food]

    # 3. 첫 줄에서 음식명 추출
    first_line = caption.split("\n")[0].lower()
    for key, num in mapping.items():
        if len(key) >= 2 and key in first_line:
            return num

    return None


def fetch_instagram_posts():
    """Instagram Graph API로 모든 게시물 가져오기"""
    posts = []
    url = f"https://graph.facebook.com/v18.0/{IG_ACCOUNT_ID}/media"
    params = {
        "fields": "id,caption,permalink,media_type,media_url,thumbnail_url,timestamp,children{media_url,media_type}",
        "access_token": IG_ACCESS_TOKEN,
        "limit": 100
    }

    while url:
        response = requests.get(url, params=params)
        if response.status_code != 200:
            print(f"❌ Instagram API 오류: {response.status_code}")
            break

        data = response.json()
        posts.extend(data.get("data", []))

        paging = data.get("paging", {})
        url = paging.get("next")
        params = {}

    return posts


def download_image(url: str, save_path: Path) -> bool:
    """이미지 다운로드"""
    try:
        response = requests.get(url, timeout=30)
        if response.status_code == 200:
            save_path.write_bytes(response.content)
            return True
    except Exception as e:
        print(f"      다운로드 오류: {e}")
    return False


def update_notion_posted(page_id: str, permalink: str, has_caption: bool):
    """노션 페이지를 게시완료 상태로 업데이트 (재시도 로직 포함)"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "인스타상태": {"select": {"name": "게시완료"}},
            "인스타URL": {"url": permalink},
            "insta_caption": {"checkbox": has_caption},
        }
    }

    for attempt in range(3):
        try:
            response = requests.patch(url, headers=get_notion_headers(), json=payload)
            if response.status_code == 200:
                return True
            elif response.status_code == 429:  # Rate limit
                print(f"      ⏳ Rate limit, 60초 대기 (시도 {attempt + 1}/3)")
                time.sleep(60)
                raise RateLimitError("Rate limit exceeded")
            else:
                if attempt == 2:
                    raise Exception(f"Notion API error: {response.status_code}")
        except RateLimitError:
            if attempt == 2:
                raise
            continue
    return False


def move_to_posted(folder: Path, num: int, name: str) -> Path:
    """폴더를 4_posted로 이동"""
    if not POSTED_DIR.exists():
        POSTED_DIR.mkdir(parents=True)

    dest = POSTED_DIR / folder.name
    if dest.exists():
        # 이미 존재하면 내용 병합
        for item in folder.iterdir():
            target = dest / item.name
            if item.is_dir():
                if target.exists():
                    # 하위 파일들 병합
                    for sub in item.iterdir():
                        sub_target = target / sub.name
                        if not sub_target.exists():
                            shutil.copy2(sub, sub_target)
                else:
                    shutil.copytree(item, target)
            else:
                if not target.exists():
                    shutil.copy2(item, target)
        shutil.rmtree(folder)
    else:
        shutil.move(str(folder), str(dest))

    return dest


def rollback_local_move(content_id: int, original_path: Path):
    """로컬 이동 롤백"""
    num_str = f"{content_id:03d}"
    current = POSTED_DIR / original_path.name
    if current.exists() and original_path.parent != POSTED_DIR:
        original_path.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(current), str(original_path))
        print(f"      🔙 롤백: {original_path}")


def sync_post_atomic(content_id: int, folder: Path, local_status: str,
                     page_id: str, permalink: str, caption: str,
                     num_to_info: dict, dry_run: bool = False) -> dict:
    """
    원자적 동기화 - 전부 성공하거나 전부 실패

    §14.5 원자 트랜잭션 규칙:
    - 로컬 이동 성공 → 노션 업데이트 성공 = POSTED_SYNCED
    - 어느 하나라도 실패 = 롤백 후 FAILED
    """

    log = {
        "content_id": content_id,
        "instagram_url": permalink,
        "local_move": None,
        "notion_update": None,
        "final_status": None,
        "timestamp": datetime.now().isoformat()
    }

    original_path = folder
    info = num_to_info.get(content_id, {})

    try:
        # Step 1: 로컬 이동
        if local_status != "4_posted":
            if not dry_run:
                folder = move_to_posted(folder, content_id, info.get("name", ""))
            log["local_move"] = "success"
            print(f"   🔧 로컬: {local_status} → 4_posted")
        else:
            log["local_move"] = "already_posted"

        # Step 2: 노션 업데이트 (재시도 로직 포함)
        notion_status = info.get("status", "")
        if notion_status != "게시완료" and page_id:
            if not dry_run:
                update_notion_posted(page_id, permalink, bool(caption))
            log["notion_update"] = "success"
            print(f"   🔧 노션: {notion_status or '없음'} → 게시완료")
        else:
            log["notion_update"] = "already_posted"

        log["final_status"] = "POSTED_SYNCED"
        save_sync_log(log)
        return log

    except Exception as e:
        # 롤백: 로컬 원위치
        if log["local_move"] == "success" and not dry_run:
            rollback_local_move(content_id, original_path)
            log["local_move"] = "rolled_back"

        log["final_status"] = "FAILED"
        log["error"] = str(e)
        save_sync_log(log)
        print(f"   ❌ 실패: {e}")
        return log


def sync_instagram_to_local(dry_run: bool = False):
    """메인 동기화 함수 - 원자적 트랜잭션으로 상태 불일치 자동 수정"""
    print("━" * 60)
    print("📸 인스타그램 → 로컬/노션 역동기화 (원자 트랜잭션)")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("   §14 원칙: 인스타 게시 = Source of Truth")
    print("━" * 60)

    # 1. 노션 매핑 가져오기
    print("\n📥 노션 매핑 로드 중...")
    mapping, num_to_info = fetch_notion_mapping()
    print(f"   {len(num_to_info)}개 콘텐츠 매핑 완료")

    # 2. 인스타 게시물 가져오기
    print("\n📥 인스타그램 게시물 로드 중...")
    posts = fetch_instagram_posts()
    print(f"   {len(posts)}개 게시물")

    # 3. 게시물 매칭 및 처리
    print("\n" + "━" * 60)
    print("🔄 원자적 동기화 처리")
    print("━" * 60)

    stats = {
        "matched": 0,
        "images_downloaded": 0,
        "captions_saved": 0,
        "already_synced": 0,
        "synced": [],
        "failed": [],
        "unmatched": []
    }

    processed_nums = set()

    for post in posts:
        caption = post.get("caption", "")
        permalink = post.get("permalink", "")
        media_url = post.get("media_url", "")
        media_type = post.get("media_type", "")
        children = post.get("children", {}).get("data", [])

        # 음식 번호 추출
        num = extract_food_from_caption(caption, mapping)

        if num is None:
            stats["unmatched"].append({
                "caption": caption[:50] if caption else "(없음)",
                "permalink": permalink
            })
            continue

        # 이미 처리한 번호면 스킵 (중복 게시물)
        if num in processed_nums:
            continue

        processed_nums.add(num)
        stats["matched"] += 1

        info = num_to_info.get(num, {})
        name = info.get("name", "")
        korean = info.get("korean", "")
        page_id = info.get("page_id", "")
        notion_status = info.get("status", "")

        # 폴더 찾기 (상태 포함)
        folder, local_status = find_content_folder_with_status(num)

        print(f"\n[{stats['matched']}] #{num:03d} {name} ({korean})")

        if not folder:
            print(f"   ⚠️ 폴더 없음")
            continue

        # 이미 동기화 완료 상태인지 확인
        if local_status == "4_posted" and notion_status == "게시완료":
            stats["already_synced"] += 1
            print(f"   ✅ 이미 동기화 완료")
        else:
            # ★ 원자적 동기화 실행
            result = sync_post_atomic(
                content_id=num,
                folder=folder,
                local_status=local_status,
                page_id=page_id,
                permalink=permalink,
                caption=caption,
                num_to_info=num_to_info,
                dry_run=dry_run
            )

            if result["final_status"] == "POSTED_SYNCED":
                stats["synced"].append({
                    "num": num,
                    "name": name,
                    "korean": korean
                })
            else:
                stats["failed"].append({
                    "num": num,
                    "name": name,
                    "korean": korean,
                    "error": result.get("error", "")
                })

        # 4_posted로 이동 후 폴더 경로 업데이트
        if local_status != "4_posted":
            folder = POSTED_DIR / folder.name

        insta_dir = folder / "01_Insta&Thread"
        insta_dir.mkdir(exist_ok=True)

        # 캡션 저장
        caption_file = insta_dir / "caption.txt"
        if caption and not caption_file.exists():
            if not dry_run:
                caption_file.write_text(caption)
            print(f"   ✅ 캡션 저장 ({len(caption)}자)")
            stats["captions_saved"] += 1

        # 이미지 다운로드
        existing_images = list(insta_dir.glob("*.jpg")) + list(insta_dir.glob("*.png"))

        if not existing_images:
            if media_type == "CAROUSEL_ALBUM" and children:
                for i, child in enumerate(children):
                    child_url = child.get("media_url", "")
                    if child_url:
                        ext = ".jpg" if "jpg" in child_url.lower() else ".png"
                        save_path = insta_dir / f"slide_{i+1:02d}{ext}"
                        if not dry_run:
                            if download_image(child_url, save_path):
                                stats["images_downloaded"] += 1
                        print(f"   📷 slide_{i+1:02d}{ext} 다운로드")
            elif media_url:
                ext = ".jpg" if "jpg" in media_url.lower() else ".png"
                save_path = insta_dir / f"slide_01{ext}"
                if not dry_run:
                    if download_image(media_url, save_path):
                        stats["images_downloaded"] += 1
                print(f"   📷 slide_01{ext} 다운로드")

    # 4. 결과 리포트
    print("\n" + "━" * 60)
    print("📊 동기화 결과")
    print("━" * 60)
    print(f"📸 인스타 게시물: {len(posts)}개")
    print(f"✅ 매칭 성공: {stats['matched']}개")
    print(f"🔄 동기화 완료: {len(stats['synced'])}개")
    print(f"✓ 이미 동기화: {stats['already_synced']}개")
    print(f"📷 이미지 다운로드: {stats['images_downloaded']}개")
    print(f"📝 캡션 저장: {stats['captions_saved']}개")
    print(f"❌ 실패: {len(stats['failed'])}개")
    print(f"⚠️ 매칭 실패: {len(stats['unmatched'])}개")

    if stats["synced"]:
        print("\n✅ 동기화 완료 목록:")
        for item in stats["synced"]:
            print(f"   #{item['num']:03d} {item['korean']}")

    if stats["failed"]:
        print("\n❌ 실패 목록:")
        for item in stats["failed"]:
            print(f"   #{item['num']:03d} {item['korean']}: {item['error']}")

    if stats["unmatched"]:
        print("\n⚠️ 매칭 실패 목록:")
        for item in stats["unmatched"][:5]:
            print(f"   - {item['caption']}")
        if len(stats["unmatched"]) > 5:
            print(f"   ... 외 {len(stats['unmatched']) - 5}개")

    print("━" * 60)

    return stats


def main():
    import sys

    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("🔍 DRY RUN 모드 (실제 변경 안 함)")

    sync_instagram_to_local(dry_run=dry_run)


if __name__ == "__main__":
    main()
