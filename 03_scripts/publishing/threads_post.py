#!/usr/bin/env python3
"""
Threads 게시 스크립트 v2.0
- 4장 캐러셀 지원 (Common 01, 02, 03, 09)
- v1.1 캡션 직접 사용 (변환 없음)
- Cloudinary URL 자동 생성

업데이트: 2026-02-16
"""

import os
import sys
import json
import time
import requests
from pathlib import Path
from typing import Optional, Dict, Any, List
from dotenv import load_dotenv

# 프로젝트 루트
ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

# Threads API 설정
THREADS_USER_ID = os.getenv("THREADS_USER_ID")
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_API_URL = "https://graph.threads.net/v1.0"

# Cloudinary 설정
CLOUDINARY_CLOUD_NAME = os.getenv("CLOUDINARY_CLOUD_NAME")

# 콘텐츠 경로
CONTENTS_DIR = ROOT / "01_contents"

# 캐러셀 이미지 순서 (Common 파일 번호)
CAROUSEL_ORDER = ["01_Cover", "02_Food", "03_DogWithFood", "09_Cta"]


def get_content_folder(number: int) -> Optional[Path]:
    """콘텐츠 번호로 폴더 경로 찾기"""
    pattern = f"{number:03d}_*"
    matches = list(CONTENTS_DIR.glob(pattern))
    if matches:
        return matches[0]
    return None


def get_food_name(folder: Path) -> tuple[str, str]:
    """폴더에서 영문/한글 음식명 추출"""
    # 폴더명: 008_Banana
    folder_name = folder.name
    parts = folder_name.split("_", 1)
    if len(parts) == 2:
        english_name = parts[1]
        # metadata.json에서 한글명 가져오기
        metadata_path = folder / "metadata.json"
        korean_name = english_name
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    meta = json.load(f)
                    korean_name = meta.get("name_kr", english_name)
            except:
                pass
        return english_name, korean_name
    return folder_name, folder_name


def get_carousel_images(folder: Path, food_name: str) -> List[Path]:
    """캐러셀용 4장 이미지 경로 반환 (Common 01, 02, 03, 09)"""
    images = []
    folder_num = folder.name.split("_")[0]

    for img_type in CAROUSEL_ORDER:
        # 패턴: 008_Banana_Common_01_Cover.png
        pattern = f"{folder_num}_{food_name}_Common_{img_type}.png"
        img_path = folder / pattern

        if img_path.exists():
            images.append(img_path)
        else:
            print(f"  ⚠️ 이미지 없음: {pattern}")

    return images


def get_threads_caption(folder: Path, food_name: str) -> Optional[str]:
    """Threads v1.1 캡션 파일 읽기"""
    # 패턴: Banana_SAFE_Threads_Caption.txt
    caption_dir = folder / "01_Insta&Thread"

    if not caption_dir.exists():
        return None

    # 안전도별 캡션 파일 찾기
    for safety in ["SAFE", "CAUTION", "DANGER", "FORBIDDEN"]:
        caption_file = caption_dir / f"{food_name}_{safety}_Threads_Caption.txt"
        if caption_file.exists():
            with open(caption_file, 'r', encoding='utf-8') as f:
                return f.read().strip()

    return None


def upload_to_cloudinary(image_path: Path, public_id: str) -> Optional[str]:
    """이미지를 Cloudinary에 업로드하고 URL 반환"""
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET")
    )

    try:
        result = cloudinary.uploader.upload(
            str(image_path),
            public_id=public_id,
            overwrite=True,
            resource_type="image"
        )
        return result.get("secure_url")
    except Exception as e:
        print(f"  ❌ Cloudinary 업로드 실패: {e}")
        return None


def get_or_upload_image_url(image_path: Path, folder_name: str, img_index: int) -> Optional[str]:
    """Cloudinary URL 가져오기 (없으면 업로드)"""
    # public_id 생성: threads/008_Banana/01
    public_id = f"threads/{folder_name}/{img_index:02d}"

    # 기존 URL 확인
    base_url = f"https://res.cloudinary.com/{CLOUDINARY_CLOUD_NAME}/image/upload"
    existing_url = f"{base_url}/{public_id}.png"

    try:
        resp = requests.head(existing_url, timeout=5)
        if resp.status_code == 200:
            return existing_url
    except:
        pass

    # 업로드
    print(f"  📤 업로드 중: {image_path.name}")
    return upload_to_cloudinary(image_path, public_id)


