#!/usr/bin/env python3
"""
텔레그램 봇 리모컨 v1.0
Project Sunshine - 터미널 원격 제어

기능:
- 파이프라인 상태 확인
- 콘텐츠 게시
- 데이터 동기화
- Instagram 통계 조회

사용법:
    python services/scripts/telegram_bot.py

Author: 송지영 대리
Date: 2026-01-30
"""

import os
import sys
import json
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 설정
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

import requests


class TelegramBotRemote:
    """텔레그램 봇 리모컨 클래스"""

    def __init__(self):
        self.bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        self.chat_id = os.getenv("TELEGRAM_CHAT_ID", "5360443525")
        self.base_url = f"https://api.telegram.org/bot{self.bot_token}"
        self.last_update_id = 0

        # 게시 가능한 콘텐츠 목록
        self.content_map = {
            "strawberry": "딸기",
            "mango": "망고",
            "orange": "오렌지",
            "pear": "배",
            "kiwi": "키위",
            "papaya": "파파야",
            "peach": "복숭아",
            "rice": "흰쌀밥",
            "cucumber": "오이",
            "pringles": "프링글스",
            "sausage": "소시지",
            "coca_cola": "코카콜라",
            "avocado": "아보카도",
            "olive": "올리브",
        }

        # 사용자 상태 (대화 컨텍스트)
        self.user_state = {}

    def is_configured(self) -> bool:
        return bool(self.bot_token)

    def send_message(self, text: str, reply_markup: dict = None) -> bool:
        """메시지 전송"""
        try:
            url = f"{self.base_url}/sendMessage"
            data = {
                "chat_id": self.chat_id,
                "text": text,
                "parse_mode": "HTML"
            }
            if reply_markup:
                data["reply_markup"] = json.dumps(reply_markup)

            response = requests.post(url, json=data, timeout=10)
            return response.status_code == 200
        except Exception as e:
            print(f"메시지 전송 실패: {e}")
            return False

    def get_updates(self, timeout: int = 30) -> list:
        """새 메시지 가져오기 (long polling)"""
        try:
            url = f"{self.base_url}/getUpdates"
            params = {
                "offset": self.last_update_id + 1,
                "timeout": timeout,
                "allowed_updates": ["message", "callback_query"]
            }
            response = requests.get(url, params=params, timeout=timeout + 10)

            if response.status_code == 200:
                data = response.json()
                return data.get("result", [])
            return []
        except Exception as e:
            print(f"업데이트 가져오기 실패: {e}")
            return []

    def answer_callback(self, callback_id: str, text: str = "") -> bool:
        """콜백 쿼리 응답"""
        try:
            url = f"{self.base_url}/answerCallbackQuery"
            response = requests.post(url, json={
                "callback_query_id": callback_id,
                "text": text
            }, timeout=10)
            return response.status_code == 200
        except:
            return False

    def show_main_menu(self):
        """메인 메뉴 표시"""
        keyboard = {
            "inline_keyboard": [
                [
                    {"text": "📊 상태 확인", "callback_data": "status"},
                    {"text": "🔄 동기화", "callback_data": "sync"}
                ],
                [
                    {"text": "📤 게시하기", "callback_data": "publish"},
                    {"text": "📈 통계", "callback_data": "stats"}
                ],
                [
                    {"text": "🎬 대시보드", "callback_data": "dashboard"},
                    {"text": "❓ 도움말", "callback_data": "help"}
                ]
            ]
        }

        self.send_message(
            "🌻 <b>Project Sunshine 리모컨</b>\n\n원하는 기능을 선택하세요:",
            reply_markup=keyboard
        )

    def show_publish_menu(self):
        """게시할 콘텐츠 선택 메뉴"""
        # 2열로 콘텐츠 버튼 배치
        buttons = []
        row = []
        for topic_en, topic_kr in self.content_map.items():
            row.append({"text": f"🍽️ {topic_kr}", "callback_data": f"pub_{topic_en}"})
            if len(row) == 2:
                buttons.append(row)
                row = []
        if row:
            buttons.append(row)

        buttons.append([{"text": "◀️ 뒤로", "callback_data": "menu"}])

        keyboard = {"inline_keyboard": buttons}
        self.send_message(
            "📤 <b>게시할 콘텐츠 선택</b>\n\n어떤 콘텐츠를 게시할까요?",
            reply_markup=keyboard
        )

    def handle_status(self):
        """파이프라인 상태 확인"""
        status_file = ROOT / "services/dashboard/status.json"

        if status_file.exists():
            with open(status_file, 'r', encoding='utf-8') as f:
                status = json.load(f)

            pipeline = status.get("pipeline", {})
            current_step = pipeline.get("current_step", "대기")
            is_running = pipeline.get("is_running", False)

            if is_running:
                msg = f"🔄 <b>파이프라인 실행 중</b>\n\n현재 단계: {current_step}"
            else:
                last_topic = pipeline.get("topic", "-")
                msg = f"✅ <b>파이프라인 대기 중</b>\n\n마지막 작업: {last_topic}"
        else:
            msg = "📊 상태 파일을 찾을 수 없습니다."

        keyboard = {"inline_keyboard": [[{"text": "◀️ 메뉴", "callback_data": "menu"}]]}
        self.send_message(msg, reply_markup=keyboard)

    def handle_sync(self):
        """데이터 동기화 실행"""
        self.send_message("🔄 데이터 동기화 중...")

        try:
            from core.utils.sync_manager import sync_all_data
            result = sync_all_data()

            added = result.get("added", 0)
            updated = result.get("updated", 0)

            msg = f"✅ <b>동기화 완료!</b>\n\n추가: {added}건\n업데이트: {updated}건"
        except Exception as e:
            msg = f"❌ 동기화 실패: {str(e)}"

        keyboard = {"inline_keyboard": [[{"text": "◀️ 메뉴", "callback_data": "menu"}]]}
        self.send_message(msg, reply_markup=keyboard)

    def handle_stats(self):
        """Instagram 통계 조회"""
        stats_file = ROOT / "config/data/instagram_stats.json"

        if stats_file.exists():
            with open(stats_file, 'r', encoding='utf-8') as f:
                stats = json.load(f)

            summary = stats.get("summary", {})
            account = stats.get("account", {})

            msg = f"""📈 <b>Instagram 통계</b>

👤 팔로워: {account.get('followers', 0)}명
📸 게시물: {summary.get('total_posts', 0)}개
❤️ 총 좋아요: {summary.get('total_likes', 0)}
💬 총 댓글: {summary.get('total_comments', 0)}
📊 평균 좋아요: {summary.get('avg_likes', 0):.1f}

마지막 업데이트: {stats.get('last_updated', '-')[:16]}"""
        else:
            msg = "📈 통계 파일을 찾을 수 없습니다."

        keyboard = {"inline_keyboard": [[{"text": "◀️ 메뉴", "callback_data": "menu"}]]}
        self.send_message(msg, reply_markup=keyboard)

    def handle_publish(self, topic: str):
        """콘텐츠 게시 실행"""
        topic_kr = self.content_map.get(topic, topic)

        self.send_message(f"📤 <b>{topic_kr}</b> 게시 시작합니다...")

        try:
            # publish_content.py 실행
            script_path = ROOT / "services/scripts/publish_content.py"
            result = subprocess.run(
                [sys.executable, str(script_path), topic],
                capture_output=True,
                text=True,
                cwd=str(ROOT),
                timeout=120
            )

            output = result.stdout + result.stderr

            # 결과 파싱
            if "🎉 Instagram 게시 완료!" in output:
                # URL 추출
                import re
                url_match = re.search(r'URL: (https://[^\s]+)', output)
                url = url_match.group(1) if url_match else ""

                msg = f"✅ <b>{topic_kr} 게시 완료!</b>"
                if url:
                    msg += f"\n\n🔗 {url}"
            elif "시뮬레이션 모드" in output:
                msg = f"⚠️ <b>{topic_kr}</b> 시뮬레이션 완료\n(실제 게시 안 됨)"
            else:
                # 에러 메시지 추출
                error_lines = [l for l in output.split('\n') if '❌' in l or 'Error' in l]
                error_msg = error_lines[0] if error_lines else "알 수 없는 오류"
                msg = f"❌ <b>{topic_kr} 게시 실패</b>\n\n{error_msg[:200]}"

        except subprocess.TimeoutExpired:
            msg = f"⏱️ <b>{topic_kr}</b> 게시 타임아웃 (2분 초과)"
        except Exception as e:
            msg = f"❌ 게시 오류: {str(e)}"

        keyboard = {"inline_keyboard": [[{"text": "◀️ 메뉴", "callback_data": "menu"}]]}
        self.send_message(msg, reply_markup=keyboard)

    def handle_help(self):
        """도움말 표시"""
        msg = """❓ <b>도움말</b>

<b>명령어:</b>
/start - 메뉴 표시
/status - 상태 확인
/sync - 데이터 동기화
/stats - Instagram 통계
/publish [topic] - 콘텐츠 게시

<b>버튼 사용:</b>
메뉴에서 원하는 기능을 탭하세요.

<b>게시 가능 콘텐츠:</b>
strawberry, mango, orange, pear, kiwi,
papaya, peach, rice, cucumber, pringles,
sausage, coca_cola, avocado, olive"""

        keyboard = {"inline_keyboard": [[{"text": "◀️ 메뉴", "callback_data": "menu"}]]}
        self.send_message(msg, reply_markup=keyboard)

    def handle_dashboard(self):
        """대시보드 링크"""
        msg = """🎬 <b>대시보드 열기</b>

터미널에서 다음 명령 실행:
<code>streamlit run services/dashboard/app.py</code>

또는 이미 실행 중이라면:
http://localhost:8501"""

        keyboard = {"inline_keyboard": [[{"text": "◀️ 메뉴", "callback_data": "menu"}]]}
        self.send_message(msg, reply_markup=keyboard)

    def process_update(self, update: dict):
        """업데이트 처리"""
        self.last_update_id = update.get("update_id", 0)

        # 콜백 쿼리 (버튼 클릭)
        if "callback_query" in update:
            callback = update["callback_query"]
            callback_id = callback["id"]
            data = callback.get("data", "")
            from_id = callback.get("from", {}).get("id")

            # 보안: 본인 chat_id만 허용
            if str(from_id) != str(self.chat_id):
                self.answer_callback(callback_id, "권한이 없습니다")
                return

            self.answer_callback(callback_id)

            if data == "menu":
                self.show_main_menu()
            elif data == "status":
                self.handle_status()
            elif data == "sync":
                self.handle_sync()
            elif data == "stats":
                self.handle_stats()
            elif data == "publish":
                self.show_publish_menu()
            elif data == "help":
                self.handle_help()
            elif data == "dashboard":
                self.handle_dashboard()
            elif data.startswith("pub_"):
                topic = data[4:]  # "pub_strawberry" → "strawberry"
                self.handle_publish(topic)

        # 일반 메시지
        elif "message" in update:
            message = update["message"]
            chat_id = message.get("chat", {}).get("id")
            text = message.get("text", "").strip()

            # 보안: 본인 chat_id만 허용
            if str(chat_id) != str(self.chat_id):
                return

            # 명령어 처리
            if text.startswith("/"):
                cmd_parts = text.split()
                cmd = cmd_parts[0].lower()

                if cmd in ["/start", "/menu"]:
                    self.show_main_menu()
                elif cmd == "/status":
                    self.handle_status()
                elif cmd == "/sync":
                    self.handle_sync()
                elif cmd == "/stats":
                    self.handle_stats()
                elif cmd == "/help":
                    self.handle_help()
                elif cmd == "/publish":
                    if len(cmd_parts) > 1:
                        topic = cmd_parts[1].lower()
                        if topic in self.content_map:
                            self.handle_publish(topic)
                        else:
                            self.send_message(f"❌ 알 수 없는 콘텐츠: {topic}")
                    else:
                        self.show_publish_menu()
                else:
                    self.send_message("❓ 알 수 없는 명령입니다. /help 를 입력하세요.")
            else:
                # 일반 텍스트는 메뉴 표시
                self.show_main_menu()

    def run(self):
        """봇 실행 (메인 루프)"""
        if not self.is_configured():
            print("❌ TELEGRAM_BOT_TOKEN이 설정되지 않았습니다.")
            print("   .env 파일에 TELEGRAM_BOT_TOKEN=your_token 추가하세요.")
            return

        print("=" * 50)
        print("🤖 Project Sunshine 텔레그램 봇 시작")
        print("=" * 50)
        print(f"Chat ID: {self.chat_id}")
        print("봇이 메시지를 기다리는 중...")
        print("종료: Ctrl+C")
        print("=" * 50)

        # 시작 메시지 전송
        self.send_message("🌻 <b>Project Sunshine 봇 시작!</b>\n\n/start 를 입력하거나 아래 메뉴를 사용하세요.")
        self.show_main_menu()

        try:
            while True:
                updates = self.get_updates(timeout=30)

                for update in updates:
                    try:
                        self.process_update(update)
                    except Exception as e:
                        print(f"업데이트 처리 오류: {e}")

        except KeyboardInterrupt:
            print("\n봇 종료...")
            self.send_message("👋 봇이 종료되었습니다.")


if __name__ == "__main__":
    bot = TelegramBotRemote()
    bot.run()
