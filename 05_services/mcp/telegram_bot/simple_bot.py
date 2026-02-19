#!/usr/bin/env python3
"""
Project Sunshine 텔레그램 봇 (Simple Version)
직접 API 호출 방식 - 라이브러리 의존성 없음

기능:
- /create → 버튼 메뉴로 음식 선택
- /status → 상태 확인
- /list → 목록
- /help → 도움말
- /approve → PD 승인
- /reject → PD 반려

🔐 PD 봉인 운영 원칙 (2026-02-03 확정)

1. 로컬 폴더 = 상태의 결과
   - 상태의 "원인"은 metadata / Sheets / API
   - 폴더는 결과물일 뿐 판단 근거 아님

2. posted 이동은 단방향
   - posted → contents 되돌림 ❌
   - 재작업 시 새 food_id 생성

3. 동기화 우선순위
   Instagram API > Sheets > Local metadata > Folder

4. 미리보기 자동화
   - 미리보기 버튼 삭제
   - verified/approved 선택 시 이미지 4장 자동 전송
"""

import os
import sys
import json
import ssl
import re
import time
import urllib.request
import urllib.parse
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# .env 로드
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ALLOWED_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '5360443525')

# SSL 컨텍스트
SSL_CTX = ssl.create_default_context()
SSL_CTX.check_hostname = False
SSL_CTX.verify_mode = ssl.CERT_NONE

# 스레드 풀
executor = ThreadPoolExecutor(max_workers=2)

# 이모지 매핑
EMOJI_MAP = {
    # 과일
    "apple": "🍎", "banana": "🍌", "blueberry": "🫐", "cherry": "🍒",
    "grape": "🍇", "mango": "🥭", "orange": "🍊", "peach": "🍑",
    "pear": "🍐", "strawberry": "🍓", "watermelon": "🍉", "kiwi": "🥝",
    # 채소
    "broccoli": "🥦", "carrot": "🥕", "spinach": "🥬", "pumpkin": "🎃",
    "sweet_potato": "🍠", "potato": "🥔", "cucumber": "🥒", "cabbage": "🥬",
    # 단백질
    "chicken": "🍗", "beef": "🥩", "pork": "🥓", "duck": "🦆",
    "salmon": "🐟", "tuna": "🐟", "shrimp": "🦐", "egg": "🥚",
    "boiled_egg": "🥚", "cheese": "🧀", "tofu": "🧈",
    # 위험
    "chocolate": "🍫", "grape": "🍇", "budweiser": "🍺", "coca_cola": "🥤",
}

# 한글 → 영문 음식 매핑
FOOD_MAPPING = {
    "오리고기": "duck", "삶은달걀": "boiled_egg", "시금치": "spinach",
    "새우": "shrimp", "사과": "apple", "바나나": "banana",
    "당근": "carrot", "닭고기": "chicken", "소고기": "beef",
    "연어": "salmon", "브로콜리": "broccoli", "고구마": "sweet_potato",
    "포도": "grape", "초콜릿": "chocolate", "망고": "mango",
}

# 영문 → 한글 역매핑
FOOD_NAME_KR = {v: k for k, v in FOOD_MAPPING.items()}

# 상태 폴더 목록
STATUS_FOLDERS = ["1_cover_only", "2_body_ready", "3_approved"]


def find_folder_by_food_id(food_id: str) -> Path | None:
    """
    food_id로 실제 폴더 경로 찾기

    폴더명 패턴:
    - {번호}_{food_id}_{한글명}
    - {food_id}_{한글명}

    검색 순서: 2_body_ready → 3_approved → 1_cover_only
    """
    contents_dir = PROJECT_ROOT / "contents"
    food_id_lower = food_id.lower()

    # 검색 순서 (body_ready 우선)
    search_dirs = [
        contents_dir / "2_body_ready",
        contents_dir / "3_approved",
        contents_dir / "1_cover_only",
    ]

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue

        for folder in search_dir.iterdir():
            if not folder.is_dir():
                continue

            folder_name = folder.name.lower()
            parts = folder_name.split("_")

            # 패턴 매칭
            for i, part in enumerate(parts):
                # 정확히 일치
                if part == food_id_lower:
                    print(f"[DEBUG] find_folder_by_food_id: {food_id} → {folder}")
                    return folder
                # 숫자 접미사 제거 후 매칭 (blackberry2 → blackberry)
                if part.rstrip("0123456789") == food_id_lower:
                    print(f"[DEBUG] find_folder_by_food_id: {food_id} → {folder} (숫자 제거)")
                    return folder

    print(f"[DEBUG] find_folder_by_food_id: {food_id} → None (폴더 없음)")
    return None


def get_folder_status(folder_path: Path) -> str:
    """폴더 위치로 상태 반환"""
    if not folder_path:
        return "unknown"

    parent = folder_path.parent.name

    status_map = {
        "1_cover_only": "cover_only",
        "2_body_ready": "body_ready",
        "3_approved": "approved",
    }

    # 4_posted의 경우 YYYY-MM 하위 폴더
    if "4_posted" in str(folder_path):
        return "posted"

    return status_map.get(parent, "unknown")


def create_default_metadata(food_id: str, folder_path: Path) -> dict:
    """
    기본 metadata.json 생성

    승인 시 metadata가 없으면 자동 생성
    """
    metadata = {
        "food_id": food_id,
        "status": "generated",
        "created_at": datetime.now().isoformat(),
        "folder_name": folder_path.name if folder_path else "unknown",
    }

    if folder_path and folder_path.exists():
        metadata_file = folder_path / "metadata.json"
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        print(f"[DEBUG] created metadata: {metadata_file}")

    return metadata


def update_metadata_status(food_id: str, status: str, **kwargs) -> bool:
    """
    metadata.json 상태 업데이트

    Args:
        food_id: 콘텐츠 ID
        status: 새 상태 (approved, rejected, etc.)
        **kwargs: 추가 필드 (approved_by, approved_at 등)

    Returns:
        성공 여부
    """
    folder = find_folder_by_food_id(food_id)
    if not folder:
        return False

    metadata_file = folder / "metadata.json"

    # 기존 메타데이터 로드 또는 생성
    if metadata_file.exists():
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    else:
        metadata = create_default_metadata(food_id, folder)

    # 상태 업데이트
    metadata["status"] = status
    metadata.update(kwargs)

    # 저장
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    print(f"[DEBUG] updated metadata status: {food_id} → {status}")
    return True


def move_to_approved(food_id: str) -> tuple[bool, str]:
    """
    폴더를 3_approved로 이동

    Args:
        food_id: 콘텐츠 ID

    Returns:
        (성공 여부, 메시지)
    """
    import shutil

    folder = find_folder_by_food_id(food_id)
    if not folder:
        return False, "폴더를 찾을 수 없음"

    current_status = get_folder_status(folder)

    # 이미 approved면 이동 불필요
    if current_status == "approved":
        return True, "이미 approved 폴더에 있음"

    # 이미 posted면 이동 금지
    if current_status == "posted":
        return False, "이미 게시된 콘텐츠는 이동 불가"

    # 이동 대상 경로
    approved_dir = PROJECT_ROOT / "contents" / "3_approved"
    approved_dir.mkdir(parents=True, exist_ok=True)

    dest = approved_dir / folder.name

    if dest.exists():
        return False, f"이동 대상 폴더가 이미 존재: {dest.name}"

    try:
        shutil.move(str(folder), str(dest))
        print(f"[DEBUG] moved to approved: {folder.name}")
        return True, f"3_approved로 이동 완료"
    except Exception as e:
        return False, f"이동 실패: {str(e)}"


def load_caption(food_id: str) -> str | None:
    """
    캡션 파일 로드

    🔐 UX 매핑 v1.0:
    - 승인 후 이미지 대신 캡션 표시
    - 이미 본 것 → 다시 안 보여줌

    Args:
        food_id: 콘텐츠 ID

    Returns:
        캡션 텍스트 또는 None
    """
    folder = find_folder_by_food_id(food_id)
    if not folder:
        return None

    # 캡션 파일 우선순위
    caption_files = [
        folder / "caption_instagram.txt",
        folder / "caption.txt",
    ]

    for caption_file in caption_files:
        if caption_file.exists():
            try:
                with open(caption_file, 'r', encoding='utf-8') as f:
                    return f.read().strip()
            except Exception as e:
                print(f"[load_caption] 캡션 읽기 실패: {e}")

    return None


def show_approval_menu(chat_id: str, food_id: str):
    """
    승인 메뉴 표시 (신고 후 재검증용)

    🔐 UX 매핑 v1.0:
    - reoverlay/regenerate 후 반드시 호출
    - 새로 만든 것은 반드시 보여줘야 함

    Args:
        chat_id: 텔레그램 채팅 ID
        food_id: 콘텐츠 ID
    """
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ 승인", "callback_data": f"approve:{food_id}"},
                {"text": "🚫 반려", "callback_data": f"reject:{food_id}"}
            ],
            [
                {"text": "⚠️ 신고", "callback_data": f"report:{food_id}"}
            ],
            [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
        ]
    }
    send_message_with_keyboard(
        chat_id,
        "👆 이미지를 확인하고 다음 단계를 선택하세요:",
        keyboard
    )


def send_preview_with_approval(chat_id: str, food_id: str):
    """
    이미지 4장 미리보기 + 승인 메뉴

    🔐 UX 매핑 v1.0:
    - reoverlay/regenerate 후 반드시 호출
    - 새 결과물은 반드시 미리보기 필요

    Args:
        chat_id: 텔레그램 채팅 ID
        food_id: 콘텐츠 ID
    """
    print(f"[DEBUG] send_preview_with_approval: food_id={food_id}")

    folder = find_folder_by_food_id(food_id)
    if not folder:
        send_message(chat_id, f"❌ 폴더 없음: {food_id}")
        return

    # 이미지 4장
    images = [
        folder / f"{food_id}_00.png",
        folder / f"{food_id}_01.png",
        folder / f"{food_id}_02.png",
        folder / f"{food_id}_03.png",
    ]

    existing = [str(img) for img in images if img.exists()]

    if not existing:
        send_message(chat_id, f"❌ 이미지 없음: {food_id}")
        return

    send_message(chat_id, f"📸 <b>미리보기 전송 중...</b> ({len(existing)}장)")

    # 미디어 그룹으로 전송
    success = send_media_group(chat_id, existing)

    if success:
        # 승인 메뉴 (게시 버튼 아님!)
        show_approval_menu(chat_id, food_id)
    else:
        send_message(chat_id, "❌ 이미지 전송 실패")


def api_call(method: str, data: dict = None, json_data: dict = None) -> dict:
    """Telegram API 호출"""
    url = f"https://api.telegram.org/bot{TOKEN}/{method}"

    if json_data:
        # JSON 형식으로 전송 (키보드 등)
        json_bytes = json.dumps(json_data).encode('utf-8')
        req = urllib.request.Request(url, data=json_bytes)
        req.add_header('Content-Type', 'application/json')
    elif data:
        data_encoded = urllib.parse.urlencode(data).encode('utf-8')
        req = urllib.request.Request(url, data=data_encoded)
    else:
        req = urllib.request.Request(url)

    with urllib.request.urlopen(req, context=SSL_CTX, timeout=60) as response:
        return json.loads(response.read().decode('utf-8'))


def send_message(chat_id: str, text: str, parse_mode: str = 'HTML') -> bool:
    """메시지 전송"""
    try:
        result = api_call('sendMessage', {
            'chat_id': chat_id,
            'text': text,
            'parse_mode': parse_mode
        })
        return result.get('ok', False)
    except Exception as e:
        print(f"⚠️ 메시지 전송 실패: {e}")
        return False


def send_message_with_keyboard(chat_id: str, text: str, keyboard: dict) -> bool:
    """키보드와 함께 메시지 전송"""
    try:
        result = api_call('sendMessage', json_data={
            'chat_id': chat_id,
            'text': text,
            'parse_mode': 'HTML',
            'reply_markup': keyboard
        })
        return result.get('ok', False)
    except Exception as e:
        print(f"⚠️ 키보드 메시지 전송 실패: {e}")
        return False


