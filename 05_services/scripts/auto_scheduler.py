#!/usr/bin/env python3
"""
Project Sunshine - 자동 게시 스케줄러 v2.0

기능:
- 예약 게시 관리
- launchd 기반 자동 실행 (macOS)
- 게시 큐 관리
- 텔레그램 알림 연동
- 실행 로그 기록

사용법:
    # 스케줄 추가
    python auto_scheduler.py add --topic rice --date 2026-01-30 --time 18:00

    # 스케줄 목록
    python auto_scheduler.py list

    # 스케줄러 실행 (launchd에서 호출)
    python auto_scheduler.py run

    # 다음 예정 게시 확인
    python auto_scheduler.py next

    # 테스트 모드 (실제 게시 안 함)
    python auto_scheduler.py run --dry-run

Author: 송지영 대리
Date: 2026-01-30
Version: 2.0
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import argparse
import logging
import asyncio

# 프로젝트 루트 설정
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

# .env 파일 로드
from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# 로그 디렉토리 확인
LOG_DIR = ROOT / 'config/logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / 'scheduler.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# 스케줄 파일 경로
SCHEDULE_FILE = ROOT / 'config/settings/publish_schedule.json'
HISTORY_FILE = ROOT / 'config/settings/publishing_history.json'

# 기본 게시 시간 (한국시간 오후 6시)
DEFAULT_PUBLISH_HOUR = 18
DEFAULT_PUBLISH_MINUTE = 0


class PublishScheduler:
    """자동 게시 스케줄러"""

    def __init__(self):
        self.schedule_file = SCHEDULE_FILE
        self.schedule = self._load_schedule()

    def _load_schedule(self) -> Dict[str, Any]:
        """스케줄 파일 로드"""
        if self.schedule_file.exists():
            with open(self.schedule_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "scheduled": [],
            "completed": [],
            "failed": [],
            "settings": {
                "default_time": "18:00",
                "timezone": "Asia/Seoul",
                "notify_telegram": True,
                "auto_retry": True,
                "max_retries": 3
            }
        }

    def _save_schedule(self):
        """스케줄 파일 저장"""
        self.schedule_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.schedule_file, 'w', encoding='utf-8') as f:
            json.dump(self.schedule, f, ensure_ascii=False, indent=2)
        logger.info(f"스케줄 저장: {self.schedule_file}")

    def add_schedule(
        self,
        topic: str,
        topic_kr: str,
        publish_date: str,
        publish_time: str = "18:00",
        priority: int = 5
    ) -> Dict[str, Any]:
        """게시 스케줄 추가

        Args:
            topic: 영문 주제명
            topic_kr: 한글 주제명
            publish_date: 게시 날짜 (YYYY-MM-DD)
            publish_time: 게시 시간 (HH:MM)
            priority: 우선순위 (1-10, 높을수록 우선)

        Returns:
            추가된 스케줄 항목
        """
        # 중복 체크
        for item in self.schedule["scheduled"]:
            if item["topic"] == topic:
                logger.warning(f"이미 스케줄됨: {topic}")
                return item

        schedule_item = {
            "id": len(self.schedule["scheduled"]) + len(self.schedule["completed"]) + 1,
            "topic": topic,
            "topic_kr": topic_kr,
            "scheduled_date": publish_date,
            "scheduled_time": publish_time,
            "priority": priority,
            "status": "pending",
            "retries": 0,
            "created_at": datetime.now().isoformat(),
            "updated_at": datetime.now().isoformat()
        }

        self.schedule["scheduled"].append(schedule_item)
        self._save_schedule()
        logger.info(f"스케줄 추가: {topic_kr} ({topic}) - {publish_date} {publish_time}")

        return schedule_item

    def remove_schedule(self, topic: str) -> bool:
        """스케줄 제거"""
        for i, item in enumerate(self.schedule["scheduled"]):
            if item["topic"] == topic:
                removed = self.schedule["scheduled"].pop(i)
                self._save_schedule()
                logger.info(f"스케줄 제거: {removed['topic_kr']}")
                return True
        return False

    def get_due_schedules(self) -> List[Dict[str, Any]]:
        """현재 시간 기준 게시 대상 조회"""
        now = datetime.now()
        due = []

        for item in self.schedule.get("scheduled", []):
            # 필수 필드 확인
            date_str = item.get('scheduled_date')
            time_str = item.get('scheduled_time', '18:00')
            status = item.get('status', 'pending')

            if not date_str:
                continue

            try:
                scheduled_dt = datetime.strptime(
                    f"{date_str} {time_str}",
                    "%Y-%m-%d %H:%M"
                )
                if scheduled_dt <= now and status == "pending":
                    due.append(item)
            except ValueError:
                continue

        # 우선순위 정렬
        due.sort(key=lambda x: (-x.get("priority", 0), x.get("scheduled_date", "")))
        return due

    def get_upcoming_schedules(self, days: int = 7) -> List[Dict[str, Any]]:
        """향후 N일간 스케줄 조회"""
        now = datetime.now()
        end_date = now + timedelta(days=days)
        upcoming = []

        for item in self.schedule.get("scheduled", []):
            # scheduled_date 필드 확인
            date_str = item.get('scheduled_date')
            if not date_str:
                continue

            try:
                scheduled_dt = datetime.strptime(date_str, "%Y-%m-%d")
                if now.date() <= scheduled_dt.date() <= end_date.date():
                    upcoming.append(item)
            except ValueError:
                continue

        upcoming.sort(key=lambda x: x.get("scheduled_date", ""))
        return upcoming

    def mark_completed(self, topic: str, result: Dict[str, Any]):
        """게시 완료 처리"""
        for i, item in enumerate(self.schedule["scheduled"]):
            if item["topic"] == topic:
                item["status"] = "completed"
                item["completed_at"] = datetime.now().isoformat()
                item["result"] = result

                self.schedule["completed"].append(item)
                self.schedule["scheduled"].pop(i)
                self._save_schedule()

                logger.info(f"게시 완료: {item['topic_kr']}")
                return True
        return False

    def mark_failed(self, topic: str, error: str):
        """게시 실패 처리"""
        for item in self.schedule["scheduled"]:
            if item["topic"] == topic:
                item["retries"] += 1
                item["last_error"] = error
                item["updated_at"] = datetime.now().isoformat()

                max_retries = self.schedule["settings"].get("max_retries", 3)
                if item["retries"] >= max_retries:
                    item["status"] = "failed"
                    self.schedule["failed"].append(item)
                    self.schedule["scheduled"].remove(item)
                    logger.error(f"게시 실패 (최대 재시도 초과): {item['topic_kr']}")
                else:
                    logger.warning(f"게시 실패 (재시도 {item['retries']}/{max_retries}): {item['topic_kr']}")

                self._save_schedule()
                return True
        return False

    def auto_schedule_pending(self, start_date: Optional[str] = None) -> List[Dict[str, Any]]:
        """대기 중인 주제 자동 스케줄링

        publishing_history.json의 pending 목록에서 자동으로 스케줄 생성
        """
        if not HISTORY_FILE.exists():
            logger.error("게시 이력 파일 없음")
            return []

        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)

        pending_topics = history.get("pending", [])
        if not pending_topics:
            logger.info("대기 중인 주제 없음")
            return []

        # 시작 날짜 설정
        if start_date:
            current_date = datetime.strptime(start_date, "%Y-%m-%d")
        else:
            current_date = datetime.now() + timedelta(days=1)

        # 이미 스케줄된 주제 제외
        scheduled_topics = {item["topic"] for item in self.schedule["scheduled"]}

        added = []
        for topic in pending_topics:
            if topic in scheduled_topics:
                continue

            # 주제별 한글명 매핑 (간단 버전)
            topic_kr_map = {
                "grape": "포도", "spinach": "시금치", "zucchini": "애호박",
                "cabbage": "양배추", "chicken": "닭고기", "beef": "소고기",
                "pork": "돼지고기", "turkey": "칠면조", "salmon": "연어",
                "shrimp": "새우", "tuna": "참치", "egg": "계란",
                "cheese": "치즈", "yogurt": "요거트"
            }
            topic_kr = topic_kr_map.get(topic, topic)

            schedule_item = self.add_schedule(
                topic=topic,
                topic_kr=topic_kr,
                publish_date=current_date.strftime("%Y-%m-%d"),
                publish_time="18:00"
            )
            added.append(schedule_item)

            # 다음 날짜로 이동
            current_date += timedelta(days=1)

        logger.info(f"{len(added)}개 주제 자동 스케줄됨")
        return added

    def get_calendar_data(self, year: int, month: int) -> Dict[str, List[Dict]]:
        """월간 캘린더 데이터 생성"""
        calendar_data = {}

        # 스케줄된 항목
        for item in self.schedule["scheduled"]:
            date = item["scheduled_date"]
            if date.startswith(f"{year}-{month:02d}"):
                if date not in calendar_data:
                    calendar_data[date] = []
                calendar_data[date].append({
                    "topic": item["topic"],
                    "topic_kr": item["topic_kr"],
                    "time": item["scheduled_time"],
                    "status": "scheduled"
                })

        # 완료된 항목
        for item in self.schedule["completed"]:
            date = item["scheduled_date"]
            if date.startswith(f"{year}-{month:02d}"):
                if date not in calendar_data:
                    calendar_data[date] = []
                calendar_data[date].append({
                    "topic": item["topic"],
                    "topic_kr": item["topic_kr"],
                    "time": item["scheduled_time"],
                    "status": "completed"
                })

        return calendar_data

    def print_schedule(self):
        """스케줄 출력"""
        print("\n" + "=" * 60)
        print("📅 게시 스케줄")
        print("=" * 60)

        if not self.schedule["scheduled"]:
            print("예정된 게시 없음")
        else:
            print(f"\n{'날짜':<12} {'시간':<6} {'주제':<15} {'우선순위':<8} {'상태'}")
            print("-" * 60)
            for item in sorted(self.schedule["scheduled"], key=lambda x: x["scheduled_date"]):
                print(f"{item['scheduled_date']:<12} {item['scheduled_time']:<6} "
                      f"{item['topic_kr']:<15} {item['priority']:<8} {item['status']}")

        print("\n" + "=" * 60)


def main():
    parser = argparse.ArgumentParser(description="자동 게시 스케줄러")
    subparsers = parser.add_subparsers(dest="command", help="명령어")

    # add 명령
    add_parser = subparsers.add_parser("add", help="스케줄 추가")
    add_parser.add_argument("--topic", required=True, help="영문 주제명")
    add_parser.add_argument("--topic-kr", help="한글 주제명")
    add_parser.add_argument("--date", required=True, help="게시 날짜 (YYYY-MM-DD)")
    add_parser.add_argument("--time", default="18:00", help="게시 시간 (HH:MM)")
    add_parser.add_argument("--priority", type=int, default=5, help="우선순위 (1-10)")

    # remove 명령
    remove_parser = subparsers.add_parser("remove", help="스케줄 제거")
    remove_parser.add_argument("--topic", required=True, help="영문 주제명")

    # list 명령
    subparsers.add_parser("list", help="스케줄 목록")

    # auto 명령
    auto_parser = subparsers.add_parser("auto", help="자동 스케줄링")
    auto_parser.add_argument("--start-date", help="시작 날짜 (YYYY-MM-DD)")

    # run 명령
    run_parser = subparsers.add_parser("run", help="스케줄러 실행")
    run_parser.add_argument("--dry-run", action="store_true", help="테스트 모드 (실제 게시 안 함)")

    # next 명령
    subparsers.add_parser("next", help="다음 예정 게시 확인")

    # cover 명령 (표지 현황 체크)
    cover_parser = subparsers.add_parser("cover", help="표지 현황 체크")
    cover_parser.add_argument("--threshold", type=int, default=30, help="알림 임계값 (기본: 30)")

    args = parser.parse_args()
    scheduler = PublishScheduler()

    if args.command == "add":
        topic_kr = args.topic_kr or args.topic
        scheduler.add_schedule(
            topic=args.topic,
            topic_kr=topic_kr,
            publish_date=args.date,
            publish_time=args.time,
            priority=args.priority
        )
        print(f"✅ 스케줄 추가: {topic_kr} - {args.date} {args.time}")

    elif args.command == "remove":
        if scheduler.remove_schedule(args.topic):
            print(f"✅ 스케줄 제거: {args.topic}")
        else:
            print(f"❌ 스케줄 없음: {args.topic}")

    elif args.command == "list":
        scheduler.print_schedule()

    elif args.command == "auto":
        added = scheduler.auto_schedule_pending(args.start_date)
        print(f"✅ {len(added)}개 주제 자동 스케줄됨")
        scheduler.print_schedule()

    elif args.command == "run":
        dry_run = getattr(args, 'dry_run', False)
        asyncio.run(run_scheduled_publish(scheduler, dry_run=dry_run))

    elif args.command == "next":
        show_next_scheduled(scheduler)

    elif args.command == "cover":
        result = check_cover_sources(alert_threshold=args.threshold)
        print("\n" + "=" * 50)
        print("📊 표지 이미지 현황")
        print("=" * 50)
        print(f"   02_ready (게시 대기): {result['ready_count']}개")
        print(f"   03_cover_sources (원본): {result['source_count']}개")
        print(f"   알림 임계값: {args.threshold}개")
        if result['alert_sent']:
            print(f"\n   ⚠️ 텔레그램 알림 전송됨!")
        elif result['ready_count'] > args.threshold:
            print(f"\n   ✅ 충분한 표지 보유 중")
        print("=" * 50 + "\n")

    else:
        parser.print_help()


async def run_scheduled_publish(scheduler: PublishScheduler, dry_run: bool = False):
    """스케줄된 게시 실행"""
    from services.scripts.publishing.publish_content import publish_content, CONTENT_MAP

    logger.info("=" * 60)
    logger.info(f"🕐 스케줄러 실행 시작 - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    logger.info(f"   모드: {'테스트 (dry-run)' if dry_run else '실제 게시'}")
    logger.info("=" * 60)

    # 게시 대상 조회
    due = scheduler.get_due_schedules()

    if not due:
        logger.info("📭 게시 대상 없음")
        send_telegram_notification("📭 스케줄러: 게시 대상 없음")
        return

    logger.info(f"📤 {len(due)}개 게시 대상 발견:")
    for item in due:
        logger.info(f"   - {item['topic_kr']} ({item['topic']}) - 예정: {item['scheduled_date']} {item['scheduled_time']}")

    # 각 콘텐츠 게시 실행
    success_count = 0
    fail_count = 0

    for item in due:
        topic = item["topic"]
        topic_kr = item["topic_kr"]

        logger.info(f"\n{'='*40}")
        logger.info(f"📤 게시 시작: {topic_kr} ({topic})")
        logger.info(f"{'='*40}")

        # 콘텐츠 매핑 확인
        if topic not in CONTENT_MAP:
            logger.error(f"❌ 콘텐츠 매핑 없음: {topic}")
            scheduler.mark_failed(topic, "콘텐츠 매핑 없음")
            fail_count += 1
            continue

        if dry_run:
            logger.info(f"🧪 [DRY-RUN] {topic_kr} 게시 시뮬레이션")
            scheduler.mark_completed(topic, {
                "instagram_url": "https://instagram.com/p/dry-run-test",
                "post_id": "dry-run-test",
                "simulated": True
            })
            success_count += 1
            continue

        try:
            # 실제 게시 실행
            result = await publish_content(topic)

            if result and result.success:
                publish_results = result.data.get("publish_results", {})
                instagram_result = publish_results.get("instagram", {})

                if instagram_result.get("success"):
                    post_id = instagram_result.get("post_id", "")
                    permalink = instagram_result.get("permalink", "")

                    scheduler.mark_completed(topic, {
                        "instagram_url": permalink,
                        "post_id": post_id
                    })

                    logger.info(f"✅ 게시 완료: {topic_kr}")
                    logger.info(f"   URL: {permalink}")

                    send_telegram_notification(
                        f"✅ <b>{topic_kr} 게시 완료!</b>\n\n🔗 {permalink}"
                    )
                    success_count += 1
                else:
                    error = instagram_result.get("error", "알 수 없는 오류")
                    scheduler.mark_failed(topic, error)
                    logger.error(f"❌ 게시 실패: {topic_kr} - {error}")
                    fail_count += 1
            else:
                error = result.error if result else "결과 없음"
                scheduler.mark_failed(topic, error)
                logger.error(f"❌ 게시 실패: {topic_kr} - {error}")
                fail_count += 1

        except Exception as e:
            error_msg = str(e)
            scheduler.mark_failed(topic, error_msg)
            logger.error(f"❌ 게시 오류: {topic_kr} - {error_msg}")
            fail_count += 1

    # 결과 요약
    logger.info("\n" + "=" * 60)
    logger.info(f"📊 스케줄러 실행 완료")
    logger.info(f"   성공: {success_count}개 / 실패: {fail_count}개")
    logger.info("=" * 60)

    if fail_count > 0:
        send_telegram_notification(
            f"⚠️ <b>스케줄러 실행 완료</b>\n\n성공: {success_count}개\n실패: {fail_count}개"
        )

    # 표지 소스 현황 체크 (30개 이하면 알림)
    cover_threshold = scheduler.schedule.get("settings", {}).get("cover_alert_threshold", 30)
    check_cover_sources(alert_threshold=cover_threshold)


def show_next_scheduled(scheduler: PublishScheduler):
    """다음 예정 게시 표시"""
    upcoming = scheduler.get_upcoming_schedules(days=7)

    print("\n" + "=" * 60)
    print("📅 향후 7일간 게시 예정")
    print("=" * 60)

    if not upcoming:
        print("예정된 게시 없음")
    else:
        print(f"\n{'날짜':<12} {'시간':<6} {'주제':<15} {'상태'}")
        print("-" * 50)
        for item in upcoming:
            status = "⏳ 대기" if item["status"] == "pending" else item["status"]
            print(f"{item['scheduled_date']:<12} {item['scheduled_time']:<6} "
                  f"{item['topic_kr']:<15} {status}")

    print("\n" + "=" * 60)


def send_telegram_notification(message: str):
    """텔레그램 알림 전송"""
    try:
        import requests

        bot_token = os.getenv("TELEGRAM_BOT_TOKEN")
        chat_id = os.getenv("TELEGRAM_CHAT_ID", "5360443525")

        if not bot_token:
            logger.warning("텔레그램 토큰 없음 - 알림 스킵")
            return

        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(url, json={
            "chat_id": chat_id,
            "text": message,
            "parse_mode": "HTML"
        }, timeout=10)

        if response.status_code == 200:
            logger.info("📱 텔레그램 알림 전송 완료")
        else:
            logger.warning(f"텔레그램 알림 실패: {response.status_code}")

    except Exception as e:
        logger.warning(f"텔레그램 알림 오류: {e}")


def check_cover_sources(alert_threshold: int = 30) -> dict:
    """표지 소스 현황 체크 및 알림

    Args:
        alert_threshold: 이 숫자 이하면 텔레그램 알림

    Returns:
        {"ready_count": int, "source_count": int, "alert_sent": bool}
    """
    cover_ready_dir = ROOT / "content/images/000_cover/02_ready"
    cover_source_dir = ROOT / "content/images/000_cover/03_cover_sources"

    # 02_ready 폴더 카운트 (png 파일만)
    ready_count = len(list(cover_ready_dir.glob("*.png"))) if cover_ready_dir.exists() else 0

    # 03_cover_sources 폴더 카운트
    source_count = len(list(cover_source_dir.glob("*.png"))) if cover_source_dir.exists() else 0

    logger.info(f"📊 표지 현황: Ready={ready_count}개, Source={source_count}개")

    alert_sent = False

    # 표지 레디가 30개 이하면 알림
    if ready_count <= alert_threshold:
        alert_msg = (
            f"⚠️ <b>표지 이미지 부족 알림</b>\n\n"
            f"📁 02_ready: <b>{ready_count}개</b> (임계값: {alert_threshold}개)\n"
            f"📁 03_cover_sources: {source_count}개\n\n"
            f"🔔 새 표지 제작이 필요합니다!"
        )
        send_telegram_notification(alert_msg)
        alert_sent = True
        logger.warning(f"⚠️ 표지 부족 알림 전송: {ready_count}개 (임계값: {alert_threshold}개)")

    return {
        "ready_count": ready_count,
        "source_count": source_count,
        "alert_sent": alert_sent
    }


if __name__ == "__main__":
    main()
