#!/usr/bin/env python3
"""
pd_remote.py — PD 텔레그램 리모컨
Project Sunshine v1.0

[명령어]
  다음   — 게시 전 5개 목록 + 가장 낮은 번호 미리보기
  게시   — 미리보기 중인 항목 즉시 게시 (인스타+쓰레드)
  목록   — 승인대기 전체 목록
  현황   — 전체 현황 숫자

[실행]
  python3 pd_remote.py              # 포그라운드
  nohup python3 pd_remote.py &      # 백그라운드

Author: 최부장 (Claude Code)
Date: 2026-03-06
"""

import os
import sys
import json
import time
import requests
from datetime import datetime
from pathlib import Path

# 같은 폴더의 모듈 임포트
sys.path.insert(0, os.path.dirname(__file__))
from notion_sync import NotionSync, load_env
from notion_worker import (
    publish_to_instagram,
    publish_to_threads_only,
    find_content_folder,
)

# ============================================================
# 설정
# ============================================================

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"

TELEGRAM_CHAT_ID = "5360443525"
APPROVAL_TIMEOUT = 180  # 3분 (초)

# 마지막 미리보기 항목 (세션 상태)
last_preview = None
last_top5 = []


# ============================================================
# 로깅
# ============================================================

LOG_DIR = PROJECT_ROOT / "logs"
LOG_FILE = LOG_DIR / "pd_bot.log"


def log(message: str):
    """터미널 + 로그파일 동시 출력 (flush=True 필수)"""
    timestamp = datetime.now().strftime("%H:%M:%S")
    line = f"[{timestamp}] {message}"
    print(line, flush=True)  # flush=True — 즉시 출력

    # 로그파일에도 기록
    try:
        LOG_DIR.mkdir(exist_ok=True)
        with open(LOG_FILE, "a", encoding="utf-8") as f:
            f.write(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {message}\n")
    except:
        pass  # 로그 실패해도 계속 진행


# ============================================================
# 텔레그램 함수
# ============================================================

def get_token():
    return os.environ.get("TELEGRAM_BOT_TOKEN", "")


def send_text(text: str, reply_markup: dict = None):
    """텍스트 메시지 전송"""
    token = get_token()
    if not token:
        return None

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "text": text,
            "parse_mode": "HTML",
        }
        if reply_markup:
            data["reply_markup"] = reply_markup

        resp = requests.post(url, json=data, timeout=15)
        result = resp.json()
        return result.get("result", {}).get("message_id")
    except Exception as e:
        log(f"  ❌ 텍스트 전송 실패: {e}")
        return None


def send_photo(image_url: str, caption: str = ""):
    """사진 전송 (URL)"""
    token = get_token()
    if not token or not image_url:
        return None

    try:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        data = {
            "chat_id": TELEGRAM_CHAT_ID,
            "photo": image_url,
        }
        if caption:
            data["caption"] = caption[:1024]
            data["parse_mode"] = "HTML"

        resp = requests.post(url, json=data, timeout=30)
        return resp.json().get("result", {}).get("message_id")
    except Exception as e:
        log(f"  ❌ 사진 전송 실패: {e}")
        return None


def send_local_photo(file_path: Path, caption: str = ""):
    """로컬 사진 파일 전송"""
    token = get_token()
    if not token or not file_path.exists():
        return None

    try:
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        with open(file_path, 'rb') as f:
            files = {'photo': f}
            data = {"chat_id": TELEGRAM_CHAT_ID}
            if caption:
                data["caption"] = caption[:1024]
                data["parse_mode"] = "HTML"

            resp = requests.post(url, data=data, files=files, timeout=60)
        return resp.json().get("result", {}).get("message_id")
    except Exception as e:
        log(f"  ❌ 로컬 사진 전송 실패: {e}")
        return None


def get_updates(last_update_id: int, timeout: int = 30):
    """새 메시지 가져오기"""
    token = get_token()
    if not token:
        return []

    try:
        url = f"https://api.telegram.org/bot{token}/getUpdates"
        params = {
            "offset": last_update_id + 1,
            "timeout": timeout,
            "allowed_updates": ["message", "callback_query"]
        }
        resp = requests.get(url, params=params, timeout=timeout + 10)
        return resp.json().get("result", [])
    except:
        return []


