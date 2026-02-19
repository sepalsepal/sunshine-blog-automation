#!/usr/bin/env python3
"""
# ============================================================
# ContentQueue - 콘텐츠 대기열 자동 관리 시스템
# ============================================================
#
# 역할:
#    1. 게시 대기 중인 콘텐츠 자동 관리
#    2. 우선순위 기반 다음 게시 콘텐츠 선택
#    3. 게시 완료 처리 및 이력 자동 갱신
#
# 우선순위 기준:
#    1. scheduled_date가 있으면 날짜순 (오늘/과거 우선)
#    2. priority 값 (높을수록 우선)
#    3. 생성일순 (오래된 것 먼저)
#
# Author: 김대리 (파일 관리 담당)
# Date: 2026-01-30
# ============================================================
"""

import json
from pathlib import Path
from datetime import datetime, date
from typing import Dict, Any, Optional, List, Tuple
from dataclasses import dataclass, field, asdict
from enum import Enum


# 경로 설정
ROOT = Path(__file__).parent.parent.parent
CONFIG_DIR = ROOT / "config" / "settings"

# 데이터 파일 경로
PUBLISH_SCHEDULE = CONFIG_DIR / "publish_schedule.json"
PUBLISHING_HISTORY = CONFIG_DIR / "publishing_history.json"


class ContentStatus(Enum):
    """콘텐츠 상태"""
    PENDING = "pending"
    SCHEDULED = "scheduled"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


@dataclass
class QueueItem:
    """대기열 항목"""
    id: int
    topic: str
    topic_kr: str
    status: str = "pending"
    priority: int = 5  # 1~10, 높을수록 우선
    scheduled_date: Optional[str] = None  # YYYY-MM-DD
    scheduled_time: Optional[str] = None  # HH:MM
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    retries: int = 0
    note: Optional[str] = None
    result: Optional[Dict] = None

    def __post_init__(self):
        now = datetime.now().isoformat()
        if not self.created_at:
            self.created_at = now
        if not self.updated_at:
            self.updated_at = now

    def to_dict(self) -> Dict:
        """딕셔너리 변환"""
        return {k: v for k, v in asdict(self).items() if v is not None}

    @classmethod
    def from_dict(cls, data: Dict) -> "QueueItem":
        """딕셔너리에서 생성"""
        return cls(
            id=data.get("id", 0),
            topic=data.get("topic", ""),
            topic_kr=data.get("topic_kr", ""),
            status=data.get("status", "pending"),
            priority=data.get("priority", 5),
            scheduled_date=data.get("scheduled_date"),
            scheduled_time=data.get("scheduled_time"),
            created_at=data.get("created_at"),
            updated_at=data.get("updated_at"),
            retries=data.get("retries", 0),
            note=data.get("note"),
            result=data.get("result")
        )


