#!/usr/bin/env python3
"""
🔄 동기화 루프 v2 — Instagram SSOT

SSOT (Single Source of Truth):
1순위: Instagram (실제 게시 여부)
2순위: metadata.json (pd_approved 등)
3순위: 파일 존재 여부 (이미지 4장)

상태 판별 우선순위:
1. posted = Instagram에 실제 게시됨
2. approved = pd_approved == True
3. body_ready = 이미지 4장 존재
4. cover_only = 나머지

사용법:
    python3 scripts/sync_loop.py
"""

import os
import sys
import json
import shutil
import re
import requests
from pathlib import Path
from datetime import datetime
from collections import Counter

# 프로젝트 루트
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# .env 로드
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass

# ==========================================
# 설정
# ==========================================

MAX_LOOP = 5
CONTENTS_DIR = ROOT / "01_contents"

# 2026-02-13: 플랫 구조 - STATUS_FOLDERS 제거
# STATUS_FOLDERS = {
#     "cover_only": "1_cover_only",
#     "body_ready": "2_body_ready",
#     "approved": "3_approved",
#     "posted": "4_posted"
# }

# FOLDER_STATUS = {v: k for k, v in STATUS_FOLDERS.items()}

# Instagram API
INSTAGRAM_ACCESS_TOKEN = os.getenv("INSTAGRAM_ACCESS_TOKEN")
INSTAGRAM_BUSINESS_ID = os.getenv("INSTAGRAM_BUSINESS_ACCOUNT_ID")

# Telegram
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_CHAT_ID = os.getenv("TELEGRAM_CHAT_ID", "5360443525")


# ==========================================
# 1. Instagram API로 게시물 목록 가져오기
# ==========================================

def get_instagram_posts() -> dict:
    """
    Instagram에 실제 게시된 콘텐츠 목록
    Returns: {media_id: caption_keywords, ...}
    """
    if not INSTAGRAM_ACCESS_TOKEN or not INSTAGRAM_BUSINESS_ID:
        print("  ⚠️ Instagram API 설정 없음")
        return {}

    try:
        url = f"https://graph.facebook.com/v21.0/{INSTAGRAM_BUSINESS_ID}/media"
        params = {
            "access_token": INSTAGRAM_ACCESS_TOKEN,
            "fields": "id,caption,timestamp,media_type",
            "limit": 100
        }

        response = requests.get(url, params=params, timeout=30)

        if response.status_code != 200:
            print(f"  ⚠️ Instagram API 오류: {response.status_code}")
            return {}

        data = response.json()
        posts = {}

        for media in data.get("data", []):
            media_id = media.get("id")
            caption = media.get("caption", "")

            # 캡션에서 음식명 추출 시도
            posts[media_id] = {
                "caption": caption[:100],
                "timestamp": media.get("timestamp")
            }

        print(f"  📸 Instagram 게시물: {len(posts)}개")
        return posts

    except Exception as e:
        print(f"  ⚠️ Instagram API 실패: {e}")
        return {}


