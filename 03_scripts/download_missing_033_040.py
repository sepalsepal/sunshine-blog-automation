#!/usr/bin/env python3
"""
Blog Image Standard v1.2 - 누락된 033-040 음식사진 다운로드
"""

import os
import requests
from PIL import Image, ImageEnhance
from dotenv import load_dotenv

load_dotenv()

BASE_PATH = "/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine"
PD_REVIEW = f"{BASE_PATH}/박pd_확인용"
CONTENTS_1 = f"{BASE_PATH}/contents/1_cover_only"

PEXELS_API_KEY = os.getenv("PEXELS_API_KEY")

# 검색어 매핑
SEARCH_QUERIES = {
    "baguette": "baguette bread isolated white background",
    "red_bean_bread": "red bean bread anpan isolated white background",
    "cauliflower": "cauliflower isolated white background close up",
    "bean_sprouts": "bean sprouts isolated white background",
    "yogurt": "yogurt cup isolated white background",
    "lotus_root": "lotus root slice isolated white background",
}

# 033-040 폴더 매핑 (누락 항목만)
FOLDER_MAP = {
    "033_baguette": "baguette",
    "034_red_bean_bread": "red_bean_bread",
    "037_cauliflower": "cauliflower",
    "038_bean_sprouts": "bean_sprouts",
    "039_yogurt": "yogurt",
    "040_lotus_root": "lotus_root",
}


def search_pexels(query):
    """Pexels API로 이미지 검색"""
    url = "https://api.pexels.com/v1/search"
    headers = {"Authorization": PEXELS_API_KEY}
    params = {"query": query, "per_page": 1, "size": "large"}

    resp = requests.get(url, headers=headers, params=params)
    resp.raise_for_status()
    data = resp.json()

    if data.get("photos"):
        return data["photos"][0]["src"]["large2x"]
    return None


def download_image(url, output_path):
    """이미지 다운로드"""
    resp = requests.get(url, stream=True)
    resp.raise_for_status()

    with open(output_path, 'wb') as f:
        for chunk in resp.iter_content(chunk_size=8192):
            f.write(chunk)


def process_image(input_path, output_path):
    """1080x1080 크롭 + 톤 보정 (Blog Image Standard v1.1)"""
    img = Image.open(input_path)
    if img.mode != 'RGB':
        img = img.convert('RGB')

    # 정사각형 중앙 크롭
    width, height = img.size
    min_dim = min(width, height)
    left = (width - min_dim) // 2
    top = (height - min_dim) // 2
    img = img.crop((left, top, left + min_dim, top + min_dim))

    # 1080x1080 리사이즈
    img = img.resize((1080, 1080), Image.LANCZOS)

    # 톤 보정
    enhancer = ImageEnhance.Brightness(img)
    img = enhancer.enhance(1.05)
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(0.95)
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.03)

    img.save(output_path, 'PNG', optimize=True)
    return os.path.getsize(output_path) / 1024


def download_and_process(folder_name, food_key):
    """Pexels API로 검색 후 다운로드 및 처리"""
    query = SEARCH_QUERIES.get(food_key, food_key)

    # 2026-02-13: 플랫 구조 - blog → 02_Blog
    blog_dir = f"{CONTENTS_1}/{folder_name}/02_Blog"
    output_path = f"{blog_dir}/2_음식사진.png"

    # 이미 있으면 스킵
    if os.path.exists(output_path):
        print(f"⏭️ {folder_name}: 이미 존재함")
        return True

    os.makedirs(blog_dir, exist_ok=True)
    raw_path = f"{PD_REVIEW}/{folder_name}_raw.jpg"

    try:
        # Pexels API 검색
        image_url = search_pexels(query)
        if not image_url:
            print(f"❌ {folder_name}: 검색 결과 없음")
            return False

        # 다운로드
        download_image(image_url, raw_path)

        # 처리
        size_kb = process_image(raw_path, output_path)
        os.remove(raw_path)

        print(f"✅ {folder_name} -> 2_음식사진.png ({size_kb:.0f}KB)")
        return True

    except Exception as e:
        print(f"❌ {folder_name}: {e}")
        if os.path.exists(raw_path):
            os.remove(raw_path)
        return False


def main():
    if not PEXELS_API_KEY:
        print("❌ PEXELS_API_KEY가 .env에 없습니다")
        return

    os.makedirs(PD_REVIEW, exist_ok=True)

    print("=" * 50)
    print("Blog Image Standard v1.2 - 누락 033-040 처리")
    print("=" * 50)
    print()

    success = 0
    total = len(FOLDER_MAP)

    for folder_name, food_key in FOLDER_MAP.items():
        if download_and_process(folder_name, food_key):
            success += 1

    print()
    print("=" * 50)
    print(f"완료: {success}/{total}")
    print("=" * 50)


if __name__ == "__main__":
    main()