def answer_callback(callback_id: str, text: str = None) -> bool:
    """콜백 응답 (버튼 클릭 후 로딩 제거)"""
    try:
        data = {'callback_query_id': callback_id}
        if text:
            data['text'] = text
        result = api_call('answerCallbackQuery', data)
        return result.get('ok', False)
    except Exception as e:
        print(f"⚠️ 콜백 응답 실패: {e}")
        return False


def send_photo(chat_id: str, photo_path: str, caption: str = None) -> bool:
    """단일 사진 전송"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"

        with open(photo_path, 'rb') as photo:
            # multipart/form-data로 전송
            import io
            boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'

            body = io.BytesIO()
            body.write(f'--{boundary}\r\n'.encode())
            body.write(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode())

            body.write(f'--{boundary}\r\n'.encode())
            body.write(f'Content-Disposition: form-data; name="photo"; filename="{Path(photo_path).name}"\r\n'.encode())
            body.write(b'Content-Type: image/png\r\n\r\n')
            body.write(photo.read())
            body.write(b'\r\n')

            if caption:
                body.write(f'--{boundary}\r\n'.encode())
                body.write(f'Content-Disposition: form-data; name="caption"\r\n\r\n{caption}\r\n'.encode())

            body.write(f'--{boundary}--\r\n'.encode())

            req = urllib.request.Request(url, data=body.getvalue())
            req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

            with urllib.request.urlopen(req, context=SSL_CTX, timeout=60) as response:
                result = json.loads(response.read().decode('utf-8'))
                return result.get('ok', False)
    except Exception as e:
        print(f"⚠️ 사진 전송 실패: {e}")
        return False


def send_media_group(chat_id: str, photo_paths: list) -> bool:
    """미디어 그룹 (여러 사진) 전송"""
    try:
        url = f"https://api.telegram.org/bot{TOKEN}/sendMediaGroup"

        import io
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'

        body = io.BytesIO()

        # chat_id
        body.write(f'--{boundary}\r\n'.encode())
        body.write(f'Content-Disposition: form-data; name="chat_id"\r\n\r\n{chat_id}\r\n'.encode())

        # media JSON
        media = []
        for i, path in enumerate(photo_paths):
            media.append({
                "type": "photo",
                "media": f"attach://photo{i}",
                "caption": f"{i+1}/{len(photo_paths)}" if i == 0 else ""
            })

        body.write(f'--{boundary}\r\n'.encode())
        body.write(f'Content-Disposition: form-data; name="media"\r\n\r\n{json.dumps(media)}\r\n'.encode())

        # 각 사진 파일
        for i, path in enumerate(photo_paths):
            with open(path, 'rb') as photo:
                body.write(f'--{boundary}\r\n'.encode())
                body.write(f'Content-Disposition: form-data; name="photo{i}"; filename="{Path(path).name}"\r\n'.encode())
                body.write(b'Content-Type: image/png\r\n\r\n')
                body.write(photo.read())
                body.write(b'\r\n')

        body.write(f'--{boundary}--\r\n'.encode())

        req = urllib.request.Request(url, data=body.getvalue())
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

        with urllib.request.urlopen(req, context=SSL_CTX, timeout=120) as response:
            result = json.loads(response.read().decode('utf-8'))
            return result.get('ok', False)
    except Exception as e:
        print(f"⚠️ 미디어 그룹 전송 실패: {e}")
        return False


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 음식 목록 동적 로드
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_ready_foods() -> dict:
    """
    "표지만 ready" 상태인 음식 추출

    조건:
    ✅ 표지 있음 (food_00.png 존재)
    ✅ 본문 없음 (food_01.png 없음)
    ✅ 아직 게시 안 됨

    Returns:
        {"SAFE": [...], "CAUTION": [...], "DANGER": [...]}
    """
    images_dir = PROJECT_ROOT / "contents"
    safety_path = PROJECT_ROOT / "config/settings/food_safety.json"
    history_path = PROJECT_ROOT / "config/data/publishing_history.csv"

    # 안전도 DB 로드
    if safety_path.exists():
        safety_db = json.loads(safety_path.read_text())
        safe_list = safety_db.get('safe', [])
        caution_list = safety_db.get('caution', [])
        danger_list = safety_db.get('danger', [])
    else:
        safe_list, caution_list, danger_list = [], [], []

    # 게시 완료된 음식 목록 로드
    posted_foods = set()
    if history_path.exists():
        try:
            lines = history_path.read_text().strip().split('\n')
            for line in lines[1:]:  # 헤더 스킵
                parts = line.split(',')
                if len(parts) >= 8 and parts[7].strip() == '게시완료':
                    posted_foods.add(parts[1].strip())  # 영문명
        except:
            pass

    result = {"SAFE": [], "CAUTION": [], "DANGER": []}

    if not images_dir.exists():
        return result

    # 폴더 스캔
    for folder in sorted(images_dir.iterdir()):
        if not folder.is_dir():
            continue

        # 특수 폴더 제외
        if folder.name.startswith("000_") or "archive" in folder.name.lower():
            continue

        # 폴더명 파싱: "169_duck_오리고기"
        parts = folder.name.split("_")
        if len(parts) < 3:
            continue

        food_key = parts[1]
        food_name = "_".join(parts[2:])

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 핵심 필터링 로직
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        # 1. 표지 파일 확인 (있어야 함)
        cover_file = folder / f"{food_key}_00.png"
        if not cover_file.exists():
            continue

        # 2. 본문 파일 확인 (없어야 함!)
        body_file_1 = folder / f"{food_key}_01.png"
        if body_file_1.exists():
            # 본문 이미 있음 → 완료된 콘텐츠, 스킵
            continue

        # 3. 게시 상태 확인 (게시 안 됐어야 함)
        if food_key in posted_foods:
            continue

        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
        # 여기까지 오면: cover_ready 상태
        # = /create 버튼에 표시할 대상
        # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

        # 안전도 분류
        emoji = EMOJI_MAP.get(food_key, "🍽️")
        food_info = {"name": food_name, "key": food_key, "emoji": emoji}

        if food_key in safe_list:
            result["SAFE"].append(food_info)
        elif food_key in caution_list:
            result["CAUTION"].append(food_info)
        elif food_key in danger_list:
            result["DANGER"].append(food_info)
        else:
            result["SAFE"].append(food_info)  # 기본값

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 상태별 음식 분류
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def get_foods_by_status() -> dict:
    """
    상태별로 음식 분류 (PD 승인 시스템 포함)

    Returns:
        {
            "cover_only": [...],     # 표지만 완료 → 본문 생성 필요
            "verified": [...],       # 검증 완료 → PD 승인 대기
            "approved": [...],       # PD 승인됨 → 게시 가능
            "rejected": [...],       # PD 반려됨 → 재생성 필요
        }
    """
    from core.publish_gate import get_content_metadata

    images_dir = PROJECT_ROOT / "contents"
    safety_path = PROJECT_ROOT / "config/settings/food_safety.json"
    history_path = PROJECT_ROOT / "config/data/publishing_history.csv"

    # 안전도 DB 로드
    if safety_path.exists():
        safety_db = json.loads(safety_path.read_text())
        safe_list = safety_db.get('safe', [])
        caution_list = safety_db.get('caution', [])
        danger_list = safety_db.get('danger', [])
    else:
        safe_list, caution_list, danger_list = [], [], []

    # 게시 완료된 음식 목록 로드
    posted_foods = set()
    if history_path.exists():
        try:
            lines = history_path.read_text().strip().split('\n')
            for line in lines[1:]:
                parts = line.split(',')
                if len(parts) >= 8:
                    status = parts[7].strip()
                    # v3: status_enum 통일 (posted 또는 게시완료)
                    if status in ('posted', '게시완료'):
                        posted_foods.add(parts[1].strip())
        except:
            pass

    result = {
        "cover_only": [],      # 표지만 있음 → 본문 생성 필요
        "verified": [],        # 검증 완료 → PD 승인 대기
        "approved": [],        # PD 승인됨 → 게시 가능
        "rejected": [],        # PD 반려됨 → 재생성 필요
    }

    if not images_dir.exists():
        return result

    # v3 구조: 상태 폴더 내 콘텐츠 스캔
    STATUS_FOLDERS = ["1_cover_only", "2_body_ready", "3_approved"]

    all_folders = []
    for status_folder in STATUS_FOLDERS:
        status_dir = images_dir / status_folder
        if status_dir.exists():
            for folder in status_dir.iterdir():
                if folder.is_dir():
                    all_folders.append(folder)

    # v2 호환: contents/ 루트에 있는 폴더도 스캔
    for folder in images_dir.iterdir():
        if folder.is_dir() and folder.name not in STATUS_FOLDERS:
            if not folder.name.startswith(("🔒", "reference", "sunshine", "test")):
                all_folders.append(folder)

    for folder in sorted(all_folders, key=lambda f: f.name):
        if not folder.is_dir():
            continue

        # 특수 폴더 제외
        if folder.name.startswith("000_") or "archive" in folder.name.lower():
            continue

        # 폴더명 파싱
        parts = folder.name.split("_")
        if len(parts) < 3:
            continue

        food_key = parts[1]
        food_name = "_".join(parts[2:])

        # 파일 존재 여부 확인
        cover = folder / f"{food_key}_00.png"
        body1 = folder / f"{food_key}_01.png"
        body2 = folder / f"{food_key}_02.png"

        if not cover.exists():
            continue  # 표지도 없으면 스킵

        # 게시 여부 확인
        if food_key in posted_foods:
            continue  # 이미 게시됨 → 스킵

        # 안전도 & 이모지
        emoji = EMOJI_MAP.get(food_key, "🍽️")

        # 안전도 분류
        if food_key in danger_list:
            safety = "DANGER"
        elif food_key in caution_list:
            safety = "CAUTION"
        else:
            safety = "SAFE"

        food_info = {
            "name": food_name,
            "key": food_key,
            "emoji": emoji,
            "safety": safety
        }

        # 메타데이터에서 상태 확인
        metadata = get_content_metadata(food_key)
        status = metadata.get("status", "generated") if metadata else "generated"
        pd_approved = metadata.get("pd_approved", False) if metadata else False

        # 상태별 분류
        if not body1.exists() or not body2.exists():
            # 본문 없음 → 표지만 완료
            result["cover_only"].append(food_info)
        elif status == "rejected":
            # PD 반려됨
            food_info["reject_reason"] = metadata.get("rejected_reason", "")
            result["rejected"].append(food_info)
        elif status == "approved" or pd_approved:
            # PD 승인됨 → 게시 가능
            result["approved"].append(food_info)
        else:
            # 본문 있음 + 승인 안됨 → 검증 완료 (승인 대기)
            result["verified"].append(food_info)

    return result


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 인라인 키보드 생성
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def create_food_keyboard() -> dict:
    """
    상태별 구분된 메인 키보드 (PD 승인 시스템 반영)

    🔐 UI 리디자인 (2026-02-03 PD 확정)
    - 섹션별 구분선 추가
    - 가독성 개선
    """
    foods = get_foods_by_status()
    keyboard = []

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 📸 표지만 완료 섹션
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cover_only = foods.get("cover_only", [])
    if cover_only:
        # 구분선
        keyboard.append([{
            "text": "━━━━━━━━━━━━━━━━━━━━",
            "callback_data": "divider:1"
        }])
        keyboard.append([{
            "text": f"📸 표지만 완료 ({len(cover_only)}개)",
            "callback_data": "section:cover_only"
        }])

        for i in range(0, min(len(cover_only), 6), 2):
            row = []
            for food in cover_only[i:i+2]:
                prefix = "⚠️" if food["safety"] == "CAUTION" else "🚫" if food["safety"] == "DANGER" else "🔘"
                row.append({
                    "text": f"{prefix} {food['name']}",
                    "callback_data": f"create:{food['key']}"
                })
            if row:
                keyboard.append(row)

        if len(cover_only) > 6:
            keyboard.append([{
                "text": f"📂 표지 완료 전체 보기 (+{len(cover_only) - 6}개)",
                "callback_data": "show_cover_only"
            }])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ⏳ 검증 완료 (PD 승인 대기)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    verified = foods.get("verified", [])
    if verified:
        # 구분선
        keyboard.append([{
            "text": "━━━━━━━━━━━━━━━━━━━━",
            "callback_data": "divider:2"
        }])
        keyboard.append([{
            "text": f"⏳ 승인 대기 ({len(verified)}개) - PD 승인 필요",
            "callback_data": "section:verified"
        }])

        for i in range(0, min(len(verified), 6), 2):
            row = []
            for food in verified[i:i+2]:
                row.append({
                    "text": f"⏳🔘 {food['name']}",
                    "callback_data": f"verify_menu:{food['key']}"
                })
            if row:
                keyboard.append(row)

        if len(verified) > 6:
            keyboard.append([{
                "text": f"📂 승인 대기 전체 보기 (+{len(verified) - 6}개)",
                "callback_data": "show_verified"
            }])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # ✅ PD 승인됨 (게시 가능)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    approved = foods.get("approved", [])
    if approved:
        # 구분선
        keyboard.append([{
            "text": "━━━━━━━━━━━━━━━━━━━━",
            "callback_data": "divider:3"
        }])
        keyboard.append([{
            "text": f"✅ 승인됨 ({len(approved)}개) - 게시 가능",
            "callback_data": "section:approved"
        }])

        for i in range(0, min(len(approved), 4), 2):
            row = []
            for food in approved[i:i+2]:
                row.append({
                    "text": f"✅🔘 {food['name']}",
                    "callback_data": f"approved_menu:{food['key']}"
                })
            if row:
                keyboard.append(row)

        if len(approved) > 4:
            keyboard.append([{
                "text": f"📂 승인됨 전체 보기 (+{len(approved) - 4}개)",
                "callback_data": "show_approved"
            }])

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 🚫 PD 반려됨 (재생성 필요)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    rejected = foods.get("rejected", [])
    if rejected:
        # 구분선
        keyboard.append([{
            "text": "━━━━━━━━━━━━━━━━━━━━",
            "callback_data": "divider:4"
        }])
        keyboard.append([{
            "text": f"🚫 반려됨 ({len(rejected)}개) - 재생성 필요",
            "callback_data": "section:rejected"
        }])

        for i in range(0, min(len(rejected), 4), 2):
            row = []
            for food in rejected[i:i+2]:
                row.append({
                    "text": f"🚫🔘 {food['name']}",
                    "callback_data": f"rejected_menu:{food['key']}"
                })
            if row:
                keyboard.append(row)

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 목록 없을 때
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if not cover_only and not verified and not approved and not rejected:
        keyboard.append([{
            "text": "📭 생성 가능한 콘텐츠가 없습니다",
            "callback_data": "none"
        }])

    # 하단 구분선 + 메뉴
    keyboard.append([{
        "text": "━━━━━━━━━━━━━━━━━━━━",
        "callback_data": "divider:bottom"
    }])
    keyboard.append([{
        "text": "📂 전체 목록 보기 (카테고리별)",
        "callback_data": "show_categories"
    }])

    return {"inline_keyboard": keyboard}


def create_cover_only_keyboard() -> dict:
    """표지만 완료 전체 목록"""
    foods = get_foods_by_status().get("cover_only", [])
    keyboard = []

    # 헤더
    keyboard.append([{
        "text": f"📸 표지만 완료 ({len(foods)}개)",
        "callback_data": "section:header"
    }])

    # 2개씩 배치
    for i in range(0, len(foods), 2):
        row = []
        for food in foods[i:i+2]:
            prefix = "⚠️" if food["safety"] == "CAUTION" else "🚫" if food["safety"] == "DANGER" else ""
            row.append({
                "text": f"{prefix}{food['emoji']} {food['name']}",
                "callback_data": f"create:{food['key']}"
            })
        if row:
            keyboard.append(row)

    # 뒤로가기
    keyboard.append([{"text": "🔙 메인 메뉴", "callback_data": "show_main"}])

    return {"inline_keyboard": keyboard}


def create_ready_to_post_keyboard() -> dict:
    """게시 대기 전체 목록 (deprecated - verified로 변경)"""
    return create_verified_keyboard()


def create_verified_keyboard() -> dict:
    """검증 완료 (승인 대기) 전체 목록"""
    foods = get_foods_by_status().get("verified", [])
    keyboard = []

    keyboard.append([{
        "text": f"⏳ 승인 대기 ({len(foods)}개)",
        "callback_data": "section:header"
    }])

    for i in range(0, len(foods), 2):
        row = []
        for food in foods[i:i+2]:
            row.append({
                "text": f"⏳{food['emoji']} {food['name']}",
                "callback_data": f"verify_menu:{food['key']}"
            })
        if row:
            keyboard.append(row)

    keyboard.append([{"text": "🔙 메인 메뉴", "callback_data": "show_main"}])
    return {"inline_keyboard": keyboard}


def create_approved_keyboard() -> dict:
    """PD 승인됨 전체 목록"""
    foods = get_foods_by_status().get("approved", [])
    keyboard = []

    keyboard.append([{
        "text": f"✅ 승인됨 ({len(foods)}개)",
        "callback_data": "section:header"
    }])

    for i in range(0, len(foods), 2):
        row = []
        for food in foods[i:i+2]:
            row.append({
                "text": f"✅{food['emoji']} {food['name']}",
                "callback_data": f"approved_menu:{food['key']}"
            })
        if row:
            keyboard.append(row)

    keyboard.append([{"text": "🔙 메인 메뉴", "callback_data": "show_main"}])
    return {"inline_keyboard": keyboard}


def create_category_menu() -> dict:
    """안전도별 카테고리 메뉴"""
    foods = get_ready_foods()

    keyboard = [
        [{"text": f"🟢 SAFE ({len(foods.get('SAFE', []))}개)", "callback_data": "category:SAFE"}],
        [{"text": f"🟡 CAUTION ({len(foods.get('CAUTION', []))}개)", "callback_data": "category:CAUTION"}],
        [{"text": f"🔴 DANGER ({len(foods.get('DANGER', []))}개)", "callback_data": "category:DANGER"}],
        [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
    ]

    return {"inline_keyboard": keyboard}


def create_category_foods_keyboard(category: str) -> dict:
    """카테고리별 음식 목록"""
    foods = get_ready_foods().get(category, [])
    keyboard = []

    # 2개씩 배치
    for i in range(0, len(foods), 2):
        row = []
        for food in foods[i:i+2]:
            prefix = "⚠️" if category == "CAUTION" else "🚫" if category == "DANGER" else ""
            row.append({
                "text": f"{prefix}{food['emoji']} {food['name']}",
                "callback_data": f"create:{food['key']}"
            })
        if row:
            keyboard.append(row)

    # 뒤로가기
    keyboard.append([{"text": "🔙 뒤로", "callback_data": "show_categories"}])

    return {"inline_keyboard": keyboard}


def get_food_key(food_name: str) -> str:
    """한글 → 영문 변환"""
    return FOOD_MAPPING.get(food_name, food_name)


def handle_help(chat_id: str):
    """도움말"""
    text = """