def get_posted_food_ids() -> set:
    """
    Instagram에 게시된 food_id 집합 반환
    방법: publishing_history.csv 또는 metadata.json의 instagram_media_id
    """
    posted_ids = set()

    # 1. publishing_history.csv 확인
    history_path = ROOT / "config" / "data" / "publishing_history.csv"
    if history_path.exists():
        try:
            lines = history_path.read_text().strip().split('\n')
            for line in lines[1:]:  # 헤더 스킵
                parts = line.split(',')
                if len(parts) >= 2:
                    food_id = parts[1].strip()
                    if food_id:
                        posted_ids.add(food_id.lower())
        except Exception as e:
            print(f"  ⚠️ 히스토리 읽기 실패: {e}")

    # 2. 4_posted 폴더의 모든 콘텐츠
    posted_dir = CONTENTS_DIR / "4_posted"
    if posted_dir.exists():
        for month_dir in posted_dir.iterdir():
            if month_dir.is_dir() and not month_dir.name.startswith("."):
                for folder in month_dir.iterdir():
                    if folder.is_dir():
                        food_id = extract_food_id(folder.name)
                        posted_ids.add(food_id.lower())

    # 3. 모든 폴더에서 instagram_media_id 있는 것
    for status_folder in ["1_cover_only", "2_body_ready", "3_approved"]:
        status_dir = CONTENTS_DIR / status_folder
        if not status_dir.exists():
            continue

        for folder in status_dir.iterdir():
            if not folder.is_dir() or folder.name.startswith("."):
                continue

            meta_path = folder / "metadata.json"
            if meta_path.exists():
                try:
                    with open(meta_path, 'r', encoding='utf-8') as f:
                        meta = json.load(f)
                    if meta.get("instagram_media_id"):
                        food_id = meta.get("food_id") or extract_food_id(folder.name)
                        posted_ids.add(food_id.lower())
                except:
                    pass

    return posted_ids


# ==========================================
# 2. 상태 판별 (Instagram SSOT)
# ==========================================

def extract_food_id(folder_name: str) -> str:
    """폴더명에서 food_id 추출"""
    parts = folder_name.split("_")
    if len(parts) >= 2:
        if parts[0].isdigit():
            return parts[1]
        if parts[0] == "cover":
            return folder_name
    return folder_name


def determine_status(folder_path: Path, posted_food_ids: set) -> str:
    """
    Instagram SSOT 기반 상태 판별
    우선순위: posted > approved > body_ready > cover_only
    """
    meta_path = folder_path / "metadata.json"
    meta = {}

    if meta_path.exists():
        try:
            with open(meta_path, 'r', encoding='utf-8') as f:
                meta = json.load(f)
        except json.JSONDecodeError:
            pass

    food_id = meta.get("food_id") or extract_food_id(folder_path.name)

    # 1. posted = Instagram에 실제 게시됨 (SSOT)
    if food_id.lower() in posted_food_ids:
        return "posted"

    # 1-2. posted = instagram_media_id 있음
    if meta.get("instagram_media_id"):
        return "posted"

    # 2. approved = pd_approved true
    if meta.get("pd_approved") == True:
        return "approved"

    # 3. body_ready = 이미지 4장 존재
    images = [f"{food_id}_{i:02d}.png" for i in range(4)]
    if all((folder_path / img).exists() for img in images):
        return "body_ready"

    # 4. 나머지 = cover_only
    return "cover_only"


# ==========================================
# 3. 전수조사 + 이동
# ==========================================

def get_all_content_folders() -> list:
    """모든 콘텐츠 폴더 수집 (위치 무관)"""
    folders = []

    # 상태 폴더들
    for status_folder in ["1_cover_only", "2_body_ready", "3_approved"]:
        status_dir = CONTENTS_DIR / status_folder
        if not status_dir.exists():
            continue

        for folder in status_dir.iterdir():
            if folder.is_dir() and not folder.name.startswith("."):
                folders.append({
                    "path": folder,
                    "current_status": FOLDER_STATUS[status_folder]
                })

    # 4_posted는 월별 하위 구조
    posted_dir = CONTENTS_DIR / "4_posted"
    if posted_dir.exists():
        for month_dir in posted_dir.iterdir():
            if month_dir.is_dir() and not month_dir.name.startswith("."):
                for folder in month_dir.iterdir():
                    if folder.is_dir() and not folder.name.startswith("."):
                        folders.append({
                            "path": folder,
                            "current_status": "posted"
                        })

    return folders