def create_image_container(image_url: str) -> Optional[str]:
    """단일 이미지 컨테이너 생성"""
    url = f"{THREADS_API_URL}/{THREADS_USER_ID}/threads"

    params = {
        "access_token": THREADS_ACCESS_TOKEN,
        "media_type": "IMAGE",
        "image_url": image_url,
        "is_carousel_item": "true"
    }

    try:
        resp = requests.post(url, params=params, timeout=30)
        data = resp.json()

        if "id" in data:
            return data["id"]
        else:
            print(f"  ❌ 이미지 컨테이너 실패: {data}")
            return None
    except Exception as e:
        print(f"  ❌ API 오류: {e}")
        return None


def create_carousel_container(children_ids: List[str], caption: str) -> Optional[str]:
    """캐러셀 컨테이너 생성"""
    url = f"{THREADS_API_URL}/{THREADS_USER_ID}/threads"

    params = {
        "access_token": THREADS_ACCESS_TOKEN,
        "media_type": "CAROUSEL",
        "children": ",".join(children_ids),
        "text": caption
    }

    try:
        resp = requests.post(url, params=params, timeout=30)
        data = resp.json()

        if "id" in data:
            print(f"  ✅ 캐러셀 컨테이너 생성: {data['id']}")
            return data["id"]
        else:
            print(f"  ❌ 캐러셀 컨테이너 실패: {data}")
            return None
    except Exception as e:
        print(f"  ❌ API 오류: {e}")
        return None


def wait_for_container(container_id: str, max_wait: int = 30) -> bool:
    """컨테이너 상태가 FINISHED가 될 때까지 대기"""
    url = f"{THREADS_API_URL}/{container_id}"
    params = {
        "access_token": THREADS_ACCESS_TOKEN,
        "fields": "status"
    }

    for _ in range(max_wait):
        try:
            resp = requests.get(url, params=params, timeout=10)
            data = resp.json()
            status = data.get("status")

            if status == "FINISHED":
                return True
            elif status == "ERROR":
                print(f"  ❌ 컨테이너 오류: {data}")
                return False

            time.sleep(1)
        except Exception as e:
            print(f"  ⚠️ 상태 확인 오류: {e}")
            time.sleep(1)

    print("  ⚠️ 타임아웃")
    return False


def publish_container(container_id: str) -> Optional[Dict[str, Any]]:
    """컨테이너 게시"""
    url = f"{THREADS_API_URL}/{THREADS_USER_ID}/threads_publish"

    params = {
        "access_token": THREADS_ACCESS_TOKEN,
        "creation_id": container_id
    }

    try:
        resp = requests.post(url, params=params, timeout=30)
        data = resp.json()

        if "id" in data:
            post_id = data["id"]
            # Threads URL 형식
            threads_url = f"https://www.threads.net/@sunshinedogfood/post/{post_id}"
            print(f"  ✅ 게시 완료!")
            return {
                "success": True,
                "post_id": post_id,
                "url": threads_url
            }
        else:
            print(f"  ❌ 게시 실패: {data}")
            return {"success": False, "error": str(data)}
    except Exception as e:
        print(f"  ❌ 게시 오류: {e}")
        return {"success": False, "error": str(e)}


