"""
RetryAgent - 실패 자동 재시도 에이전트
Project Sunshine Agent System
이름: 이리트라이

역할:
- 실패한 작업 자동 재시도
- 지수 백오프 전략
- 실패 원인 분석
- 복구 가능 여부 판단
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
from enum import Enum
import traceback

from .base import BaseAgent, AgentResult, AgentStatus


class FailureType(Enum):
    """실패 유형 분류"""
    NETWORK = "network"           # 네트워크 오류 - 재시도 가능
    API_RATE_LIMIT = "rate_limit" # API 제한 - 대기 후 재시도
    AUTH = "authentication"       # 인증 오류 - 재시도 불가
    VALIDATION = "validation"     # 검증 오류 - 재시도 불가
    RESOURCE = "resource"         # 리소스 부족 - 재시도 가능
    TIMEOUT = "timeout"           # 타임아웃 - 재시도 가능
    UNKNOWN = "unknown"           # 알 수 없음 - 제한적 재시도


class RetryStrategy(Enum):
    """재시도 전략"""
    IMMEDIATE = "immediate"       # 즉시 재시도
    LINEAR = "linear"             # 선형 대기
    EXPONENTIAL = "exponential"   # 지수 백오프
    FIBONACCI = "fibonacci"       # 피보나치 백오프


class RetryAgent(BaseAgent):
    """
    실패 자동 재시도 전문 에이전트 (이리트라이)

    기능:
    1. 실패한 작업 자동 재시도
    2. 지능적 백오프 전략
    3. 실패 원인 분석 및 분류
    4. 복구 가능 여부 자동 판단
    """

    # 실패 유형별 재시도 설정
    RETRY_CONFIG = {
        FailureType.NETWORK: {
            "max_retries": 5,
            "strategy": RetryStrategy.EXPONENTIAL,
            "base_delay": 1.0,
            "max_delay": 60.0
        },
        FailureType.API_RATE_LIMIT: {
            "max_retries": 3,
            "strategy": RetryStrategy.EXPONENTIAL,
            "base_delay": 60.0,
            "max_delay": 300.0
        },
        FailureType.AUTH: {
            "max_retries": 0,  # 재시도 불가
            "strategy": RetryStrategy.IMMEDIATE,
            "base_delay": 0,
            "max_delay": 0
        },
        FailureType.VALIDATION: {
            "max_retries": 0,  # 재시도 불가
            "strategy": RetryStrategy.IMMEDIATE,
            "base_delay": 0,
            "max_delay": 0
        },
        FailureType.RESOURCE: {
            "max_retries": 3,
            "strategy": RetryStrategy.LINEAR,
            "base_delay": 5.0,
            "max_delay": 30.0
        },
        FailureType.TIMEOUT: {
            "max_retries": 3,
            "strategy": RetryStrategy.EXPONENTIAL,
            "base_delay": 2.0,
            "max_delay": 30.0
        },
        FailureType.UNKNOWN: {
            "max_retries": 2,
            "strategy": RetryStrategy.EXPONENTIAL,
            "base_delay": 5.0,
            "max_delay": 60.0
        }
    }

    # 에러 메시지 패턴 → 실패 유형 매핑
    ERROR_PATTERNS = {
        FailureType.NETWORK: [
            "connection", "network", "unreachable", "dns", "socket",
            "ConnectionError", "TimeoutError", "네트워크"
        ],
        FailureType.API_RATE_LIMIT: [
            "rate limit", "too many requests", "429", "quota",
            "limit exceeded", "throttle"
        ],
        FailureType.AUTH: [
            "unauthorized", "401", "403", "forbidden", "invalid token",
            "authentication", "access denied", "인증"
        ],
        FailureType.VALIDATION: [
            "validation", "invalid", "required field", "format error",
            "type error", "검증"
        ],
        FailureType.RESOURCE: [
            "memory", "disk", "storage", "resource", "capacity",
            "메모리", "저장공간"
        ],
        FailureType.TIMEOUT: [
            "timeout", "timed out", "deadline", "시간 초과"
        ]
    }

    def __init__(self, config_path: Optional[str] = None):
        super().__init__(config_path)
        self._failed_tasks_file = Path(__file__).parent.parent / "logs" / "failed_tasks.json"
        self._retry_history_file = Path(__file__).parent.parent / "logs" / "retry_history.json"
        self._failed_tasks = []
        self._retry_history = []
        self._load_state()

    @property
    def name(self) -> str:
        return "RetryAgent"

    def _load_state(self) -> None:
        """저장된 상태 로드"""
        try:
            if self._failed_tasks_file.exists():
                with open(self._failed_tasks_file, 'r', encoding='utf-8') as f:
                    self._failed_tasks = json.load(f)

            if self._retry_history_file.exists():
                with open(self._retry_history_file, 'r', encoding='utf-8') as f:
                    self._retry_history = json.load(f)
        except Exception as e:
            self.log(f"상태 로드 실패: {e}", level="warning")

    def _save_state(self) -> None:
        """상태 저장"""
        try:
            # logs 디렉토리 생성
            self._failed_tasks_file.parent.mkdir(parents=True, exist_ok=True)

            with open(self._failed_tasks_file, 'w', encoding='utf-8') as f:
                json.dump(self._failed_tasks, f, ensure_ascii=False, indent=2, default=str)

            with open(self._retry_history_file, 'w', encoding='utf-8') as f:
                json.dump(self._retry_history, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            self.log(f"상태 저장 실패: {e}", level="error")

    def classify_failure(self, error: Union[str, Exception]) -> FailureType:
        """
        에러를 분석하여 실패 유형 분류

        Args:
            error: 에러 메시지 또는 예외

        Returns:
            실패 유형
        """
        error_str = str(error).lower()

        for failure_type, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in error_str:
                    return failure_type

        return FailureType.UNKNOWN

    def calculate_delay(
        self,
        strategy: RetryStrategy,
        attempt: int,
        base_delay: float,
        max_delay: float
    ) -> float:
        """
        재시도 대기 시간 계산

        Args:
            strategy: 재시도 전략
            attempt: 현재 시도 횟수 (1부터 시작)
            base_delay: 기본 대기 시간
            max_delay: 최대 대기 시간

        Returns:
            대기 시간 (초)
        """
        if strategy == RetryStrategy.IMMEDIATE:
            delay = 0
        elif strategy == RetryStrategy.LINEAR:
            delay = base_delay * attempt
        elif strategy == RetryStrategy.EXPONENTIAL:
            delay = base_delay * (2 ** (attempt - 1))
        elif strategy == RetryStrategy.FIBONACCI:
            # 피보나치 수열 기반
            fib = [1, 1]
            for _ in range(attempt - 1):
                fib.append(fib[-1] + fib[-2])
            delay = base_delay * fib[min(attempt, len(fib) - 1)]
        else:
            delay = base_delay

        return min(delay, max_delay)

    def is_recoverable(self, failure_type: FailureType) -> bool:
        """복구 가능한 실패인지 확인"""
        config = self.RETRY_CONFIG.get(failure_type, {})
        return config.get("max_retries", 0) > 0

    def add_failed_task(
        self,
        task_id: str,
        task_type: str,
        input_data: Any,
        error: str,
        agent_name: Optional[str] = None
    ) -> Dict:
        """
        실패한 작업 등록

        Args:
            task_id: 작업 ID
            task_type: 작업 유형
            input_data: 입력 데이터
            error: 에러 메시지
            agent_name: 실패한 에이전트 이름

        Returns:
            등록된 작업 정보
        """
        failure_type = self.classify_failure(error)
        config = self.RETRY_CONFIG.get(failure_type, {})

        task = {
            "task_id": task_id,
            "task_type": task_type,
            "input_data": input_data,
            "error": error,
            "failure_type": failure_type.value,
            "agent_name": agent_name,
            "is_recoverable": self.is_recoverable(failure_type),
            "max_retries": config.get("max_retries", 0),
            "retry_count": 0,
            "status": "pending" if self.is_recoverable(failure_type) else "unrecoverable",
            "created_at": datetime.now().isoformat(),
            "last_retry": None,
            "next_retry": None
        }

        # 복구 가능하면 다음 재시도 시간 계산
        if task["is_recoverable"]:
            delay = self.calculate_delay(
                strategy=RetryStrategy(config.get("strategy", RetryStrategy.EXPONENTIAL).value),
                attempt=1,
                base_delay=config.get("base_delay", 1.0),
                max_delay=config.get("max_delay", 60.0)
            )
            task["next_retry"] = (datetime.now() + timedelta(seconds=delay)).isoformat()

        self._failed_tasks.append(task)
        self._save_state()

        self.log(f"실패 작업 등록: {task_id} ({failure_type.value})")
        return task

    def get_pending_retries(self) -> List[Dict]:
        """재시도 대기 중인 작업 목록"""
        now = datetime.now()
        pending = []

        for task in self._failed_tasks:
            if task["status"] == "pending":
                next_retry = task.get("next_retry")
                if next_retry:
                    retry_time = datetime.fromisoformat(next_retry)
                    if retry_time <= now:
                        pending.append(task)

        return pending

    async def retry_task(
        self,
        task: Dict,
        executor: Optional[Callable] = None
    ) -> AgentResult:
        """
        단일 작업 재시도

        Args:
            task: 재시도할 작업
            executor: 실행 함수 (None이면 시뮬레이션)

        Returns:
            재시도 결과
        """
        task_id = task["task_id"]
        failure_type = FailureType(task["failure_type"])
        config = self.RETRY_CONFIG.get(failure_type, {})

        # 재시도 횟수 확인
        if task["retry_count"] >= task["max_retries"]:
            task["status"] = "exhausted"
            self._save_state()
            return AgentResult(
                success=False,
                error=f"최대 재시도 횟수 초과 ({task['max_retries']}회)",
                metadata={"task_id": task_id, "final_status": "exhausted"}
            )

        # 재시도 실행
        task["retry_count"] += 1
        task["last_retry"] = datetime.now().isoformat()

        self.log(f"재시도 #{task['retry_count']}: {task_id}")

        try:
            if executor:
                result = await executor(task["input_data"])
            else:
                # 시뮬레이션 모드
                result = AgentResult(
                    success=True,
                    data={"simulated": True, "task_id": task_id}
                )

            if result.success:
                task["status"] = "recovered"
                self._retry_history.append({
                    "task_id": task_id,
                    "recovered_at": datetime.now().isoformat(),
                    "retry_count": task["retry_count"],
                    "failure_type": task["failure_type"]
                })
                self.log(f"복구 성공: {task_id} ({task['retry_count']}회 시도)")
            else:
                # 다음 재시도 예약
                delay = self.calculate_delay(
                    strategy=RetryStrategy(config.get("strategy", "exponential")),
                    attempt=task["retry_count"] + 1,
                    base_delay=config.get("base_delay", 1.0),
                    max_delay=config.get("max_delay", 60.0)
                )
                task["next_retry"] = (datetime.now() + timedelta(seconds=delay)).isoformat()
                self.log(f"재시도 실패: {task_id}, 다음 시도: {delay}초 후")

            self._save_state()
            return result

        except Exception as e:
            self.log(f"재시도 중 오류: {e}", level="error")

            # 다음 재시도 예약
            delay = self.calculate_delay(
                strategy=RetryStrategy(config.get("strategy", "exponential")),
                attempt=task["retry_count"] + 1,
                base_delay=config.get("base_delay", 1.0),
                max_delay=config.get("max_delay", 60.0)
            )
            task["next_retry"] = (datetime.now() + timedelta(seconds=delay)).isoformat()
            self._save_state()

            return AgentResult(
                success=False,
                error=str(e),
                metadata={"task_id": task_id, "retry_count": task["retry_count"]}
            )

    async def process_all_pending(self) -> Dict:
        """대기 중인 모든 재시도 처리"""
        pending = self.get_pending_retries()

        if not pending:
            return {
                "processed": 0,
                "recovered": 0,
                "failed": 0,
                "message": "재시도할 작업이 없습니다"
            }

        results = {
            "processed": len(pending),
            "recovered": 0,
            "failed": 0,
            "details": []
        }

        for task in pending:
            result = await self.retry_task(task)
            detail = {
                "task_id": task["task_id"],
                "success": result.success,
                "retry_count": task["retry_count"]
            }

            if result.success:
                results["recovered"] += 1
            else:
                results["failed"] += 1
                detail["error"] = result.error

            results["details"].append(detail)

        return results

    def get_statistics(self) -> Dict:
        """재시도 통계"""
        total = len(self._failed_tasks)
        pending = sum(1 for t in self._failed_tasks if t["status"] == "pending")
        recovered = sum(1 for t in self._failed_tasks if t["status"] == "recovered")
        exhausted = sum(1 for t in self._failed_tasks if t["status"] == "exhausted")
        unrecoverable = sum(1 for t in self._failed_tasks if t["status"] == "unrecoverable")

        # 실패 유형별 통계
        by_type = {}
        for task in self._failed_tasks:
            ft = task["failure_type"]
            if ft not in by_type:
                by_type[ft] = {"total": 0, "recovered": 0}
            by_type[ft]["total"] += 1
            if task["status"] == "recovered":
                by_type[ft]["recovered"] += 1

        return {
            "total_failures": total,
            "pending": pending,
            "recovered": recovered,
            "exhausted": exhausted,
            "unrecoverable": unrecoverable,
            "recovery_rate": round(recovered / total * 100, 1) if total > 0 else 0,
            "by_failure_type": by_type
        }

    def clear_resolved(self) -> int:
        """해결된 작업 정리"""
        before = len(self._failed_tasks)
        self._failed_tasks = [
            t for t in self._failed_tasks
            if t["status"] not in ["recovered", "exhausted", "unrecoverable"]
        ]
        removed = before - len(self._failed_tasks)
        self._save_state()
        return removed

    async def execute(self, input_data: Any) -> AgentResult:
        """
        재시도 작업 실행

        input_data 형식:
        {
            "action": "add" | "retry" | "process_all" | "stats" | "clear",
            "task_id": "...",
            "task_type": "...",
            "input_data": {...},
            "error": "..."
        }
        """
        try:
            action = input_data.get("action", "stats")

            if action == "add":
                task = self.add_failed_task(
                    task_id=input_data.get("task_id", f"task_{datetime.now().strftime('%Y%m%d%H%M%S')}"),
                    task_type=input_data.get("task_type", "unknown"),
                    input_data=input_data.get("task_input", {}),
                    error=input_data.get("error", "Unknown error"),
                    agent_name=input_data.get("agent_name")
                )

                return AgentResult(
                    success=True,
                    data=task,
                    metadata={"action": action}
                )

            elif action == "retry":
                task_id = input_data.get("task_id")
                task = next((t for t in self._failed_tasks if t["task_id"] == task_id), None)

                if not task:
                    return AgentResult(
                        success=False,
                        error=f"작업을 찾을 수 없습니다: {task_id}"
                    )

                result = await self.retry_task(task)
                return result

            elif action == "process_all":
                results = await self.process_all_pending()

                return AgentResult(
                    success=True,
                    data=results,
                    metadata={"action": action}
                )

            elif action == "stats":
                return AgentResult(
                    success=True,
                    data=self.get_statistics(),
                    metadata={"action": action}
                )

            elif action == "clear":
                removed = self.clear_resolved()

                return AgentResult(
                    success=True,
                    data={"removed_count": removed},
                    metadata={"action": action}
                )

            elif action == "list":
                status_filter = input_data.get("status")
                tasks = self._failed_tasks
                if status_filter:
                    tasks = [t for t in tasks if t["status"] == status_filter]

                return AgentResult(
                    success=True,
                    data={"tasks": tasks, "count": len(tasks)},
                    metadata={"action": action}
                )

            else:
                return AgentResult(
                    success=False,
                    error=f"알 수 없는 액션: {action}"
                )

        except Exception as e:
            self.log(f"재시도 에이전트 오류: {e}", level="error")
            return AgentResult(
                success=False,
                error=str(e)
            )


# 테스트용 코드
if __name__ == "__main__":
    async def test():
        agent = RetryAgent()

        # 실패 작업 등록 테스트
        result = await agent.run({
            "action": "add",
            "task_id": "post_001",
            "task_type": "instagram_post",
            "task_input": {"topic": "banana"},
            "error": "Connection timeout: network unreachable",
            "agent_name": "PublisherAgent"
        })
        print("작업 등록:", result)

        # 통계 확인
        result = await agent.run({"action": "stats"})
        print("통계:", result)

        # 모든 대기 중 작업 처리
        result = await agent.run({"action": "process_all"})
        print("처리 결과:", result)

    asyncio.run(test())