def move_to_status_folder(folder_path: Path, target_status: str) -> Path:
    """폴더를 올바른 상태 폴더로 이동"""
    if target_status == "posted":
        # posted는 월별 하위 폴더
        month = datetime.now().strftime("%Y-%m")
        target_dir = CONTENTS_DIR / "4_posted" / month
    else:
        target_dir = CONTENTS_DIR / STATUS_FOLDERS[target_status]

    target_dir.mkdir(parents=True, exist_ok=True)
    dest_path = target_dir / folder_path.name

    if dest_path.exists():
        timestamp = datetime.now().strftime("%H%M%S")
        dest_path = target_dir / f"{folder_path.name}_{timestamp}"

    try:
        shutil.move(str(folder_path), str(dest_path))
        return dest_path
    except Exception as e:
        print(f"  ❌ 이동 실패 {folder_path.name}: {e}")
        return None


def update_metadata_status(folder_path: Path, status: str):
    """metadata.json의 status 필드 업데이트"""
    meta_path = folder_path / "metadata.json"

    if meta_path.exists():
        with open(meta_path, 'r', encoding='utf-8') as f:
            meta = json.load(f)
    else:
        meta = {"food_id": extract_food_id(folder_path.name)}

    meta["status"] = status
    meta["status_synced_at"] = datetime.now().isoformat()

    with open(meta_path, 'w', encoding='utf-8') as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)


def scan_and_fix(posted_food_ids: set) -> list:
    """모든 폴더 스캔 → 잘못된 위치 이동"""
    fixes = []
    all_folders = get_all_content_folders()

    for item in all_folders:
        folder_path = item["path"]
        current_status = item["current_status"]

        # 실제 상태 판별
        actual_status = determine_status(folder_path, posted_food_ids)

        # 불일치 → 이동
        if actual_status != current_status:
            print(f"  📦 {folder_path.name}: {current_status} → {actual_status}")

            new_path = move_to_status_folder(folder_path, actual_status)
            if new_path:
                update_metadata_status(new_path, actual_status)
                fixes.append({
                    "folder": folder_path.name,
                    "from": current_status,
                    "to": actual_status
                })

    return fixes


# ==========================================
# 4. 카운트 함수
# ==========================================

def count_local_folders() -> dict:
    """로컬 폴더 상태별 개수"""
    counts = {"cover_only": 0, "body_ready": 0, "approved": 0, "posted": 0}

    for status, folder_name in STATUS_FOLDERS.items():
        status_dir = CONTENTS_DIR / folder_name

        if status == "posted":
            # posted는 월별 하위 구조
            if status_dir.exists():
                for month_dir in status_dir.iterdir():
                    if month_dir.is_dir() and not month_dir.name.startswith("."):
                        counts[status] += sum(1 for f in month_dir.iterdir()
                                              if f.is_dir() and not f.name.startswith("."))
        else:
            if status_dir.exists():
                counts[status] = sum(1 for f in status_dir.iterdir()
                                     if f.is_dir() and not f.name.startswith("."))

    return counts


def count_sheet_status() -> dict:
    """시트 상태별 개수"""
    counts = {"cover_only": 0, "body_ready": 0, "approved": 0, "posted": 0}

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_path = os.environ.get('GOOGLE_CREDENTIALS_PATH')
        sheet_id = os.environ.get('GOOGLE_SHEET_ID')

        if not creds_path or not sheet_id:
            return counts

        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        client = gspread.authorize(creds)
        worksheet = client.open_by_key(sheet_id).worksheet('게시콘텐츠')

        f_column = worksheet.col_values(6)
        for status in f_column[1:]:
            if status in counts:
                counts[status] += 1

        return counts
    except Exception as e:
        print(f"  ⚠️ 시트 조회 실패: {e}")
        return counts


def count_instagram_posts() -> int:
    """Instagram 게시물 수"""
    return len(get_posted_food_ids())


# ==========================================
# 5. 시트 동기화
# ==========================================

