#!/usr/bin/env python3
"""
# ============================================================
# Project Sunshine - Publishing History Tracker
# ============================================================
#
# Instagram 게시 이력 관리
#
# 사용법:
#   python scripts/publishing_tracker.py --list          # 게시 이력 보기
#   python scripts/publishing_tracker.py --add apple     # 게시 기록 추가
#   python scripts/publishing_tracker.py --stats         # 통계 보기
#   python scripts/publishing_tracker.py --export        # CSV 내보내기
#
# ============================================================
"""

import argparse
import json
import csv
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

PROJECT_ROOT = Path(__file__).parent.parent
HISTORY_FILE = PROJECT_ROOT / "config" / "publishing_history.json"


class PublishingTracker:
    """게시 이력 추적 클래스"""

    def __init__(self):
        self.history_file = HISTORY_FILE
        self.data = self._load_history()

    def _load_history(self) -> Dict:
        """이력 데이터 로드"""
        if self.history_file.exists():
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "published_posts": [],
            "draft_posts": [],
            "statistics": {
                "total_published": 0,
                "total_reach": 0,
                "total_engagement": 0
            }
        }

    def _save_history(self):
        """이력 데이터 저장"""
        self.history_file.parent.mkdir(exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def add_published(
        self,
        topic: str,
        post_id: str = None,
        post_url: str = None,
        platform: str = "instagram",
        slides_count: int = 10,
        hashtag_count: int = 30,
        notes: str = ""
    ) -> Dict:
        """게시 기록 추가"""

        # 이모지 매핑
        emoji_map = {
            "apple": "🍎", "banana": "🍌", "cherry": "🍒",
            "blueberry": "🫐", "strawberry": "🍓", "watermelon": "🍉",
            "grape": "🍇", "carrot": "🥕", "sweet_potato": "🍠",
            "pumpkin": "🎃"
        }

        record = {
            "id": len(self.data["published_posts"]) + 1,
            "topic": topic,
            "emoji": emoji_map.get(topic, "🐕"),
            "platform": platform,
            "post_id": post_id,
            "post_url": post_url,
            "published_at": datetime.now().isoformat(),
            "slides_count": slides_count,
            "hashtag_count": hashtag_count,
            "notes": notes,
            "insights": {
                "reach": 0,
                "impressions": 0,
                "likes": 0,
                "comments": 0,
                "saves": 0,
                "shares": 0
            }
        }

        self.data["published_posts"].append(record)
        self.data["statistics"]["total_published"] += 1
        self._save_history()

        print(f"✅ 게시 기록 추가됨: {record['emoji']} {topic}")
        print(f"   ID: {record['id']}")
        print(f"   시간: {record['published_at']}")

        return record

    def update_insights(
        self,
        record_id: int,
        reach: int = 0,
        impressions: int = 0,
        likes: int = 0,
        comments: int = 0,
        saves: int = 0,
        shares: int = 0
    ) -> bool:
        """인사이트 업데이트"""
        for post in self.data["published_posts"]:
            if post["id"] == record_id:
                post["insights"] = {
                    "reach": reach,
                    "impressions": impressions,
                    "likes": likes,
                    "comments": comments,
                    "saves": saves,
                    "shares": shares
                }
                post["insights_updated_at"] = datetime.now().isoformat()

                # 통계 업데이트
                self._update_statistics()
                self._save_history()

                print(f"✅ 인사이트 업데이트됨: ID {record_id}")
                return True

        print(f"❌ 기록을 찾을 수 없음: ID {record_id}")
        return False

    def _update_statistics(self):
        """전체 통계 업데이트"""
        total_reach = 0
        total_engagement = 0

        for post in self.data["published_posts"]:
            insights = post.get("insights", {})
            total_reach += insights.get("reach", 0)
            total_engagement += (
                insights.get("likes", 0) +
                insights.get("comments", 0) +
                insights.get("saves", 0) +
                insights.get("shares", 0)
            )

        self.data["statistics"]["total_reach"] = total_reach
        self.data["statistics"]["total_engagement"] = total_engagement

    def list_published(self, limit: int = 20) -> List[Dict]:
        """게시 이력 목록"""
        posts = self.data["published_posts"][-limit:]
        return list(reversed(posts))

    def get_post(self, record_id: int) -> Optional[Dict]:
        """특정 게시물 조회"""
        for post in self.data["published_posts"]:
            if post["id"] == record_id:
                return post
        return None

    def get_by_topic(self, topic: str) -> List[Dict]:
        """주제별 게시 이력"""
        return [p for p in self.data["published_posts"] if p["topic"] == topic]

    def get_statistics(self) -> Dict:
        """통계 조회"""
        self._update_statistics()

        posts = self.data["published_posts"]
        stats = self.data["statistics"].copy()

        # 추가 통계 계산
        if posts:
            # 주제별 카운트
            topic_counts = {}
            for post in posts:
                topic = post["topic"]
                topic_counts[topic] = topic_counts.get(topic, 0) + 1

            stats["by_topic"] = topic_counts
            stats["unique_topics"] = len(topic_counts)

            # 평균 참여율
            if stats["total_reach"] > 0:
                stats["avg_engagement_rate"] = round(
                    (stats["total_engagement"] / stats["total_reach"]) * 100, 2
                )
            else:
                stats["avg_engagement_rate"] = 0

        return stats

    def export_csv(self, filename: str = None) -> str:
        """CSV로 내보내기"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"publishing_history_{timestamp}.csv"

        export_path = PROJECT_ROOT / "logs" / filename
        export_path.parent.mkdir(exist_ok=True)

        with open(export_path, 'w', newline='', encoding='utf-8-sig') as f:
            writer = csv.writer(f)

            # 헤더
            writer.writerow([
                "ID", "주제", "플랫폼", "게시일", "Post ID", "URL",
                "도달", "노출", "좋아요", "댓글", "저장", "공유", "메모"
            ])

            # 데이터
            for post in self.data["published_posts"]:
                insights = post.get("insights", {})
                writer.writerow([
                    post["id"],
                    post["topic"],
                    post["platform"],
                    post["published_at"][:10],
                    post.get("post_id", ""),
                    post.get("post_url", ""),
                    insights.get("reach", 0),
                    insights.get("impressions", 0),
                    insights.get("likes", 0),
                    insights.get("comments", 0),
                    insights.get("saves", 0),
                    insights.get("shares", 0),
                    post.get("notes", "")
                ])

        print(f"✅ CSV 내보내기 완료: {export_path}")
        return str(export_path)

    def print_history(self, limit: int = 10):
        """이력 출력"""
        posts = self.list_published(limit)

        print(f"\n{'='*60}")
        print(f"📊 Instagram 게시 이력 (최근 {len(posts)}개)")
        print(f"{'='*60}")

        if not posts:
            print("\n  게시 이력이 없습니다.")
            print("  python publishing_tracker.py --add <topic> 으로 추가하세요.")
        else:
            print(f"\n{'ID':>4} │ {'주제':<12} │ {'게시일':<12} │ {'도달':>8} │ {'참여':>6}")
            print("-" * 60)

            for post in posts:
                insights = post.get("insights", {})
                reach = insights.get("reach", 0)
                engagement = (
                    insights.get("likes", 0) +
                    insights.get("comments", 0) +
                    insights.get("saves", 0)
                )
                date = post["published_at"][:10]

                print(f"{post['id']:>4} │ {post['emoji']} {post['topic']:<10} │ {date:<12} │ {reach:>8,} │ {engagement:>6,}")

        print(f"\n{'='*60}")

    def print_statistics(self):
        """통계 출력"""
        stats = self.get_statistics()

        print(f"\n{'='*60}")
        print(f"📈 게시 통계")
        print(f"{'='*60}")

        print(f"\n  📊 전체 통계")
        print(f"     총 게시물: {stats['total_published']}개")
        print(f"     총 도달: {stats['total_reach']:,}")
        print(f"     총 참여: {stats['total_engagement']:,}")
        print(f"     평균 참여율: {stats.get('avg_engagement_rate', 0):.2f}%")

        if "by_topic" in stats:
            print(f"\n  📌 주제별 게시 횟수")
            for topic, count in sorted(stats["by_topic"].items(), key=lambda x: -x[1]):
                print(f"     {topic}: {count}회")

        print(f"\n{'='*60}")


def main():
    parser = argparse.ArgumentParser(description="Project Sunshine 게시 이력 추적")
    parser.add_argument("--list", action="store_true", help="게시 이력 보기")
    parser.add_argument("--add", type=str, metavar="TOPIC", help="게시 기록 추가")
    parser.add_argument("--post-id", type=str, help="Instagram Post ID")
    parser.add_argument("--url", type=str, help="게시물 URL")
    parser.add_argument("--notes", type=str, default="", help="메모")
    parser.add_argument("--update", type=int, metavar="ID", help="인사이트 업데이트")
    parser.add_argument("--reach", type=int, default=0, help="도달")
    parser.add_argument("--likes", type=int, default=0, help="좋아요")
    parser.add_argument("--comments", type=int, default=0, help="댓글")
    parser.add_argument("--saves", type=int, default=0, help="저장")
    parser.add_argument("--stats", action="store_true", help="통계 보기")
    parser.add_argument("--export", action="store_true", help="CSV 내보내기")
    parser.add_argument("--topic", type=str, help="특정 주제 이력 보기")

    args = parser.parse_args()
    tracker = PublishingTracker()

    if args.add:
        tracker.add_published(
            topic=args.add,
            post_id=args.post_id,
            post_url=args.url,
            notes=args.notes
        )

    elif args.update:
        tracker.update_insights(
            record_id=args.update,
            reach=args.reach,
            likes=args.likes,
            comments=args.comments,
            saves=args.saves
        )

    elif args.stats:
        tracker.print_statistics()

    elif args.export:
        tracker.export_csv()

    elif args.topic:
        posts = tracker.get_by_topic(args.topic)
        print(f"\n'{args.topic}' 게시 이력: {len(posts)}개")
        for post in posts:
            print(f"  - {post['published_at'][:10]}: ID {post['id']}")

    else:
        tracker.print_history()
        print("\n사용법:")
        print("  --add TOPIC         게시 기록 추가")
        print("  --update ID         인사이트 업데이트")
        print("  --stats             통계 보기")
        print("  --export            CSV 내보내기")


if __name__ == "__main__":
    main()
