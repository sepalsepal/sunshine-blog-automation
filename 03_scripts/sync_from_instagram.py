#!/usr/bin/env python3
"""
Instagram 기준 단방향 동기화
SSOT: Instagram > Local > Sheet
목표: 3중 일치 (IG = 로컬 = 시트 = 41)
"""
import os
import sys
import json
import re
import shutil
from pathlib import Path
from datetime import datetime

sys.path.insert(0, '/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine')

from dotenv import load_dotenv
load_dotenv(Path('/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/.env'))

import gspread
from google.oauth2.service_account import Credentials

# 경로
PROJECT_ROOT = Path('/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine')
CONTENTS_DIR = PROJECT_ROOT / 'contents'
INSTAGRAM_DATA = PROJECT_ROOT / 'config/data/instagram_posts.json'

MAX_LOOP = 5


def load_instagram_posts():
    """Instagram 게시물 데이터 로드"""
    with open(INSTAGRAM_DATA, 'r', encoding='utf-8') as f:
        data = json.load(f)
    return data['posts']


def extract_food_id_from_folder(folder_name):
    """폴더명에서 food_id 추출"""
    # 번호 제거: 032_boiled_egg_삶은달걀 -> boiled_egg_삶은달걀
    name = re.sub(r'^\d+_', '', folder_name)
    parts = name.split('_')

    # 영문만 추출
    eng_parts = [p.lower() for p in parts if re.match(r'^[a-zA-Z]+$', p)]

    if not eng_parts:
        return folder_name.lower()

    food_id = '_'.join(eng_parts)

    # 중복 패턴 처리: apple_apple -> apple
    if '_' in food_id:
        split = food_id.split('_')
        if len(split) == 2 and split[0] == split[1]:
            food_id = split[0]

    return food_id


def scan_local_posted():
    """로컬 posted 폴더 스캔"""
    posted_dir = CONTENTS_DIR / '4_posted'
    folders = {}

    if not posted_dir.exists():
        return folders

    for month_dir in posted_dir.iterdir():
        if month_dir.is_dir() and re.match(r'^\d{4}-\d{2}$', month_dir.name):
            for folder in month_dir.iterdir():
                if folder.is_dir() and not folder.name.startswith('.'):
                    food_id = extract_food_id_from_folder(folder.name)
                    folders[food_id] = folder

    return folders


def scan_all_folders():
    """모든 폴더 스캔 (posted 제외)"""
    folders = {}

    for status_dir in ['1_cover_only', '2_body_ready', '3_approved']:
        status_path = CONTENTS_DIR / status_dir
        if status_path.exists():
            for folder in status_path.iterdir():
                if folder.is_dir() and not folder.name.startswith('.'):
                    if '_미지정' in folder.name or folder.name.startswith('cover_'):
                        continue
                    food_id = extract_food_id_from_folder(folder.name)
                    folders[food_id] = folder

    return folders


def sync_local_folders(ig_posts):
    """Instagram 기준으로 로컬 폴더 동기화"""
    fixes = 0

    # Instagram food_id 목록
    ig_food_ids = {p['food_id'] for p in ig_posts}

    # 현재 로컬 posted 폴더
    local_posted = scan_local_posted()
    local_posted_ids = set(local_posted.keys())

    # 다른 폴더들
    other_folders = scan_all_folders()

    # 1. Instagram에 있는데 로컬 posted에 없는 것 → 찾아서 이동
    missing_in_local = ig_food_ids - local_posted_ids
    for food_id in missing_in_local:
        if food_id in other_folders:
            src = other_folders[food_id]

            # posted_id 찾기
            post = next((p for p in ig_posts if p['food_id'] == food_id), None)
            if post:
                posted_at = post.get('posted_at', '')[:7] or '2026-02'  # YYYY-MM
                dest_dir = CONTENTS_DIR / '4_posted' / posted_at
                dest_dir.mkdir(parents=True, exist_ok=True)

                # 새 폴더명 (posted_id 또는 기존 이름)
                new_name = src.name  # 기존 이름 유지
                dest = dest_dir / new_name

                if not dest.exists():
                    shutil.move(str(src), str(dest))
                    print(f"  [이동] {src.name} → 4_posted/{posted_at}/")

                    # metadata 업데이트
                    update_metadata(dest, 'posted', post)
                    fixes += 1

    # 2. 로컬 posted에 있는데 Instagram에 없는 것 → cover_only로 이동
    extra_in_local = local_posted_ids - ig_food_ids
    for food_id in extra_in_local:
        src = local_posted[food_id]
        dest = CONTENTS_DIR / '1_cover_only' / src.name

        if not dest.exists():
            shutil.move(str(src), str(dest))
            print(f"  [복구] {src.name} → 1_cover_only/")

            # metadata 업데이트
            update_metadata(dest, 'cover_only')
            fixes += 1

    return fixes