def answer_callback(callback_id: str, text: str = ""):
    """콜백 응답"""
    token = get_token()
    if not token:
        return

    try:
        url = f"https://api.telegram.org/bot{token}/answerCallbackQuery"
        requests.post(url, json={
            "callback_query_id": callback_id,
            "text": text
        }, timeout=10)
    except:
        pass


# ============================================================
# 이미지 가져오기
# ============================================================

def get_carousel_images(number: int, food_name_en: str):
    """
    캐러셀 이미지 4장 경로 가져오기
    반환: [커버, Food, DogWithFood, CTA] 경로 리스트

    신규 구조: images/01_insta&threads/
    레거시: 01_Insta&Thread/
    """
    content_folder = find_content_folder(number, food_name_en)
    if not content_folder:
        return []

    # 신규 구조: images/01_insta&threads/
    insta_folder = content_folder / "images" / "01_insta&threads"

    # 레거시 구조: 01_Insta&Thread/
    if not insta_folder.exists():
        insta_folder = content_folder / "01_Insta&Thread"

    if not insta_folder.exists():
        return []

    images = []
    patterns = [
        ["*01*Cover*", "*Cover*", "slide_01*"],
        ["*02*Food*", "*Food*", "slide_02*"],
        ["*03*DogWithFood*", "*DogWithFood*", "slide_03*"],
        ["*04*Cta*", "*09*Cta*", "*Cta*", "slide_04*"],
    ]

    for pattern_list in patterns:
        found = None
        for pattern in pattern_list:
            matches = [f for f in insta_folder.glob(pattern)
                      if f.suffix.lower() in ['.png', '.jpg', '.jpeg']]
            if matches:
                found = matches[0]
                break
        if found:
            images.append(found)

    return images


def get_captions(number: int, food_name_en: str):
    """
    캡션 파일 읽기
    반환: {"insta": "...", "threads": "..."}

    신규 구조: captions/
    레거시: 01_Insta&Thread/
    """
    content_folder = find_content_folder(number, food_name_en)
    if not content_folder:
        return {"insta": "", "threads": ""}

    # 신규 구조: captions/
    caption_folder = content_folder / "captions"

    # 레거시 구조: 01_Insta&Thread/
    if not caption_folder.exists():
        caption_folder = content_folder / "01_Insta&Thread"

    if not caption_folder.exists():
        return {"insta": "", "threads": ""}

    result = {"insta": "", "threads": ""}

    # 인스타 캡션
    for f in caption_folder.glob("*_Insta_Caption.txt"):
        with open(f, 'r', encoding='utf-8') as file:
            result["insta"] = file.read().strip()
        break

    # 쓰레드 캡션
    for f in caption_folder.glob("*_Threads_Caption.txt"):
        with open(f, 'r', encoding='utf-8') as file:
            result["threads"] = file.read().strip()
        break

    # 쓰레드 캡션 없으면 인스타 캡션 사용
    if not result["threads"]:
        result["threads"] = result["insta"]

    return result


# ============================================================
# 게시 완료 썸네일 가져오기
# ============================================================

def fetch_post_thumbnail(post_url: str):
    """
    Instagram Graph API로 게시물 썸네일 가져오기.

    반환: 이미지 URL 또는 None
    """
    if not post_url:
        return None

    # post_url에서 post_id 추출 시도
    # 형식: https://instagram.com/p/{media_id} 또는 media ID 직접
    import re

    # 실제로는 permalink에서 shortcode를 가져오는데,
    # 우리 코드에서 반환하는 post_url은 media_id 기반
    # https://instagram.com/p/{media_id} → media_id 추출

    match = re.search(r'/p/(\d+)', post_url)
    if match:
        media_id = match.group(1)
    else:
        # URL 전체가 ID인 경우
        media_id = post_url.split('/')[-1] if '/' in post_url else post_url

    if not media_id:
        return None

    ig_token = os.environ.get('INSTAGRAM_ACCESS_TOKEN')
    if not ig_token:
        return None

    try:
        url = (
            f"https://graph.facebook.com/v18.0/{media_id}"
            f"?fields=thumbnail_url,media_url,permalink"
            f"&access_token={ig_token}"
        )
        resp = requests.get(url, timeout=15)
        data = resp.json()

        image_url = data.get("media_url") or data.get("thumbnail_url")
        return image_url
    except Exception as e:
        log(f"⚠️ 썸네일 조회 실패: {e}")
        return None


