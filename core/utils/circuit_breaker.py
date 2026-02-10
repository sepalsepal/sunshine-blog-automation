"""
SunFlow Circuit Breaker (P2)
- API 장애 감지 및 자동 차단
- 점진적 복구 (Half-Open 상태)
- 장애 격리로 시스템 보호
"""

import time
import asyncio
from datetime import datetime, timedelta
from typing import Callable, Optional, Dict, Any
from dataclasses import dataclass, field
from enum import Enum
from functools import wraps
import json
from pathlib import Path

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent


class CircuitState(Enum):
    """회로 상태"""
    CLOSED = "closed"       # 정상 - 요청 허용
    OPEN = "open"           # 차단 - 요청 거부
    HALF_OPEN = "half_open" # 테스트 - 제한적 허용


@dataclass
class CircuitStats:
    """회로 통계"""
    total_calls: int = 0
    successful_calls: int = 0
    failed_calls: int = 0
    consecutive_failures: int = 0
    last_failure_time: Optional[datetime] = None
    last_success_time: Optional[datetime] = None
    state_changed_at: datetime = field(default_factory=datetime.now)


class CircuitBreaker:
    """
    서킷 브레이커 패턴 구현

    상태 전이:
    CLOSED → OPEN: 연속 실패 횟수 초과
    OPEN → HALF_OPEN: 대기 시간 경과
    HALF_OPEN → CLOSED: 테스트 성공
    HALF_OPEN → OPEN: 테스트 실패
    """

    # 기본 설정
    DEFAULT_FAILURE_THRESHOLD = 3       # 연속 실패 임계값
    DEFAULT_RECOVERY_TIMEOUT = 60       # OPEN 상태 유지 시간 (초)
    DEFAULT_HALF_OPEN_CALLS = 1         # HALF_OPEN에서 허용할 호출 수

    # 서비스별 회로
    _circuits: Dict[str, 'CircuitBreaker'] = {}

    def __init__(
        self,
        name: str,
        failure_threshold: int = None,
        recovery_timeout: int = None,
        half_open_calls: int = None
    ):
        self.name = name
        self.failure_threshold = failure_threshold or self.DEFAULT_FAILURE_THRESHOLD
        self.recovery_timeout = recovery_timeout or self.DEFAULT_RECOVERY_TIMEOUT
        self.half_open_calls = half_open_calls or self.DEFAULT_HALF_OPEN_CALLS

        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self._half_open_count = 0

        # 전역 레지스트리에 등록
        CircuitBreaker._circuits[name] = self

    @classmethod
    def get_circuit(cls, name: str) -> 'CircuitBreaker':
        """이름으로 회로 조회"""
        if name not in cls._circuits:
            cls._circuits[name] = CircuitBreaker(name)
        return cls._circuits[name]

    @classmethod
    def get_all_circuits(cls) -> Dict[str, 'CircuitBreaker']:
        """모든 회로 조회"""
        return cls._circuits

    def _should_allow_request(self) -> bool:
        """요청 허용 여부 판단"""
        if self.state == CircuitState.CLOSED:
            return True

        if self.state == CircuitState.OPEN:
            # 복구 대기 시간 확인
            if self.stats.last_failure_time:
                elapsed = (datetime.now() - self.stats.last_failure_time).total_seconds()
                if elapsed >= self.recovery_timeout:
                    self._transition_to(CircuitState.HALF_OPEN)
                    return True
            return False

        if self.state == CircuitState.HALF_OPEN:
            # 제한된 호출 허용
            if self._half_open_count < self.half_open_calls:
                self._half_open_count += 1
                return True
            return False

        return False

    def _transition_to(self, new_state: CircuitState):
        """상태 전이"""
        old_state = self.state
        self.state = new_state
        self.stats.state_changed_at = datetime.now()

        if new_state == CircuitState.HALF_OPEN:
            self._half_open_count = 0

        # 로깅
        self._log_transition(old_state, new_state)

    def _log_transition(self, old_state: CircuitState, new_state: CircuitState):
        """상태 전이 로깅"""
        log_file = PROJECT_ROOT / "config" / "logs" / "circuit_breaker.log"
        log_file.parent.mkdir(parents=True, exist_ok=True)

        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "circuit": self.name,
            "from_state": old_state.value,
            "to_state": new_state.value,
            "stats": {
                "total_calls": self.stats.total_calls,
                "failures": self.stats.failed_calls,
                "consecutive_failures": self.stats.consecutive_failures
            }
        }

        with open(log_file, 'a', encoding='utf-8') as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def record_success(self):
        """성공 기록"""
        self.stats.total_calls += 1
        self.stats.successful_calls += 1
        self.stats.consecutive_failures = 0
        self.stats.last_success_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            # 테스트 성공 - 회로 닫기
            self._transition_to(CircuitState.CLOSED)

    def record_failure(self, error: Exception = None):
        """실패 기록"""
        self.stats.total_calls += 1
        self.stats.failed_calls += 1
        self.stats.consecutive_failures += 1
        self.stats.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            # 테스트 실패 - 회로 다시 열기
            self._transition_to(CircuitState.OPEN)

        elif self.state == CircuitState.CLOSED:
            if self.stats.consecutive_failures >= self.failure_threshold:
                self._transition_to(CircuitState.OPEN)

    def call(self, func: Callable, *args, **kwargs) -> Any:
        """동기 함수 호출 (회로 보호)"""
        if not self._should_allow_request():
            raise CircuitOpenError(f"Circuit '{self.name}' is OPEN")

        try:
            result = func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(e)
            raise

    async def call_async(self, func: Callable, *args, **kwargs) -> Any:
        """비동기 함수 호출 (회로 보호)"""
        if not self._should_allow_request():
            raise CircuitOpenError(f"Circuit '{self.name}' is OPEN")

        try:
            result = await func(*args, **kwargs)
            self.record_success()
            return result
        except Exception as e:
            self.record_failure(e)
            raise

    def get_status(self) -> Dict:
        """회로 상태 조회"""
        return {
            "name": self.name,
            "state": self.state.value,
            "stats": {
                "total_calls": self.stats.total_calls,
                "successful_calls": self.stats.successful_calls,
                "failed_calls": self.stats.failed_calls,
                "consecutive_failures": self.stats.consecutive_failures,
                "success_rate": (
                    self.stats.successful_calls / self.stats.total_calls * 100
                    if self.stats.total_calls > 0 else 0
                )
            },
            "config": {
                "failure_threshold": self.failure_threshold,
                "recovery_timeout": self.recovery_timeout
            },
            "last_failure": self.stats.last_failure_time.isoformat() if self.stats.last_failure_time else None,
            "last_success": self.stats.last_success_time.isoformat() if self.stats.last_success_time else None
        }

    def reset(self):
        """회로 초기화"""
        self.state = CircuitState.CLOSED
        self.stats = CircuitStats()
        self._half_open_count = 0


