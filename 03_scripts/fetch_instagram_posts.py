#!/usr/bin/env python3
"""
Instagram 게시물 전체 수집 스크립트
SSOT: Instagram 기준으로 posted_id 생성
"""
import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine')

from dotenv import load_dotenv
load_dotenv(Path('/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/.env'))

import requests

# 환경변수
INSTAGRAM_BUSINESS_ID = os.environ.get('INSTAGRAM_BUSINESS_ACCOUNT_ID')
INSTAGRAM_ACCESS_TOKEN = os.environ.get('INSTAGRAM_ACCESS_TOKEN')
API_VERSION = 'v21.0'

# 음식명 매핑 (캡션 → food_id)
FOOD_MAPPING = {
    # 과일
    'apple': 'apple', '사과': 'apple',
    'banana': 'banana', '바나나': 'banana',
    'blueberry': 'blueberry', 'blueberries': 'blueberry', '블루베리': 'blueberry',
    'cherry': 'cherry', 'cherries': 'cherry', '체리': 'cherry',
    'grape': 'grape', '포도': 'grape',
    'kiwi': 'kiwi', '키위': 'kiwi',
    'mango': 'mango', '망고': 'mango',
    'orange': 'orange', '오렌지': 'orange',
    'papaya': 'papaya', '파파야': 'papaya',
    'peach': 'peach', '복숭아': 'peach',
    'pear': 'pear', '배': 'pear',
    'pineapple': 'pineapple', '파인애플': 'pineapple',
    'strawberry': 'strawberry', '딸기': 'strawberry',
    'watermelon': 'watermelon', '수박': 'watermelon',

    # 채소
    'avocado': 'avocado', '아보카도': 'avocado',
    'broccoli': 'broccoli', '브로콜리': 'broccoli',
    'carrot': 'carrot', '당근': 'carrot',
    'celery': 'celery', '셀러리': 'celery',
    'cucumber': 'cucumber', '오이': 'cucumber',
    'kale': 'kale', '케일': 'kale',
    'olive': 'olive', '올리브': 'olive',
    'pumpkin': 'pumpkin', '호박': 'pumpkin',
    'spinach': 'spinach', '시금치': 'spinach',
    'sweet potato': 'sweet_potato', '고구마': 'sweet_potato',
    'zucchini': 'zucchini', '애호박': 'zucchini',

    # 단백질
    'beef': 'beef', '소고기': 'beef',
    'boiled egg': 'boiled_egg', '삶은 달걀': 'boiled_egg', '삶은달걀': 'boiled_egg',
    'chicken': 'chicken', '닭고기': 'chicken',
    'salmon': 'salmon', '연어': 'salmon',
    'shrimp': 'shrimp', '새우': 'shrimp',
    'tuna': 'tuna', '참치': 'tuna',
    'samgyeopsal': 'samgyeopsal', '삼겹살': 'samgyeopsal',
    'yangnyeom chicken': 'yangnyeom_chicken', '양념치킨': 'yangnyeom_chicken',

    # 가공식품/기타
    'budweiser': 'budweiser', '버드와이저': 'budweiser',
    'coca cola': 'coca_cola', 'cola': 'coca_cola', '콜라': 'coca_cola',
    'ice cream': 'icecream', 'icecream': 'icecream', '아이스크림': 'icecream',
    'kitkat': 'kitkat', '킷캣': 'kitkat',
    'pasta': 'pasta', '파스타': 'pasta',
    'pringles': 'pringles', '프링글스': 'pringles',
    'rice': 'rice', '쌀': 'rice', '밥': 'rice',
    'sausage': 'sausage', '소시지': 'sausage',
}


def extract_food_id_from_caption(caption: str) -> str:
    """캡션에서 food_id 추출 (첫 줄만 검사)"""
    if not caption:
        return 'unknown'

    # 첫 줄만 추출
    first_line = caption.split('\n')[0].strip().lower()

    # 이모지 및 특수문자 제거
    clean_line = re.sub(r'[^\w\s가-힣]', ' ', first_line)
    clean_line = ' '.join(clean_line.split())

    # 매핑에서 검색 (긴 것부터)
    sorted_keys = sorted(FOOD_MAPPING.keys(), key=len, reverse=True)
    for key in sorted_keys:
        if key in clean_line:
            return FOOD_MAPPING[key]

    return 'unknown'