def post_carousel_to_threads(
    number: int,
    dry_run: bool = False
) -> Optional[Dict[str, Any]]:
    """4장 캐러셀을 Threads에 게시"""

    # 폴더 찾기
    folder = get_content_folder(number)
    if not folder:
        print(f"❌ 콘텐츠 폴더 없음: {number:03d}")
        return None

    food_name, food_name_kr = get_food_name(folder)

    print(f"\n{'='*50}")
    print(f"📤 Threads 캐러셀 게시: {number:03d} {food_name_kr} ({food_name})")
    print(f"{'='*50}")

    # 이미지 4장 가져오기
    images = get_carousel_images(folder, food_name)
    if len(images) < 4:
        print(f"❌ 이미지 부족: {len(images)}/4장")
        return None

    print(f"\n📷 이미지 4장:")
    for i, img in enumerate(images, 1):
        print(f"  {i}. {img.name}")

    # 캡션 가져오기
    caption = get_threads_caption(folder, food_name)
    if not caption:
        print(f"❌ 캡션 파일 없음")
        return None

    print(f"\n📝 캡션 ({len(caption)}자):")
    print("-" * 40)
    print(caption[:200] + "..." if len(caption) > 200 else caption)
    print("-" * 40)

    if dry_run:
        print("\n[DRY-RUN] 실제 게시하지 않음")
        return {"success": True, "dry_run": True}

    # Cloudinary에 이미지 업로드 및 URL 획득
    print(f"\n☁️ Cloudinary 이미지 준비:")
    image_urls = []
    for i, img_path in enumerate(images):
        url = get_or_upload_image_url(img_path, folder.name, i + 1)
        if url:
            image_urls.append(url)
            print(f"  ✅ {i+1}번: {url[:60]}...")
        else:
            print(f"  ❌ {i+1}번 실패")
            return None

    # 이미지 컨테이너 생성
    print(f"\n🔧 이미지 컨테이너 생성:")
    children_ids = []
    for i, url in enumerate(image_urls):
        container_id = create_image_container(url)
        if container_id:
            children_ids.append(container_id)
            print(f"  ✅ {i+1}번: {container_id}")
            time.sleep(1)  # Rate limit
        else:
            print(f"  ❌ {i+1}번 실패")
            return None

    # 컨테이너 상태 대기
    print(f"\n⏳ 컨테이너 처리 대기...")
    for cid in children_ids:
        if not wait_for_container(cid):
            print(f"  ❌ 컨테이너 준비 실패: {cid}")
            return None
    print("  ✅ 모든 컨테이너 준비 완료")

    # 캐러셀 컨테이너 생성
    print(f"\n🎠 캐러셀 컨테이너 생성:")
    carousel_id = create_carousel_container(children_ids, caption)
    if not carousel_id:
        return None

    # 캐러셀 상태 대기
    if not wait_for_container(carousel_id):
        print("  ❌ 캐러셀 준비 실패")
        return None

    # 게시
    print(f"\n🚀 게시 중...")
    result = publish_container(carousel_id)

    return result


def main():
    """메인 실행"""
    import argparse

    parser = argparse.ArgumentParser(description="Threads 캐러셀 게시 v2.0")
    parser.add_argument("number", type=int, nargs="?", help="콘텐츠 번호 (예: 8)")
    parser.add_argument("--dry-run", action="store_true", help="실제 게시 안 함")
    parser.add_argument("--list", action="store_true", help="게시 가능 콘텐츠 목록")

    args = parser.parse_args()

    if args.list:
        print("📋 게시 가능 콘텐츠:")
        print("-" * 50)
        for folder in sorted(CONTENTS_DIR.iterdir()):
            if folder.is_dir() and folder.name[0].isdigit():
                food_name, food_name_kr = get_food_name(folder)
                images = get_carousel_images(folder, food_name)
                caption = get_threads_caption(folder, food_name)

                img_status = "✅" if len(images) == 4 else f"❌ ({len(images)}/4)"
                cap_status = "✅" if caption else "❌"

                print(f"  {folder.name}: 이미지 {img_status} 캡션 {cap_status}")

    elif args.number:
        result = post_carousel_to_threads(args.number, dry_run=args.dry_run)

        if result:
            print(f"\n{'='*50}")
            if result.get("success"):
                if result.get("dry_run"):
                    print("✅ DRY-RUN 완료")
                else:
                    print(f"✅ 게시 성공!")
                    print(f"   URL: {result.get('url')}")
            else:
                print(f"❌ 게시 실패: {result.get('error')}")
            print(f"{'='*50}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
