#!/usr/bin/env python3
"""
Instagram 통계 자동 수집 데몬 v1.0

기능:
- instagram_stats_collector.py 래핑
- launchd에서 24시간마다 실행
- 수집 완료 시 텔레그램 알림 (선택)
- 로그 파일 기록

실행 방법:
    python stats_collector_daemon.py
    python stats_collector_daemon.py --notify  # 텔레그램 알림 포함
    python stats_collector_daemon.py --dry-run # 테스트 실행

launchd 설정:
    services/scripts/launchd/com.sunshine.stats.plist
"""

import sys
import os
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# 프로젝트 루트 설정
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

# 로그 디렉토리
LOG_DIR = ROOT / "config/logs/stats"
LOG_DIR.mkdir(parents=True, exist_ok=True)

# 로깅 설정
log_file = LOG_DIR / f"stats_collector_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class StatsCollectorDaemon:
    """Instagram 통계 수집 데몬"""

    def __init__(self, notify: bool = False, dry_run: bool = False):
        self.notify = notify
        self.dry_run = dry_run
        self.start_time = datetime.now()

        # .env 로드
        try:
            from dotenv import load_dotenv
            load_dotenv(ROOT / ".env")
        except ImportError:
            logger.warning("python-dotenv 미설치, 환경변수 직접 사용")

    def run(self) -> Dict[str, Any]:
        """통계 수집 실행"""
        logger.info("=" * 60)
        logger.info("Instagram 통계 수집 데몬 시작")
        logger.info(f"실행 시간: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logger.info(f"드라이런: {self.dry_run}")
        logger.info(f"텔레그램 알림: {self.notify}")
        logger.info("=" * 60)

        result = {
            "success": False,
            "posts_collected": 0,
            "total_likes": 0,
            "total_comments": 0,
            "error": None,
            "duration_seconds": 0
        }

        try:
            if self.dry_run:
                logger.info("[DRY-RUN] 실제 API 호출 없이 테스트 실행")
                result["success"] = True
                result["posts_collected"] = 0
                result["note"] = "드라이런 모드"
            else:
                result = self._collect_stats()

            # 텔레그램 알림
            if self.notify and result["success"]:
                self._send_telegram_notification(result)

        except Exception as e:
            logger.error(f"수집 실패: {e}")
            result["error"] = str(e)

            if self.notify:
                self._send_failure_notification(str(e))

        # 소요 시간
        duration = (datetime.now() - self.start_time).total_seconds()
        result["duration_seconds"] = round(duration, 2)

        logger.info("=" * 60)
        logger.info(f"수집 완료: {result['posts_collected']}개 게시물")
        logger.info(f"소요 시간: {duration:.2f}초")
        logger.info("=" * 60)

        return result

    def _collect_stats(self) -> Dict[str, Any]:
        """실제 통계 수집 (기존 collector 활용)"""
        from services.scripts.instagram_stats_collector import InstagramStatsCollector

        collector = InstagramStatsCollector()

        # 통계 수집
        logger.info("Instagram API 호출 중...")
        stats = collector.collect_all_stats()

        # 게시 이력 업데이트
        logger.info("게시 이력 업데이트 중...")
        collector.update_history_with_stats()

        # 결과 집계
        total_likes = 0
        total_comments = 0

        for topic, data in stats.items():
            post_stats = data.get("stats", {})
            total_likes += post_stats.get("likes", 0)
            total_comments += post_stats.get("comments", 0)

        return {
            "success": True,
            "posts_collected": len(stats),
            "total_likes": total_likes,
            "total_comments": total_comments,
            "error": None
        }

    def _send_telegram_notification(self, result: Dict[str, Any]):
        """텔레그램 성공 알림"""
        try:
            from core.pipeline.telegram_notifier import TelegramNotifier

            notifier = TelegramNotifier()
            if not notifier.is_configured():
                logger.warning("텔레그램 토큰 미설정, 알림 스킵")
                return

            message = f"""
<b>Instagram 통계 수집 완료</b>

수집 시간: {self.start_time.strftime('%Y-%m-%d %H:%M')}
게시물 수: <b>{result['posts_collected']}개</b>
총 좋아요: <b>{result['total_likes']:,}</b>
총 댓글: <b>{result['total_comments']:,}</b>
소요 시간: {result['duration_seconds']:.1f}초

다음 수집: 내일 오전 9시
            """.strip()

            success = notifier._send_message(message)
            if success:
                logger.info("텔레그램 알림 전송 완료")
            else:
                logger.warning("텔레그램 알림 전송 실패")

        except ImportError:
            logger.warning("telegram_notifier 모듈 로드 실패")
        except Exception as e:
            logger.error(f"텔레그램 알림 오류: {e}")

    def _send_failure_notification(self, error: str):
        """텔레그램 실패 알림"""
        try:
            from core.pipeline.telegram_notifier import TelegramNotifier

            notifier = TelegramNotifier()
            if not notifier.is_configured():
                return

            message = f"""
<b>Instagram 통계 수집 실패</b>

시간: {self.start_time.strftime('%Y-%m-%d %H:%M')}
오류: {error}

확인이 필요합니다.
            """.strip()

            notifier._send_message(message)

        except Exception as e:
            logger.error(f"실패 알림 전송 오류: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="Instagram 통계 자동 수집 데몬",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python stats_collector_daemon.py              # 기본 실행
  python stats_collector_daemon.py --notify     # 텔레그램 알림 포함
  python stats_collector_daemon.py --dry-run    # 테스트 실행

launchd 설정:
  1. plist 복사: cp launchd/com.sunshine.stats.plist ~/Library/LaunchAgents/
  2. 로드: launchctl load ~/Library/LaunchAgents/com.sunshine.stats.plist
  3. 확인: launchctl list | grep sunshine
  4. 언로드: launchctl unload ~/Library/LaunchAgents/com.sunshine.stats.plist
        """
    )

    parser.add_argument(
        "--notify",
        action="store_true",
        help="수집 완료 시 텔레그램 알림 전송"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="실제 API 호출 없이 테스트 실행"
    )

    args = parser.parse_args()

    daemon = StatsCollectorDaemon(
        notify=args.notify,
        dry_run=args.dry_run
    )

    result = daemon.run()

    # 종료 코드
    sys.exit(0 if result["success"] else 1)


if __name__ == "__main__":
    main()