def send_publish_confirmation(insta_url: str, threads_url: str, num: int, name: str):
    """
    게시 완료 후 썸네일 전송.
    """
    log(f"📸 게시 확인 썸네일 전송...")

    # Instagram 썸네일 가져오기
    thumbnail = fetch_post_thumbnail(insta_url)

    if thumbnail:
        caption = (
            f"✅ <b>게시 확인</b>\n\n"
            f"📸 인스타: {insta_url}\n"
            f"🧵 쓰레드: {threads_url}"
        )
        send_photo(thumbnail, caption)
        log(f"✅ 썸네일 전송 완료")
    else:
        log(f"⚠️ 썸네일 없음 — URL로 대체")


# ============================================================
# 명령어: 다음 (안전도 선택 → 콘텐츠 목록)
# ============================================================

def cmd_다음(sync: NotionSync):
    """안전도 선택 버튼 표시"""
    # 각 안전도별 미제작 개수 조회
    미제작_전체 = sync.poll_status_changes("미제작", field="인스타_상태")

    safe_count = len([x for x in 미제작_전체 if x.get("안전도") == "SAFE"])
    caution_count = len([x for x in 미제작_전체 if x.get("안전도") == "CAUTION"])
    forbidden_count = len([x for x in 미제작_전체 if x.get("안전도") == "FORBIDDEN"])

    if not 미제작_전체:
        send_text("📭 게시 전 항목이 없습니다")
        return

    # 안전도 선택 버튼
    keyboard = {
        "inline_keyboard": [
            [
                {"text": f"🟢 SAFE ({safe_count})", "callback_data": "safety:SAFE"},
            ],
            [
                {"text": f"🟡 CAUTION ({caution_count})", "callback_data": "safety:CAUTION"},
            ],
            [
                {"text": f"🔴 FORBIDDEN ({forbidden_count})", "callback_data": "safety:FORBIDDEN"},
            ],
        ]
    }

    msg = "━━━━━━━━━━━━━━━━━━\n"
    msg += "📋 <b>안전도 선택</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += f"🟢 SAFE: {safe_count}건\n"
    msg += f"🟡 CAUTION: {caution_count}건\n"
    msg += f"🔴 FORBIDDEN: {forbidden_count}건\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += "게시할 안전도를 선택하세요:"

    send_text(msg, reply_markup=keyboard)


def cmd_다음_by_safety(sync: NotionSync, safety: str):
    """선택된 안전도의 게시 전 5개 목록 + 미리보기"""
    global last_preview, last_top5

    # 안전도 이모지
    safety_emoji = {"SAFE": "🟢", "CAUTION": "🟡", "FORBIDDEN": "🔴"}.get(safety, "")

    # 1. 해당 안전도의 미제작 조회 (번호 낮은 순)
    미제작 = sync.poll_status_changes("미제작", field="인스타_상태")
    미제작_filtered = [x for x in 미제작 if x.get("안전도") == safety]
    미제작_filtered.sort(key=lambda x: x.get("번호", 999))
    top5 = 미제작_filtered[:5]
    last_top5 = top5

    if not top5:
        send_text(f"📭 {safety_emoji} {safety} 게시 전 항목이 없습니다")
        return

    # 2. 목록 텍스트 전송
    msg = "━━━━━━━━━━━━━━━━━━\n"
    msg += f"📋 <b>{safety_emoji} {safety} 게시 전 (5개)</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    for i, item in enumerate(top5):
        num = item.get("번호", 0)
        name = item.get("음식명", "")
        msg += f"{i+1}. [{num:03d}] {name}\n"
    msg += "━━━━━━━━━━━━━━━━━━"
    send_text(msg)

    # 3. 1번 항목 미리보기
    target = top5[0]
    send_preview(target, top5, sync)