class CircuitOpenError(Exception):
    """회로 열림 예외"""
    pass


def circuit_protected(circuit_name: str, failure_threshold: int = 3, recovery_timeout: int = 60):
    """서킷 브레이커 데코레이터"""
    def decorator(func):
        circuit = CircuitBreaker.get_circuit(circuit_name)
        circuit.failure_threshold = failure_threshold
        circuit.recovery_timeout = recovery_timeout

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            return circuit.call(func, *args, **kwargs)

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await circuit.call_async(func, *args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    return decorator


# 사전 정의된 회로
CIRCUITS = {
    "instagram": CircuitBreaker("instagram", failure_threshold=3, recovery_timeout=300),
    "cloudinary": CircuitBreaker("cloudinary", failure_threshold=3, recovery_timeout=120),
    "fal_ai": CircuitBreaker("fal_ai", failure_threshold=2, recovery_timeout=180),
    "telegram": CircuitBreaker("telegram", failure_threshold=5, recovery_timeout=60),
}


def get_all_circuit_status() -> Dict:
    """모든 회로 상태 조회"""
    return {
        name: circuit.get_status()
        for name, circuit in CircuitBreaker.get_all_circuits().items()
    }


# CLI 실행
if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "status":
            statuses = get_all_circuit_status()
            print("\n=== 서킷 브레이커 상태 ===\n")

            state_icons = {
                "closed": "🟢",
                "open": "🔴",
                "half_open": "🟡"
            }

            for name, status in statuses.items():
                icon = state_icons.get(status["state"], "❓")
                rate = status["stats"]["success_rate"]
                print(f"  {icon} {name}: {status['state']} | 성공률: {rate:.1f}% | 호출: {status['stats']['total_calls']}")

        elif cmd == "reset" and len(sys.argv) > 2:
            circuit_name = sys.argv[2]
            circuit = CircuitBreaker.get_circuit(circuit_name)
            circuit.reset()
            print(f"\n✅ 회로 초기화: {circuit_name}")

        elif cmd == "test":
            # 테스트
            @circuit_protected("test_circuit", failure_threshold=2, recovery_timeout=5)
            def test_function(should_fail: bool):
                if should_fail:
                    raise Exception("Test failure")
                return "Success"

            print("\n=== 서킷 브레이커 테스트 ===\n")

            # 정상 호출
            print("1. 정상 호출:", test_function(False))

            # 실패 호출
            for i in range(3):
                try:
                    test_function(True)
                except Exception as e:
                    print(f"{i+2}. 실패 호출:", str(e)[:50])

            # 차단 확인
            try:
                test_function(False)
            except CircuitOpenError as e:
                print(f"5. 차단됨:", str(e))

            print("\n✅ 테스트 완료")

        else:
            print("Usage: python circuit_breaker.py [status|reset <name>|test]")
    else:
        # 기본: 상태 표시
        statuses = get_all_circuit_status()
        total = len(statuses)
        healthy = len([s for s in statuses.values() if s["state"] == "closed"])
        print(f"\n서킷 브레이커: {healthy}/{total} CLOSED")