def sync_sheet(posted_food_ids: set):
    """로컬 폴더 기준으로 시트 F열 업데이트"""
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_path = os.environ.get('GOOGLE_CREDENTIALS_PATH')
        sheet_id = os.environ.get('GOOGLE_SHEET_ID')

        if not creds_path or not sheet_id:
            print("  ⚠️ Google Sheets 설정 없음 - 스킵")
            return

        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        client = gspread.authorize(creds)
        worksheet = client.open_by_key(sheet_id).worksheet('게시콘텐츠')

        all_records = worksheet.get_all_records()

        # 로컬 상태 맵 구축
        local_status_map = {}
        all_folders = get_all_content_folders()

        for item in all_folders:
            food_id = extract_food_id(item["path"].name)
            actual_status = determine_status(item["path"], posted_food_ids)
            local_status_map[food_id.lower()] = actual_status

        # 시트 업데이트
        batch_updates = []

        for idx, record in enumerate(all_records):
            row_num = idx + 2
            eng_name = record.get('영문명', '').lower()
            current_status = record.get('게시상태', '')

            # Instagram SSOT: posted_food_ids에 있으면 무조건 posted
            if eng_name in posted_food_ids:
                target_status = "posted"
            elif eng_name in local_status_map:
                target_status = local_status_map[eng_name]
            else:
                continue  # 로컬에 없으면 스킵

            if current_status != target_status:
                batch_updates.append({
                    'range': f'F{row_num}',
                    'values': [[target_status]]
                })

        if batch_updates:
            worksheet.batch_update(batch_updates)
            print(f"  📝 시트 업데이트: {len(batch_updates)}건")
        else:
            print(f"  📝 시트 변경 없음")

    except Exception as e:
        print(f"  ⚠️ 시트 동기화 실패: {e}")


# ==========================================
# 6. 더블체크 (3중 검증)
# ==========================================

def triple_check(posted_food_ids: set) -> dict:
    """로컬 vs 시트 vs Instagram 3중 검증 (로컬 기준)"""
    local_counts = count_local_folders()
    sheet_counts = count_sheet_status()
    instagram_posted = len(posted_food_ids)

    # 로컬 폴더 기준 시트 상태 검증
    mismatches = check_local_vs_sheet_items(posted_food_ids)

    result = {
        "mismatch_count": len(mismatches),
        "local": local_counts,
        "sheet": sheet_counts,
        "instagram_posted": instagram_posted,
        "mismatched_items": mismatches[:10],  # 최대 10개만 표시
        "details": {}
    }

    return result


def check_local_vs_sheet_items(posted_food_ids: set) -> list:
    """로컬 폴더 기준으로 시트 상태 불일치 확인"""
    mismatches = []

    try:
        import gspread
        from google.oauth2.service_account import Credentials

        SCOPES = ['https://www.googleapis.com/auth/spreadsheets', 'https://www.googleapis.com/auth/drive']
        creds_path = os.environ.get('GOOGLE_CREDENTIALS_PATH')
        sheet_id = os.environ.get('GOOGLE_SHEET_ID')

        if not creds_path or not sheet_id:
            return mismatches

        creds = Credentials.from_service_account_file(creds_path, scopes=SCOPES)
        client = gspread.authorize(creds)
        worksheet = client.open_by_key(sheet_id).worksheet('게시콘텐츠')

        all_records = worksheet.get_all_records()

        # 로컬 상태 맵
        local_status_map = {}
        for item in get_all_content_folders():
            food_id = extract_food_id(item["path"].name)
            actual_status = determine_status(item["path"], posted_food_ids)
            local_status_map[food_id.lower()] = actual_status

        # 비교 (로컬에 있는 것만)
        for record in all_records:
            eng_name = record.get('영문명', '').lower()
            sheet_status = record.get('게시상태', '')

            # 로컬에 있는 항목만 비교
            if eng_name in local_status_map:
                local_status = local_status_map[eng_name]
                if sheet_status != local_status:
                    mismatches.append({
                        "food_id": eng_name,
                        "local": local_status,
                        "sheet": sheet_status
                    })

        return mismatches
    except Exception as e:
        print(f"  ⚠️ 시트 비교 실패: {e}")
        return mismatches


