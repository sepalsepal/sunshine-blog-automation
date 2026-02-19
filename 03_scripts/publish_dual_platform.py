#!/usr/bin/env python3
"""
Instagram + Threads 통합 게시 스크립트

워크플로우:
1. 이미지 중복 검사
2. 캡션 규칙 검증 (8단계)
3. Cloudinary 업로드
4. Instagram 게시
5. Threads 게시
6. 폴더 이동 (3_approved → 4_posted)
7. Google Sheets 업데이트

사용법:
    python publish_dual_platform.py poached_egg
    python publish_dual_platform.py poached_egg --dry-run
"""

import os
import sys
import json
import shutil
import hashlib
import time
import re
import requests
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')


class Colors:
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    END = '\033[0m'
    BOLD = '\033[1m'


# ============ 검증 함수들 ============

def check_image_duplicates(image_paths: list) -> dict:
    """이미지 중복 검사 (MD5 해시)"""
    print(f"\n{Colors.CYAN}[검증 1] 이미지 중복 검사{Colors.END}")

    hashes = {}
    duplicates = []

    for i, path in enumerate(image_paths):
        if not path.exists():
            print(f"   {Colors.RED}❌ 파일 없음: {path.name}{Colors.END}")
            return {'passed': False, 'error': f'파일 없음: {path.name}'}

        with open(path, 'rb') as f:
            h = hashlib.md5(f.read()).hexdigest()

        if h in hashes:
            duplicates.append((hashes[h], i))
        else:
            hashes[h] = i

    if duplicates:
        print(f"   {Colors.RED}❌ 중복 발견:{Colors.END}")
        for dup in duplicates:
            print(f"      이미지 {dup[0]:02d}와 {dup[1]:02d} 동일")
        return {'passed': False, 'duplicates': duplicates}

    print(f"   {Colors.GREEN}✅ 중복 없음 - 4장 모두 다른 이미지{Colors.END}")
    return {'passed': True}


def validate_caption(caption: str, platform: str = 'instagram') -> dict:
    """캡션 8단계 규칙 검증"""
    print(f"\n{Colors.CYAN}[검증 2] 캡션 규칙 검증 ({platform}){Colors.END}")

    checks = {
        '안전도 이모지': False,
        '주의사항 리스트': False,
        '급여량 정보': False,
        '핵심 메시지': False,
        'CTA': False,
        'AI 고지': False,
        '해시태그': False,
    }

    # 1. 안전도 이모지
    if any(emoji in caption for emoji in ['✅', '⚠️', '❌', '🟢', '🟡', '🔴']):
        checks['안전도 이모지'] = True

    # 2. 주의사항 리스트 (• 3개 이상)
    bullet_count = caption.count('•')
    if bullet_count >= 3:
        checks['주의사항 리스트'] = True

    # 3. 급여량 정보
    if '소형견' in caption and '중형견' in caption and '대형견' in caption:
        checks['급여량 정보'] = True

    # 4. 핵심 메시지
    if '📌' in caption or '"' in caption or '💡' in caption:
        checks['핵심 메시지'] = True

    # 5. CTA
    if any(word in caption for word in ['저장', '공유', '💾']):
        checks['CTA'] = True

    # 6. AI 고지
    if 'AI' in caption and ('생성' in caption or 'generated' in caption.lower()):
        checks['AI 고지'] = True

    # 7. 해시태그 (12개 이상)
    hashtags = re.findall(r'#\w+', caption)
    if len(hashtags) >= 12:
        checks['해시태그'] = True

    passed = sum(checks.values())
    total = len(checks)

    for item, ok in checks.items():
        status = f"{Colors.GREEN}✅{Colors.END}" if ok else f"{Colors.RED}❌{Colors.END}"
        print(f"   {status} {item}")

    print(f"\n   결과: {passed}/{total}")

    return {
        'passed': passed == total,
        'score': f'{passed}/{total}',
        'checks': checks
    }


# ============ 업로드 함수들 ============