🐕 <b>Project Sunshine 봇</b>

<b>📋 명령어 (한글/영어 모두 가능)</b>

/생성 또는 /create
→ 버튼으로 음식 선택

/상태 [음식] 또는 /status [음식]
→ 특정 음식 상태 확인

/목록 또는 /list
→ 전체 콘텐츠 목록

/정리 [음식] 또는 /clean [음식]
→ 폴더 정리 (파이널 4장만 유지)

<b>🔐 PD 승인 명령어</b>

/승인 [음식] 또는 /approve [음식]
→ 콘텐츠 게시 승인

/반려 [음식] [사유] 또는 /reject [음식] [사유]
→ 콘텐츠 반려 (재생성 필요)

/도움말 또는 /help
→ 이 도움말

<b>💡 추천:</b>
/생성 입력 → 버튼 메뉴에서 선택

<b>📝 직접 입력 예시:</b>
/생성 오리고기
/상태 duck
/승인 duck
/반려 duck 색상이_이상함
"""
    send_message(chat_id, text)


def handle_create(chat_id: str, args: list):
    """콘텐츠 생성 - 인자 없으면 버튼 메뉴"""
    if not args:
        # 동기화 먼저 실행 (2026-02-03 PD 지시)
        try:
            from utils.sync_status import sync_all_contents
            sync_all_contents()
        except Exception as e:
            print(f"⚠️ 동기화 오류 (무시): {e}")

        # 버튼 메뉴 표시
        send_message_with_keyboard(
            chat_id,
            "🍽️ <b>생성할 음식을 선택하세요</b>\n\n"
            "📸 표지만 완료 → 본문 생성 필요\n"
            "⏳ 승인 대기 → PD 승인 필요\n"
            "✅ 승인됨 → 게시 가능",
            create_food_keyboard()
        )
        return

    food_name = args[0]
    start_content_creation(chat_id, food_name)


def show_verify_menu(chat_id: str, food_key: str):
    """
    검증 완료 콘텐츠 - 이미지 자동 전송 + 승인/반려 버튼

    🔐 PD 확정 UX (2026-02-03):
    1. 이미지 4장 먼저 자동 전송
    2. 승인/반려 버튼 노출
    (미리보기 버튼 삭제됨)
    """
    from core.publish_gate import get_content_metadata

    print(f"[DEBUG] show_verify_menu: food_key={food_key}")

    # 폴더 찾기 (새 매핑 함수 사용)
    content_folder = find_folder_by_food_id(food_key)

    if not content_folder:
        send_message(chat_id, f"❌ 폴더 없음: {food_key}")
        return

    print(f"[DEBUG] content_folder: {content_folder}")

    # 메타데이터 로드
    metadata = get_content_metadata(food_key) or {}
    food_name = "_".join(content_folder.name.split("_")[2:])

    # 1. 이미지 4장 자동 전송 (미리보기 버튼 대체)
    images = [
        content_folder / f"{food_key}_00.png",
        content_folder / f"{food_key}_01.png",
        content_folder / f"{food_key}_02.png",
        content_folder / f"{food_key}_03.png",
    ]

    existing = [str(img) for img in images if img.exists()]

    if existing:
        send_message(chat_id, f"📸 <b>{food_name}</b> 미리보기 ({len(existing)}장)")
        send_media_group(chat_id, existing)

    # 2. 승인/반려 버튼 + 신고 버튼 (항상 표시)
    msg = f"""
⏳ <b>PD 승인 대기</b>

📁 <b>콘텐츠:</b> {food_name} ({food_key})
🖼️ <b>이미지:</b> {len(existing)}장

━━━━━━━━━━━━━━━━━━
승인 또는 반려를 선택하세요.
"""

    keyboard = {
        "inline_keyboard": [
            [
                {"text": "✅ 승인", "callback_data": f"approve:{food_key}"},
                {"text": "❌ 반려", "callback_data": f"reject_prompt:{food_key}"}
            ],
            [{"text": "⚠️ 신고", "callback_data": f"report:{food_key}"}],
            [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
        ]
    }

    send_message_with_keyboard(chat_id, msg, keyboard)


def show_approved_menu(chat_id: str, food_key: str):
    """
    PD 승인됨 콘텐츠 - 이미지 자동 전송 + 게시 버튼

    🔐 PD 확정 UX (2026-02-03):
    1. 이미지 4장 먼저 자동 전송
    2. 게시하기 버튼 노출
    (미리보기 버튼 삭제됨)
    """
    from core.publish_gate import get_content_metadata

    print(f"[DEBUG] show_approved_menu: food_key={food_key}")

    # 폴더 찾기 (새 매핑 함수 사용)
    content_folder = find_folder_by_food_id(food_key)

    if not content_folder:
        send_message(chat_id, f"❌ 폴더 없음: {food_key}")
        return

    print(f"[DEBUG] content_folder: {content_folder}")

    metadata = get_content_metadata(food_key) or {}
    approved_at = metadata.get("approved_at", "알 수 없음")
    approved_by = metadata.get("approved_by", "알 수 없음")
    food_name = "_".join(content_folder.name.split("_")[2:])

    # 1. 이미지 4장 자동 전송
    images = [
        content_folder / f"{food_key}_00.png",
        content_folder / f"{food_key}_01.png",
        content_folder / f"{food_key}_02.png",
        content_folder / f"{food_key}_03.png",
    ]

    existing = [str(img) for img in images if img.exists()]

    if existing:
        send_message(chat_id, f"📸 <b>{food_name}</b> 미리보기 ({len(existing)}장)")
        send_media_group(chat_id, existing)

    # 2. 게시하기 버튼 + 신고 버튼 (항상 표시)
    msg = f"""
