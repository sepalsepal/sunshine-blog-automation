#!/usr/bin/env python3
"""
# ============================================================
# Project Sunshine - Content Calendar System
# ============================================================
#
# 콘텐츠 게시 일정 관리 시스템
#
# 사용법:
#   python scripts/content_calendar.py --view           # 일정 보기
#   python scripts/content_calendar.py --add apple 2025-01-25
#   python scripts/content_calendar.py --week           # 이번 주 일정
#   python scripts/content_calendar.py --suggest        # 다음 일정 추천
#
# ============================================================
"""

import argparse
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Optional

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
CALENDAR_FILE = PROJECT_ROOT / "config" / "content_calendar.json"
CONFIG_DIR = PROJECT_ROOT / "config"

# 최적 게시 시간 (정분석 분석 기반)
OPTIMAL_TIMES = {
    "best": {"day": "Tuesday", "time": "19:00", "kr_day": "화요일"},
    "good": [
        {"day": "Thursday", "time": "19:00", "kr_day": "목요일"},
        {"day": "Saturday", "time": "14:00", "kr_day": "토요일"}
    ],
    "avoid": {"day": "Monday", "period": "morning", "kr_day": "월요일 오전"}
}

# 콘텐츠 카테고리
CATEGORIES = {
    "safe_fruits": {
        "topics": ["apple", "banana", "blueberry", "strawberry", "watermelon"],
        "emoji": "🍎",
        "priority": 1
    },
    "safe_vegetables": {
        "topics": ["carrot", "sweet_potato", "pumpkin"],
        "emoji": "🥕",
        "priority": 2
    },
    "dangerous": {
        "topics": ["grape", "onion", "chocolate", "avocado"],
        "emoji": "🚫",
        "priority": 3
    },
    "conditional": {
        "topics": ["cherry", "peach", "mango"],
        "emoji": "⚠️",
        "priority": 2
    }
}


