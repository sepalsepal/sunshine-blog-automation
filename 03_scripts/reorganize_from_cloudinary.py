#!/usr/bin/env python3
"""
reorganize_from_cloudinary.py - Cloudinary 복구 이미지를 노션 기준으로 재정리
"""

import os
import sys
import re
import shutil
import requests
from pathlib import Path
from collections import defaultdict
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
NOTION_API_VERSION = "2022-06-28"

CONTENTS_DIR = PROJECT_ROOT / "01_contents"
RESTORE_DIR = CONTENTS_DIR / "cloudinary_restore"

# 2026-02-13: 플랫 구조 - STATUS_FOLDER_MAP 제거
# STATUS_FOLDER_MAP = {
#     "게시완료": "4_posted",
#     "승인완료": "3_approved",
#     "본문완료": "2_body_ready",
#     "표지완료": "1_cover_only",
#     "": "1_cover_only",  # 기본값
# }


def get_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": NOTION_API_VERSION
    }


def fetch_notion_contents():
    """노션 DB에서 136개 콘텐츠 목록 가져오기"""
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
            print(f"❌ Notion API 오류: {response.status_code}")
            break

        data = response.json()

        for page in data.get("results", []):
            props = page.get("properties", {})

            num = props.get("번호", {}).get("number")
            if num is None:
                continue

            # 영문명
            en_name = ""
            if props.get("이름", {}).get("title"):
                en_name = props["이름"]["title"][0]["plain_text"] if props["이름"]["title"] else ""

            # 한글명
            kr_name = ""
            if props.get("한글명", {}).get("rich_text"):
                kr_name = props["한글명"]["rich_text"][0]["plain_text"] if props["한글명"]["rich_text"] else ""

            # 폴더명
            folder_name = ""
            if props.get("폴더명", {}).get("rich_text"):
                folder_name = props["폴더명"]["rich_text"][0]["plain_text"] if props["폴더명"]["rich_text"] else ""

            # 인스타 상태 (주요 상태로 사용)
            status = ""
            if props.get("인스타상태", {}).get("select"):
                status = props["인스타상태"]["select"]["name"]

            contents.append({
                "번호": num,
                "영문명": en_name,
                "한글명": kr_name,
                "폴더명": folder_name,
                "상태": status,
            })

        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    return contents


def scan_cloudinary_restore():
    """복구된 Cloudinary 이미지 스캔"""
    images = defaultdict(list)

    if not RESTORE_DIR.exists():
        return images

    # 모든 이미지 파일 찾기
    for img_path in RESTORE_DIR.rglob("*"):
        if img_path.is_file() and img_path.suffix.lower() in [".jpg", ".jpeg", ".png", ".webp"]:
            # 키워드 추출 (파일명 또는 폴더명에서)
            relative = img_path.relative_to(RESTORE_DIR)
            parts = str(relative).lower().replace("_published", "").split("/")

            # 첫 번째 폴더명에서 콘텐츠 이름 추출
            if parts:
                folder_name = parts[0]
                # 번호 제거 (001_pumpkin -> pumpkin)
                match = re.match(r'^\d{3}_(.+)$', folder_name)
                if match:
                    keyword = match.group(1)
                else:
                    keyword = folder_name

                images[keyword].append(img_path)

    return images


def find_existing_folder(content_num, en_name, kr_name):
    """기존 폴더 찾기"""
    num_str = f"{content_num:03d}"

    for status_folder in ["4_posted", "3_approved", "2_body_ready", "1_cover_only"]:
        folder_path = CONTENTS_DIR / status_folder
        if not folder_path.exists():
            continue

        for item in folder_path.iterdir():
            if item.is_dir() and item.name.startswith(num_str):
                return item

    return None


def match_cloudinary_images(content, cloudinary_images):
    """콘텐츠와 매칭되는 Cloudinary 이미지 찾기"""
    matches = []
    en_name = content["영문명"].lower().replace(" ", "_")
    kr_name = content["한글명"]

    # 영문명으로 매칭
    if en_name in cloudinary_images:
        matches.extend(cloudinary_images[en_name])

    # 영문명 변형으로 매칭 (예: coca_cola -> cocacola)
    en_name_no_underscore = en_name.replace("_", "")
    for key, imgs in cloudinary_images.items():
        if key.replace("_", "") == en_name_no_underscore:
            matches.extend(imgs)

    # project_sunshine 하위 폴더에서도 찾기
    ps_path = RESTORE_DIR / "project_sunshine" / en_name
    if ps_path.exists():
        matches.extend(ps_path.glob("*.*"))

    # sunshinedogfood 하위에서도 찾기
    sdf_path = RESTORE_DIR / "sunshinedogfood" / en_name
    if sdf_path.exists():
        matches.extend(sdf_path.glob("*.*"))

    # threads 하위에서도 찾기
    threads_path = RESTORE_DIR / "threads" / en_name
    if threads_path.exists():
        matches.extend(threads_path.glob("*.*"))

    return list(set(matches))