def upload_to_cloudinary(image_paths: list, topic: str) -> list:
    """Cloudinary 업로드"""
    print(f"\n{Colors.CYAN}[단계 1] Cloudinary 업로드{Colors.END}")

    import cloudinary
    import cloudinary.uploader

    cloudinary.config(
        cloud_name=os.getenv('CLOUDINARY_CLOUD_NAME'),
        api_key=os.getenv('CLOUDINARY_API_KEY'),
        api_secret=os.getenv('CLOUDINARY_API_SECRET')
    )

    urls = []
    for i, img in enumerate(image_paths):
        print(f"   업로드 중: {img.name}")
        result = cloudinary.uploader.upload(
            str(img),
            folder=f'threads/{topic}',
            public_id=f'{topic}_{i:02d}',
            overwrite=True,
            resource_type='image'
        )
        urls.append(result['secure_url'])
        print(f"   {Colors.GREEN}✅ 완료{Colors.END}")

    return urls


def publish_to_instagram(image_urls: list, caption: str) -> dict:
    """Instagram 캐러셀 게시"""
    print(f"\n{Colors.CYAN}[단계 2] Instagram 게시{Colors.END}")

    ig_user_id = os.getenv('INSTAGRAM_BUSINESS_ACCOUNT_ID')
    ig_token = os.getenv('INSTAGRAM_ACCESS_TOKEN')

    if not ig_user_id or not ig_token:
        print(f"   {Colors.RED}❌ Instagram 토큰 미설정{Colors.END}")
        return {'success': False, 'error': 'Instagram 토큰 미설정'}

    base_url = 'https://graph.facebook.com/v18.0'

    try:
        # 1. 각 이미지 컨테이너 생성
        container_ids = []
        for i, url in enumerate(image_urls):
            resp = requests.post(
                f'{base_url}/{ig_user_id}/media',
                data={
                    'image_url': url,
                    'is_carousel_item': 'true',
                    'access_token': ig_token
                }
            )
            data = resp.json()
            if 'id' not in data:
                return {'success': False, 'error': f'이미지 {i} 컨테이너 실패: {data}'}
            container_ids.append(data['id'])
            print(f"   ✅ 이미지 {i+1}/4 컨테이너 생성")
            time.sleep(1)

        # 2. 캐러셀 컨테이너 생성
        resp = requests.post(
            f'{base_url}/{ig_user_id}/media',
            data={
                'media_type': 'CAROUSEL',
                'children': ','.join(container_ids),
                'caption': caption,
                'access_token': ig_token
            }
        )
        data = resp.json()
        if 'id' not in data:
            return {'success': False, 'error': f'캐러셀 생성 실패: {data}'}
        carousel_id = data['id']
        print(f"   ✅ 캐러셀 컨테이너 생성")

        time.sleep(3)

        # 3. 게시
        resp = requests.post(
            f'{base_url}/{ig_user_id}/media_publish',
            data={
                'creation_id': carousel_id,
                'access_token': ig_token
            }
        )
        data = resp.json()
        if 'id' in data:
            post_id = data['id']
            print(f"   {Colors.GREEN}✅ Instagram 게시 완료!{Colors.END}")
            print(f"   Post ID: {post_id}")
            return {'success': True, 'post_id': post_id}
        else:
            return {'success': False, 'error': f'게시 실패: {data}'}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def publish_to_threads(image_urls: list, caption: str, topic: str) -> dict:
    """Threads 캐러셀 게시"""
    print(f"\n{Colors.CYAN}[단계 3] Threads 게시{Colors.END}")

    threads_user_id = os.getenv('THREADS_USER_ID')
    threads_token = os.getenv('THREADS_ACCESS_TOKEN')

    if not threads_user_id or not threads_token:
        print(f"   {Colors.RED}❌ Threads 토큰 미설정{Colors.END}")
        return {'success': False, 'error': 'Threads 토큰 미설정'}

    base_url = 'https://graph.threads.net/v1.0'

    try:
        # 1. 각 이미지 컨테이너 생성
        media_ids = []
        for i, url in enumerate(image_urls):
            resp = requests.post(
                f'{base_url}/{threads_user_id}/threads',
                data={
                    'media_type': 'IMAGE',
                    'image_url': url,
                    'access_token': threads_token
                }
            )
            data = resp.json()
            if 'id' not in data:
                return {'success': False, 'error': f'이미지 {i} 컨테이너 실패: {data}'}
            media_ids.append(data['id'])
            print(f"   ✅ 이미지 {i+1}/4 컨테이너 생성")
            time.sleep(1)

        # 2. 캐러셀 컨테이너 생성
        resp = requests.post(
            f'{base_url}/{threads_user_id}/threads',
            data={
                'media_type': 'CAROUSEL',
                'children': ','.join(media_ids),
                'text': caption,
                'access_token': threads_token
            }
        )
        data = resp.json()
        if 'id' not in data:
            return {'success': False, 'error': f'캐러셀 생성 실패: {data}'}
        carousel_id = data['id']
        print(f"   ✅ 캐러셀 컨테이너 생성")

        time.sleep(3)

        # 3. 게시
        resp = requests.post(
            f'{base_url}/{threads_user_id}/threads_publish',
            data={
                'creation_id': carousel_id,
                'access_token': threads_token
            }
        )
        data = resp.json()
        if 'id' in data:
            post_id = data['id']
            threads_url = f'https://www.threads.net/@sunshinedogfood/post/{post_id}'
            print(f"   {Colors.GREEN}✅ Threads 게시 완료!{Colors.END}")
            print(f"   Post ID: {post_id}")
            print(f"   URL: {threads_url}")

            # Google Sheets 업데이트
            try:
                from services.scripts.threads_sheet_updater import update_threads_status
                update_threads_status(topic, post_id, threads_url, 'posted')
            except Exception as e:
                print(f"   {Colors.YELLOW}⚠️ 시트 업데이트 실패: {e}{Colors.END}")

            return {'success': True, 'post_id': post_id, 'url': threads_url}
        else:
            return {'success': False, 'error': f'게시 실패: {data}'}

    except Exception as e:
        return {'success': False, 'error': str(e)}