def extract_shortcode_from_permalink(permalink: str) -> str:
    """permalink에서 shortcode 추출"""
    # https://www.instagram.com/p/DUPHwxiUT7/ → DUPHwxiUT7
    if not permalink:
        return ''

    match = re.search(r'/p/([A-Za-z0-9_-]+)', permalink)
    if match:
        return match.group(1)
    return ''


def fetch_all_posts() -> list:
    """Instagram 게시물 전체 수집"""

    if not INSTAGRAM_BUSINESS_ID or not INSTAGRAM_ACCESS_TOKEN:
        print("❌ Instagram API 환경변수 미설정")
        return []

    url = f"https://graph.facebook.com/{API_VERSION}/{INSTAGRAM_BUSINESS_ID}/media"
    params = {
        "access_token": INSTAGRAM_ACCESS_TOKEN,
        "fields": "id,caption,timestamp,permalink,media_type",
        "limit": 100
    }

    all_posts = []

    while url:
        response = requests.get(url, params=params)
        data = response.json()

        if 'error' in data:
            print(f"❌ API 오류: {data['error'].get('message', 'Unknown error')}")
            break

        posts = data.get('data', [])
        all_posts.extend(posts)

        # 다음 페이지
        paging = data.get('paging', {})
        url = paging.get('next')
        params = {}  # 다음 페이지 URL에 이미 파라미터 포함

    return all_posts


def process_posts(raw_posts: list) -> list:
    """원시 데이터를 처리하여 posted_id 생성"""

    result = []

    for post in raw_posts:
        caption = post.get('caption', '')
        permalink = post.get('permalink', '')

        food_id = extract_food_id_from_caption(caption)
        shortcode = extract_shortcode_from_permalink(permalink)

        if food_id == 'unknown':
            print(f"  ⚠️ 음식 식별 불가: {caption[:50]}...")
            continue

        posted_id = f"{food_id}__{shortcode}" if shortcode else food_id

        # timestamp 파싱
        timestamp = post.get('timestamp', '')
        posted_at = timestamp[:10] if timestamp else ''

        result.append({
            'media_id': post.get('id', ''),
            'food_id': food_id,
            'shortcode': shortcode,
            'posted_id': posted_id,
            'posted_at': posted_at,
            'permalink': permalink,
            'caption_preview': caption[:100] if caption else ''
        })

    return result


def main():
    print("=== Instagram 게시물 수집 ===\n")

    # 1. API 호출
    print("1. Instagram API 호출...")
    raw_posts = fetch_all_posts()
    print(f"   수집된 게시물: {len(raw_posts)}개\n")

    if not raw_posts:
        print("❌ 게시물을 가져올 수 없습니다.")
        return

    # 2. 데이터 처리
    print("2. 데이터 처리...")
    posts = process_posts(raw_posts)
    print(f"   처리된 게시물: {len(posts)}개\n")

    # 3. 결과 저장
    output_path = Path('/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/config/data/instagram_posts.json')
    output_path.parent.mkdir(parents=True, exist_ok=True)

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump({
            'fetched_at': datetime.now().isoformat(),
            'total_count': len(posts),
            'posts': posts
        }, f, ensure_ascii=False, indent=2)

    print(f"3. 결과 저장: {output_path}")

    # 4. 요약 출력
    print(f"\n=== 수집 결과 ===")
    print(f"총 게시물: {len(posts)}개")

    # food_id별 카운트
    food_counts = {}
    for p in posts:
        fid = p['food_id']
        food_counts[fid] = food_counts.get(fid, 0) + 1

    # 중복 확인
    duplicates = {k: v for k, v in food_counts.items() if v > 1}
    if duplicates:
        print(f"\n중복 게시물:")
        for fid, count in duplicates.items():
            print(f"  - {fid}: {count}회")

    print(f"\n✅ 수집 완료!")

    return posts


if __name__ == '__main__':
    main()