✅ <b>PD 승인 완료</b>

📁 <b>콘텐츠:</b> {food_name} ({food_key})
⏰ <b>승인 시각:</b> {approved_at[:16] if len(approved_at) > 16 else approved_at}
👤 <b>승인자:</b> {approved_by}

━━━━━━━━━━━━━━━━━━
게시하시겠습니까?
"""

    keyboard = {
        "inline_keyboard": [
            [{"text": "🚀 게시하기", "callback_data": f"publish:{food_key}"}],
            [{"text": "⚠️ 신고", "callback_data": f"report:{food_key}"}],
            [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
        ]
    }

    send_message_with_keyboard(chat_id, msg, keyboard)


def show_rejected_menu(chat_id: str, food_key: str):
    """PD 반려됨 콘텐츠 - 재생성 메뉴"""
    from core.publish_gate import get_content_metadata

    print(f"[DEBUG] show_rejected_menu: food_key={food_key}")

    # 폴더 찾기 (새 매핑 함수 사용)
    content_folder = find_folder_by_food_id(food_key)

    if not content_folder:
        send_message(chat_id, f"❌ 폴더 없음: {food_key}")
        return

    print(f"[DEBUG] content_folder: {content_folder}")

    metadata = get_content_metadata(food_key) or {}
    rejected_at = metadata.get("rejected_at", "알 수 없음")
    rejected_reason = metadata.get("rejected_reason", "사유 없음")

    food_name = "_".join(content_folder.name.split("_")[2:])
    msg = f"""
🚫 <b>PD 반려됨</b>

📁 <b>콘텐츠:</b> {food_name} ({food_key})
⏰ <b>반려 시각:</b> {rejected_at[:16] if len(rejected_at) > 16 else rejected_at}
📝 <b>반려 사유:</b> {rejected_reason}

━━━━━━━━━━━━━━━━━━
재생성이 필요합니다.
"""

    keyboard = {
        "inline_keyboard": [
            [{"text": "🔄 재생성", "callback_data": f"create:{food_key}"}],
            [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
        ]
    }

    send_message_with_keyboard(chat_id, msg, keyboard)


def show_verified_list(chat_id: str):
    """승인 대기 전체 목록"""
    send_message_with_keyboard(
        chat_id,
        "⏳ <b>승인 대기 콘텐츠</b>\n\n음식을 선택하면 승인/반려 메뉴가 표시됩니다:",
        create_verified_keyboard()
    )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 신고 시스템 (2026-02-03 PD 확정)
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def show_report_menu(chat_id: str, food_key: str):
    """신고 유형 선택 메뉴"""
    msg = f"""
⚠️ <b>신고하기</b>

📁 콘텐츠: {food_key}

무엇이 문제인가요?
"""

    keyboard = {
        "inline_keyboard": [
            [{"text": "🔄 이미 게시됨 (동기화 오류)", "callback_data": f"report_sync:{food_key}"}],
            [{"text": "🖼️ 이미지 문제 (깨짐/이상)", "callback_data": f"report_image:{food_key}"}],
            [{"text": "📝 정보 오류 (텍스트 틀림)", "callback_data": f"report_info:{food_key}"}],
            [{"text": "🔤 텍스트 중첩 (P0)", "callback_data": f"report_text_overlap:{food_key}"}],
            [{"text": "❓ 기타", "callback_data": f"report_other:{food_key}"}],
            [{"text": "⬅️ 취소", "callback_data": f"cancel_report:{food_key}"}],
        ]
    }

    send_message_with_keyboard(chat_id, msg, keyboard)


def handle_report_sync(chat_id: str, food_key: str):
    """
    SYNC_ERROR 처리 - 완전 자동

    1. 3중 동기화 실행
    2. 결과에 따라 자동 이동
    3. 결과 알림
    """
    from utils.report_handler import handle_sync_error

    send_message(chat_id, "🔄 동기화 확인 중...")

    result = handle_sync_error(food_key)

    if result.get("auto_resolved"):
        msg = f"""
✅ <b>자동 처리 완료</b>

📁 콘텐츠: {food_key}
📊 확인 결과: 이미 게시됨
🔄 조치: posted/ 폴더로 이동됨
📍 출처: {result.get('source', 'unknown')}
"""
    else:
        msg = f"""
ℹ️ <b>확인 완료</b>

📁 콘텐츠: {food_key}
📊 확인 결과: 게시되지 않음
📍 현재 상태: {result.get('final_status', 'unknown')}
📍 출처: {result.get('source', 'unknown')}
"""

    keyboard = {
        "inline_keyboard": [
            [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
        ]
    }

    send_message_with_keyboard(chat_id, msg, keyboard)


def handle_report_image(chat_id: str, food_key: str):
    """
    IMAGE_ERROR 처리 - 반자동 (확인 + 알림)
    """
    from utils.report_handler import handle_image_error

    send_message(chat_id, "🖼️ 이미지 확인 중...")

    result = handle_image_error(food_key)

    if result.get("all_valid"):
        msg = f"""
ℹ️ <b>이미지 확인 완료</b>

📁 콘텐츠: {food_key}
🖼️ 파일 상태: 모든 이미지 정상

문제가 지속되면 구체적인 내용을 알려주세요.
"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
            ]
        }
    else:
        issues = result.get("issues", [])
        issues_text = "\n".join(f"• {i}" for i in issues) if issues else "알 수 없음"

        msg = f"""
⚠️ <b>이미지 문제 발견</b>

📁 콘텐츠: {food_key}
🖼️ 문제:
{issues_text}

재생성이 필요합니다.
"""
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔄 재생성", "callback_data": f"create:{food_key}"}],
                [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
            ]
        }

    send_message_with_keyboard(chat_id, msg, keyboard)


def handle_report_info(chat_id: str, food_key: str):
    """
    INFO_ERROR 처리 - PD 확인 필요 (자동 수정 금지)
    """
    from utils.report_handler import handle_info_error

    handle_info_error(food_key)

    msg = f"""
📝 <b>정보 오류 신고 접수</b>

📁 콘텐츠: {food_key}

어떤 정보가 잘못되었나요?
(텍스트로 입력해 주세요)

예: "효능 텍스트가 틀렸어요"
"""

    send_message(chat_id, msg)


def handle_report_other(chat_id: str, food_key: str):
    """
    OTHER 처리 - PD 확인 필요
    """
    from utils.report_handler import handle_other_error

    handle_other_error(food_key)

    msg = f"""
❓ <b>기타 신고 접수</b>

📁 콘텐츠: {food_key}

문제 내용을 입력해 주세요.
(텍스트로 입력해 주세요)
"""

    send_message(chat_id, msg)


def handle_reoverlay(chat_id: str, food_key: str):
    """
    텍스트 오버레이 재작업 — 성공 판정 기준 강화

    🔐 성공 판정 체크리스트:
    1. 스크립트 존재 확인
    2. returncode=0 확인
    3. 파일 수정시간 변경 확인
    4. 파일 크기 > 0 확인

    ⚠️ print("완료")는 절대 성공 기준이 아니다
    """
    send_message(chat_id, f"🔄 텍스트 재작업 시작: {food_key}\n\n이미지는 유지하고 텍스트만 재작업합니다...")

    def run_reoverlay():
        import subprocess

        try:
            # ═══════════════════════════════════════════
            # STEP 1: 폴더 및 이미지 파일 확인
            # ═══════════════════════════════════════════
            folder = find_folder_by_food_id(food_key)
            if not folder:
                send_message(chat_id, f"❌ 폴더 없음: {food_key}")
                return

            image_files = sorted(folder.glob(f"{food_key}_*.png"))
            image_files = [f for f in image_files if 'metadata' not in f.name.lower()]

            if len(image_files) < 4:
                send_message(chat_id, f"❌ 이미지 부족: {len(image_files)}장")
                return

            # ═══════════════════════════════════════════
            # STEP 2: 기존 이미지 수정시간 기록 (검증용)
            # ═══════════════════════════════════════════
            before_mtimes = {f.name: f.stat().st_mtime for f in image_files}
            print(f"[DEBUG] 이전 수정시간 기록: {len(before_mtimes)}개")

            # ═══════════════════════════════════════════
            # STEP 3: 텍스트 오버레이 스크립트 실행
            # ═══════════════════════════════════════════
            overlay_script = PROJECT_ROOT / "services" / "scripts" / "text_overlay.py"
            reoverlay_script = PROJECT_ROOT / "services" / "scripts" / "reoverlay.py"

            script_path = None
            if reoverlay_script.exists():
                script_path = reoverlay_script
            elif overlay_script.exists():
                script_path = overlay_script

            if not script_path:
                # 스크립트 없음 → 수동 확인 안내
                send_message(chat_id, f"""
⚠️ <b>텍스트 재작업 스크립트 없음</b>

📂 콘텐츠: {food_key}
❌ scripts/text_overlay.py 또는 scripts/reoverlay.py 필요

수동으로 텍스트 오버레이를 수정해주세요.
수정 후 아래 이미지를 확인하세요.
""")
                # 이미지 미리보기는 보여줌 (수동 검증용)
                send_preview_with_approval(chat_id, food_key)
                return

            result = subprocess.run(
                ["python3", str(script_path), str(folder), food_key],
                capture_output=True,
                text=True,
                timeout=120,
                cwd=str(PROJECT_ROOT)
            )

            print(f"[DEBUG] 스크립트 실행: returncode={result.returncode}")
            if result.stdout:
                print(f"[DEBUG] stdout: {result.stdout[:200]}")
            if result.stderr:
                print(f"[DEBUG] stderr: {result.stderr[:200]}")

            if result.returncode != 0:
                send_message(chat_id, f"""
❌ <b>텍스트 재작업 실패</b>

📂 콘텐츠: {food_key}
오류: {result.stderr[:300] if result.stderr else '알 수 없는 오류'}
""")
                return

            # ═══════════════════════════════════════════
            # 🔴 성공 판정 기준 1: 파일 수정시간 변경 확인
            # ═══════════════════════════════════════════
            after_mtimes = {f.name: f.stat().st_mtime for f in image_files}

            modified_count = 0
            for fname, before_mtime in before_mtimes.items():
                after_mtime = after_mtimes.get(fname, before_mtime)
                if after_mtime > before_mtime:
                    modified_count += 1
                    print(f"[DEBUG] 수정됨: {fname}")

            if modified_count == 0:
                send_message(chat_id, f"""
⚠️ <b>텍스트 재작업 검증 주의</b>

📂 콘텐츠: {food_key}
❌ 이미지가 수정되지 않았습니다.

스크립트 실행은 됐지만 결과물이 변경되지 않았습니다.
아래 이미지를 확인해주세요.
""")
                # 이미지 미리보기는 보여줌 (수동 검증용)
                send_preview_with_approval(chat_id, food_key)
                return

            # ═══════════════════════════════════════════
            # 🔴 성공 판정 기준 2: 이미지 파일 크기 > 0
            # ═══════════════════════════════════════════
            for img in image_files:
                if img.stat().st_size == 0:
                    send_message(chat_id, f"❌ 빈 이미지 파일: {img.name}")
                    return

            # ═══════════════════════════════════════════
            # ✅ 모든 검증 통과 → 성공
            # ═══════════════════════════════════════════
            send_message(chat_id, f"""
✅ <b>텍스트 재작업 완료!</b>

📂 콘텐츠: {food_key}
🔧 수정된 이미지: {modified_count}장
📍 상태: body_ready (유지)

아래 이미지를 확인하고 승인/반려를 결정하세요.
""")
            # 🔐 UX 매핑 v1.0: 이미지 4장 + 승인 메뉴
            send_preview_with_approval(chat_id, food_key)

        except subprocess.TimeoutExpired:
            send_message(chat_id, f"❌ 재작업 시간 초과 (120초)")
        except Exception as e:
            import traceback
            print(f"[handle_reoverlay] 오류: {traceback.format_exc()}")
            send_message(chat_id, f"❌ 재작업 실패: {str(e)[:200]}")

    # 백그라운드 실행
    executor.submit(run_reoverlay)


