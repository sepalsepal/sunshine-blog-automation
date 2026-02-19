#!/usr/bin/env python3 -u
"""
Project Sunshine 텔레그램 봇
PD님이 텔레그램에서 직접 명령 가능

명령어:
  /create [음식] - 콘텐츠 생성
  /status [음식] - 진행 상태 확인
  /list - 대기 중인 콘텐츠
  /help - 명령어 안내
"""

import os
import sys
import json
import asyncio
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor

# 버퍼링 비활성화 (로그 즉시 출력)
sys.stdout.reconfigure(line_buffering=True)
sys.stderr.reconfigure(line_buffering=True)

# 프로젝트 루트 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

# 환경변수 로드
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / '.env')

TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
ALLOWED_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID', '5360443525')

# 스레드 풀 (파이프라인 실행용)
executor = ThreadPoolExecutor(max_workers=2)

# 한글 → 영문 음식 매핑
FOOD_MAPPING = {
    # 과일
    "사과": "apple",
    "바나나": "banana",
    "블루베리": "blueberry",
    "체리": "cherry",
    "망고": "mango",
    "오렌지": "orange",
    "복숭아": "peach",
    "배": "pear",
    "파인애플": "pineapple",
    "딸기": "strawberry",
    "수박": "watermelon",
    "키위": "kiwi",
    "파파야": "papaya",
    "포도": "grape",
    "블랙베리": "blackberry",
    # 채소
    "브로콜리": "broccoli",
    "당근": "carrot",
    "오이": "cucumber",
    "호박": "pumpkin",
    "고구마": "sweet_potato",
    "감자": "potato",
    "시금치": "spinach",
    "양배추": "cabbage",
    "케일": "kale",
    "셀러리": "celery",
    "애호박": "zucchini",
    "우엉": "burdock",
    # 단백질
    "닭고기": "chicken",
    "소고기": "beef",
    "돼지고기": "pork",
    "오리고기": "duck",
    "칠면조": "turkey",
    "연어": "salmon",
    "참치": "tuna",
    "고등어": "mackerel",
    "새우": "shrimp",
    "삶은달걀": "boiled_egg",
    "달걀": "egg",
    "두부": "tofu",
    "치즈": "cheese",
    "요거트": "yogurt",
    "삼겹살": "samgyeopsal",
    # 기타
    "쌀": "rice",
    "아보카도": "avocado",
    "올리브": "olive",
    "소시지": "sausage",
    # 위험 식품
    "초콜릿": "chocolate",
    "아이스크림": "icecream",
    "콜라": "coca_cola",
    "버드와이저": "budweiser",
    "프링글스": "pringles",
    "킷캣": "kitkat",
    "양념치킨": "yangnyeom",
}


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 유틸리티 함수
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

def is_authorized(update: Update) -> bool:
    """PD님 채팅만 허용"""
    return str(update.effective_chat.id) == ALLOWED_CHAT_ID


def get_food_key(food_name: str) -> str:
    """한글 → 영문 변환 (이미 영문이면 그대로)"""
    return FOOD_MAPPING.get(food_name, food_name)