def organize_content(content, cloudinary_images, dry_run=False):
    """콘텐츠 폴더 정리"""
    num = content["번호"]
    en_name = content["영문명"]
    kr_name = content["한글명"]
    status = content["상태"]

    num_str = f"{num:03d}"
    folder_name = f"{num_str}_{en_name}_{kr_name}" if kr_name else f"{num_str}_{en_name}"

    # 상태에 따른 대상 폴더
    status_folder = STATUS_FOLDER_MAP.get(status, "1_cover_only")
    target_dir = CONTENTS_DIR / status_folder / folder_name

    # 기존 폴더 확인
    existing = find_existing_folder(num, en_name, kr_name)

    # 매칭 이미지 찾기
    matched_images = match_cloudinary_images(content, cloudinary_images)

    result = {
        "번호": num_str,
        "영문명": en_name,
        "한글명": kr_name,
        "상태": status,
        "기존폴더": str(existing) if existing else None,
        "매칭이미지": len(matched_images),
        "대상폴더": str(target_dir),
        "처리": "skip",
    }

    # 기존 폴더 있으면 스킵
    if existing:
        result["처리"] = "existing"
        return result

    # 이미지가 있으면 폴더 생성 및 이미지 복사
    if matched_images:
        if not dry_run:
            # blog 폴더 생성
            blog_dir = target_dir / "02_Blog"
            blog_dir.mkdir(parents=True, exist_ok=True)

            # 이미지 복사
            for i, img_path in enumerate(sorted(matched_images)[:10]):
                # 슬라이드 번호 부여
                ext = img_path.suffix
                dest_name = f"slide_{i+1:02d}{ext}"
                dest_path = blog_dir / dest_name

                shutil.copy2(img_path, dest_path)

        result["처리"] = "created"
    else:
        result["처리"] = "no_images"

    return result


def main():
    print("━" * 60)
    print("📁 Cloudinary → 콘텐츠 폴더 재정리")
    print("━" * 60)

    # 1. 노션 데이터 가져오기
    print("\n📋 노션 DB 조회 중...")
    notion_contents = fetch_notion_contents()
    print(f"   {len(notion_contents)}개 콘텐츠")

    # 2. Cloudinary 복구 이미지 스캔
    print("\n📸 Cloudinary 복구 이미지 스캔 중...")
    cloudinary_images = scan_cloudinary_restore()
    print(f"   {len(cloudinary_images)}개 콘텐츠 그룹")
    for key in list(cloudinary_images.keys())[:10]:
        print(f"      - {key}: {len(cloudinary_images[key])}개")
    if len(cloudinary_images) > 10:
        print(f"      ... 외 {len(cloudinary_images) - 10}개")

    # 3. 정리 실행
    print("\n🔄 폴더 정리 실행 중...")
    results = []

    for content in notion_contents:
        result = organize_content(content, cloudinary_images, dry_run=False)
        results.append(result)

        if result["처리"] == "created":
            print(f"   ✅ {result['번호']}: {result['영문명']} → 생성")
        elif result["처리"] == "existing":
            print(f"   📁 {result['번호']}: {result['영문명']} → 기존 유지")

    # 4. 결과 통계
    created = sum(1 for r in results if r["처리"] == "created")
    existing = sum(1 for r in results if r["처리"] == "existing")
    no_images = sum(1 for r in results if r["처리"] == "no_images")
    skipped = sum(1 for r in results if r["처리"] == "skip")

    print("\n" + "━" * 60)
    print("📊 재정리 완료")
    print("━" * 60)
    print(f"📋 노션 전체: {len(notion_contents)}개")
    print(f"✅ 새로 생성: {created}개")
    print(f"📁 기존 유지: {existing}개")
    print(f"❌ 이미지 없음: {no_images}개")
    print("━" * 60)

    # 5. 불일치 리포트
    if no_images > 0:
        print("\n⚠️ 이미지 없는 콘텐츠 (Cloudinary에 없음):")
        for r in results:
            if r["처리"] == "no_images":
                print(f"   {r['번호']}: {r['영문명']} ({r['한글명']})")

    # 6. 최종 폴더 현황
    print("\n📁 최종 폴더 현황:")
    for status_folder in ["4_posted", "3_approved", "2_body_ready", "1_cover_only"]:
        folder_path = CONTENTS_DIR / status_folder
        if folder_path.exists():
            count = len([d for d in folder_path.iterdir() if d.is_dir() and not d.name.startswith(".")])
            print(f"   {status_folder}/: {count}개")


if __name__ == "__main__":
    main()
