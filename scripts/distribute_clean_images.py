#!/usr/bin/env python3
"""
distribute_clean_images.py - 클린 이미지 배치 스크립트
99_CleanReady/ → 각 콘텐츠 0_clean/ 복사 + 노션 업데이트

§17 클린 이미지 관리 규칙 준수:
- ✅ 복사 (cp) 만 허용
- ❌ 이동 (mv) 금지
- 99_CleanReady = 원본 백업 (절대 삭제 금지)
"""

import os
import shutil
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")

CONTENTS_DIR = PROJECT_ROOT / "contents"
CLEAN_READY_DIR = CONTENTS_DIR / "99_CleanReady"
STATUS_DIRS = ["4_posted", "3_approved", "2_body_ready", "1_cover_only"]


def get_notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }


def fetch_notion_mapping():
    """노션에서 음식명 → 번호/page_id 매핑 생성"""
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

    for page in pages:
        props = page.get("properties", {})
        num = props.get("번호", {}).get("number")
        if num is None:
            continue

        title_arr = props.get("이름", {}).get("title", [])
        name = title_arr[0].get("plain_text", "").lower() if title_arr else ""

        korean_arr = props.get("한글명", {}).get("rich_text", [])
        korean = korean_arr[0].get("plain_text", "") if korean_arr else ""

        mapping[num] = {
            "name": name,
            "korean": korean,
            "page_id": page["id"]
        }

        # 역방향 매핑 (이름 → 번호)
        if name:
            mapping[name] = num
            mapping[name.replace("_", "")] = num
        if korean:
            mapping[korean] = num

    return mapping


def find_content_folder(num: int) -> Path:
    """번호로 콘텐츠 폴더 찾기"""
    num_str = f"{num:03d}"
    for status_dir in STATUS_DIRS:
        status_path = CONTENTS_DIR / status_dir
        if not status_path.exists():
            continue
        for item in status_path.iterdir():
            if item.is_dir() and item.name.startswith(num_str):
                return item
    return None


def find_content_by_keyword(keyword: str) -> tuple:
    """키워드로 콘텐츠 폴더 찾기"""
    keyword = keyword.lower().strip()

    for status_dir in STATUS_DIRS:
        status_path = CONTENTS_DIR / status_dir
        if not status_path.exists():
            continue
        for item in status_path.iterdir():
            if not item.is_dir():
                continue
            folder_name = item.name.lower()
            # 폴더명에 키워드 포함 여부 확인
            if keyword in folder_name:
                try:
                    num = int(item.name[:3])
                    return item, num
                except ValueError:
                    continue
    return None, None


def update_notion_clean_status(num: int, has_clean: bool, mapping: dict):
    """노션 표지_Clean 열 업데이트"""
    info = mapping.get(num)
    if not info or not isinstance(info, dict):
        return False

    page_id = info.get("page_id")
    if not page_id:
        return False

    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {
        "properties": {
            "표지_Clean": {"select": {"name": "완료"} if has_clean else None}
        }
    }

    response = requests.patch(url, headers=get_notion_headers(), json=payload)
    return response.status_code == 200


def distribute_clean_images(image_mapping: dict = None, dry_run: bool = False):
    """
    클린 이미지 배치 실행

    image_mapping: {파일명: 콘텐츠번호} 딕셔너리 (수동 매핑용)
    """
    print("━" * 60)
    print("📷 클린 이미지 배치")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("   §17 규칙: 복사만 허용, 원본 유지")
    print("━" * 60)

    if not CLEAN_READY_DIR.exists():
        print(f"❌ 폴더 없음: {CLEAN_READY_DIR}")
        return

    # 노션 매핑 로드
    print("\n📥 노션 매핑 로드 중...")
    notion_mapping = fetch_notion_mapping()
    print(f"   {len([k for k in notion_mapping.keys() if isinstance(k, int)])}개 콘텐츠")

    # 이미지 파일 목록
    images = [f for f in CLEAN_READY_DIR.iterdir()
              if f.is_file() and f.suffix.lower() in [".png", ".jpg", ".jpeg", ".webp"]]

    print(f"\n📁 99_CleanReady/ 이미지: {len(images)}개")

    stats = {
        "copied": [],
        "skipped": [],
        "not_found": [],
        "notion_updated": []
    }

    for img in images:
        filename = img.name

        # 매핑에서 번호 찾기
        num = None
        if image_mapping and filename in image_mapping:
            num = image_mapping[filename]
        else:
            # 파일명 첫 단어로 자동 매칭 시도
            keyword = filename.split("_")[0].lower()
            if keyword in notion_mapping and isinstance(notion_mapping[keyword], int):
                num = notion_mapping[keyword]
            else:
                # 폴더명 검색
                folder, found_num = find_content_by_keyword(keyword)
                if folder:
                    num = found_num

        if num is None:
            stats["not_found"].append(filename)
            continue

        # 콘텐츠 폴더 찾기
        content_folder = find_content_folder(num)
        if not content_folder:
            stats["not_found"].append(f"{filename} (#{num:03d} 폴더 없음)")
            continue

        # 0_clean 폴더 생성
        clean_folder = content_folder / "0_clean"

        if not dry_run:
            clean_folder.mkdir(exist_ok=True)

        # 대상 파일 경로
        dest_path = clean_folder / filename

        # 이미 존재하면 스킵
        if dest_path.exists():
            stats["skipped"].append(f"#{num:03d} {filename}")
            continue

        # 복사 (이동 아님!)
        if not dry_run:
            shutil.copy2(img, dest_path)

        info = notion_mapping.get(num, {})
        korean = info.get("korean", "") if isinstance(info, dict) else ""
        print(f"   ✅ #{num:03d} {korean} ← {filename}")
        stats["copied"].append(f"#{num:03d} {korean}")

        # 노션 업데이트
        if not dry_run:
            if update_notion_clean_status(num, True, notion_mapping):
                stats["notion_updated"].append(num)

    # 결과 리포트
    print("\n" + "━" * 60)
    print("📊 배치 결과")
    print("━" * 60)
    print(f"✅ 복사 완료: {len(stats['copied'])}개")
    print(f"⏭️ 스킵 (이미 존재): {len(stats['skipped'])}개")
    print(f"❌ 매칭 실패: {len(stats['not_found'])}개")
    print(f"📋 노션 업데이트: {len(stats['notion_updated'])}개")

    if stats["not_found"]:
        print("\n⚠️ 매칭 실패 파일:")
        for f in stats["not_found"]:
            print(f"   - {f}")

    print("━" * 60)

    return stats


def main():
    import sys

    dry_run = "--dry-run" in sys.argv

    if dry_run:
        print("🔍 DRY RUN 모드 (실제 복사 안 함)\n")

    # 수동 매핑이 필요한 경우 여기에 추가
    # 파일명에 음식명이 없는 Higgsfield 파일용
    manual_mapping = {}

    distribute_clean_images(manual_mapping, dry_run)


if __name__ == "__main__":
    main()