def find_content_folder(food_key: str) -> Path | None:
    """콘텐츠 폴더 찾기"""
    import re
    images_dir = PROJECT_ROOT / 'content/images'

    if not images_dir.exists():
        return None

    # 정확한 매칭: {번호}_{food_key}_ 패턴
    exact_pattern = re.compile(rf'^\d{{3}}_{food_key}_')
    for folder in sorted(images_dir.iterdir()):
        if folder.is_dir() and exact_pattern.match(folder.name):
            return folder

    return None


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# /도움 명령어
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """명령어 안내"""
    if not is_authorized(update):
        await update.message.reply_text("⛔ 권한이 없습니다.")
        return

    help_text = """
🐕 <b>Project Sunshine 봇</b>

<b>명령어 목록:</b>

/create [음식] - 콘텐츠 생성
  예: /create 오리고기
  예: /create duck

/status [음식] - 진행 상태 확인
  예: /status 오리고기

/list - 생성 가능한 콘텐츠 목록

/safety - 음식 안전도 DB 확인

/help - 이 안내 메시지

<b>참고:</b>
음식명은 한글/영문 모두 가능합니다.
"""
    await update.message.reply_text(help_text, parse_mode='HTML')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# /생성 명령어
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def create_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """콘텐츠 생성"""
    if not is_authorized(update):
        await update.message.reply_text("⛔ 권한이 없습니다.")
        return

    # 음식 이름 파싱
    if not context.args:
        await update.message.reply_text(
            "❌ 음식 이름을 입력해주세요.\n\n예: /생성 오리고기\n예: /생성 duck"
        )
        return

    food_name = context.args[0]
    food_key = get_food_key(food_name)

    # 시작 알림
    start_msg = await update.message.reply_text(
        f"🚀 <b>콘텐츠 생성 시작</b>\n\n"
        f"📦 음식: {food_name}\n"
        f"🔑 키: {food_key}\n"
        f"⏳ 처리 중...",
        parse_mode='HTML'
    )

    try:
        # 파이프라인 임포트
        from mcp.pipelines.auto_content import AutoContentPipeline

        pipeline = AutoContentPipeline()

        # 비동기 실행 (봇이 멈추지 않게)
        loop = asyncio.get_event_loop()
        success = await loop.run_in_executor(executor, pipeline.run, food_key, False)

        if success:
            # 성공 시 시작 메시지 수정
            await start_msg.edit_text(
                f"✅ <b>콘텐츠 생성 완료</b>\n\n"
                f"📦 음식: {food_name} ({food_key})\n"
                f"📊 상세 보고서는 별도 메시지로 전송됨",
                parse_mode='HTML'
            )
        else:
            await start_msg.edit_text(
                f"❌ <b>콘텐츠 생성 실패</b>\n\n"
                f"📦 음식: {food_name} ({food_key})\n"
                f"💡 /상태 {food_name} 으로 상세 확인",
                parse_mode='HTML'
            )

    except Exception as e:
        await start_msg.edit_text(
            f"❌ <b>생성 오류</b>\n\n"
            f"📦 음식: {food_name}\n"
            f"⚠️ 오류: {str(e)[:200]}",
            parse_mode='HTML'
        )


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# /상태 명령어
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def status_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """진행 상태 확인"""
    if not is_authorized(update):
        await update.message.reply_text("⛔ 권한이 없습니다.")
        return

    if not context.args:
        await update.message.reply_text(
            "❌ 음식 이름을 입력해주세요.\n\n예: /상태 오리고기"
        )
        return

    food_name = context.args[0]
    food_key = get_food_key(food_name)

    # 콘텐츠 폴더 확인
    content_folder = find_content_folder(food_key)

    if not content_folder:
        await update.message.reply_text(
            f"📭 <b>{food_name}</b> ({food_key})\n\n콘텐츠 폴더 없음",
            parse_mode='HTML'
        )
        return

    # 이미지 확인
    cover = content_folder / f"{food_key}_00.png"
    metadata = content_folder / f"{food_key}_00_metadata.json"
    body_images = list(content_folder.glob(f"{food_key}_0[1-9].png"))

    # 메타데이터 확인
    rule_info = "없음"
    if metadata.exists():
        try:
            meta = json.loads(metadata.read_text())
            rule_info = f"{meta.get('rule_name', '?')} ({meta.get('rule_hash', '?')[:8]})"
        except:
            rule_info = "파싱 오류"

    status_text = f"""
📦 <b>{food_name}</b> ({food_key})

📁 폴더: {content_folder.name}
🎨 표지: {'✅' if cover.exists() else '❌'}
📋 메타데이터: {'✅' if metadata.exists() else '❌'}
📐 규칙: {rule_info}
📷 본문: {len(body_images)}장
"""

    # 각 이미지 크기 표시
    if body_images:
        status_text += "\n<b>본문 이미지:</b>\n"
        for img in sorted(body_images):
            size_kb = img.stat().st_size / 1024
            status = "✅" if size_kb > 500 else "⚠️"
            status_text += f"  {status} {img.name} ({size_kb:.0f}KB)\n"

    await update.message.reply_text(status_text, parse_mode='HTML')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# /목록 명령어
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """생성 가능한 콘텐츠 목록"""
    if not is_authorized(update):
        await update.message.reply_text("⛔ 권한이 없습니다.")
        return

    # 안전도 DB에서 음식 목록 가져오기
    safety_path = PROJECT_ROOT / "config/settings/food_safety.json"

    if not safety_path.exists():
        await update.message.reply_text("❌ 안전도 DB 없음")
        return

    safety_db = json.loads(safety_path.read_text())

    # 이미 콘텐츠가 있는 음식 확인
    images_dir = PROJECT_ROOT / 'content/images'
    existing = set()

    if images_dir.exists():
        for folder in images_dir.iterdir():
            if folder.is_dir():
                parts = folder.name.split('_')
                if len(parts) >= 2:
                    existing.add(parts[1])

    text = "📋 <b>콘텐츠 현황</b>\n\n"

    # 안전 음식
    safe_foods = safety_db.get('safe', [])
    safe_with_content = [f for f in safe_foods if f in existing]
    safe_without_content = [f for f in safe_foods if f not in existing]

    text += f"<b>🟢 SAFE ({len(safe_foods)}개)</b>\n"
    text += f"  ✅ 완료: {len(safe_with_content)}개\n"
    text += f"  ⏳ 대기: {len(safe_without_content)}개\n\n"

    # 주의 음식
    caution_foods = safety_db.get('caution', [])
    caution_with_content = [f for f in caution_foods if f in existing]

    text += f"<b>🟡 CAUTION ({len(caution_foods)}개)</b>\n"
    text += f"  ✅ 완료: {len(caution_with_content)}개\n\n"

    # 위험 음식
    danger_foods = safety_db.get('danger', [])
    danger_with_content = [f for f in danger_foods if f in existing]

    text += f"<b>🔴 DANGER ({len(danger_foods)}개)</b>\n"
    text += f"  ✅ 완료: {len(danger_with_content)}개\n\n"

    # 최근 생성 가능한 음식 5개
    if safe_without_content:
        text += "<b>💡 생성 추천:</b>\n"
        for food in safe_without_content[:5]:
            korean = next((k for k, v in FOOD_MAPPING.items() if v == food), food)
            text += f"  • /생성 {korean}\n"

    await update.message.reply_text(text, parse_mode='HTML')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# /안전도 명령어
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def safety_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """음식 안전도 확인"""
    if not is_authorized(update):
        await update.message.reply_text("⛔ 권한이 없습니다.")
        return

    safety_path = PROJECT_ROOT / "config/settings/food_safety.json"

    if not safety_path.exists():
        await update.message.reply_text("❌ 안전도 DB 없음")
        return

    safety_db = json.loads(safety_path.read_text())

    text = "🏷️ <b>음식 안전도 DB</b>\n\n"

    # SAFE
    safe_foods = safety_db.get('safe', [])
    text += f"<b>🟢 SAFE ({len(safe_foods)}개)</b>\n"
    text += ", ".join(safe_foods[:15])
    if len(safe_foods) > 15:
        text += f" 외 {len(safe_foods)-15}개"
    text += "\n\n"

    # CAUTION
    caution_foods = safety_db.get('caution', [])
    text += f"<b>🟡 CAUTION ({len(caution_foods)}개)</b>\n"
    text += ", ".join(caution_foods)
    text += "\n\n"

    # DANGER
    danger_foods = safety_db.get('danger', [])
    text += f"<b>🔴 DANGER ({len(danger_foods)}개)</b>\n"
    text += ", ".join(danger_foods)

    await update.message.reply_text(text, parse_mode='HTML')


# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
# 메인
# ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """에러 핸들러"""
    import logging
    logging.error(f"Exception: {context.error}")


def main():
    """봇 시작"""
    import time

    if not TOKEN:
        print("❌ TELEGRAM_BOT_TOKEN 없음")
        return

    print("=" * 50)
    print("🤖 Project Sunshine 텔레그램 봇")
    print("=" * 50)
    print(f"   허용된 Chat ID: {ALLOWED_CHAT_ID}")
    print(f"   시작 시간: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 50)

    max_retries = 3
    retry_delay = 10

    for attempt in range(max_retries):
        try:
            # 봇 생성
            app = Application.builder().token(TOKEN).build()

            # 에러 핸들러 등록
            app.add_error_handler(error_handler)

            # 명령어 핸들러 등록 (영문만 - 텔레그램 봇 API 제약)
            app.add_handler(CommandHandler("help", help_command))
            app.add_handler(CommandHandler("start", help_command))
            app.add_handler(CommandHandler("create", create_command))
            app.add_handler(CommandHandler("status", status_command))
            app.add_handler(CommandHandler("list", list_command))
            app.add_handler(CommandHandler("safety", safety_command))

            # 봇 실행 (폴링 방식)
            print(f"✅ 봇 실행 중... (시도 {attempt + 1}/{max_retries})")
            app.run_polling(
                allowed_updates=Update.ALL_TYPES,
                drop_pending_updates=True,
                poll_interval=2.0
            )
            break  # 정상 종료

        except Exception as e:
            print(f"⚠️ 봇 오류 (시도 {attempt + 1}): {e}")
            if attempt < max_retries - 1:
                print(f"   {retry_delay}초 후 재시도...")
                time.sleep(retry_delay)
            else:
                print("❌ 최대 재시도 초과, 봇 종료")
                raise


if __name__ == "__main__":
    main()
