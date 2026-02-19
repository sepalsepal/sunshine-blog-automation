#!/usr/bin/env python3
"""
Threads 캐러셀 업로더 (중복 체크 포함)
- 업로드 전 4장 이미지 중복 검사
- 중복 발견 시 업로드 차단
"""

import os
import sys
import json
import time
import hashlib
import requests
from pathlib import Path
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent.parent / '.env')

THREADS_USER_ID = os.getenv('THREADS_USER_ID')
THREADS_ACCESS_TOKEN = os.getenv('THREADS_ACCESS_TOKEN')
BASE_URL = 'https://graph.threads.net/v1.0'


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    END = '\033[0m'


def get_file_hash(filepath: Path) -> str:
    """파일 MD5 해시 계산"""
    with open(filepath, 'rb') as f:
        return hashlib.md5(f.read()).hexdigest()


def check_image_duplicates(image_paths: list) -> tuple[bool, list]:
    """
    이미지 중복 검사
    Returns: (is_valid, duplicate_pairs)
    """
    hashes = {}
    duplicates = []

    for i, path in enumerate(image_paths):
        h = get_file_hash(path)
        if h in hashes:
            duplicates.append((hashes[h], i))
        else:
            hashes[h] = i

    return len(duplicates) == 0, duplicates


def upload_to_cloudinary(image_path: Path, topic: str, num: int) -> str:
    """Cloudinary에 이미지 업로드 (MCP 대신 API 직접 호출)"""
    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )

    result = cloudinary.uploader.upload(
        str(image_path),
        folder=f'threads/{topic}',
        public_id=f'{topic}_{num:02d}_v3',
        overwrite=True,
        resource_type='image'
    )

    return result['secure_url']


def upload_carousel(topic: str, folder_path: Path, caption: str, image_urls: list = None) -> dict:
    """
    Threads 캐러셀 업로드 (중복 체크 포함)
    """
    print(f'\n{Colors.BLUE}=== Threads 캐러셀 업로드: {topic} ==={Colors.END}\n')

    # 이미지 URL이 없으면 로컬에서 찾기
    if not image_urls:
        # cloudinary_urls.json 확인
        urls_file = folder_path / 'cloudinary_urls.json'
        if urls_file.exists():
            with open(urls_file) as f:
                data = json.load(f)
            image_urls = data.get('urls', [])[:4]

    if not image_urls or len(image_urls) < 4:
        print(f'{Colors.RED}❌ 이미지 URL 4장 필요{Colors.END}')
        return None

    # STEP 0: 이미지 중복 검사 (URL에서 로컬 파일 매핑)
    print(f'{Colors.YELLOW}[STEP 0] 이미지 중복 검사{Colors.END}')

    local_images = []
    for i in range(4):
        for ext in ['.png', '.jpg']:
            img_path = folder_path / f'{topic}_{i:02d}{ext}'
            if img_path.exists():
                local_images.append(img_path)
                break

    if len(local_images) >= 4:
        is_valid, duplicates = check_image_duplicates(local_images[:4])
        if not is_valid:
            print(f'{Colors.RED}❌ 중복 이미지 발견! 업로드 차단{Colors.END}')
            for dup in duplicates:
                print(f'   - 이미지 {dup[0]:02d}와 {dup[1]:02d} 동일')
            return None
        print(f'{Colors.GREEN}✅ 중복 없음 - 4장 모두 다른 이미지{Colors.END}')
    else:
        print(f'{Colors.YELLOW}⚠️ 로컬 이미지 부족 - 중복 검사 스킵{Colors.END}')

    # STEP 1: URL 접근 검증
    print(f'\n{Colors.YELLOW}[STEP 1] URL 접근 검증{Colors.END}')
    for i, url in enumerate(image_urls):
        resp = requests.head(url, timeout=10)
        status = '✅' if resp.status_code == 200 else '❌'
        print(f'   {status} [{i}] {resp.status_code}')
        if resp.status_code != 200:
            print(f'{Colors.RED}❌ 이미지 접근 실패{Colors.END}')
            return None

    # STEP 2: 이미지 컨테이너 생성
    print(f'\n{Colors.YELLOW}[STEP 2] 이미지 컨테이너 생성{Colors.END}')
    media_ids = []
    for i, url in enumerate(image_urls):
        resp = requests.post(
            f'{BASE_URL}/{THREADS_USER_ID}/threads',
            data={
                'media_type': 'IMAGE',
                'image_url': url,
                'access_token': THREADS_ACCESS_TOKEN
            }
        )
        if resp.status_code != 200:
            print(f'{Colors.RED}❌ 컨테이너 생성 실패: {resp.text}{Colors.END}')
            return None
        media_id = resp.json()['id']
        media_ids.append(media_id)
        print(f'   ✅ [{i}] {media_id}')
        time.sleep(1)

    # STEP 3: 캐러셀 컨테이너 생성
    print(f'\n{Colors.YELLOW}[STEP 3] 캐러셀 컨테이너 생성{Colors.END}')
    resp = requests.post(
        f'{BASE_URL}/{THREADS_USER_ID}/threads',
        data={
            'media_type': 'CAROUSEL',
            'children': ','.join(media_ids),
            'text': caption,
            'access_token': THREADS_ACCESS_TOKEN
        }
    )
    if resp.status_code != 200:
        print(f'{Colors.RED}❌ 캐러셀 생성 실패: {resp.text}{Colors.END}')
        return None
    carousel_id = resp.json()['id']
    print(f'   ✅ {carousel_id}')

    # STEP 4: 게시 발행
    print(f'\n{Colors.YELLOW}[STEP 4] 게시 발행{Colors.END}')
    print('   ⏳ 3초 대기...')
    time.sleep(3)

    resp = requests.post(
        f'{BASE_URL}/{THREADS_USER_ID}/threads_publish',
        data={
            'creation_id': carousel_id,
            'access_token': THREADS_ACCESS_TOKEN
        }
    )
    if resp.status_code != 200:
        print(f'{Colors.RED}❌ 게시 실패: {resp.text}{Colors.END}')
        return None

    result = resp.json()
    post_id = result['id']
    threads_url = f'https://www.threads.net/@sunshinedogfood/post/{post_id}'

    print(f'\n{Colors.GREEN}╔══════════════════════════════════════╗')
    print(f'║         ✅ 게시 완료!                 ║')
    print(f'╚══════════════════════════════════════╝{Colors.END}')
    print(f'Post ID: {post_id}')
    print(f'URL: {threads_url}')

    # Google Sheets 자동 업데이트 (G열)
    try:
        from services.scripts.threads_sheet_updater import update_threads_status
        sheet_result = update_threads_status(
            topic_en=topic,
            post_id=post_id,
            threads_url=threads_url,
            status='posted'
        )
        if sheet_result['success']:
            print(f'{Colors.GREEN}📊 Google Sheets G열 업데이트 완료{Colors.END}')
        else:
            print(f'{Colors.YELLOW}⚠️ 시트 업데이트 실패: {sheet_result["message"]}{Colors.END}')
    except Exception as e:
        print(f'{Colors.YELLOW}⚠️ 시트 업데이트 스킵: {e}{Colors.END}')

    return {
        'post_id': post_id,
        'url': threads_url
    }


if __name__ == '__main__':
    # 테스트
    print('Threads Uploader - 사용법:')
    print('  from services.scripts.threads_uploader import upload_carousel')
    print('  upload_carousel("carrot", Path("contents/4_posted/002_carrot"), caption)')
