"""
게시 실패 자동 재시도 시스템
Project Sunshine - RetryManager

기능:
- 게시 실패 시 자동 재시도 (최대 3회)
- 재시도 간격: exponential backoff (5분, 15분, 30분)
- 실패 이력 기록 (publish_schedule.json)
- 최종 실패 시 텔레그램 알림

작성자: 김대리
작성일: 2026-01-30
"""

import asyncio
import json
import os
from datetime import datetime, timedelta
from pathlib import Path
from typing import Callable, Optional, Dict, Any, Awaitable
from dataclasses import dataclass, field, asdict
from enum import Enum


class RetryStatus(Enum):
    """재시도 상태"""
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    SUCCESS = "success"
    FAILED = "failed"
    EXHAUSTED = "exhausted"  # 최대 재시도 횟수 초과


@dataclass
class RetryRecord:
    """재시도 기록"""
    topic: str
    topic_kr: str
    attempt: int
    status: str
    error: Optional[str] = None
    timestamp: str = field(default_factory=lambda: datetime.now().isoformat())
    next_retry_at: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class RetryManager:
    """게시 실패 자동 재시도 관리자

    사용법:
        manager = RetryManager()

        async def publish_func():
            # 게시 로직
            return {"success": True, "post_id": "123"}

        result = await manager.execute_with_retry(
            topic="strawberry",
            topic_kr="딸기",
            publish_func=publish_func
        )
    """

    # 재시도 간격 (분) - exponential backoff
    RETRY_INTERVALS = [5, 15, 30]  # 5분, 15분, 30분
    MAX_RETRIES = 3

    def __init__(self, schedule_path: Optional[Path] = None):
        """초기화

        Args:
            schedule_path: publish_schedule.json 경로 (기본: config/settings/)
        """
        self.root = Path(__file__).parent.parent.parent
        self.schedule_path = schedule_path or self.root / "config" / "settings" / "publish_schedule.json"
        self._notifier = None

    @property
    def notifier(self):
        """텔레그램 알림 모듈 (lazy loading)"""
        if self._notifier is None:
            try:
                from core.pipeline.telegram_notifier import TelegramNotifier
                self._notifier = TelegramNotifier()
            except ImportError:
                self._notifier = None
        return self._notifier

    def _load_schedule(self) -> Dict[str, Any]:
        """스케줄 파일 로드"""
        if not self.schedule_path.exists():
            return {
                "scheduled": [],
                "completed": [],
                "failed": [],
                "settings": {
                    "default_time": "18:00",
                    "timezone": "Asia/Seoul",
                    "notify_telegram": True,
                    "auto_retry": True,
                    "max_retries": self.MAX_RETRIES
                }
            }

        with open(self.schedule_path, 'r', encoding='utf-8') as f:
            return json.load(f)

    def _save_schedule(self, data: Dict[str, Any]) -> None:
        """스케줄 파일 저장"""
        self.schedule_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.schedule_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _get_retry_interval(self, attempt: int) -> int:
        """재시도 간격 계산 (분)

        Args:
            attempt: 현재 시도 횟수 (1-based)

        Returns:
            대기 시간 (분)
        """
        if attempt <= 0:
            return self.RETRY_INTERVALS[0]

        idx = min(attempt - 1, len(self.RETRY_INTERVALS) - 1)
        return self.RETRY_INTERVALS[idx]

    def _record_failure(
        self,
        topic: str,
        topic_kr: str,
        attempt: int,
        error: str,
        next_retry_at: Optional[datetime] = None
    ) -> None:
        """실패 이력 기록

        Args:
            topic: 영문 토픽명
            topic_kr: 한글 토픽명
            attempt: 시도 횟수
            error: 오류 메시지
            next_retry_at: 다음 재시도 예정 시간
        """
        schedule = self._load_schedule()

        record = {
            "topic": topic,
            "topic_kr": topic_kr,
            "attempt": attempt,
            "error": error,
            "timestamp": datetime.now().isoformat(),
            "next_retry_at": next_retry_at.isoformat() if next_retry_at else None,
            "status": "pending_retry" if next_retry_at else "exhausted"
        }

        # 기존 실패 기록에서 같은 토픽 제거 (최신 기록만 유지)
        schedule["failed"] = [
            f for f in schedule.get("failed", [])
            if f.get("topic") != topic
        ]

        # 새 기록 추가
        schedule["failed"].append(record)

        self._save_schedule(schedule)
        print(f"   [RetryManager] 실패 기록 저장: {topic} (시도 {attempt}/{self.MAX_RETRIES})")

    def _record_success(self, topic: str, topic_kr: str, result: Dict[str, Any]) -> None:
        """성공 이력 기록 및 실패 기록 제거

        Args:
            topic: 영문 토픽명
            topic_kr: 한글 토픽명
            result: 게시 결과
        """
        schedule = self._load_schedule()

        # 실패 기록에서 제거
        schedule["failed"] = [
            f for f in schedule.get("failed", [])
            if f.get("topic") != topic
        ]

        self._save_schedule(schedule)
        print(f"   [RetryManager] 성공 기록, 실패 이력 제거: {topic}")

    def _send_final_failure_notification(
        self,
        topic: str,
        topic_kr: str,
        error: str,
        attempts: int
    ) -> bool:
        """최종 실패 시 텔레그램 알림

        Args:
            topic: 영문 토픽명
            topic_kr: 한글 토픽명
            error: 최종 오류 메시지
            attempts: 총 시도 횟수

        Returns:
            알림 전송 성공 여부
        """
        if not self.notifier or not self.notifier.is_configured():
            print("   [RetryManager] 텔레그램 미설정, 알림 스킵")
            return False

        message = f"""
<b>게시 최종 실패</b>

<b>콘텐츠:</b> {topic.upper()} ({topic_kr})
<b>시도 횟수:</b> {attempts}회
<b>오류:</b> {error}

재시도 횟수를 모두 소진했습니다.
수동 확인이 필요합니다.
        """

        result = self.notifier._send_message(message.strip())
        if result:
            print(f"   [RetryManager] 최종 실패 알림 전송 완료")
        return result

    def _send_retry_notification(
        self,
        topic: str,
        topic_kr: str,
        attempt: int,
        error: str,
        next_retry_at: datetime
    ) -> bool:
        """재시도 예정 알림

        Args:
            topic: 영문 토픽명
            topic_kr: 한글 토픽명
            attempt: 현재 시도 횟수
            error: 오류 메시지
            next_retry_at: 다음 재시도 시간

        Returns:
            알림 전송 성공 여부
        """
        if not self.notifier or not self.notifier.is_configured():
            return False

        remaining = self.MAX_RETRIES - attempt
        next_time = next_retry_at.strftime("%H:%M")

        message = f"""
<b>게시 실패 - 재시도 예정</b>

<b>콘텐츠:</b> {topic.upper()} ({topic_kr})
<b>시도:</b> {attempt}/{self.MAX_RETRIES}회
<b>남은 재시도:</b> {remaining}회
<b>오류:</b> {error[:100]}

<b>다음 재시도:</b> {next_time}
        """

        return self.notifier._send_message(message.strip())

    async def execute_with_retry(
        self,
        topic: str,
        topic_kr: str,
        publish_func: Callable[[], Awaitable[Dict[str, Any]]],
        notify_on_retry: bool = True,
        notify_on_final_failure: bool = True
    ) -> Dict[str, Any]:
        """재시도 로직으로 게시 함수 실행

        Args:
            topic: 영문 토픽명
            topic_kr: 한글 토픽명
            publish_func: 게시 함수 (async callable, Dict 반환)
            notify_on_retry: 재시도 시 텔레그램 알림 여부
            notify_on_final_failure: 최종 실패 시 텔레그램 알림 여부

        Returns:
            {
                "success": bool,
                "data": {...},  # 성공 시 게시 결과
                "error": str,   # 실패 시 오류 메시지
                "attempts": int,
                "status": str   # success, exhausted
            }
        """
        last_error = ""

        for attempt in range(1, self.MAX_RETRIES + 1):
            print(f"\n   [RetryManager] 시도 {attempt}/{self.MAX_RETRIES}: {topic}")

            try:
                # 게시 함수 실행
                result = await publish_func()

                # 성공 여부 확인
                if isinstance(result, dict) and result.get("success", False):
                    self._record_success(topic, topic_kr, result)
                    print(f"   [RetryManager] 게시 성공: {topic}")
                    return {
                        "success": True,
                        "data": result,
                        "attempts": attempt,
                        "status": RetryStatus.SUCCESS.value
                    }

                # 실패 (result가 False이거나 success=False)
                last_error = result.get("error", "Unknown error") if isinstance(result, dict) else str(result)
                print(f"   [RetryManager] 게시 실패: {last_error}")

            except Exception as e:
                last_error = f"{type(e).__name__}: {str(e)}"
                print(f"   [RetryManager] 예외 발생: {last_error}")

            # 재시도 여부 결정
            if attempt < self.MAX_RETRIES:
                # 다음 재시도 시간 계산
                interval = self._get_retry_interval(attempt)
                next_retry_at = datetime.now() + timedelta(minutes=interval)

                # 실패 기록
                self._record_failure(topic, topic_kr, attempt, last_error, next_retry_at)

                # 재시도 알림
                if notify_on_retry:
                    self._send_retry_notification(
                        topic, topic_kr, attempt, last_error, next_retry_at
                    )

                print(f"   [RetryManager] {interval}분 후 재시도 예정 ({next_retry_at.strftime('%H:%M')})")

                # 대기
                await asyncio.sleep(interval * 60)  # 분 -> 초
            else:
                # 최대 재시도 횟수 초과
                self._record_failure(topic, topic_kr, attempt, last_error, None)

                if notify_on_final_failure:
                    self._send_final_failure_notification(
                        topic, topic_kr, last_error, attempt
                    )

        # 모든 재시도 실패
        return {
            "success": False,
            "error": last_error,
            "attempts": self.MAX_RETRIES,
            "status": RetryStatus.EXHAUSTED.value
        }

    def get_pending_retries(self) -> list:
        """재시도 대기 중인 항목 조회

        Returns:
            재시도 대기 목록
        """
        schedule = self._load_schedule()
        return [
            f for f in schedule.get("failed", [])
            if f.get("status") == "pending_retry"
        ]

    def get_exhausted_items(self) -> list:
        """재시도 소진된 항목 조회

        Returns:
            재시도 소진 목록
        """
        schedule = self._load_schedule()
        return [
            f for f in schedule.get("failed", [])
            if f.get("status") == "exhausted"
        ]

    def clear_failure_record(self, topic: str) -> bool:
        """특정 토픽의 실패 기록 제거

        Args:
            topic: 영문 토픽명

        Returns:
            제거 성공 여부
        """
        schedule = self._load_schedule()
        original_count = len(schedule.get("failed", []))

        schedule["failed"] = [
            f for f in schedule.get("failed", [])
            if f.get("topic") != topic
        ]

        if len(schedule["failed"]) < original_count:
            self._save_schedule(schedule)
            print(f"   [RetryManager] 실패 기록 제거: {topic}")
            return True

        return False

    def reset_retry_count(self, topic: str) -> bool:
        """특정 토픽의 재시도 횟수 초기화 (재시도 재개)

        Args:
            topic: 영문 토픽명

        Returns:
            초기화 성공 여부
        """
        schedule = self._load_schedule()

        for item in schedule.get("failed", []):
            if item.get("topic") == topic:
                item["attempt"] = 0
                item["status"] = "pending_retry"
                item["next_retry_at"] = datetime.now().isoformat()
                self._save_schedule(schedule)
                print(f"   [RetryManager] 재시도 횟수 초기화: {topic}")
                return True

        return False


