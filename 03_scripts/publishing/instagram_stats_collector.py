#!/usr/bin/env python3
"""
Instagram 성과 데이터 수집기 v1.0

기능:
- 게시물 인게이지먼트 데이터 수집
- 좋아요, 댓글, 저장 수 추적
- publishing_history.json 자동 업데이트

사용법:
    python instagram_stats_collector.py
    python instagram_stats_collector.py --update-history

Note:
    Instagram Graph API 토큰이 필요합니다.
    .env 파일에 INSTAGRAM_ACCESS_TOKEN 설정 필요.
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Any
import argparse
import logging

# 프로젝트 루트 설정
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# 파일 경로
HISTORY_FILE = ROOT / "config/settings/publishing_history.json"
STATS_FILE = ROOT / "config/data/instagram_stats.json"

# .env 로드
try:
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")
except ImportError:
    pass


class InstagramStatsCollector:
    """Instagram 성과 데이터 수집기"""

    def __init__(self):
        self.access_token = os.getenv("INSTAGRAM_ACCESS_TOKEN")
        self.instagram_id = os.getenv("INSTAGRAM_BUSINESS_ID")
        self.history = self._load_history()
        self.stats = self._load_stats()

    def _load_history(self) -> Dict[str, Any]:
        """게시 이력 로드"""
        if HISTORY_FILE.exists():
            with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"published": [], "pending": []}

    def _save_history(self):
        """게시 이력 저장"""
        self.history["last_updated"] = datetime.now().strftime("%Y-%m-%d")
        with open(HISTORY_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.history, f, ensure_ascii=False, indent=2)
        logger.info(f"게시 이력 저장: {HISTORY_FILE}")

    def _load_stats(self) -> Dict[str, Any]:
        """통계 데이터 로드"""
        if STATS_FILE.exists():
            with open(STATS_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "posts": {},
            "daily_summary": [],
            "last_updated": None
        }

    def _save_stats(self):
        """통계 데이터 저장"""
        self.stats["last_updated"] = datetime.now().isoformat()
        STATS_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(STATS_FILE, 'w', encoding='utf-8') as f:
            json.dump(self.stats, f, ensure_ascii=False, indent=2)
        logger.info(f"통계 저장: {STATS_FILE}")

    def fetch_post_insights(self, post_id: str) -> Optional[Dict[str, int]]:
        """게시물 인사이트 조회 (Graph API)

        Args:
            post_id: Instagram 게시물 ID

        Returns:
            인사이트 데이터 (likes, comments, saved, reach)
        """
        if not self.access_token:
            logger.warning("Instagram Access Token이 설정되지 않음")
            return None

        try:
            import requests

            # 기본 메트릭 조회
            url = f"https://graph.facebook.com/v18.0/{post_id}"
            params = {
                "fields": "like_count,comments_count,timestamp,permalink",
                "access_token": self.access_token
            }
            response = requests.get(url, params=params, timeout=10)

            if response.status_code == 200:
                data = response.json()
                return {
                    "likes": data.get("like_count", 0),
                    "comments": data.get("comments_count", 0),
                    "timestamp": data.get("timestamp", ""),
                    "permalink": data.get("permalink", "")
                }
            else:
                logger.warning(f"API 에러: {response.status_code} - {response.text}")
                return None

        except ImportError:
            logger.error("requests 모듈이 필요합니다: pip install requests")
            return None
        except Exception as e:
            logger.error(f"인사이트 조회 실패: {e}")
            return None

    def collect_all_stats(self) -> Dict[str, Dict]:
        """모든 게시물 통계 수집"""
        collected = {}

        for item in self.history.get("published", []):
            post_id = item.get("post_id")
            topic = item.get("topic")

            if not post_id:
                continue

            logger.info(f"수집 중: {item.get('topic_kr', topic)} (ID: {post_id})")

            # API 호출
            insights = self.fetch_post_insights(post_id)

            if insights:
                collected[topic] = {
                    "post_id": post_id,
                    "topic_kr": item.get("topic_kr", topic),
                    "publish_date": item.get("date", ""),
                    "instagram_url": item.get("instagram_url", ""),
                    "stats": insights,
                    "collected_at": datetime.now().isoformat()
                }

                # 통계 저장
                self.stats["posts"][topic] = collected[topic]
            else:
                # API 없을 때 더미 데이터 (실제 사용 시 제거)
                collected[topic] = {
                    "post_id": post_id,
                    "topic_kr": item.get("topic_kr", topic),
                    "publish_date": item.get("date", ""),
                    "instagram_url": item.get("instagram_url", ""),
                    "stats": {
                        "likes": 0,
                        "comments": 0,
                        "note": "API 토큰 필요"
                    },
                    "collected_at": datetime.now().isoformat()
                }
                self.stats["posts"][topic] = collected[topic]

        self._save_stats()
        return collected

    def update_history_with_stats(self):
        """게시 이력에 통계 데이터 추가"""
        for item in self.history.get("published", []):
            topic = item.get("topic")
            if topic in self.stats.get("posts", {}):
                stats = self.stats["posts"][topic].get("stats", {})
                item["likes"] = stats.get("likes", 0)
                item["comments"] = stats.get("comments", 0)

        self._save_history()

    def generate_report(self) -> str:
        """성과 리포트 생성"""
        report = []
        report.append("=" * 60)
        report.append("📊 Instagram 성과 리포트")
        report.append(f"생성일시: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        report.append("=" * 60)

        total_likes = 0
        total_comments = 0

        for topic, data in self.stats.get("posts", {}).items():
            stats = data.get("stats", {})
            likes = stats.get("likes", 0)
            comments = stats.get("comments", 0)

            total_likes += likes
            total_comments += comments

            report.append(f"\n📌 {data.get('topic_kr', topic)}")
            report.append(f"   게시일: {data.get('publish_date', '-')}")
            report.append(f"   좋아요: {likes:,}")
            report.append(f"   댓글: {comments:,}")
            report.append(f"   URL: {data.get('instagram_url', '-')}")

        report.append("\n" + "=" * 60)
        report.append("📈 총계")
        report.append(f"   총 게시물: {len(self.stats.get('posts', {}))}")
        report.append(f"   총 좋아요: {total_likes:,}")
        report.append(f"   총 댓글: {total_comments:,}")
        if len(self.stats.get('posts', {})) > 0:
            report.append(f"   평균 좋아요: {total_likes // len(self.stats.get('posts', {})):,}")
        report.append("=" * 60)

        return "\n".join(report)

    def print_summary(self):
        """요약 출력"""
        print(self.generate_report())


def main():
    parser = argparse.ArgumentParser(description="Instagram 성과 데이터 수집기")
    parser.add_argument("--update-history", action="store_true", help="게시 이력 업데이트")
    parser.add_argument("--report", action="store_true", help="리포트 출력")
    args = parser.parse_args()

    collector = InstagramStatsCollector()

    # 통계 수집
    print("📊 Instagram 성과 데이터 수집 중...")
    stats = collector.collect_all_stats()
    print(f"✅ {len(stats)}개 게시물 데이터 수집 완료")

    if args.update_history:
        collector.update_history_with_stats()
        print("✅ 게시 이력 업데이트 완료")

    if args.report or not args.update_history:
        collector.print_summary()


if __name__ == "__main__":
    main()