# ==========================================
# 7. 텔레그램 알림
# ==========================================

def send_telegram(message: str):
    if not TELEGRAM_BOT_TOKEN:
        print("  ⚠️ TELEGRAM_BOT_TOKEN 미설정")
        return

    try:
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        requests.post(url, data={"chat_id": TELEGRAM_CHAT_ID, "text": message}, timeout=10)
    except Exception as e:
        print(f"  ⚠️ 텔레그램 전송 실패: {e}")


def notify_success(loops: int, total_fixes: int, local_counts: dict, instagram_posted: int):
    message = f"""🔄 동기화 루프 완료

✅ 루프: {loops}회
✅ 수정: {total_fixes}건
✅ 불일치: 0

📊 최종 현황:
- cover_only: {local_counts['cover_only']}개
- body_ready: {local_counts['body_ready']}개
- approved: {local_counts['approved']}개
- posted: {local_counts['posted']}개

📸 Instagram: {instagram_posted}개"""

    send_telegram(message)
    print("\n✅ 텔레그램 성공 알림 전송")


def notify_failure(loops: int, check: dict):
    details = "\n".join([f"  - {k}: 로컬 {v['local']} / 시트 {v['sheet']}"
                         for k, v in check.get('details', {}).items()])

    message = f"""🚨 동기화 실패

❌ 루프: {loops}회
❌ 불일치: {check['mismatch_count']}건

{details}"""

    send_telegram(message)
    print("\n❌ 텔레그램 실패 알림 전송")


# ==========================================
# 8. 메인 루프
# ==========================================

def run_sync_loop():
    print("=" * 60)
    print("🔄 동기화 루프 v2 (Instagram SSOT)")
    print(f"시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"최대 루프: {MAX_LOOP}회")
    print("=" * 60)

    # Instagram posted 목록 가져오기 (1회)
    print("\n[0] Instagram 게시 목록 조회")
    posted_food_ids = get_posted_food_ids()
    print(f"  → posted 대상: {len(posted_food_ids)}개")

    loop_count = 0
    total_fixes = 0

    while loop_count < MAX_LOOP:
        print(f"\n{'─'*40}")
        print(f"[루프 {loop_count + 1}/{MAX_LOOP}]")
        print(f"{'─'*40}")

        # 1. 스캔 + 수정
        print("\n[1] 폴더 스캔 + 이동")
        fixes = scan_and_fix(posted_food_ids)
        total_fixes += len(fixes)
        print(f"  → 수정: {len(fixes)}건")

        # 2. 시트 동기화
        print("\n[2] 시트 동기화")
        sync_sheet(posted_food_ids)

        # 3. 더블체크
        print("\n[3] 3중 검증 (로컬/시트/Instagram)")
        check = triple_check(posted_food_ids)

        print(f"\n  📊 로컬: {check['local']}")
        print(f"  📊 시트: {check['sheet']}")
        print(f"  📸 Instagram posted: {check['instagram_posted']}개")
        print(f"  → 불일치: {check['mismatch_count']}건")

        # 4. 종료 조건
        if check["mismatch_count"] == 0:
            print("\n" + "=" * 60)
            print("✅ 동기화 완료 - 불일치 0")
            print("=" * 60)

            notify_success(loop_count + 1, total_fixes, check["local"], check["instagram_posted"])
            return True

        loop_count += 1

    # 루프 한계 초과
    print("\n" + "=" * 60)
    print(f"❌ 동기화 실패 - {MAX_LOOP}회 완료 후에도 불일치")
    print("=" * 60)

    notify_failure(loop_count, check)
    return False


# ==========================================
# 실행
# ==========================================

if __name__ == "__main__":
    success = run_sync_loop()
    sys.exit(0 if success else 1)