def send_preview(target: dict, top5: list, sync: NotionSync):
    """항목 미리보기 전송 (이미지 4장 + 캡션 + 버튼)"""
    global last_preview
    last_preview = target

    num = target.get("번호", 0)
    name = target.get("음식명", "")
    name_en = target.get("음식명_EN", "")
    page_id = target.get("page_id", "")

    send_text(f"▶ <b>[{num:03d}] {name}</b> 미리보기를 전송합니다")

    # 4. 캐러셀 4장 전송
    images = get_carousel_images(num, name_en)
    if images:
        labels = ["📸 1. 커버", "📸 2. Food", "📸 3. DogWithFood", "📸 4. CTA"]
        for i, img_path in enumerate(images):
            label = labels[i] if i < len(labels) else f"📸 {i+1}"
            send_local_photo(img_path, label)
            time.sleep(0.3)
    else:
        send_text("⚠️ 이미지 없음")

    # 5. 캡션 전송
    captions = get_captions(num, name_en)

    if captions["insta"]:
        # 캡션이 길면 앞부분만
        insta_preview = captions["insta"][:2000]
        if len(captions["insta"]) > 2000:
            insta_preview += "\n...(생략)"
        send_text(f"📸 <b>인스타 캡션:</b>\n\n{insta_preview}")

    if captions["threads"]:
        threads_preview = captions["threads"][:2000]
        if len(captions["threads"]) > 2000:
            threads_preview += "\n...(생략)"
        send_text(f"🧵 <b>쓰레드 캡션:</b>\n\n{threads_preview}")

    # 6. 승인/반려 + 번호 선택 버튼
    buttons = [
        [
            {"text": "✅ 승인 (즉시 게시)", "callback_data": f"approve:{page_id[:30]}"},
            {"text": "❌ 반려", "callback_data": f"reject:{page_id[:30]}"},
        ]
    ]

    # 2번, 3번 선택 버튼
    select_row = []
    if len(top5) > 1:
        item2 = top5[1]
        select_row.append({
            "text": f"📌 2번 {item2.get('음식명', '')[:6]}",
            "callback_data": f"select:1:{item2.get('page_id', '')[:25]}"
        })
    if len(top5) > 2:
        item3 = top5[2]
        select_row.append({
            "text": f"📌 3번 {item3.get('음식명', '')[:6]}",
            "callback_data": f"select:2:{item3.get('page_id', '')[:25]}"
        })
    if select_row:
        buttons.append(select_row)

    keyboard = {"inline_keyboard": buttons}
    send_text("━━━━━━━━━━━━━━━━━━\n⏱ <b>3분 후 자동 게시</b>\n━━━━━━━━━━━━━━━━━━",
              reply_markup=keyboard)


# ============================================================
# 명령어: 게시
# ============================================================

def cmd_게시(sync: NotionSync):
    """미리보기 중인 항목 즉시 게시"""
    global last_preview

    if not last_preview:
        send_text("❌ 먼저 '다음'으로 미리보기를 확인하세요")
        return

    publish_both(last_preview, sync)


# ============================================================
# 명령어: 목록
# ============================================================

def cmd_목록(sync: NotionSync):
    """승인대기 전체 목록"""
    승인대기 = sync.poll_status_changes("승인대기", field="인스타_상태")
    승인대기.sort(key=lambda x: x.get("번호", 999))

    if not 승인대기:
        send_text("📭 승인대기 항목이 없습니다")
        return

    msg = f"📋 <b>승인대기 목록 ({len(승인대기)}건)</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    for i, item in enumerate(승인대기[:20]):  # 최대 20개
        num = item.get("번호", 0)
        name = item.get("음식명", "")
        safety = item.get("안전도", "")
        msg += f"{i+1}. [{num:03d}] {name} — {safety}\n"

    if len(승인대기) > 20:
        msg += f"... 외 {len(승인대기) - 20}건"

    send_text(msg)


# ============================================================
# 명령어: 현황
# ============================================================

def cmd_현황(sync: NotionSync):
    """전체 현황 숫자"""
    게시완료 = sync.poll_status_changes("게시완료", field="인스타_상태")
    승인대기 = sync.poll_status_changes("승인대기", field="인스타_상태")
    미제작 = sync.poll_status_changes("미제작", field="인스타_상태")

    today = datetime.now().strftime("%Y-%m-%d")

    msg = f"📊 <b>현황</b> ({today})\n"
    msg += "━━━━━━━━━━━━━━━━━━\n"
    msg += f"게시완료: <b>{len(게시완료)}건</b>\n"
    msg += f"승인대기: <b>{len(승인대기)}건</b>\n"
    msg += f"게시 전: <b>{len(미제작)}건</b>\n"
    msg += "━━━━━━━━━━━━━━━━━━"

    send_text(msg)


# ============================================================
# 게시 (인스타 + 쓰레드 동시)
# ============================================================

