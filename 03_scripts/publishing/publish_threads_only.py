#!/usr/bin/env python3
"""
Threads 전용 게시 스크립트
- Instagram 없이 Threads만 게시
- 캐러셀 4장 지원
"""

import os
import sys
import time
import requests
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import cloudinary
import cloudinary.uploader

# Cloudinary 설정
cloudinary.config(
    cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
    api_key=os.getenv("CLOUDINARY_API_KEY"),
    api_secret=os.getenv("CLOUDINARY_API_SECRET")
)

# Threads API 설정
THREADS_USER_ID = os.getenv("THREADS_USER_ID")
THREADS_ACCESS_TOKEN = os.getenv("THREADS_ACCESS_TOKEN")
THREADS_API_URL = "https://graph.threads.net/v1.0"

# 콘텐츠 폴더 매핑
CONTENT_MAP = {
    "pumpkin": "001_pumpkin_published",
    "blueberries": "002_blueberries_published",
    "carrot": "003_carrot_published",
    "apple": "004_apple_published",
    "sweet_potato": "005_sweet_potato_published",
    "cherries": "006_cherries_published",
    "pineapple": "007_pineapple_published",
    "watermelon": "008_watermelon_published",
    "banana": "009_banana_published",
    "broccoli": "010_broccoli_published",
    "strawberry": "011_strawberry_published",
    "mango": "012_mango_published",
}

TOPIC_KR_MAP = {
    "pumpkin": "호박", "blueberries": "블루베리", "carrot": "당근",
    "apple": "사과", "sweet_potato": "고구마", "cherries": "체리",
    "pineapple": "파인애플", "watermelon": "수박", "banana": "바나나",
    "broccoli": "브로콜리", "strawberry": "딸기", "mango": "망고",
}


def upload_to_cloudinary(image_paths: list, topic: str) -> list:
    """이미지를 Cloudinary에 업로드하고 URL 반환"""
    urls = []
    for i, path in enumerate(image_paths):
        public_id = f"threads/{topic}/{topic}_{i:02d}"
        result = cloudinary.uploader.upload(
            path,
            public_id=public_id,
            overwrite=True
        )
        urls.append(result["secure_url"])
        print(f"  ☁️ 업로드: {path} → {result['secure_url'][:50]}...")
    return urls


def post_to_threads(caption: str, image_urls: list) -> dict:
    """Threads에 캐러셀 게시"""
    if not THREADS_USER_ID or not THREADS_ACCESS_TOKEN:
        return {"success": False, "error": "Threads API 미설정 (토큰 확인 필요)"}

    print(f"\n📤 Threads 캐러셀 게시 중... ({len(image_urls)}장)")

    try:
        # 1. 각 이미지별 미디어 컨테이너 생성
        media_container_ids = []
        for i, img_url in enumerate(image_urls):
            url = f"{THREADS_API_URL}/{THREADS_USER_ID}/threads"
            params = {
                "access_token": THREADS_ACCESS_TOKEN,
                "media_type": "IMAGE",
                "image_url": img_url,
                "is_carousel_item": "true"
            }

            resp = requests.post(url, params=params, timeout=30)
            data = resp.json()

            if "id" not in data:
                error_msg = data.get("error", {}).get("message", str(data))
                return {"success": False, "error": f"이미지 {i+1} 컨테이너 실패: {error_msg}"}

            media_container_ids.append(data["id"])
            print(f"   ✅ 이미지 {i+1}/{len(image_urls)} 컨테이너 생성")
            time.sleep(1)

        # 2. 캐러셀 컨테이너 생성
        carousel_url = f"{THREADS_API_URL}/{THREADS_USER_ID}/threads"
        carousel_params = {
            "access_token": THREADS_ACCESS_TOKEN,
            "media_type": "CAROUSEL",
            "children": ",".join(media_container_ids),
            "text": caption
        }

        resp = requests.post(carousel_url, params=carousel_params, timeout=30)
        data = resp.json()

        if "id" not in data:
            error_msg = data.get("error", {}).get("message", str(data))
            return {"success": False, "error": f"캐러셀 컨테이너 실패: {error_msg}"}

        carousel_container_id = data["id"]
        print(f"   ✅ 캐러셀 컨테이너 생성")
        time.sleep(3)

        # 3. 캐러셀 게시
        pub_url = f"{THREADS_API_URL}/{THREADS_USER_ID}/threads_publish"
        pub_params = {
            "access_token": THREADS_ACCESS_TOKEN,
            "creation_id": carousel_container_id
        }

        resp = requests.post(pub_url, params=pub_params, timeout=30)
        data = resp.json()

        if "id" in data:
            post_id = data["id"]
            threads_url = f"https://www.threads.net/post/{post_id}"
            return {"success": True, "post_id": post_id, "url": threads_url}
        else:
            error_msg = data.get("error", {}).get("message", str(data))
            return {"success": False, "error": f"게시 실패: {error_msg}"}

    except Exception as e:
        return {"success": False, "error": str(e)}


def publish_threads_only(topic: str):
    """Threads 전용 게시 (Instagram 제외)"""
    folder = CONTENT_MAP.get(topic)
    if not folder:
        print(f"❌ 지원하지 않는 토픽: {topic}")
        return

    image_dir = ROOT / "content" / "images" / folder
    topic_kr = TOPIC_KR_MAP.get(topic, topic)

    print("=" * 60)
    print(f"🧵 {topic.upper()} ({topic_kr}) - Threads 전용 게시")
    print("=" * 60)

    # 이미지 수집 (01-04)
    image_paths = []
    for i in range(1, 5):
        img_path = image_dir / f"{topic}_{i:02d}.png"
        if img_path.exists():
            image_paths.append(str(img_path))
            print(f"  ✅ {img_path.name}")
        else:
            # 00-03 형식 시도
            img_path = image_dir / f"{topic}_{i-1:02d}.png"
            if img_path.exists():
                image_paths.append(str(img_path))
                print(f"  ✅ {img_path.name}")

    if len(image_paths) < 4:
        print(f"❌ 이미지 부족: {len(image_paths)}/4장")
        return

    # 캡션 로드 (Threads용)
    threads_caption_path = image_dir / "caption_threads.txt"
    if threads_caption_path.exists():
        with open(threads_caption_path, 'r', encoding='utf-8') as f:
            caption = f.read().strip()
    else:
        # 기본 캡션
        caption = f"다들 {topic_kr} 어떻게 주고 있어?\n\n너네 강아지는 이거 좋아해? 댓글 ㄱㄱ 🐕"

    print(f"\n캡션:")
    print("-" * 40)
    print(caption)
    print("-" * 40)

    # Cloudinary 업로드
    print(f"\n☁️ Cloudinary 업로드 중...")
    cloudinary_urls = upload_to_cloudinary(image_paths, topic)

    if len(cloudinary_urls) < 4:
        print(f"❌ 업로드 실패")
        return

    # Threads 게시
    result = post_to_threads(caption, cloudinary_urls)

    print("\n" + "=" * 60)
    if result.get("success"):
        print(f"🎉 Threads 게시 완료!")
        print(f"   Post ID: {result.get('post_id')}")
        print(f"   URL: {result.get('url')}")
    else:
        print(f"❌ Threads 게시 실패: {result.get('error')}")
    print("=" * 60)

    return result


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="Threads 전용 게시")
    parser.add_argument("topic", help="게시할 토픽명")
    args = parser.parse_args()

    publish_threads_only(args.topic.lower())
