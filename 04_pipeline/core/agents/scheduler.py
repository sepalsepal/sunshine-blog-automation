"""
SchedulerAgent - 콘텐츠 스케줄링 에이전트
Project Sunshine Agent System
이름: 한스케줄

역할:
- 최적 포스팅 시간 분석
- 콘텐츠 게시 스케줄 관리
- 자동 예약 포스팅
- 시간대별 인게이지먼트 분석
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from zoneinfo import ZoneInfo

from .base import BaseAgent, AgentResult


class SchedulerAgent(BaseAgent):
    """
    콘텐츠 스케줄링 전문 에이전트 (한스케줄)

    기능:
    1. 최적 포스팅 시간 분석
    2. 주간/월간 스케줄 생성
    3. 자동 예약 포스팅 큐 관리
    4. 타임존 기반 스케줄링
    """

    # 한국 시간대 기준 최적 포스팅 시간 (인스타그램 분석 기반)
    OPTIMAL_POSTING_HOURS = {
        "weekday": [7, 8, 12, 13, 18, 19, 20, 21],  # 평일: 출퇴근, 점심, 저녁
        "weekend": [9, 10, 11, 14, 15, 16, 20, 21],  # 주말: 오전~오후, 저녁
    }

    # 카테고리별 최적 시간대
    CATEGORY_OPTIMAL_TIMES = {
        "fruit": {"hours": [9, 10, 15], "reason": "간식 시간대"},
        "vegetable": {"hours": [11, 12, 18], "reason": "식사 관련 시간대"},
        "meat": {"hours": [17, 18, 19], "reason": "저녁 식사 준비 시간"},
        "seafood": {"hours": [11, 12, 18], "reason": "식사 시간대"},
        "dairy": {"hours": [8, 9, 20], "reason": "아침/저녁 간식 시간"},
        "dangerous": {"hours": [12, 19, 21], "reason": "주의 콘텐츠는 집중 시간대"},
    }

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        self._schedule_file = Path(__file__).parent.parent / "config" / "posting_schedule.json"
        self._queue_file = Path(__file__).parent.parent / "config" / "posting_queue.json"
        self._timezone = ZoneInfo("Asia/Seoul")
        self._load_schedules()

    @property
    def name(self) -> str:
        return "SchedulerAgent"

    def _load_schedules(self) -> None:
        """저장된 스케줄 로드"""
        self._schedule = {}
        self._queue = []

        if self._schedule_file.exists():
            try:
                with open(self._schedule_file, 'r', encoding='utf-8') as f:
                    self._schedule = json.load(f)
            except Exception as e:
                self.log(f"스케줄 로드 실패: {e}", level="warning")

        if self._queue_file.exists():
            try:
                with open(self._queue_file, 'r', encoding='utf-8') as f:
                    self._queue = json.load(f)
            except Exception as e:
                self.log(f"큐 로드 실패: {e}", level="warning")

    def _save_schedules(self) -> None:
        """스케줄 저장"""
        try:
            with open(self._schedule_file, 'w', encoding='utf-8') as f:
                json.dump(self._schedule, f, ensure_ascii=False, indent=2)
            with open(self._queue_file, 'w', encoding='utf-8') as f:
                json.dump(self._queue, f, ensure_ascii=False, indent=2, default=str)
            self.log("스케줄 저장 완료")
        except Exception as e:
            self.log(f"스케줄 저장 실패: {e}", level="error")

    def get_optimal_time(self, category: str = "general", date: Optional[datetime] = None) -> datetime:
        """
        최적 포스팅 시간 계산

        Args:
            category: 콘텐츠 카테고리
            date: 기준 날짜 (None이면 오늘)

        Returns:
            최적 포스팅 시간 (datetime)
        """
        if date is None:
            date = datetime.now(self._timezone)

        is_weekend = date.weekday() >= 5
        day_type = "weekend" if is_weekend else "weekday"

        # 카테고리별 최적 시간 또는 기본 최적 시간
        if category in self.CATEGORY_OPTIMAL_TIMES:
            optimal_hours = self.CATEGORY_OPTIMAL_TIMES[category]["hours"]
        else:
            optimal_hours = self.OPTIMAL_POSTING_HOURS[day_type]

        # 현재 시간 이후의 가장 가까운 최적 시간 찾기
        current_hour = date.hour
        for hour in optimal_hours:
            if hour > current_hour:
                return date.replace(hour=hour, minute=0, second=0, microsecond=0)

        # 오늘 최적 시간이 다 지났으면 내일 첫 번째 최적 시간
        next_day = date + timedelta(days=1)
        next_is_weekend = next_day.weekday() >= 5
        next_day_type = "weekend" if next_is_weekend else "weekday"
        next_optimal_hours = self.OPTIMAL_POSTING_HOURS[next_day_type]

        return next_day.replace(
            hour=next_optimal_hours[0],
            minute=0,
            second=0,
            microsecond=0
        )

    def generate_weekly_schedule(
        self,
        topics: List[str],
        start_date: Optional[datetime] = None,
        posts_per_day: int = 1
    ) -> List[Dict]:
        """
        주간 포스팅 스케줄 생성

        Args:
            topics: 포스팅할 주제 목록
            start_date: 시작 날짜
            posts_per_day: 하루 포스팅 횟수

        Returns:
            스케줄 목록
        """
        if start_date is None:
            start_date = datetime.now(self._timezone)

        schedule = []
        topic_index = 0

        for day in range(7):
            current_date = start_date + timedelta(days=day)
            is_weekend = current_date.weekday() >= 5
            day_type = "weekend" if is_weekend else "weekday"
            optimal_hours = self.OPTIMAL_POSTING_HOURS[day_type][:posts_per_day]

            for hour in optimal_hours:
                if topic_index >= len(topics):
                    break

                scheduled_time = current_date.replace(
                    hour=hour, minute=0, second=0, microsecond=0
                )

                schedule.append({
                    "topic": topics[topic_index],
                    "scheduled_time": scheduled_time.isoformat(),
                    "day_of_week": current_date.strftime("%A"),
                    "day_type": day_type,
                    "status": "pending"
                })
                topic_index += 1

        return schedule

    def add_to_queue(self, topic: str, scheduled_time: datetime, priority: int = 5) -> Dict:
        """
        포스팅 큐에 항목 추가

        Args:
            topic: 주제
            scheduled_time: 예약 시간
            priority: 우선순위 (1-10, 높을수록 우선)

        Returns:
            추가된 큐 항목
        """
        queue_item = {
            "id": f"queue_{datetime.now().strftime('%Y%m%d%H%M%S')}_{topic}",
            "topic": topic,
            "scheduled_time": scheduled_time.isoformat(),
            "priority": priority,
            "status": "queued",
            "created_at": datetime.now(self._timezone).isoformat(),
            "attempts": 0
        }

        self._queue.append(queue_item)
        # 우선순위와 시간으로 정렬
        self._queue.sort(key=lambda x: (-x["priority"], x["scheduled_time"]))
        self._save_schedules()

        self.log(f"큐 추가: {topic} @ {scheduled_time.strftime('%Y-%m-%d %H:%M')}")
        return queue_item

    def get_next_posting(self) -> Optional[Dict]:
        """다음 포스팅할 항목 가져오기"""
        now = datetime.now(self._timezone)

        for item in self._queue:
            if item["status"] == "queued":
                scheduled = datetime.fromisoformat(item["scheduled_time"])
                if scheduled <= now:
                    return item

        return None

    def mark_completed(self, queue_id: str, success: bool = True) -> None:
        """큐 항목 완료 처리"""
        for item in self._queue:
            if item["id"] == queue_id:
                item["status"] = "completed" if success else "failed"
                item["completed_at"] = datetime.now(self._timezone).isoformat()
                break
        self._save_schedules()

    def get_queue_status(self) -> Dict:
        """큐 상태 요약"""
        total = len(self._queue)
        queued = sum(1 for item in self._queue if item["status"] == "queued")
        completed = sum(1 for item in self._queue if item["status"] == "completed")
        failed = sum(1 for item in self._queue if item["status"] == "failed")

        return {
            "total": total,
            "queued": queued,
            "completed": completed,
            "failed": failed,
            "next_posting": self.get_next_posting()
        }

    def analyze_best_times(self, engagement_data: List[Dict]) -> Dict:
        """
        인게이지먼트 데이터 기반 최적 시간 분석

        Args:
            engagement_data: 기존 포스팅 인게이지먼트 데이터

        Returns:
            시간대별 평균 인게이지먼트 분석 결과
        """
        hourly_engagement = {hour: [] for hour in range(24)}

        for data in engagement_data:
            try:
                posted_time = datetime.fromisoformat(data.get("posted_at", ""))
                hour = posted_time.hour
                engagement = data.get("likes", 0) + data.get("comments", 0) * 2
                hourly_engagement[hour].append(engagement)
            except:
                continue

        # 시간대별 평균 계산
        analysis = {}
        for hour, engagements in hourly_engagement.items():
            if engagements:
                avg = sum(engagements) / len(engagements)
                analysis[hour] = {
                    "average_engagement": round(avg, 2),
                    "post_count": len(engagements),
                    "total_engagement": sum(engagements)
                }

        # 최적 시간 추천
        if analysis:
            best_hours = sorted(
                analysis.keys(),
                key=lambda h: analysis[h]["average_engagement"],
                reverse=True
            )[:5]

            return {
                "hourly_analysis": analysis,
                "recommended_hours": best_hours,
                "best_hour": best_hours[0] if best_hours else 12
            }

        return {
            "hourly_analysis": {},
            "recommended_hours": self.OPTIMAL_POSTING_HOURS["weekday"][:5],
            "best_hour": 19
        }

    async def execute(self, input_data: Any) -> AgentResult:
        """
        스케줄링 작업 실행

        input_data 형식:
        {
            "action": "generate_schedule" | "add_to_queue" | "get_next" | "analyze",
            "topics": ["topic1", "topic2"],  # generate_schedule용
            "topic": "topic_name",  # add_to_queue용
            "scheduled_time": "2024-01-01T12:00:00",  # add_to_queue용
            "engagement_data": [...]  # analyze용
        }
        """
        try:
            action = input_data.get("action", "generate_schedule")

            if action == "generate_schedule":
                topics = input_data.get("topics", [])
                if not topics:
                    return AgentResult(
                        success=False,
                        error="주제 목록이 필요합니다"
                    )

                schedule = self.generate_weekly_schedule(
                    topics=topics,
                    posts_per_day=input_data.get("posts_per_day", 1)
                )

                self._schedule = {
                    "created_at": datetime.now(self._timezone).isoformat(),
                    "items": schedule
                }
                self._save_schedules()

                return AgentResult(
                    success=True,
                    data={
                        "schedule": schedule,
                        "total_posts": len(schedule),
                        "duration_days": 7
                    },
                    metadata={"action": action}
                )

            elif action == "add_to_queue":
                topic = input_data.get("topic")
                scheduled_time_str = input_data.get("scheduled_time")

                if not topic:
                    return AgentResult(success=False, error="주제가 필요합니다")

                if scheduled_time_str:
                    scheduled_time = datetime.fromisoformat(scheduled_time_str)
                else:
                    category = input_data.get("category", "general")
                    scheduled_time = self.get_optimal_time(category)

                queue_item = self.add_to_queue(
                    topic=topic,
                    scheduled_time=scheduled_time,
                    priority=input_data.get("priority", 5)
                )

                return AgentResult(
                    success=True,
                    data=queue_item,
                    metadata={"action": action}
                )

            elif action == "get_next":
                next_item = self.get_next_posting()
                queue_status = self.get_queue_status()

                return AgentResult(
                    success=True,
                    data={
                        "next_posting": next_item,
                        "queue_status": queue_status
                    },
                    metadata={"action": action}
                )

            elif action == "analyze":
                engagement_data = input_data.get("engagement_data", [])
                analysis = self.analyze_best_times(engagement_data)

                return AgentResult(
                    success=True,
                    data=analysis,
                    metadata={"action": action}
                )

            elif action == "get_status":
                return AgentResult(
                    success=True,
                    data=self.get_queue_status(),
                    metadata={"action": action}
                )

            else:
                return AgentResult(
                    success=False,
                    error=f"알 수 없는 액션: {action}"
                )

        except Exception as e:
            self.log(f"스케줄링 오류: {e}", level="error")
            return AgentResult(
                success=False,
                error=str(e)
            )


# 테스트용 코드
if __name__ == "__main__":
    async def test():
        agent = SchedulerAgent()

        # 주간 스케줄 생성 테스트
        result = await agent.run({
            "action": "generate_schedule",
            "topics": ["banana", "cherry", "blueberry", "carrot", "chicken"],
            "posts_per_day": 1
        })
        print("스케줄 생성 결과:", result)

        # 큐 추가 테스트
        result = await agent.run({
            "action": "add_to_queue",
            "topic": "watermelon",
            "category": "fruit",
            "priority": 8
        })
        print("큐 추가 결과:", result)

        # 상태 확인
        result = await agent.run({"action": "get_status"})
        print("큐 상태:", result)

    asyncio.run(test())