def publish_both(item: dict, sync: NotionSync):
    """인스타 + 쓰레드 동시 게시 (실시간 진행 알림)"""
    global last_preview

    page_id = item.get("page_id", "")
    num = item.get("번호", 0)
    name = item.get("음식명", "")
    name_en = item.get("음식명_EN", "")

    # ━━━ 시작 알림 ━━━
    log(f"🔔 승인 수신: [{num:03d}] {name}")
    send_text(f"🔄 <b>[{num:03d}] {name}</b> 게시 시작...")

    # 동시 게시 방지 (상태 잠금)
    sync.update_status(page_id, "게시중", field="인스타_상태")
    sync.update_status(page_id, "게시중", field="쓰레드_상태")

    insta_url = ""
    threads_url = ""
    insta_success = False
    thread_success = False

    try:
        # ━━━ 인스타 게시 ━━━
        log(f"📤 인스타 게시 시작...")
        send_text("📤 인스타 업로드 중...")

        insta = publish_to_instagram(
            page_id=page_id,
            food_name_kr=name,
            food_name_en=name_en,
            number=num
        )

        insta_url = insta.get("post_url", "")
        insta_success = insta.get("success", False)

        if insta_success:
            sync.record_publish(page_id, insta_url, field="인스타_상태")
            log(f"✅ 인스타 완료: {insta_url}")
            send_text("✅ 인스타 완료!")
        else:
            error_msg = insta.get("error", "알 수 없음")
            sync.update_status(page_id, "오류", error_msg, field="인스타_상태")
            log(f"❌ 인스타 실패: {error_msg}")
            send_text(f"❌ 인스타 실패: {error_msg[:100]}")

        # ━━━ 쓰레드 게시 ━━━
        log(f"📤 쓰레드 게시 시작...")
        send_text("📤 쓰레드 업로드 중...")

        thread = publish_to_threads_only(
            page_id=page_id,
            food_name_kr=name,
            food_name_en=name_en,
            number=num
        )

        threads_url = thread.get("threads_url", "")
        thread_success = thread.get("success", False)

        if thread_success:
            sync.record_publish(page_id, threads_url, field="쓰레드_상태")
            log(f"✅ 쓰레드 완료: {threads_url}")
            send_text("✅ 쓰레드 완료!")
        else:
            error_msg = thread.get("error", "알 수 없음")
            sync.update_status(page_id, "오류", error_msg, field="쓰레드_상태")
            log(f"❌ 쓰레드 실패: {error_msg}")
            send_text(f"❌ 쓰레드 실패: {error_msg[:100]}")

        # ━━━ 노션 업데이트 알림 ━━━
        log(f"📝 노션 상태 업데이트...")
        send_text("📝 노션 상태 업데이트 중...")

        # ━━━ 최종 완료 알림 ━━━
        log(f"🎉 게시 완료: [{num:03d}] {name}")
        result_msg = f"🎉 <b>[{num:03d}] {name}</b> 게시 완료!\n\n"
        result_msg += f"📸 인스타: {insta_url if insta_success else '실패'}\n"
        result_msg += f"🧵 쓰레드: {threads_url if thread_success else '실패'}"
        send_text(result_msg)

        # ━━━ 게시 확인 썸네일 전송 ━━━
        if insta_success and insta_url:
            send_publish_confirmation(insta_url, threads_url, num, name)

        # 미리보기 초기화
        last_preview = None

    except Exception as e:
        log(f"❌ 게시 오류: {e}")
        sync.update_status(page_id, "오류", str(e), field="인스타_상태")
        send_text(f"❌ 게시 오류: {str(e)[:200]}")


def reject_item(item: dict, sync: NotionSync):
    """항목 반려"""
    global last_preview

    page_id = item.get("page_id", "")
    num = item.get("번호", 0)
    name = item.get("음식명", "")

    sync.update_status(page_id, "수정필요", field="인스타_상태")
    sync.update_status(page_id, "수정필요", field="쓰레드_상태")

    send_text(f"❌ <b>[{num:03d}] {name}</b> 반려됨\n\n노션 PD_메모에 수정사항을 작성해주세요.")
    log(f"❌ 반려: [{num:03d}] {name}")

    last_preview = None


# ============================================================
# 메인 루프
# ============================================================