def update_metadata(folder_path, status, post=None):
    """metadata.json 업데이트"""
    meta_path = folder_path / 'metadata.json'

    if meta_path.exists():
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    else:
        meta = {}

    meta['status'] = status
    meta['synced_at'] = datetime.now().isoformat()

    if post and status == 'posted':
        meta['posted_id'] = post.get('posted_id', '')
        meta['instagram_url'] = post.get('permalink', '')
        meta['posted_at'] = post.get('posted_at', '')
        meta['media_id'] = post.get('media_id', '')
    elif status != 'posted':
        # posted가 아닌 경우 관련 필드 제거
        for key in ['posted_id', 'instagram_url', 'posted_at', 'media_id']:
            meta.pop(key, None)

    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def sync_sheet(ig_posts):
    """Instagram 기준으로 시트 동기화"""
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    sheet_id = os.environ.get('GOOGLE_SHEET_ID')
    creds_path = os.environ.get('GOOGLE_CREDENTIALS_PATH')

    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    worksheet = client.open_by_key(sheet_id).worksheet('게시콘텐츠')

    all_data = worksheet.get_all_values()
    b_idx = 1  # B열: food_id
    f_idx = 5  # F열: status
    g_idx = 6  # G열: posted_at
    h_idx = 7  # H열: instagram_url

    # Instagram food_id → post 매핑
    ig_map = {p['food_id']: p for p in ig_posts}
    ig_food_ids = set(ig_map.keys())

    batch_updates = []
    fixes = 0

    for idx, row in enumerate(all_data[1:], start=2):
        if len(row) <= b_idx:
            continue

        food_id = row[b_idx].strip().lower()
        if not food_id or food_id.endswith('_dup'):
            continue

        current_status = row[f_idx].strip() if len(row) > f_idx else ''

        if food_id in ig_food_ids:
            # Instagram에 있음 → posted
            if current_status != 'posted':
                batch_updates.append({'range': f'F{idx}', 'values': [['posted']]})
                fixes += 1

            # posted_at, instagram_url 업데이트
            post = ig_map[food_id]
            if post.get('posted_at'):
                batch_updates.append({'range': f'G{idx}', 'values': [[post['posted_at']]]})
            if post.get('permalink'):
                batch_updates.append({'range': f'H{idx}', 'values': [[post['permalink']]]})
        else:
            # Instagram에 없음 → posted가 아니어야 함
            if current_status == 'posted':
                batch_updates.append({'range': f'F{idx}', 'values': [['cover_only']]})
                fixes += 1

    if batch_updates:
        worksheet.batch_update(batch_updates)

    return fixes


def count_local_posted():
    """로컬 posted 폴더 수"""
    return len(scan_local_posted())


def count_sheet_posted():
    """시트 posted 수"""
    SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
    sheet_id = os.environ.get('GOOGLE_SHEET_ID')
    creds_path = os.environ.get('GOOGLE_CREDENTIALS_PATH')

    creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
    client = gspread.authorize(creds)
    worksheet = client.open_by_key(sheet_id).worksheet('게시콘텐츠')

    all_data = worksheet.get_all_values()
    f_idx = 5

    count = 0
    for row in all_data[1:]:
        if len(row) > f_idx and row[f_idx].strip() == 'posted':
            count += 1

    return count


def main():
    print("=" * 50)
    print("Instagram 기준 단방향 동기화")
    print("목표: IG = 로컬 = 시트 = 41")
    print("=" * 50)

    # Instagram 데이터 로드
    ig_posts = load_instagram_posts()
    ig_count = len(ig_posts)
    print(f"\n[Instagram] {ig_count}개")

    loop_count = 0

    while loop_count < MAX_LOOP:
        print(f"\n{'='*20} 루프 {loop_count + 1}/{MAX_LOOP} {'='*20}")

        # 1. 로컬 동기화
        print("\n[1] 로컬 폴더 동기화...")
        local_fixes = sync_local_folders(ig_posts)
        local_count = count_local_posted()
        print(f"    수정: {local_fixes}건, 현재: {local_count}개")

        # 2. 시트 동기화
        print("\n[2] 시트 동기화...")
        sheet_fixes = sync_sheet(ig_posts)
        sheet_count = count_sheet_posted()
        print(f"    수정: {sheet_fixes}건, 현재: {sheet_count}개")

        # 3. 검증
        print(f"\n[검증]")
        print(f"  Instagram: {ig_count}개")
        print(f"  로컬:      {local_count}개")
        print(f"  시트:      {sheet_count}개")

        if ig_count == local_count == sheet_count:
            print(f"\n{'='*50}")
            print(f"✅ 3중 일치 달성! ({ig_count}개)")
            print(f"{'='*50}")
            return True

        if local_fixes == 0 and sheet_fixes == 0:
            print("\n⚠️ 더 이상 수정할 항목 없음, 불일치 상태 유지")
            break

        loop_count += 1

    print(f"\n{'='*50}")
    print(f"❌ {MAX_LOOP}회 루프 후에도 불일치")
    print(f"  Instagram: {ig_count}개")
    print(f"  로컬:      {count_local_posted()}개")
    print(f"  시트:      {count_sheet_posted()}개")
    print(f"{'='*50}")
    return False


if __name__ == '__main__':
    success = main()
    sys.exit(0 if success else 1)