def handle_report_text_overlap(chat_id: str, food_key: str):
    """
    TEXT_OVERLAP 처리 - 텍스트 중첩 문제

    🔐 상태 Enum v1.0 규칙:
    - TEXT_OVERLAP → reoverlay (텍스트 오버레이만 재작업)
    - 이미지 유지, body_ready 상태 유지
    - ❌ regenerate (이미지 재생성) 아님!
    """
    from utils.report_handler import handle_text_overlap_error

    send_message(chat_id, "🔤 텍스트 중첩 확인 중...")

    result = handle_text_overlap_error(food_key)

    action_type = result.get('action_type', 'reoverlay')

    msg = f"""
🔤 <b>텍스트 중첩 신고 접수</b>

📁 콘텐츠: {food_key}
⚠️ 이슈: 텍스트 중첩 문제
📝 상태: {result.get('status', 'body_ready')} (유지)
🔧 조치: {result.get('recommendation', '텍스트 오버레이 재작업')}

━━━━━━━━━━━━━━━━━━
💡 이미지는 유지하고 텍스트만 재작업합니다.
"""

    keyboard = {
        "inline_keyboard": [
            [{"text": "🔄 텍스트 재작업 (Reoverlay)", "callback_data": f"reoverlay:{food_key}"}],
            [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
        ]
    }

    send_message_with_keyboard(chat_id, msg, keyboard)


def show_approved_list(chat_id: str):
    """승인됨 전체 목록"""
    send_message_with_keyboard(
        chat_id,
        "✅ <b>PD 승인된 콘텐츠</b>\n\n음식을 선택하면 게시 메뉴가 표시됩니다:",
        create_approved_keyboard()
    )


def show_preview_and_post(chat_id: str, food_key: str):
    """전체 완료 콘텐츠 미리보기 및 게시 확인"""
    print(f"[DEBUG] show_preview_and_post: food_key={food_key}")

    # 폴더 찾기 (새 매핑 함수 사용)
    content_folder = find_folder_by_food_id(food_key)

    if not content_folder:
        send_message(chat_id, f"❌ 폴더 없음: {food_key}")
        return

    print(f"[DEBUG] content_folder: {content_folder}")

    # 파일 목록 확인
    files = list(content_folder.glob(f"{food_key}_*.png"))
    files = [f for f in files if not 'metadata' in f.name and not 'raw' in f.name]
    files.sort()

    # 상태 메시지
    food_name = "_".join(content_folder.name.split("_")[2:])
    msg = f"""
✅ <b>게시 준비 완료</b>

📁 <b>폴더:</b> {content_folder.name}
📸 <b>이미지:</b> {len(files)}장

<b>파일 목록:</b>
"""
    for f in files[:5]:
        msg += f"• {f.name}\n"
    if len(files) > 5:
        msg += f"... 외 {len(files) - 5}개\n"

    msg += f"""
━━━━━━━━━━━━━━━━━━
게시하시겠습니까?
"""

    # 게시 확인 버튼
    keyboard = {
        "inline_keyboard": [
            [
                {"text": "📤 게시하기", "callback_data": f"publish:{food_key}"},
                {"text": "👀 미리보기", "callback_data": f"send_preview:{food_key}"}
            ],
            [{"text": "🔙 뒤로", "callback_data": "show_main"}]
        ]
    }

    send_message_with_keyboard(chat_id, msg, keyboard)


def show_cover_preview(chat_id: str, food_key: str):
    """
    표지 선택 시 - 미리보기 + 본문 생성 버튼만 표시

    🔐 원칙: 표지는 결정, 본문은 실행
    (파이프라인 자동 실행 금지)
    """
    from core.publish_gate import get_content_metadata

    print(f"[DEBUG] show_cover_preview: food_key={food_key}")

    # 폴더 찾기 (새 매핑 함수 사용)
    content_folder = find_folder_by_food_id(food_key)

    if not content_folder:
        send_message(chat_id, f"❌ 폴더를 찾을 수 없습니다: {food_key}")
        return

    print(f"[DEBUG] content_folder: {content_folder}")

    # 표지 이미지 경로
    cover_image = content_folder / f"{food_key}_00.png"

    # 메타데이터 조회
    metadata = get_content_metadata(food_key) or {}
    food_name = "_".join(content_folder.name.split("_")[2:])
    safety_level = "unknown"

    # 안전도 조회
    safety_path = PROJECT_ROOT / "config/settings/food_safety.json"
    if safety_path.exists():
        safety_db = json.loads(safety_path.read_text())
        if food_key in safety_db.get('safe', []):
            safety_level = "🟢 SAFE"
        elif food_key in safety_db.get('caution', []):
            safety_level = "🟡 CAUTION"
        elif food_key in safety_db.get('danger', []):
            safety_level = "🔴 DANGER"

    # 1. 표지 이미지 전송 (1장만)
    if cover_image.exists():
        send_photo(chat_id, str(cover_image), f"📸 표지 미리보기: {food_name}")
    else:
        send_message(chat_id, f"⚠️ 표지 이미지 없음: {food_key}")
        return

    # 2. 본문 생성 버튼 표시 (파이프라인 실행 X)
    msg = f"""
📋 <b>표지 확인</b>

📁 <b>콘텐츠:</b> {food_name} ({food_key})
🔒 <b>안전도:</b> {safety_level}

━━━━━━━━━━━━━━━━━━
본문 생성을 진행하시겠습니까?
"""

    keyboard = {
        "inline_keyboard": [
            [{"text": "🎨 본문 생성 (Flux 2.0 Pro)", "callback_data": f"generate_body:{food_key}"}],
            [{"text": "❌ 다시 선택", "callback_data": "show_cover_only"}],
            [{"text": "⬅️ 메인 메뉴", "callback_data": "show_main"}]
        ]
    }

    send_message_with_keyboard(chat_id, msg, keyboard)


def start_content_creation(chat_id: str, food_input: str):
    """콘텐츠 생성 실행 (본문 이미지 생성) - generate_body 버튼 클릭 시에만 호출"""
    food_key = get_food_key(food_input)

    # 한글 이름 찾기
    food_name_kr = FOOD_NAME_KR.get(food_key, food_input)

    send_message(chat_id, f"🚀 <b>생성 시작</b>\n\n음식: {food_name_kr}\n키: {food_key}\n\n처리 중...")

    def run_pipeline():
        try:
            from mcp.pipelines.auto_content import AutoContentPipeline
            pipeline = AutoContentPipeline()
            success = pipeline.run(food_key, dry_run=False)

            if success:
                send_message(chat_id, f"✅ <b>생성 완료</b>\n\n{food_name_kr} ({food_key})")
            else:
                send_message(chat_id, f"❌ <b>생성 실패</b>\n\n{food_name_kr}\n\n/status {food_key} 로 상세 확인")
        except Exception as e:
            send_message(chat_id, f"❌ <b>오류</b>\n\n{str(e)[:200]}")

    # 백그라운드 실행
    executor.submit(run_pipeline)


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 버튼 클릭 (콜백) 처리
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def handle_callback(callback_query: dict):
    """버튼 클릭 처리"""
    callback_id = callback_query.get("id", "")
    chat_id = str(callback_query.get("message", {}).get("chat", {}).get("id", ""))
    data = callback_query.get("data", "")

    # 권한 체크
    if chat_id != ALLOWED_CHAT_ID:
        answer_callback(callback_id, "⛔ 권한 없음")
        return

    print(f"📥 콜백: {data}")

    # 콜백 응답 (로딩 표시 제거)
    answer_callback(callback_id)

    if data.startswith("create:"):
        # 표지만 완료 → 미리보기 + 본문 생성 버튼 (수정됨)
        # 🔐 원칙: 표지는 결정, 본문은 실행
        food_key = data.split(":")[1]
        show_cover_preview(chat_id, food_key)

    elif data.startswith("generate_body:"):
        # 본문 생성 버튼 클릭 → 실제 파이프라인 실행
        food_key = data.split(":")[1]
        start_content_creation(chat_id, food_key)

    elif data.startswith("preview:"):
        # 전체 완료 → 미리보기/게시 확인
        food_key = data.split(":")[1]
        show_preview_and_post(chat_id, food_key)

    elif data.startswith("section:"):
        # 섹션 헤더 클릭 → 아무 동작 없음
        pass

    elif data == "show_cover_only":
        # 표지만 완료 전체 목록
        send_message_with_keyboard(
            chat_id,
            "📸 <b>표지만 완료 (본문 생성 필요)</b>\n\n음식을 선택하면 표지 미리보기 후 본문 생성을 진행합니다:",
            create_cover_only_keyboard()
        )

    elif data == "show_ready_to_post":
        # 게시 대기 전체 목록
        send_message_with_keyboard(
            chat_id,
            "✅ <b>전체 완료 (게시 대기)</b>\n\n음식을 선택하면 미리보기/게시를 진행합니다:",
            create_ready_to_post_keyboard()
        )

    elif data == "show_categories":
        # 안전도별 카테고리
        send_message_with_keyboard(
            chat_id,
            "📋 <b>안전도별 음식 목록</b>\n\n카테고리를 선택하세요:",
            create_category_menu()
        )

    elif data.startswith("category:"):
        # 카테고리별 음식
        category = data.split(":")[1]
        category_names = {
            "SAFE": "🟢 SAFE (먹어도 됨)",
            "CAUTION": "🟡 CAUTION (주의 필요)",
            "DANGER": "🔴 DANGER (금지 식품)"
        }
        send_message_with_keyboard(
            chat_id,
            f"<b>{category_names.get(category, category)}</b>\n\n음식을 선택하세요:",
            create_category_foods_keyboard(category)
        )

    elif data == "show_main":
        # 메인 메뉴
        send_message_with_keyboard(
            chat_id,
            "🍽️ <b>생성할 음식을 선택하세요</b>",
            create_food_keyboard()
        )

    elif data.startswith("send_preview:"):
        # 실제 이미지 4장 전송
        food_key = data.split(":")[1]
        send_preview_images(chat_id, food_key)

    elif data.startswith("publish:"):
        # 인스타그램 게시
        food_key = data.split(":")[1]
        publish_to_instagram(chat_id, food_key)

    elif data.startswith("verify_menu:"):
        # 검증 완료 → 승인 메뉴 표시
        food_key = data.split(":")[1]
        show_verify_menu(chat_id, food_key)

    elif data.startswith("approved_menu:"):
        # 승인됨 → 게시 메뉴 표시
        food_key = data.split(":")[1]
        show_approved_menu(chat_id, food_key)

    elif data.startswith("rejected_menu:"):
        # 반려됨 → 재생성 메뉴 표시
        food_key = data.split(":")[1]
        show_rejected_menu(chat_id, food_key)

    elif data.startswith("approve:"):
        # 버튼으로 승인
        food_key = data.split(":")[1]
        handle_approve(chat_id, [food_key])

    elif data.startswith("reject_prompt:"):
        # 반려 사유 입력 안내
        food_key = data.split(":")[1]
        send_message(chat_id, f"🚫 <b>반려 사유를 입력하세요</b>\n\n/반려 {food_key} [사유]\n\n예: /반려 {food_key} 색상이_이상함")

    elif data == "show_verified":
        # 승인 대기 전체 목록
        show_verified_list(chat_id)

    elif data == "show_approved":
        # 승인됨 전체 목록
        show_approved_list(chat_id)

    elif data.startswith("report:"):
        # 신고 메뉴 표시
        food_key = data.split(":")[1]
        show_report_menu(chat_id, food_key)

    elif data.startswith("report_sync:"):
        # 동기화 오류 신고 처리
        food_key = data.split(":")[1]
        handle_report_sync(chat_id, food_key)

    elif data.startswith("report_image:"):
        # 이미지 오류 신고 처리
        food_key = data.split(":")[1]
        handle_report_image(chat_id, food_key)

    elif data.startswith("report_info:"):
        # 정보 오류 신고 처리
        food_key = data.split(":")[1]
        handle_report_info(chat_id, food_key)

    elif data.startswith("report_other:"):
        # 기타 신고 처리
        food_key = data.split(":")[1]
        handle_report_other(chat_id, food_key)

    elif data.startswith("report_text_overlap:"):
        # 텍스트 중첩 신고 처리
        food_key = data.split(":")[1]
        handle_report_text_overlap(chat_id, food_key)

    elif data.startswith("reoverlay:"):
        # 텍스트 오버레이 재작업 (이미지 유지)
        food_key = data.split(":")[1]
        handle_reoverlay(chat_id, food_key)

    elif data.startswith("edit_caption:"):
        # 캡션 수정 안내
        food_key = data.split(":")[1]
        folder = find_folder_by_food_id(food_key)
        if folder:
            caption_file = folder / "caption_instagram.txt"
            send_message(chat_id, f"""
✏️ <b>캡션 수정 안내</b>

📁 콘텐츠: {food_key}
📂 파일: {caption_file}

현재 캡션 수정은 파일을 직접 편집해야 합니다.
수정 후 다시 게시를 시도하세요.
""")
        else:
            send_message(chat_id, f"❌ 폴더 없음: {food_key}")

    elif data.startswith("upload_cloudinary:"):
        # Cloudinary 업로드
        food_key = data.split(":")[1]
        handle_upload_cloudinary(chat_id, food_key)

    elif data.startswith("cancel_report:"):
        # 신고 취소
        food_key = data.split(":")[1]
        send_message(chat_id, "ℹ️ 신고가 취소되었습니다.")

    elif data.startswith("divider:"):
        # 구분선 클릭 - 무시
        pass

    elif data == "none":
        # 목록 없음
        pass


def send_preview_images(chat_id: str, food_key: str):
    """미리보기 - 실제 이미지 4장 전송"""
    print(f"[DEBUG] send_preview_images: food_key={food_key}")

    # 폴더 찾기 (새 매핑 함수 사용)
    content_folder = find_folder_by_food_id(food_key)

    if not content_folder:
        send_message(chat_id, f"❌ 폴더 없음: {food_key}")
        return

    print(f"[DEBUG] content_folder: {content_folder}")

    # 파이널 이미지 4장
    images = [
        content_folder / f"{food_key}_00.png",
        content_folder / f"{food_key}_01.png",
        content_folder / f"{food_key}_02.png",
        content_folder / f"{food_key}_03.png",
    ]

    # 존재하는 파일만
    existing = [str(img) for img in images if img.exists()]

    if not existing:
        send_message(chat_id, f"❌ 이미지 없음: {food_key}")
        return

    send_message(chat_id, f"📸 <b>미리보기 전송 중...</b> ({len(existing)}장)")

    # 미디어 그룹으로 전송
    success = send_media_group(chat_id, existing)

    if success:
        # 게시 확인 버튼
        keyboard = {
            "inline_keyboard": [
                [{"text": "🚀 게시하기", "callback_data": f"publish:{food_key}"}],
                [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
            ]
        }
        send_message_with_keyboard(
            chat_id,
            "👆 미리보기입니다. 게시하시겠습니까?",
            keyboard
        )
    else:
        send_message(chat_id, "❌ 이미지 전송 실패")


def publish_to_instagram(chat_id: str, food_key: str):
    """인스타그램 게시 — API 호출만 (업로드 코드 없음)

    🔐 핵심 원칙 (2026-02-04):
    - Cloudinary 업로드는 body_ready 진입 시 이미 완료됨
    - 이 함수는 Instagram API 호출만 수행
    - 게시 실패 원인 = Instagram API 하나로 한정

    🔐 상태 Enum v1.0 규칙:
    1. 게시 성공 → posted 상태로 전이
    2. 게시 실패 → approved 유지 + post_failed 플래그
    3. ⚠️ 게시 실패 ≠ 반려 (rejected)
    """
    from core.cloudinary_prepare import is_cloudinary_ready, ensure_cloudinary_ready

    # 폴더 확인
    folder = find_folder_by_food_id(food_key)
    if not folder:
        send_message(chat_id, f"❌ 폴더 없음: {food_key}")
        return

    # ═══════════════════════════════════════════
    # STEP 1: Cloudinary 준비 상태 확인 (핵심!)
    # ═══════════════════════════════════════════
    ready, errors = is_cloudinary_ready(folder, food_key)

    if not ready:
        error_msg = "\n".join([f"• {e}" for e in errors])
        send_message(chat_id, f"""
⚠️ <b>게시 불가 — Cloudinary 준비 안 됨</b>

📂 콘텐츠: {food_key}

❌ 문제:
{error_msg}

Cloudinary 업로드 후 다시 시도하세요.
""")
        keyboard = {
            "inline_keyboard": [
                [{"text": "☁️ Cloudinary 업로드", "callback_data": f"upload_cloudinary:{food_key}"}],
                [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
            ]
        }
        send_message_with_keyboard(chat_id, "해결:", keyboard)
        return

    # ═══════════════════════════════════════════
    # STEP 2: metadata에서 image_urls 로드 (이미 검증됨)
    # ═══════════════════════════════════════════
    metadata_path = folder / "metadata.json"
    with open(metadata_path, 'r', encoding='utf-8') as f:
        metadata = json.load(f)

    image_urls = metadata.get("image_urls")

    # 🔴 타입 최종 확인 (방어 코드)
    if not isinstance(image_urls, list) or len(image_urls) < 2:
        send_message(chat_id, f"❌ image_urls 오류: type={type(image_urls).__name__}, count={len(image_urls) if isinstance(image_urls, list) else 'N/A'}")
        keyboard = {"inline_keyboard": [[{"text": "☁️ Cloudinary 재업로드", "callback_data": f"upload_cloudinary:{food_key}"}]]}
        send_message_with_keyboard(chat_id, "해결:", keyboard)
        return

    print(f"[DEBUG] image_urls 검증 통과: {len(image_urls)}개, type=list[str]")

    # ═══════════════════════════════════════════
    # STEP 3: 상태 확인 (approved 필수)
    # ═══════════════════════════════════════════
    status = metadata.get("status", "")
    if status != "approved":
        send_message(chat_id, f"⚠️ 승인되지 않은 콘텐츠입니다.\n\n현재 상태: {status}")
        keyboard = {
            "inline_keyboard": [
                [{"text": "✅ 승인하기", "callback_data": f"approve:{food_key}"}],
                [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
            ]
        }
        send_message_with_keyboard(chat_id, "먼저 승인이 필요합니다:", keyboard)
        return

    # ═══════════════════════════════════════════
    # STEP 4: 캡션 로드
    # ═══════════════════════════════════════════
    caption = metadata.get("caption", "")
    if not caption:
        caption_files = [
            folder / "caption_instagram.txt",
            folder / "caption.txt",
        ]
        for cf in caption_files:
            if cf.exists():
                caption = cf.read_text(encoding='utf-8').strip()
                break

    if not caption:
        send_message(chat_id, f"⚠️ 캡션이 없습니다: {food_key}")
        keyboard = {"inline_keyboard": [[{"text": "✏️ 캡션 추가", "callback_data": f"edit_caption:{food_key}"}]]}
        send_message_with_keyboard(chat_id, "해결:", keyboard)
        return

    # ✅ 모든 조건 충족 — 게시 진행 (Instagram API만!)
    send_message(chat_id, f"🚀 <b>게시 시작</b>: {food_key}\n\n☁️ Cloudinary: 준비됨 ✅\n📝 캡션: 준비됨 ✅\n\n📤 Instagram API 호출 중...")

    def run_publish():
        try:
            import asyncio
            import sys
            sys.path.insert(0, str(PROJECT_ROOT))

            from services.scripts.publishing.publish_content import publish_content

            # 비동기 함수 실행
            result = asyncio.run(publish_content(food_key, auto_retry=False))

            if result.get("success"):
                # 시뮬레이션 체크
                data = result.get("data", {})
                if data.get("simulated"):
                    send_message(chat_id, f"""
⚠️ <b>시뮬레이션 모드</b>

📁 음식: {food_key}
📤 상태: approved (유지)

❗ Instagram 토큰/계정ID가 설정되지 않았습니다.
.env 파일을 확인해주세요.
""")
                    return

                # 🔐 실제 성공 → posted 상태로 전이
                post_id = data.get("post_id", "")
                permalink = data.get("permalink", "")

                # ═══════════════════════════════════════════
                # 🔴 성공 판정 기준 1: media_id 존재
                # ═══════════════════════════════════════════
                if not post_id:
                    send_message(chat_id, f"❌ 게시 실패: media_id 없음")
                    return

                # ═══════════════════════════════════════════
                # 🔴 성공 판정 기준 2: metadata.json 업데이트
                # ═══════════════════════════════════════════
                folder = find_folder_by_food_id(food_key)
                if folder:
                    metadata_path = folder / "metadata.json"
                    if metadata_path.exists():
                        with open(metadata_path, 'r', encoding='utf-8') as f:
                            metadata = json.load(f)
                    else:
                        metadata = {"food_id": food_key}

                    metadata["status"] = "posted"
                    metadata["posted_at"] = datetime.now().isoformat()
                    metadata["instagram_media_id"] = post_id
                    metadata["instagram_url"] = permalink

                    with open(metadata_path, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)

                    print(f"[DEBUG] metadata.json 업데이트: status=posted, media_id={post_id}")

                    # ═══════════════════════════════════════════
                    # 🔴 성공 판정 기준 3: 폴더 이동 (4_posted)
                    # ═══════════════════════════════════════════
                    import shutil
                    posted_dir = PROJECT_ROOT / "contents" / "4_posted" / datetime.now().strftime("%Y-%m")
                    posted_dir.mkdir(parents=True, exist_ok=True)

                    new_folder = posted_dir / folder.name
                    if not new_folder.exists():
                        try:
                            shutil.move(str(folder), str(new_folder))
                            print(f"[DEBUG] 폴더 이동: {folder.name} → 4_posted/{datetime.now().strftime('%Y-%m')}/")
                        except Exception as move_err:
                            print(f"[DEBUG] 폴더 이동 실패 (무시): {move_err}")

                # ═══════════════════════════════════════════
                # ✅ 모든 검증 통과 → 성공
                # ═══════════════════════════════════════════
                send_message(chat_id, f"""
✅ <b>게시 완료!</b>

📁 음식: {food_key}
📤 Post ID: {post_id}
🔗 URL: {permalink or 'N/A'}
📍 상태: posted
📁 이동: 4_posted/{datetime.now().strftime('%Y-%m')}/

Instagram에서 확인하세요!
""")
            else:
                # 🔐 실패 → approved 유지 + post_failed 플래그
                error = result.get("error", "알 수 없는 오류")

                # metadata에 post_failed 플래그 설정
                update_metadata_status(
                    food_key,
                    "approved",  # 상태 유지!
                    post_failed=True,
                    post_failed_reason=error[:200],
                    post_failed_at=datetime.now().isoformat()
                )

                # 재시도 버튼 포함 메시지
                msg = f"""
⚠️ <b>게시 실패 (시스템 오류)</b>

📁 음식: {food_key}
📝 상태: approved (유지)
💬 오류: {error[:200]}

━━━━━━━━━━━━━━━━━━
ℹ️ 시스템 오류이므로 상태는 유지됩니다.
재시도하거나 나중에 다시 시도하세요.
"""
                keyboard = {
                    "inline_keyboard": [
                        [{"text": "🔄 재시도", "callback_data": f"publish:{food_key}"}],
                        [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
                    ]
                }
                send_message_with_keyboard(chat_id, msg, keyboard)
                return

        except Exception as e:
            import traceback
            error_detail = traceback.format_exc()
            print(f"[publish_to_instagram] 오류: {error_detail}")

            # 🔐 예외 발생 시에도 approved 유지
            update_metadata_status(
                food_key,
                "approved",
                post_failed=True,
                post_failed_reason=str(e)[:200],
                post_failed_at=datetime.now().isoformat()
            )

            msg = f"""
⚠️ <b>게시 실패 (시스템 오류)</b>

📁 음식: {food_key}
📝 상태: approved (유지)
💬 오류: {str(e)[:200]}

━━━━━━━━━━━━━━━━━━
재시도하거나 나중에 다시 시도하세요.
"""
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔄 재시도", "callback_data": f"publish:{food_key}"}],
                    [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
                ]
            }
            send_message_with_keyboard(chat_id, msg, keyboard)

    executor.submit(run_publish)


def handle_status(chat_id: str, args: list):
    """상태 확인"""
    if not args:
        send_message(chat_id, "❌ 음식 이름 필요\n예: /status 오리고기")
        return

    food_name = args[0]
    food_key = get_food_key(food_name)

    print(f"[DEBUG] handle_status: food_key={food_key}")

    # 폴더 찾기 (새 매핑 함수 사용)
    content_folder = find_folder_by_food_id(food_key)

    if not content_folder:
        send_message(chat_id, f"📭 {food_name}: 폴더 없음")
        return

    print(f"[DEBUG] content_folder: {content_folder}")

    cover = content_folder / f"{food_key}_00.png"
    # v2: metadata.json (v1 호환: {food_id}_00_metadata.json)
    metadata = content_folder / "metadata.json"
    if not metadata.exists():
        metadata = content_folder / f"{food_key}_00_metadata.json"
    body = list(content_folder.glob(f"{food_key}_0[1-9].png"))

    text = f"""
📦 <b>{food_name}</b> ({food_key})

📁 {content_folder.name}
🎨 표지: {'✅' if cover.exists() else '❌'}
📋 메타: {'✅' if metadata.exists() else '❌'}
📷 본문: {len(body)}장
"""
    send_message(chat_id, text)


def handle_list(chat_id: str):
    """목록"""
    safety_path = PROJECT_ROOT / "config/settings/food_safety.json"

    if not safety_path.exists():
        send_message(chat_id, "❌ 안전도 DB 없음")
        return

    safety = json.loads(safety_path.read_text())

    safe = len(safety.get('safe', []))
    caution = len(safety.get('caution', []))
    danger = len(safety.get('danger', []))

    text = f"""
📋 <b>음식 DB</b>

🟢 SAFE: {safe}개
🟡 CAUTION: {caution}개
🔴 DANGER: {danger}개

<b>생성 예시:</b>
/create duck
/create 오리고기
"""
    send_message(chat_id, text)


def handle_clean(chat_id: str, args: list):
    """폴더 정리 (F-FOLDER-CLEAN)"""
    from core.utils.folder_cleaner import clean_by_food_id, find_content_folder

    if not args:
        send_message(chat_id, "❌ 음식 이름 필요\n예: /정리 duck")
        return

    food_name = args[0]
    food_key = get_food_key(food_name)

    folder = find_content_folder(food_key)
    if not folder:
        send_message(chat_id, f"❌ 폴더 없음: {food_key}")
        return

    send_message(chat_id, f"🧹 폴더 정리 중: {folder.name}")

    result = clean_by_food_id(food_key)

    if result.get("error"):
        send_message(chat_id, f"❌ 오류: {result['error']}")
        return

    moved = len(result.get("moved", []))
    kept = len(result.get("kept", []))

    msg = f"""
✅ <b>폴더 정리 완료</b>

📁 {folder.name}
📦 아카이빙: {moved}개
📌 유지: {kept}개

<b>유지된 파일:</b>
"""
    for f in result.get("kept", [])[:6]:
        msg += f"• {f}\n"

    if moved > 0:
        msg += f"\n<b>아카이빙된 파일:</b>\n"
        for f in result.get("moved", [])[:4]:
            msg += f"• {f}\n"
        if moved > 4:
            msg += f"... 외 {moved - 4}개"

    send_message(chat_id, msg)


def handle_approve(chat_id: str, args: list):
    """
    PD 승인 - /승인 {food_id}

    🔐 LOOP 2 개선 (2026-02-04):
    1. metadata 없으면 자동 생성
    2. 상태 업데이트
    3. 폴더를 3_approved로 이동

    🔐 UX 매핑 v1.0:
    - 이미 본 이미지 → 다시 안 보여줌
    - 캡션 미리보기 표시
    - 버튼: [게시하기] [캡션 수정] [메인 메뉴]

    🔐 StateGuard v1.0:
    - 승인 전 필수 조건 검증
    - 이미지 4장 + 캡션 필수
    - Cloudinary 업로드 안 됐으면 안내
    """
    from core.publish_gate import approve_content, get_content_status
    from core.state_guard import StateGuard

    if not args:
        send_message(chat_id, "❌ 음식 ID 필요\n예: /승인 duck")
        return

    food_id = get_food_key(args[0])

    # 폴더 먼저 찾기
    folder = find_folder_by_food_id(food_id)
    if not folder:
        send_message(chat_id, f"❌ 폴더 없음: {food_id}")
        return

    current_status = get_content_status(food_id)

    # metadata 없으면 자동 생성
    if current_status == "unknown":
        print(f"[DEBUG] metadata 없음 → 자동 생성: {food_id}")
        create_default_metadata(food_id, folder)
        current_status = "generated"

    if current_status == "approved":
        send_message(chat_id, f"ℹ️ 이미 승인됨: {food_id}")
        return

    if current_status == "published":
        send_message(chat_id, f"ℹ️ 이미 게시됨: {food_id}")
        return

    # 🔐 StateGuard: 승인 전 체크리스트 검증
    guard_success, guard_errors = StateGuard.check_approval_ready(folder, food_id)

    if not guard_success:
        error_msg = "\n".join([f"• {e}" for e in guard_errors])
        send_message(chat_id, f"""
⚠️ <b>승인 불가 — 필수 조건 미충족</b>

📂 콘텐츠: {food_id}

❌ 누락 항목:
{error_msg}

위 항목을 해결한 후 다시 시도하세요.
""")
        # 에러에 따른 해결 버튼 제공
        keyboard_buttons = []
        if any("이미지" in e for e in guard_errors):
            keyboard_buttons.append([{"text": "🔄 이미지 재확인", "callback_data": f"send_preview:{food_id}"}])
        if any("캡션" in e for e in guard_errors):
            keyboard_buttons.append([{"text": "✏️ 캡션 추가", "callback_data": f"edit_caption:{food_id}"}])
        keyboard_buttons.append([{"text": "🔙 메인 메뉴", "callback_data": "show_main"}])

        keyboard = {"inline_keyboard": keyboard_buttons}
        send_message_with_keyboard(chat_id, "해결 방법:", keyboard)
        return

    # ✅ 모든 조건 충족 — 승인 진행
    # 1. metadata 상태 업데이트
    success = approve_content(food_id, approved_by="PD_telegram")

    if not success:
        # publish_gate 실패 시 직접 업데이트 시도
        success = update_metadata_status(
            food_id,
            "approved",
            pd_approved=True,
            approved_at=datetime.now().isoformat(),
            approved_by="PD_telegram"
        )

    if success:
        # 2. 폴더를 3_approved로 이동
        moved, move_msg = move_to_approved(food_id)

        send_message(chat_id, f"""
✅ <b>승인 완료</b>

📁 콘텐츠: {food_id}
📂 폴더: {folder.name}
🔄 이동: {move_msg}
⏰ 시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}
""")

        # Cloudinary 업로드 상태 확인 (경고만)
        cloud_success, _, _ = StateGuard.check_cloudinary_uploaded(folder, food_id)
        if not cloud_success:
            send_message(chat_id, """
⚠️ <b>Cloudinary 업로드 필요</b>

게시하려면 먼저 Cloudinary에 이미지를 업로드해야 합니다.
""")
            keyboard = {
                "inline_keyboard": [
                    [{"text": "☁️ Cloudinary 업로드", "callback_data": f"upload_cloudinary:{food_id}"}],
                    [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
                ]
            }
            send_message_with_keyboard(chat_id, "업로드 후 게시하세요:", keyboard)
            return

        # 🔐 UX 매핑 v1.0: 캡션 미리보기 (이미지 생략!)
        caption = load_caption(food_id)
        if caption:
            # 캡션이 너무 길면 줄임
            preview_caption = caption[:500] + "..." if len(caption) > 500 else caption
            send_message(chat_id, f"""
📝 <b>캡션 미리보기</b>

{preview_caption}
""")
        else:
            send_message(chat_id, "⚠️ 캡션 파일이 없습니다. 게시 전 캡션을 확인하세요.")

        # 게시 버튼 (미리보기 버튼 제거!)
        keyboard = {
            "inline_keyboard": [
                [{"text": "🚀 게시하기", "callback_data": f"publish:{food_id}"}],
                [{"text": "✏️ 캡션 수정", "callback_data": f"edit_caption:{food_id}"}],
                [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
            ]
        }
        send_message_with_keyboard(chat_id, "게시할 준비가 되었습니다:", keyboard)
    else:
        send_message(chat_id, f"❌ 승인 실패: {food_id}")


def handle_upload_cloudinary(chat_id: str, food_key: str):
    """
    Cloudinary 업로드 — 성공 판정 기준 강화

    🔐 성공 판정 체크리스트:
    1. URL 4개 확보
    2. URL https:// 형식 확인
    3. metadata.json 저장
    4. 저장 검증 (재로드)

    ⚠️ print("완료")는 절대 성공 기준이 아니다
    """
    send_message(chat_id, f"☁️ Cloudinary 업로드 중: {food_key}")

    def run_upload():
        try:
            # ═══════════════════════════════════════════
            # STEP 1: 폴더 및 이미지 파일 확인
            # ═══════════════════════════════════════════
            folder = find_folder_by_food_id(food_key)
            if not folder:
                send_message(chat_id, f"❌ 폴더 없음: {food_key}")
                return

            image_files = sorted(folder.glob(f"{food_key}_*.png"))
            image_files = [f for f in image_files if 'metadata' not in f.name.lower()]

            if len(image_files) < 4:
                send_message(chat_id, f"❌ 이미지 부족: {len(image_files)}장 (4장 필요)")
                return

            print(f"[DEBUG] 업로드 대상 이미지: {len(image_files)}장")

            # ═══════════════════════════════════════════
            # STEP 2: Cloudinary 업로드 실행
            # ═══════════════════════════════════════════
            import cloudinary
            import cloudinary.uploader

            cloudinary.config(
                cloud_name=os.environ.get('CLOUDINARY_CLOUD_NAME'),
                api_key=os.environ.get('CLOUDINARY_API_KEY'),
                api_secret=os.environ.get('CLOUDINARY_API_SECRET')
            )

            urls = []
            for img in image_files[:4]:
                result = cloudinary.uploader.upload(
                    str(img),
                    folder=f"project_sunshine/{food_key}",
                    public_id=img.stem,
                    overwrite=True
                )
                urls.append(result['secure_url'])
                print(f"[DEBUG] 업로드됨: {img.name} → {result['secure_url']}")

            # ═══════════════════════════════════════════
            # 🔴 성공 판정 기준 1: URL 개수 확인
            # ═══════════════════════════════════════════
            if len(urls) < 4:
                send_message(chat_id, f"❌ 업로드 실패: {len(urls)}장만 업로드됨 (4장 필요)")
                return

            # ═══════════════════════════════════════════
            # 🔴 성공 판정 기준 2: 타입 검증 (반드시 list[str])
            # ═══════════════════════════════════════════
            if not isinstance(urls, list):
                send_message(chat_id, f"❌ URLs 타입 오류: {type(urls).__name__} (list 필요)")
                return

            for i, url in enumerate(urls):
                if not isinstance(url, str):
                    send_message(chat_id, f"❌ urls[{i}] 타입 오류: {type(url).__name__} (str 필요)")
                    return

            print(f"[DEBUG] URL 타입 검증 통과: list[str], {len(urls)}개")

            # ═══════════════════════════════════════════
            # 🔴 성공 판정 기준 3: URL 유효성 확인
            # ═══════════════════════════════════════════
            invalid_urls = [u for u in urls if not u.startswith("https://")]
            if invalid_urls:
                send_message(chat_id, f"❌ 잘못된 URL 형식: {len(invalid_urls)}개")
                return

            # ═══════════════════════════════════════════
            # 🔴 성공 판정 기준 4: metadata.json 저장 (필수!)
            # ═══════════════════════════════════════════
            metadata_path = folder / "metadata.json"

            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    metadata = json.load(f)
            else:
                metadata = {"food_id": food_key}

            # 🔴 핵심: list로 저장 (타입 보장)
            metadata["image_urls"] = urls  # list[str]
            metadata["cloudinary_uploaded"] = True
            metadata["cloudinary_uploaded_at"] = datetime.now().isoformat()

            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)

            print(f"[DEBUG] metadata.json 저장됨: image_urls={len(urls)}개, type=list")

            # ═══════════════════════════════════════════
            # 🔴 성공 판정 기준 5: 저장 검증 (재로드 + 타입 체크)
            # ═══════════════════════════════════════════
            with open(metadata_path, 'r', encoding='utf-8') as f:
                verify_metadata = json.load(f)

            saved_urls = verify_metadata.get("image_urls")

            # 타입 검증
            if not isinstance(saved_urls, list):
                send_message(chat_id, f"❌ 저장 검증 실패: image_urls 타입={type(saved_urls).__name__} (list 필요)")
                return

            if len(saved_urls) < 4:
                send_message(chat_id, f"❌ 저장 검증 실패: {len(saved_urls)}개만 저장됨 (4개 필요)")
                return

            print(f"[DEBUG] 저장 검증 통과: image_urls={len(saved_urls)}개, type=list")

            # ═══════════════════════════════════════════
            # ✅ 모든 검증 통과 → 성공
            # ═══════════════════════════════════════════
            send_message(chat_id, f"""
✅ <b>Cloudinary 업로드 완료!</b>

📂 콘텐츠: {food_key}
🖼️ 이미지: {len(urls)}장
☁️ 저장소: project_sunshine/{food_key}
💾 metadata.json: 저장됨 ✅
🔍 타입 검증: list[str] ✅

이제 게시 가능합니다.
""")
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🚀 게시하기", "callback_data": f"publish:{food_key}"}],
                    [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
                ]
            }
            send_message_with_keyboard(chat_id, "다음 단계:", keyboard)

        except ImportError:
            send_message(chat_id, "❌ cloudinary 라이브러리 없음\n\npip install cloudinary 실행 필요")
        except Exception as e:
            import traceback
            print(f"[upload_cloudinary] 오류: {traceback.format_exc()}")
            send_message(chat_id, f"❌ Cloudinary 업로드 실패\n\n오류: {str(e)[:200]}")

    # 백그라운드 실행
    executor.submit(run_upload)


def handle_sync_command(chat_id: str, args: list):
    """동기화 명령 - /동기화 또는 /동기화 {food_id}"""
    from utils.sync_status import sync_content_status, sync_all_contents

    if args:
        # 특정 콘텐츠 동기화
        food_id = get_food_key(args[0])
        send_message(chat_id, f"🔄 동기화 중: {food_id}")

        try:
            result = sync_content_status(food_id)
            msg = f"""
🔄 <b>동기화 완료</b>

📁 콘텐츠: {food_id}
📊 상태: {result['final_status']}
📍 출처: {result['source']}
⏰ 시각: {result['synced_at'][:16]}
"""
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
                ]
            }
            send_message_with_keyboard(chat_id, msg, keyboard)
        except Exception as e:
            send_message(chat_id, f"❌ 동기화 오류: {str(e)[:200]}")
    else:
        # 전체 동기화
        send_message(chat_id, "🔄 전체 동기화 시작...")

        try:
            stats = sync_all_contents()
            msg = f"""
🔄 <b>전체 동기화 완료</b>

📊 처리: {stats['synced']}개
📤 이동: {stats['moved_to_posted']}개
❌ 오류: {stats['errors']}개
"""
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
                ]
            }
            send_message_with_keyboard(chat_id, msg, keyboard)
        except Exception as e:
            send_message(chat_id, f"❌ 동기화 오류: {str(e)[:200]}")