# 편의 함수
async def publish_with_retry(
    topic: str,
    topic_kr: str,
    publish_func: Callable[[], Awaitable[Dict[str, Any]]]
) -> Dict[str, Any]:
    """편의 함수: 재시도 로직으로 게시

    Args:
        topic: 영문 토픽명
        topic_kr: 한글 토픽명
        publish_func: 게시 함수

    Returns:
        게시 결과
    """
    manager = RetryManager()
    return await manager.execute_with_retry(topic, topic_kr, publish_func)


# 테스트용
if __name__ == "__main__":
    import sys
    from pathlib import Path

    # 프로젝트 루트 설정
    ROOT = Path(__file__).parent.parent.parent
    sys.path.insert(0, str(ROOT))

    # .env 로드
    from dotenv import load_dotenv
    load_dotenv(ROOT / ".env")

    async def test_retry_manager():
        """RetryManager 테스트"""
        print("=" * 60)
        print("RetryManager 테스트")
        print("=" * 60)

        manager = RetryManager()

        # 테스트용 실패 함수
        fail_count = [0]

        async def failing_publish():
            fail_count[0] += 1
            if fail_count[0] < 3:
                return {"success": False, "error": f"테스트 실패 #{fail_count[0]}"}
            return {"success": True, "post_id": "test123"}

        # 빠른 테스트를 위해 간격 수정
        manager.RETRY_INTERVALS = [0.05, 0.1, 0.15]  # 3초, 6초, 9초

        print("\n[테스트 1] 2번 실패 후 성공")
        result = await manager.execute_with_retry(
            topic="test_topic",
            topic_kr="테스트",
            publish_func=failing_publish,
            notify_on_retry=False,
            notify_on_final_failure=False
        )
        print(f"결과: {result}")

        # 상태 확인
        print(f"\n[상태] 대기 중: {len(manager.get_pending_retries())}개")
        print(f"[상태] 소진됨: {len(manager.get_exhausted_items())}개")

        # 항상 실패하는 함수 테스트
        print("\n[테스트 2] 모든 재시도 실패")
        async def always_fail():
            return {"success": False, "error": "항상 실패"}

        result = await manager.execute_with_retry(
            topic="always_fail_topic",
            topic_kr="항상실패",
            publish_func=always_fail,
            notify_on_retry=False,
            notify_on_final_failure=False
        )
        print(f"결과: {result}")

        # 상태 확인
        print(f"\n[상태] 대기 중: {len(manager.get_pending_retries())}개")
        print(f"[상태] 소진됨: {len(manager.get_exhausted_items())}개")

        # 정리
        manager.clear_failure_record("test_topic")
        manager.clear_failure_record("always_fail_topic")

        print("\n" + "=" * 60)
        print("테스트 완료")
        print("=" * 60)

    asyncio.run(test_retry_manager())