def move_to_posted(source_folder: Path, topic_en: str, topic_kr: str) -> dict:
    """폴더를 4_posted로 이동"""
    print(f"\n{Colors.CYAN}[단계 4] 폴더 이동{Colors.END}")

    posted_dir = PROJECT_ROOT / 'contents' / '4_posted'

    # 다음 번호 찾기
    existing = list(posted_dir.glob('*'))
    max_num = 0
    for folder in existing:
        if folder.is_dir() and folder.name[0].isdigit():
            try:
                num = int(folder.name.split('_')[0])
                max_num = max(max_num, num)
            except:
                pass

    next_num = max_num + 1
    new_folder_name = f"{next_num:03d}_{topic_en}"
    dest_folder = posted_dir / new_folder_name

    try:
        shutil.move(str(source_folder), str(dest_folder))
        print(f"   {Colors.GREEN}✅ 이동 완료{Colors.END}")
        print(f"   {source_folder.name} → {new_folder_name}")
        return {'success': True, 'new_path': str(dest_folder)}
    except Exception as e:
        print(f"   {Colors.RED}❌ 이동 실패: {e}{Colors.END}")
        return {'success': False, 'error': str(e)}


# ============ 메인 함수 ============

def publish_dual_platform(topic_en: str, dry_run: bool = False):
    """Instagram + Threads 동시 게시"""

    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.BOLD}📤 통합 게시: {topic_en}{Colors.END}")
    print(f"{Colors.BOLD}{'='*60}{Colors.END}")

    # 폴더 찾기
    approved_dir = PROJECT_ROOT / 'contents' / '3_approved'
    folder = None
    topic_kr = topic_en

    for f in approved_dir.iterdir():
        if f.is_dir() and topic_en in f.name:
            folder = f
            parts = f.name.split('_')
            if len(parts) >= 3:
                topic_kr = parts[-1]
            break

    if not folder:
        print(f"{Colors.RED}❌ 폴더 없음: {topic_en}{Colors.END}")
        return

    print(f"\n폴더: {folder.name}")
    print(f"주제: {topic_en} ({topic_kr})")

    # 이미지 찾기
    images = []
    for i in range(4):
        for ext in ['.png', '.jpg']:
            img = folder / f'{topic_en}_{i:02d}{ext}'
            if img.exists():
                images.append(img)
                break

    if len(images) < 4:
        print(f"{Colors.RED}❌ 이미지 부족: {len(images)}/4{Colors.END}")
        return

    # 캡션 읽기
    ig_caption_file = folder / 'caption_instagram.txt'
    th_caption_file = folder / 'caption_threads.txt'

    if not ig_caption_file.exists():
        print(f"{Colors.RED}❌ caption_instagram.txt 없음{Colors.END}")
        return

    with open(ig_caption_file) as f:
        ig_caption = f.read().strip()

    th_caption = ig_caption
    if th_caption_file.exists():
        with open(th_caption_file) as f:
            th_caption = f.read().strip()

    # ========== 검증 ==========

    # 1. 이미지 중복 검사
    dup_result = check_image_duplicates(images)
    if not dup_result['passed']:
        print(f"\n{Colors.RED}❌ 이미지 중복 - 게시 중단{Colors.END}")
        return

    # 2. 캡션 검증
    caption_result = validate_caption(ig_caption, 'instagram')
    if not caption_result['passed']:
        print(f"\n{Colors.YELLOW}⚠️ 캡션 검증 미통과 ({caption_result['score']}){Colors.END}")
        if not dry_run:
            response = input("계속 진행할까요? (y/n): ")
            if response.lower() != 'y':
                return

    if dry_run:
        print(f"\n{Colors.YELLOW}[DRY-RUN] 검증 완료 - 실제 게시 안 함{Colors.END}")
        return

    # ========== 업로드 ==========

    # 1. Cloudinary 업로드
    cloudinary_urls = upload_to_cloudinary(images, topic_en)

    # cloudinary_urls.json 저장
    with open(folder / 'cloudinary_urls.json', 'w') as f:
        json.dump({'topic': topic_en, 'urls': cloudinary_urls}, f, indent=2)

    # 2. Instagram 게시
    ig_result = publish_to_instagram(cloudinary_urls, ig_caption)

    if not ig_result['success']:
        print(f"\n{Colors.RED}❌ Instagram 게시 실패 - Threads 스킵{Colors.END}")
        print(f"   오류: {ig_result.get('error')}")
        return

    time.sleep(5)  # API 레이트 제한 방지

    # 3. Threads 게시
    th_result = publish_to_threads(cloudinary_urls, th_caption, topic_en)

    if not th_result['success']:
        print(f"\n{Colors.YELLOW}⚠️ Threads 게시 실패 (Instagram은 성공){Colors.END}")
        print(f"   오류: {th_result.get('error')}")

    # 4. 폴더 이동 (둘 다 성공 시)
    if ig_result['success'] and th_result.get('success'):
        move_result = move_to_posted(folder, topic_en, topic_kr)

    # ========== 결과 ==========

    print(f"\n{Colors.BOLD}{'='*60}{Colors.END}")
    print(f"{Colors.GREEN}✅ 게시 완료!{Colors.END}")
    print(f"{'='*60}")
    print(f"Instagram: {ig_result.get('post_id', 'N/A')}")
    print(f"Threads: {th_result.get('url', 'N/A')}")
    print(f"{'='*60}")

    return {
        'instagram': ig_result,
        'threads': th_result
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='Instagram + Threads 통합 게시')
    parser.add_argument('topic', help='영문 주제명 (예: poached_egg)')
    parser.add_argument('--dry-run', action='store_true', help='검증만 수행')

    args = parser.parse_args()

    publish_dual_platform(args.topic, args.dry_run)