def handle_reject(chat_id: str, args: list):
    """PD 반려 - /반려 {food_id} {사유}"""
    from core.publish_gate import reject_content, get_content_status

    if len(args) < 1:
        send_message(chat_id, "❌ 음식 ID 필요\n예: /반려 duck 색상이_이상함")
        return

    food_id = get_food_key(args[0])
    reason = " ".join(args[1:]) if len(args) > 1 else "사유 미기재"

    current_status = get_content_status(food_id)

    if current_status == "unknown":
        send_message(chat_id, f"❌ 메타데이터 없음: {food_id}")
        return

    if current_status == "published":
        send_message(chat_id, f"❌ 이미 게시된 콘텐츠는 반려 불가: {food_id}")
        return

    success = reject_content(food_id, reason=reason, rejected_by="PD_telegram")

    if success:
        send_message(chat_id, f"""
🚫 <b>반려 완료</b>

📁 콘텐츠: {food_id}
📝 사유: {reason}
⏰ 시각: {datetime.now().strftime('%Y-%m-%d %H:%M')}

재생성이 필요합니다.
""")
        # 재생성 버튼 표시
        keyboard = {
            "inline_keyboard": [
                [{"text": "🔄 재생성", "callback_data": f"create:{food_id}"}],
                [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
            ]
        }
        send_message_with_keyboard(chat_id, "재생성하시겠습니까?", keyboard)
    else:
        send_message(chat_id, f"❌ 반려 처리 실패: {food_id}")


def handle_text_message(chat_id: str, text: str, user_name: str = "PD"):
    """
    일반 텍스트 메시지 처리 (키워드 명령 시스템)

    🔐 PD 확정 (2026-02-03):
    1. 5개 고정 intent 파싱 (REJECT, APPROVE, SYNC, STATUS, HELP)
    2. 인식되지 않으면 김부장에게 전달
    """
    from utils.command_executor import process_text_message
    from utils.forward_logger import log_forward, format_forward_message

    result = process_text_message(text)

    if result.data and result.data.get("forward_to_manager"):
        # 명령으로 인식되지 않음 → 김부장에게 전달
        log_forward({
            "chat_id": chat_id,
            "user_name": user_name,
            "text": text
        })

        forward_msg = format_forward_message(text, user_name)
        send_message(chat_id, forward_msg)
        return

    if result.message:
        send_message(chat_id, result.message)

    # 추가 UI 처리 (승인/반려 후 버튼 표시)
    if result.success and result.data:
        action = result.data.get("action")
        food_id = result.data.get("food_id")

        if action == "approved" and food_id:
            keyboard = {
                "inline_keyboard": [
                    [
                        {"text": "👀 미리보기", "callback_data": f"send_preview:{food_id}"},
                        {"text": "🚀 게시하기", "callback_data": f"publish:{food_id}"}
                    ],
                    [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
                ]
            }
            send_message_with_keyboard(chat_id, "다음 단계를 선택하세요:", keyboard)

        elif action == "rejected" and food_id:
            keyboard = {
                "inline_keyboard": [
                    [{"text": "🔄 재생성", "callback_data": f"create:{food_id}"}],
                    [{"text": "🔙 메인 메뉴", "callback_data": "show_main"}]
                ]
            }
            send_message_with_keyboard(chat_id, "재생성하시겠습니까?", keyboard)


def process_update(update: dict):
    """업데이트 처리"""
    # 버튼 클릭 (콜백)
    if 'callback_query' in update:
        handle_callback(update['callback_query'])
        return

    # 일반 메시지
    message = update.get('message', {})
    chat_id = str(message.get('chat', {}).get('id', ''))
    text = message.get('text', '')
    user = message.get('from', {})
    user_name = user.get('first_name', 'PD')

    if not chat_id or not text:
        return

    # 권한 체크
    if chat_id != ALLOWED_CHAT_ID:
        send_message(chat_id, "⛔ 권한 없음")
        return

    # 명령어 파싱 (슬래시 명령)
    if not text.startswith('/'):
        # 일반 텍스트 → 키워드 명령 시스템
        handle_text_message(chat_id, text, user_name)
        return

    parts = text.split()
    command = parts[0].lower().replace('/', '').split('@')[0]
    args = parts[1:]

    print(f"📥 명령: {command} {args}")

    # 한글 명령어 → 영어 매핑
    command_map = {
        '생성': 'create',
        '상태': 'status',
        '목록': 'list',
        '도움말': 'help',
        '정리': 'clean',
        '승인': 'approve',
        '반려': 'reject',
        '신고': 'report',
        '동기화': 'sync',
    }
    command = command_map.get(command, command)

    if command in ('help', 'start', '도움'):
        handle_help(chat_id)
    elif command == 'create':
        handle_create(chat_id, args)
    elif command == 'status':
        handle_status(chat_id, args)
    elif command == 'list':
        handle_list(chat_id)
    elif command == 'clean':
        handle_clean(chat_id, args)
    elif command == 'approve':
        handle_approve(chat_id, args)
    elif command == 'reject':
        handle_reject(chat_id, args)
    elif command == 'report':
        # /신고 {food_id}
        if args:
            show_report_menu(chat_id, get_food_key(args[0]))
        else:
            send_message(chat_id, "❌ 음식 ID 필요\n예: /신고 kale")
    elif command == 'sync':
        # /동기화 {food_id} 또는 전체 동기화
        handle_sync_command(chat_id, args)
    else:
        send_message(chat_id, f"❓ 알 수 없는 명령: {command}\n\n/도움말 로 확인")


def main():
    """메인 폴링 루프"""
    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN 없음")
        return

    print("=" * 50)
    print("🤖 Project Sunshine 봇 (Simple)")
    print("=" * 50)
    print(f"   Chat ID: {ALLOWED_CHAT_ID}")
    print(f"   시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    # 봇 정보 확인
    try:
        me = api_call('getMe')
        if me.get('ok'):
            print(f"✅ 봇: @{me['result'].get('username')}")

        # 기존 업데이트 정리
        api_call('deleteWebhook', {'drop_pending_updates': 'true'})
        print("✅ 웹훅 정리 완료")
    except Exception as e:
        print(f"⚠️ 초기화 오류: {e}")

    offset = 0
    print("✅ 폴링 시작... (Ctrl+C로 종료)")

    while True:
        try:
            result = api_call('getUpdates', {
                'offset': offset,
                'timeout': 30,
                'allowed_updates': json.dumps(['message', 'callback_query'])
            })

            if result.get('ok'):
                for update in result.get('result', []):
                    update_id = update.get('update_id', 0)
                    offset = update_id + 1

                    try:
                        process_update(update)
                    except Exception as e:
                        print(f"⚠️ 처리 오류: {e}")

        except urllib.error.URLError as e:
            print(f"⚠️ 네트워크 오류: {e}")
            time.sleep(5)
        except Exception as e:
            print(f"⚠️ 폴링 오류: {e}")
            time.sleep(5)


if __name__ == "__main__":
    main()