class ContentCalendar:
    """콘텐츠 캘린더 관리 클래스"""

    def __init__(self):
        self.calendar_file = CALENDAR_FILE
        self.data = self._load_calendar()

    def _load_calendar(self) -> Dict:
        """캘린더 데이터 로드"""
        if self.calendar_file.exists():
            with open(self.calendar_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {
            "version": "1.0",
            "created_at": datetime.now().isoformat(),
            "schedule": [],
            "published": [],
            "settings": {
                "posts_per_week": 3,
                "optimal_days": ["Tuesday", "Thursday", "Saturday"],
                "optimal_time": "19:00"
            }
        }

    def _save_calendar(self):
        """캘린더 데이터 저장"""
        self.calendar_file.parent.mkdir(exist_ok=True)
        with open(self.calendar_file, 'w', encoding='utf-8') as f:
            json.dump(self.data, f, ensure_ascii=False, indent=2)

    def _get_topic_info(self, topic: str) -> Dict:
        """주제 정보 가져오기"""
        for category, info in CATEGORIES.items():
            if topic in info["topics"]:
                return {
                    "category": category,
                    "emoji": info["emoji"],
                    "priority": info["priority"]
                }
        return {"category": "unknown", "emoji": "🐕", "priority": 99}

    def _get_available_topics(self) -> List[str]:
        """텍스트 데이터가 있는 주제 목록"""
        topics = []
        for f in CONFIG_DIR.glob("*_text.json"):
            topic = f.stem.replace("_text", "")
            topics.append(topic)
        return sorted(topics)

    def add_schedule(self, topic: str, date: str, time: str = "19:00", notes: str = "") -> bool:
        """일정 추가"""
        try:
            scheduled_date = datetime.strptime(f"{date} {time}", "%Y-%m-%d %H:%M")
        except ValueError:
            print(f"❌ 날짜 형식 오류: {date} {time}")
            return False

        # 중복 체크
        for item in self.data["schedule"]:
            if item["date"] == date and item["topic"] == topic:
                print(f"❌ 이미 등록된 일정: {topic} on {date}")
                return False

        topic_info = self._get_topic_info(topic)

        schedule_item = {
            "id": len(self.data["schedule"]) + 1,
            "topic": topic,
            "date": date,
            "time": time,
            "datetime": scheduled_date.isoformat(),
            "category": topic_info["category"],
            "emoji": topic_info["emoji"],
            "status": "scheduled",
            "notes": notes,
            "created_at": datetime.now().isoformat()
        }

        self.data["schedule"].append(schedule_item)
        self._save_calendar()
        print(f"✅ 일정 추가됨: {topic_info['emoji']} {topic} → {date} {time}")
        return True

    def remove_schedule(self, schedule_id: int) -> bool:
        """일정 삭제"""
        for i, item in enumerate(self.data["schedule"]):
            if item["id"] == schedule_id:
                removed = self.data["schedule"].pop(i)
                self._save_calendar()
                print(f"✅ 일정 삭제됨: {removed['topic']} on {removed['date']}")
                return True
        print(f"❌ 일정을 찾을 수 없음: ID {schedule_id}")
        return False

    def mark_published(self, schedule_id: int, post_id: str = None) -> bool:
        """게시 완료 처리"""
        for item in self.data["schedule"]:
            if item["id"] == schedule_id:
                item["status"] = "published"
                item["published_at"] = datetime.now().isoformat()
                if post_id:
                    item["post_id"] = post_id

                # 게시 완료 목록에 추가
                self.data["published"].append(item.copy())
                self._save_calendar()
                print(f"✅ 게시 완료: {item['topic']}")
                return True
        return False

    def get_upcoming(self, days: int = 7) -> List[Dict]:
        """다가오는 일정"""
        now = datetime.now()
        end = now + timedelta(days=days)

        upcoming = []
        for item in self.data["schedule"]:
            if item["status"] != "scheduled":
                continue
            scheduled = datetime.fromisoformat(item["datetime"])
            if now <= scheduled <= end:
                upcoming.append(item)

        return sorted(upcoming, key=lambda x: x["datetime"])

    def get_week_schedule(self, week_offset: int = 0) -> List[Dict]:
        """특정 주의 일정"""
        now = datetime.now()
        # 이번 주 월요일
        monday = now - timedelta(days=now.weekday()) + timedelta(weeks=week_offset)
        sunday = monday + timedelta(days=6)

        week_schedule = []
        for item in self.data["schedule"]:
            scheduled = datetime.fromisoformat(item["datetime"])
            if monday <= scheduled <= sunday:
                week_schedule.append(item)

        return sorted(week_schedule, key=lambda x: x["datetime"])

    def suggest_next_posts(self, count: int = 3) -> List[Dict]:
        """다음 게시물 추천"""
        available = self._get_available_topics()
        published_topics = [p["topic"] for p in self.data["published"]]
        scheduled_topics = [s["topic"] for s in self.data["schedule"] if s["status"] == "scheduled"]

        # 아직 게시 안 한 주제 우선
        unpublished = [t for t in available if t not in published_topics and t not in scheduled_topics]

        # 카테고리 균형 맞추기
        suggestions = []
        used_categories = set()

        # 우선순위별로 정렬
        def get_priority(topic):
            info = self._get_topic_info(topic)
            return info["priority"]

        sorted_topics = sorted(unpublished, key=get_priority)

        for topic in sorted_topics:
            info = self._get_topic_info(topic)
            category = info["category"]

            # 다양한 카테고리 추천
            if len(suggestions) < count:
                if category not in used_categories or len(suggestions) < 2:
                    suggestions.append({
                        "topic": topic,
                        "category": category,
                        "emoji": info["emoji"],
                        "reason": "아직 게시 안함" if topic not in published_topics else "재게시 권장"
                    })
                    used_categories.add(category)

            if len(suggestions) >= count:
                break

        # 다음 최적 게시일 추천
        next_dates = self._get_next_optimal_dates(count)
        for i, suggestion in enumerate(suggestions):
            if i < len(next_dates):
                suggestion["suggested_date"] = next_dates[i]
                suggestion["suggested_time"] = OPTIMAL_TIMES["best"]["time"]

        return suggestions

    def _get_next_optimal_dates(self, count: int) -> List[str]:
        """다음 최적 게시일 목록"""
        optimal_days = self.data["settings"]["optimal_days"]
        dates = []
        current = datetime.now()

        while len(dates) < count:
            current += timedelta(days=1)
            day_name = current.strftime("%A")

            if day_name in optimal_days:
                date_str = current.strftime("%Y-%m-%d")
                # 이미 예약된 날짜인지 확인
                already_scheduled = any(
                    s["date"] == date_str for s in self.data["schedule"]
                    if s["status"] == "scheduled"
                )
                if not already_scheduled:
                    dates.append(date_str)

        return dates

    def view_calendar(self, show_all: bool = False):
        """캘린더 보기"""
        print(f"\n{'='*60}")
        print(f"📅 Project Sunshine 콘텐츠 캘린더")
        print(f"{'='*60}")

        # 예정된 일정
        upcoming = self.get_upcoming(days=30)
        print(f"\n📌 예정된 게시물 ({len(upcoming)}개)")
        print("-" * 40)

        if upcoming:
            for item in upcoming:
                scheduled = datetime.fromisoformat(item["datetime"])
                day_kr = self._get_korean_day(scheduled.weekday())
                print(f"  {item['emoji']} {item['topic']:15} │ {item['date']} ({day_kr}) {item['time']}")
        else:
            print("  예정된 게시물이 없습니다.")

        # 최근 게시 완료
        if show_all:
            published = self.data["published"][-5:]
            print(f"\n✅ 최근 게시 완료 ({len(published)}개)")
            print("-" * 40)
            for item in reversed(published):
                print(f"  {item['emoji']} {item['topic']:15} │ {item.get('published_at', item['date'])[:10]}")

        # 통계
        print(f"\n📊 통계")
        print("-" * 40)
        print(f"  총 예정: {len([s for s in self.data['schedule'] if s['status'] == 'scheduled'])}개")
        print(f"  총 게시: {len(self.data['published'])}개")

        print(f"\n{'='*60}")

    def view_week(self, week_offset: int = 0):
        """주간 일정 보기"""
        now = datetime.now()
        monday = now - timedelta(days=now.weekday()) + timedelta(weeks=week_offset)

        week_label = "이번 주" if week_offset == 0 else f"{week_offset}주 후" if week_offset > 0 else f"{abs(week_offset)}주 전"

        print(f"\n{'='*60}")
        print(f"📅 {week_label} 일정 ({monday.strftime('%Y-%m-%d')} ~)")
        print(f"{'='*60}")

        week_schedule = self.get_week_schedule(week_offset)
        days = ["월", "화", "수", "목", "금", "토", "일"]

        for i in range(7):
            day_date = monday + timedelta(days=i)
            day_str = day_date.strftime("%Y-%m-%d")
            day_items = [s for s in week_schedule if s["date"] == day_str]

            if day_items:
                for item in day_items:
                    status = "✅" if item["status"] == "published" else "📌"
                    print(f"  {days[i]} ({day_str}) │ {status} {item['emoji']} {item['topic']} {item['time']}")
            else:
                is_optimal = day_date.strftime("%A") in self.data["settings"]["optimal_days"]
                marker = "⭐" if is_optimal else "  "
                print(f"  {days[i]} ({day_str}) │ {marker} -")

        print(f"\n  ⭐ = 추천 게시일")
        print(f"{'='*60}")

    def _get_korean_day(self, weekday: int) -> str:
        """요일 한글 변환"""
        days = ["월", "화", "수", "목", "금", "토", "일"]
        return days[weekday]

    def auto_schedule(self, weeks: int = 2):
        """자동 일정 생성"""
        suggestions = self.suggest_next_posts(count=weeks * 3)  # 주당 3개

        print(f"\n📅 자동 일정 생성 ({weeks}주)")
        print("-" * 40)

        for suggestion in suggestions:
            if "suggested_date" in suggestion:
                self.add_schedule(
                    topic=suggestion["topic"],
                    date=suggestion["suggested_date"],
                    time=suggestion["suggested_time"],
                    notes="자동 생성"
                )

        print(f"\n✅ {len(suggestions)}개 일정이 자동 생성되었습니다.")


def main():
    parser = argparse.ArgumentParser(description="Project Sunshine 콘텐츠 캘린더")
    parser.add_argument("--view", action="store_true", help="캘린더 보기")
    parser.add_argument("--week", action="store_true", help="이번 주 일정")
    parser.add_argument("--all", action="store_true", help="모든 일정 보기")
    parser.add_argument("--add", nargs=2, metavar=("TOPIC", "DATE"), help="일정 추가 (예: apple 2025-01-25)")
    parser.add_argument("--time", default="19:00", help="게시 시간 (기본: 19:00)")
    parser.add_argument("--remove", type=int, metavar="ID", help="일정 삭제")
    parser.add_argument("--suggest", action="store_true", help="다음 게시물 추천")
    parser.add_argument("--auto", type=int, metavar="WEEKS", help="자동 일정 생성 (주 단위)")
    parser.add_argument("--published", type=int, metavar="ID", help="게시 완료 처리")

    args = parser.parse_args()

    calendar = ContentCalendar()

    if args.add:
        topic, date = args.add
        calendar.add_schedule(topic, date, args.time)

    elif args.remove:
        calendar.remove_schedule(args.remove)

    elif args.published:
        calendar.mark_published(args.published)

    elif args.suggest:
        suggestions = calendar.suggest_next_posts(5)
        print(f"\n💡 다음 게시물 추천")
        print("-" * 50)
        for i, s in enumerate(suggestions, 1):
            date_info = f" → {s.get('suggested_date', 'TBD')}" if 'suggested_date' in s else ""
            print(f"  {i}. {s['emoji']} {s['topic']:15} │ {s['reason']}{date_info}")
        print()

    elif args.auto:
        calendar.auto_schedule(args.auto)

    elif args.week:
        calendar.view_week()

    elif args.view or args.all:
        calendar.view_calendar(show_all=args.all)

    else:
        # 기본: 캘린더 보기
        calendar.view_calendar()
        print("\n사용법:")
        print("  --view              캘린더 보기")
        print("  --week              이번 주 일정")
        print("  --add TOPIC DATE    일정 추가")
        print("  --suggest           다음 게시물 추천")
        print("  --auto WEEKS        자동 일정 생성")


if __name__ == "__main__":
    main()