def main():
    global last_preview, last_top5

    load_env()

    token = get_token()
    if not token:
        print("❌ TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.", flush=True)
        return

    sync = NotionSync()
    if not sync.client:
        print("❌ Notion API 연결 실패", flush=True)
        return

    log("=" * 50)
    log("🤖 PD 리모컨 봇 시작")
    log("=" * 50)
    log(f"Chat ID: {TELEGRAM_CHAT_ID}")
    log("명령어: 다음 / 게시 / 목록 / 현황")
    log("종료: Ctrl+C")
    log("=" * 50)

    send_text("🌻 <b>PD 리모컨 시작!</b>\n\n명령어:\n• 다음 — 미리보기\n• 게시 — 즉시 게시\n• 목록 — 승인대기 목록\n• 현황 — 통계")

    last_update_id = 0
    approval_start_time = None
    approval_target = None

    try:
        while True:
            updates = get_updates(last_update_id, timeout=10)

            for update in updates:
                last_update_id = update.get("update_id", 0)

                # 콜백 쿼리 (버튼 클릭)
                if "callback_query" in update:
                    callback = update["callback_query"]
                    callback_id = callback["id"]
                    data = callback.get("data", "")
                    from_id = str(callback.get("from", {}).get("id", ""))

                    # 보안: PD만 허용
                    if from_id != TELEGRAM_CHAT_ID:
                        answer_callback(callback_id, "권한 없음")
                        continue

                    answer_callback(callback_id, "처리 중...")
                    log(f"🔘 버튼 클릭: {data[:30]}")

                    if data.startswith("approve:"):
                        # 승인
                        log("✅ [승인] 버튼 수신")
                        if last_preview:
                            publish_both(last_preview, sync)
                        approval_start_time = None

                    elif data.startswith("reject:"):
                        # 반려
                        log("❌ [반려] 버튼 수신")
                        if last_preview:
                            reject_item(last_preview, sync)
                        approval_start_time = None

                    elif data.startswith("safety:"):
                        # 안전도 선택
                        safety = data.split(":")[1]
                        log(f"🎨 안전도 선택: {safety}")
                        cmd_다음_by_safety(sync, safety)
                        # 1번 항목 자동 미리보기
                        if last_top5:
                            send_preview(last_top5[0], last_top5, sync)
                            approval_start_time = time.time()
                            approval_target = last_top5[0]

                    elif data.startswith("select:"):
                        # 번호 선택
                        parts = data.split(":")
                        if len(parts) >= 2:
                            idx = int(parts[1])
                            log(f"📌 [{idx+1}번] 선택")
                            if idx < len(last_top5):
                                send_preview(last_top5[idx], last_top5, sync)
                                approval_start_time = time.time()
                                approval_target = last_top5[idx]

                # 일반 메시지
                elif "message" in update:
                    message = update["message"]
                    chat_id = str(message.get("chat", {}).get("id", ""))
                    text = message.get("text", "").strip()

                    # 보안: PD만 허용
                    if chat_id != TELEGRAM_CHAT_ID:
                        continue

                    # 한글 명령어
                    if text == "다음":
                        log(f"📩 명령어 수신: '{text}'")
                        cmd_다음(sync)
                        # 안전도 선택 후 approval 시작 (콜백에서 처리)

                    elif text == "게시":
                        log(f"📩 명령어 수신: '{text}'")
                        cmd_게시(sync)
                        approval_start_time = None

                    elif text == "목록":
                        log(f"📩 명령어 수신: '{text}'")
                        cmd_목록(sync)

                    elif text == "현황":
                        log(f"📩 명령어 수신: '{text}'")
                        cmd_현황(sync)

                    elif text in ["/start", "/menu", "시작", "메뉴"]:
                        log(f"📩 명령어 수신: '{text}'")
                        send_text("🌻 <b>PD 리모컨</b>\n\n• 다음 — 미리보기\n• 게시 — 즉시 게시\n• 목록 — 승인대기 목록\n• 현황 — 통계")

            # 3분 타임아웃 체크
            if approval_start_time and approval_target:
                elapsed = time.time() - approval_start_time
                if elapsed >= APPROVAL_TIMEOUT:
                    log("⏱ 3분 타임아웃 → 자동 게시 시작")
                    send_text("⏱ 3분 무응답 → 자동 게시")
                    publish_both(approval_target, sync)
                    approval_start_time = None
                    approval_target = None

    except KeyboardInterrupt:
        log("봇 종료...")
        send_text("👋 PD 리모컨 종료")


if __name__ == "__main__":
    main()