class ContentQueue:
    """콘텐츠 대기열 관리 클래스"""

    def __init__(self):
        """초기화"""
        self._load_data()

    def _load_data(self):
        """데이터 파일 로드"""
        self.schedule_data = self._load_json(PUBLISH_SCHEDULE) or {
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
        self.history_data = self._load_json(PUBLISHING_HISTORY) or {
            "published": [],
            "pending": []
        }
        # 게시된 주제 집합 (빠른 조회용)
        self._published_topics = {
            item["topic"].lower()
            for item in self.history_data.get("published", [])
        }

    def _load_json(self, path: Path) -> Optional[Dict]:
        """JSON 파일 로드"""
        if path.exists():
            try:
                with open(path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"JSON 로드 실패: {path} - {e}")
        return None

    def _save_json(self, path: Path, data: Dict):
        """JSON 파일 저장 (atomic write)"""
        import tempfile
        import os

        path.parent.mkdir(parents=True, exist_ok=True)

        temp_fd, temp_path = tempfile.mkstemp(dir=path.parent, suffix=".tmp")
        try:
            with os.fdopen(temp_fd, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            os.replace(temp_path, path)
        except Exception:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
            raise

    def _save_schedule(self):
        """스케줄 데이터 저장"""
        self._save_json(PUBLISH_SCHEDULE, self.schedule_data)

    def _save_history(self):
        """히스토리 데이터 저장"""
        self.history_data["last_updated"] = date.today().isoformat()
        self._save_json(PUBLISHING_HISTORY, self.history_data)

    def _is_published(self, topic: str) -> bool:
        """주제가 이미 게시되었는지 확인"""
        return topic.lower() in self._published_topics

    def _get_sort_key(self, item: Dict) -> Tuple:
        """
        정렬 키 생성 (우선순위 기반)

        정렬 순서:
        1. scheduled_date (오늘/과거 먼저, 없으면 맨 뒤)
        2. priority (높을수록 앞)
        3. created_at (오래된 것 먼저)
        """
        today = date.today().isoformat()

        # scheduled_date 파싱
        scheduled = item.get("scheduled_date")
        if scheduled:
            # 오늘 이전이면 0, 미래면 날짜값
            is_due = 0 if scheduled <= today else 1
            date_value = scheduled
        else:
            # scheduled_date가 없으면 맨 뒤로
            is_due = 2
            date_value = "9999-12-31"

        # priority (높을수록 앞 = 음수로 변환)
        priority = -(item.get("priority", 5))

        # created_at (오래된 것 먼저)
        created = item.get("created_at", "9999-12-31")

        return (is_due, date_value, priority, created)

    def get_next_content(self) -> Optional[QueueItem]:
        """
        다음 게시할 콘텐츠 자동 선택

        우선순위:
        1. scheduled_date가 오늘이거나 지난 항목
        2. priority가 높은 항목
        3. 생성일이 오래된 항목

        Returns:
            다음 게시할 QueueItem, 없으면 None
        """
        # 데이터 새로고침
        self._load_data()

        # pending 상태인 항목만 필터링
        pending_items = [
            item for item in self.schedule_data.get("scheduled", [])
            if item.get("status") == "pending"
            and not self._is_published(item.get("topic", ""))
        ]

        if not pending_items:
            return None

        # 정렬
        pending_items.sort(key=self._get_sort_key)

        # 첫 번째 항목 반환
        return QueueItem.from_dict(pending_items[0])

    def get_due_contents(self, include_overdue: bool = True) -> List[QueueItem]:
        """
        게시 예정 콘텐츠 목록 조회

        Args:
            include_overdue: 기한 지난 항목 포함 여부

        Returns:
            게시 예정 QueueItem 목록
        """
        self._load_data()
        today = date.today().isoformat()

        due_items = []
        for item in self.schedule_data.get("scheduled", []):
            if item.get("status") != "pending":
                continue
            if self._is_published(item.get("topic", "")):
                continue

            scheduled = item.get("scheduled_date")
            if scheduled:
                if scheduled == today:
                    due_items.append(QueueItem.from_dict(item))
                elif include_overdue and scheduled < today:
                    due_items.append(QueueItem.from_dict(item))

        return sorted(due_items, key=lambda x: (x.scheduled_date or "", -x.priority))

    def add_to_queue(
        self,
        topic: str,
        topic_kr: str,
        scheduled_date: Optional[str] = None,
        scheduled_time: Optional[str] = None,
        priority: int = 5,
        note: Optional[str] = None
    ) -> QueueItem:
        """
        대기열에 콘텐츠 추가

        Args:
            topic: 영문 주제명
            topic_kr: 한글 주제명
            scheduled_date: 예정 날짜 (YYYY-MM-DD)
            scheduled_time: 예정 시간 (HH:MM, 기본값: 18:00)
            priority: 우선순위 (1~10, 기본값: 5)
            note: 메모

        Returns:
            추가된 QueueItem

        Raises:
            ValueError: 이미 게시된 주제인 경우
        """
        self._load_data()

        # 이미 게시된 주제 체크
        if self._is_published(topic):
            raise ValueError(f"이미 게시된 주제입니다: {topic}")

        # 중복 체크 (scheduled에 이미 있는지)
        existing = [
            item for item in self.schedule_data.get("scheduled", [])
            if item.get("topic", "").lower() == topic.lower()
        ]
        if existing:
            raise ValueError(f"이미 대기열에 있는 주제입니다: {topic}")

        # 새 ID 생성
        all_ids = [
            item.get("id", 0)
            for item in (
                self.schedule_data.get("scheduled", []) +
                self.schedule_data.get("completed", []) +
                self.schedule_data.get("failed", [])
            )
        ]
        new_id = max(all_ids, default=0) + 1

        # 기본 시간 설정
        if not scheduled_time:
            scheduled_time = self.schedule_data.get("settings", {}).get("default_time", "18:00")

        # 새 항목 생성
        new_item = QueueItem(
            id=new_id,
            topic=topic,
            topic_kr=topic_kr,
            status="pending",
            priority=priority,
            scheduled_date=scheduled_date,
            scheduled_time=scheduled_time,
            note=note
        )

        # scheduled 리스트에 추가
        self.schedule_data.setdefault("scheduled", []).append(new_item.to_dict())

        # pending 리스트에 추가 (history)
        if topic not in self.history_data.get("pending", []):
            self.history_data.setdefault("pending", []).append(topic)

        # 저장
        self._save_schedule()
        self._save_history()

        print(f"[+] 대기열 추가: {topic_kr} ({topic})")
        if scheduled_date:
            print(f"    예정일: {scheduled_date} {scheduled_time}")

        return new_item

    def mark_published(
        self,
        topic: str,
        instagram_url: Optional[str] = None,
        post_id: Optional[str] = None,
        score: int = 95
    ) -> bool:
        """
        게시 완료 처리

        Args:
            topic: 영문 주제명
            instagram_url: Instagram 게시물 URL
            post_id: Instagram post ID
            score: 품질 점수

        Returns:
            성공 여부
        """
        self._load_data()
        topic_lower = topic.lower()
        now = datetime.now()

        # scheduled에서 항목 찾기
        found_idx = None
        found_item = None
        for idx, item in enumerate(self.schedule_data.get("scheduled", [])):
            if item.get("topic", "").lower() == topic_lower:
                found_idx = idx
                found_item = item
                break

        if found_item:
            # completed로 이동
            completed_item = {
                **found_item,
                "status": "completed",
                "completed_at": now.isoformat(),
                "result": {
                    "instagram_url": instagram_url,
                    "post_id": post_id
                }
            }
            self.schedule_data.setdefault("completed", []).append(completed_item)
            self.schedule_data["scheduled"].pop(found_idx)

        # publishing_history 업데이트
        # 기존 항목 찾기
        existing_idx = None
        for idx, item in enumerate(self.history_data.get("published", [])):
            if item.get("topic", "").lower() == topic_lower:
                existing_idx = idx
                break

        # 주제의 한글명 찾기
        topic_kr = None
        if found_item:
            topic_kr = found_item.get("topic_kr")
        if not topic_kr:
            # completed에서 찾기
            for item in self.schedule_data.get("completed", []):
                if item.get("topic", "").lower() == topic_lower:
                    topic_kr = item.get("topic_kr")
                    break
        if not topic_kr:
            topic_kr = topic  # fallback

        new_published = {
            "topic": topic,
            "topic_kr": topic_kr,
            "date": now.strftime("%Y-%m-%d"),
            "instagram_url": instagram_url,
            "post_id": post_id,
            "score": score
        }

        if existing_idx is not None:
            self.history_data["published"][existing_idx] = new_published
        else:
            self.history_data.setdefault("published", []).append(new_published)

        # pending에서 제거
        self.history_data["pending"] = [
            p for p in self.history_data.get("pending", [])
            if p.lower() != topic_lower
        ]

        # _published_topics 업데이트
        self._published_topics.add(topic_lower)

        # 저장
        self._save_schedule()
        self._save_history()

        print(f"[v] 게시 완료 처리: {topic_kr} ({topic})")
        return True

    def mark_failed(
        self,
        topic: str,
        error_message: str,
        retry: bool = True
    ) -> bool:
        """
        게시 실패 처리

        Args:
            topic: 영문 주제명
            error_message: 에러 메시지
            retry: 재시도 여부 (True면 scheduled에 유지)

        Returns:
            성공 여부
        """
        self._load_data()
        topic_lower = topic.lower()
        now = datetime.now()

        max_retries = self.schedule_data.get("settings", {}).get("max_retries", 3)

        for idx, item in enumerate(self.schedule_data.get("scheduled", [])):
            if item.get("topic", "").lower() == topic_lower:
                retries = item.get("retries", 0) + 1

                if retry and retries < max_retries:
                    # 재시도 가능 - scheduled에 유지
                    item["retries"] = retries
                    item["updated_at"] = now.isoformat()
                    item["note"] = f"재시도 {retries}/{max_retries}: {error_message}"
                    print(f"[!] 게시 실패 (재시도 예정): {item.get('topic_kr')} - {retries}/{max_retries}")
                else:
                    # 최종 실패 - failed로 이동
                    failed_item = {
                        **item,
                        "status": "failed",
                        "failed_at": now.isoformat(),
                        "error": error_message,
                        "retries": retries
                    }
                    self.schedule_data.setdefault("failed", []).append(failed_item)
                    self.schedule_data["scheduled"].pop(idx)
                    print(f"[x] 게시 최종 실패: {item.get('topic_kr')}")

                self._save_schedule()
                return True

        print(f"[?] 대기열에서 찾을 수 없음: {topic}")
        return False

    def skip_content(self, topic: str, reason: str = "") -> bool:
        """
        콘텐츠 건너뛰기

        Args:
            topic: 영문 주제명
            reason: 건너뛰기 사유

        Returns:
            성공 여부
        """
        self._load_data()
        topic_lower = topic.lower()
        now = datetime.now()

        for idx, item in enumerate(self.schedule_data.get("scheduled", [])):
            if item.get("topic", "").lower() == topic_lower:
                item["status"] = "skipped"
                item["updated_at"] = now.isoformat()
                item["note"] = f"건너뜀: {reason}" if reason else "건너뜀"

                self._save_schedule()
                print(f"[-] 콘텐츠 건너뜀: {item.get('topic_kr')}")
                return True

        return False

    def update_priority(self, topic: str, priority: int) -> bool:
        """
        우선순위 변경

        Args:
            topic: 영문 주제명
            priority: 새 우선순위 (1~10)

        Returns:
            성공 여부
        """
        if not 1 <= priority <= 10:
            raise ValueError("우선순위는 1~10 사이여야 합니다")

        self._load_data()
        topic_lower = topic.lower()

        for item in self.schedule_data.get("scheduled", []):
            if item.get("topic", "").lower() == topic_lower:
                item["priority"] = priority
                item["updated_at"] = datetime.now().isoformat()
                self._save_schedule()
                print(f"[*] 우선순위 변경: {item.get('topic_kr')} -> {priority}")
                return True

        return False

    def reschedule(
        self,
        topic: str,
        new_date: str,
        new_time: Optional[str] = None
    ) -> bool:
        """
        일정 변경

        Args:
            topic: 영문 주제명
            new_date: 새 예정 날짜 (YYYY-MM-DD)
            new_time: 새 예정 시간 (HH:MM)

        Returns:
            성공 여부
        """
        self._load_data()
        topic_lower = topic.lower()

        for item in self.schedule_data.get("scheduled", []):
            if item.get("topic", "").lower() == topic_lower:
                item["scheduled_date"] = new_date
                if new_time:
                    item["scheduled_time"] = new_time
                item["updated_at"] = datetime.now().isoformat()
                self._save_schedule()
                print(f"[*] 일정 변경: {item.get('topic_kr')} -> {new_date} {new_time or ''}")
                return True

        return False

    def get_queue_status(self) -> Dict[str, Any]:
        """
        대기열 현황 조회

        Returns:
            대기열 통계 및 상세 정보
        """
        self._load_data()

        scheduled = self.schedule_data.get("scheduled", [])
        completed = self.schedule_data.get("completed", [])
        failed = self.schedule_data.get("failed", [])

        # 상태별 분류
        pending = [i for i in scheduled if i.get("status") == "pending"]
        in_progress = [i for i in scheduled if i.get("status") == "in_progress"]
        skipped = [i for i in scheduled if i.get("status") == "skipped"]

        # 오늘 예정
        today = date.today().isoformat()
        today_due = [
            i for i in pending
            if i.get("scheduled_date") == today
        ]

        # 연체 (기한 지남)
        overdue = [
            i for i in pending
            if i.get("scheduled_date") and i.get("scheduled_date") < today
        ]

        # 다음 콘텐츠
        next_content = self.get_next_content()

        return {
            "summary": {
                "pending": len(pending),
                "in_progress": len(in_progress),
                "completed": len(completed),
                "failed": len(failed),
                "skipped": len(skipped),
                "today_due": len(today_due),
                "overdue": len(overdue)
            },
            "next": next_content.to_dict() if next_content else None,
            "today_schedule": [QueueItem.from_dict(i).to_dict() for i in today_due],
            "overdue_items": [QueueItem.from_dict(i).to_dict() for i in overdue],
            "pending_items": [QueueItem.from_dict(i).to_dict() for i in pending[:10]],  # 상위 10개
            "settings": self.schedule_data.get("settings", {})
        }

    def print_status(self):
        """현황 출력"""
        status = self.get_queue_status()
        summary = status["summary"]

        print("\n" + "=" * 55)
        print(" ContentQueue - 대기열 현황")
        print("=" * 55)

        print(f"\n[ 전체 현황 ]")
        print(f"  대기중 (pending):   {summary['pending']:3d}개")
        print(f"  진행중 (in_progress): {summary['in_progress']:3d}개")
        print(f"  완료 (completed):   {summary['completed']:3d}개")
        print(f"  실패 (failed):      {summary['failed']:3d}개")
        print(f"  건너뜀 (skipped):   {summary['skipped']:3d}개")

        print(f"\n[ 긴급 현황 ]")
        print(f"  오늘 예정:         {summary['today_due']:3d}개")
        print(f"  연체 (기한 지남):    {summary['overdue']:3d}개")

        if status["next"]:
            next_item = status["next"]
            print(f"\n[ 다음 게시 예정 ]")
            print(f"  주제: {next_item.get('topic_kr')} ({next_item.get('topic')})")
            if next_item.get("scheduled_date"):
                print(f"  예정일: {next_item.get('scheduled_date')} {next_item.get('scheduled_time', '')}")
            print(f"  우선순위: {next_item.get('priority', 5)}")

        if status["overdue_items"]:
            print(f"\n[ 연체 항목 ]")
            for item in status["overdue_items"][:5]:
                print(f"  - {item['topic_kr']} (예정: {item['scheduled_date']})")

        print("\n" + "=" * 55)


# ============================================================
# 외부 호출용 헬퍼 함수
# ============================================================

def get_next_content() -> Optional[QueueItem]:
    """다음 게시할 콘텐츠 조회"""
    queue = ContentQueue()
    return queue.get_next_content()


def add_to_queue(
    topic: str,
    topic_kr: str,
    scheduled_date: Optional[str] = None,
    priority: int = 5,
    **kwargs
) -> QueueItem:
    """대기열에 콘텐츠 추가"""
    queue = ContentQueue()
    return queue.add_to_queue(topic, topic_kr, scheduled_date, priority=priority, **kwargs)


def mark_published(
    topic: str,
    instagram_url: Optional[str] = None,
    post_id: Optional[str] = None,
    score: int = 95
) -> bool:
    """게시 완료 처리"""
    queue = ContentQueue()
    return queue.mark_published(topic, instagram_url, post_id, score)


def get_queue_status() -> Dict[str, Any]:
    """대기열 현황 조회"""
    queue = ContentQueue()
    return queue.get_queue_status()


# ============================================================
# CLI / 테스트
# ============================================================

if __name__ == "__main__":
    import sys

    queue = ContentQueue()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "status":
            queue.print_status()

        elif cmd == "next":
            next_item = queue.get_next_content()
            if next_item:
                print(f"\n다음 게시 콘텐츠:")
                print(f"  주제: {next_item.topic_kr} ({next_item.topic})")
                print(f"  우선순위: {next_item.priority}")
                if next_item.scheduled_date:
                    print(f"  예정일: {next_item.scheduled_date} {next_item.scheduled_time or ''}")
            else:
                print("\n대기열이 비어있습니다.")

        elif cmd == "add" and len(sys.argv) >= 4:
            topic = sys.argv[2]
            topic_kr = sys.argv[3]
            scheduled = sys.argv[4] if len(sys.argv) > 4 else None
            try:
                item = queue.add_to_queue(topic, topic_kr, scheduled)
                print(f"\n추가됨: {item.topic_kr} (ID: {item.id})")
            except ValueError as e:
                print(f"\n오류: {e}")

        elif cmd == "publish" and len(sys.argv) >= 3:
            topic = sys.argv[2]
            url = sys.argv[3] if len(sys.argv) > 3 else None
            queue.mark_published(topic, instagram_url=url)

        else:
            print("사용법:")
            print("  python content_queue.py status          - 현황 조회")
            print("  python content_queue.py next            - 다음 콘텐츠")
            print("  python content_queue.py add <topic> <topic_kr> [date]")
            print("  python content_queue.py publish <topic> [url]")

    else:
        # 기본: 현황 출력
        queue.print_status()
