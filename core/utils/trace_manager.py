"""
SunFlow Trace Manager (P0)
- 전 구간 통합 Trace ID 시스템
- 파이프라인 실행 추적 및 로깅
"""

import uuid
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
from contextlib import contextmanager
from functools import wraps

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent
LOG_DIR = PROJECT_ROOT / "config" / "logs" / "traces"


class TraceManager:
    """통합 Trace ID 관리자"""

    _current_trace_id: Optional[str] = None
    _trace_stack: list = []

    def __init__(self):
        self.log_dir = LOG_DIR
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.logger = self._setup_logger()

    def _setup_logger(self) -> logging.Logger:
        """트레이스 전용 로거 설정"""
        logger = logging.getLogger("sunflow.trace")
        logger.setLevel(logging.DEBUG)

        if not logger.handlers:
            # 파일 핸들러
            log_file = self.log_dir / f"trace_{datetime.now().strftime('%Y%m%d')}.log"
            fh = logging.FileHandler(log_file, encoding='utf-8')
            fh.setLevel(logging.DEBUG)

            # 포맷터
            formatter = logging.Formatter(
                '%(asctime)s | %(trace_id)s | %(levelname)s | %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            fh.setFormatter(formatter)
            logger.addHandler(fh)

        return logger

    @classmethod
    def generate_trace_id(cls) -> str:
        """새 Trace ID 생성 (형식: SF-YYYYMMDD-XXXXXX)"""
        date_part = datetime.now().strftime('%Y%m%d')
        uuid_part = uuid.uuid4().hex[:6].upper()
        return f"SF-{date_part}-{uuid_part}"

    @classmethod
    def get_current_trace_id(cls) -> Optional[str]:
        """현재 활성 Trace ID 반환"""
        return cls._current_trace_id

    @classmethod
    def set_trace_id(cls, trace_id: str):
        """Trace ID 설정"""
        cls._current_trace_id = trace_id

    @classmethod
    @contextmanager
    def trace_context(cls, trace_id: Optional[str] = None, operation: str = "unknown"):
        """Trace 컨텍스트 매니저"""
        if trace_id is None:
            trace_id = cls.generate_trace_id()

        # 스택에 푸시
        cls._trace_stack.append(cls._current_trace_id)
        cls._current_trace_id = trace_id

        manager = cls()
        manager.log_event("TRACE_START", {"operation": operation})

        try:
            yield trace_id
        except Exception as e:
            manager.log_event("TRACE_ERROR", {"operation": operation, "error": str(e)})
            raise
        finally:
            manager.log_event("TRACE_END", {"operation": operation})
            # 스택에서 팝
            cls._current_trace_id = cls._trace_stack.pop() if cls._trace_stack else None

    def log_event(self, event_type: str, data: Dict[str, Any] = None):
        """이벤트 로깅"""
        trace_id = self._current_trace_id or "NO-TRACE"

        log_data = {
            "event": event_type,
            "timestamp": datetime.now().isoformat(),
            "data": data or {}
        }

        # 로거에 trace_id 추가
        extra = {"trace_id": trace_id}
        self.logger.info(json.dumps(log_data, ensure_ascii=False), extra=extra)

        # 상세 로그 파일 저장
        self._save_trace_detail(trace_id, log_data)

    def _save_trace_detail(self, trace_id: str, log_data: Dict):
        """트레이스 상세 로그 저장"""
        if trace_id == "NO-TRACE":
            return

        trace_file = self.log_dir / f"{trace_id}.json"

        # 기존 데이터 로드 또는 새로 생성
        if trace_file.exists():
            with open(trace_file, 'r', encoding='utf-8') as f:
                trace_data = json.load(f)
        else:
            trace_data = {
                "trace_id": trace_id,
                "created_at": datetime.now().isoformat(),
                "events": []
            }

        # 이벤트 추가
        trace_data["events"].append(log_data)
        trace_data["updated_at"] = datetime.now().isoformat()

        # 저장
        with open(trace_file, 'w', encoding='utf-8') as f:
            json.dump(trace_data, f, ensure_ascii=False, indent=2)

    def get_trace_history(self, trace_id: str) -> Optional[Dict]:
        """특정 Trace ID의 히스토리 조회"""
        trace_file = self.log_dir / f"{trace_id}.json"

        if trace_file.exists():
            with open(trace_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return None

    def get_recent_traces(self, limit: int = 10) -> list:
        """최근 트레이스 목록 조회"""
        trace_files = sorted(
            self.log_dir.glob("SF-*.json"),
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:limit]

        traces = []
        for tf in trace_files:
            with open(tf, 'r', encoding='utf-8') as f:
                data = json.load(f)
                traces.append({
                    "trace_id": data["trace_id"],
                    "created_at": data["created_at"],
                    "event_count": len(data["events"]),
                    "last_event": data["events"][-1]["event"] if data["events"] else None
                })

        return traces


def traced(operation: str = None):
    """함수 트레이싱 데코레이터"""
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            op_name = operation or func.__name__

            with TraceManager.trace_context(operation=op_name) as trace_id:
                manager = TraceManager()
                manager.log_event("FUNC_CALL", {
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                })

                result = func(*args, **kwargs)

                manager.log_event("FUNC_RETURN", {
                    "function": func.__name__,
                    "success": True
                })

                return result

        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            op_name = operation or func.__name__

            with TraceManager.trace_context(operation=op_name) as trace_id:
                manager = TraceManager()
                manager.log_event("ASYNC_FUNC_CALL", {
                    "function": func.__name__,
                    "args_count": len(args),
                    "kwargs_keys": list(kwargs.keys())
                })

                result = await func(*args, **kwargs)

                manager.log_event("ASYNC_FUNC_RETURN", {
                    "function": func.__name__,
                    "success": True
                })

                return result

        # 비동기 함수인지 확인
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return wrapper

    return decorator


# 편의 함수
def get_trace_id() -> Optional[str]:
    """현재 Trace ID 가져오기"""
    return TraceManager.get_current_trace_id()


def log_trace_event(event_type: str, data: Dict[str, Any] = None):
    """트레이스 이벤트 로깅"""
    TraceManager().log_event(event_type, data)


# CLI 실행
if __name__ == "__main__":
    import sys

    manager = TraceManager()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "list":
            traces = manager.get_recent_traces(20)
            print("\n=== 최근 Trace 목록 ===\n")
            for t in traces:
                print(f"  {t['trace_id']} | {t['created_at'][:19]} | {t['event_count']} events | {t['last_event']}")

        elif cmd == "show" and len(sys.argv) > 2:
            trace_id = sys.argv[2]
            history = manager.get_trace_history(trace_id)
            if history:
                print(f"\n=== Trace: {trace_id} ===\n")
                print(json.dumps(history, ensure_ascii=False, indent=2))
            else:
                print(f"Trace not found: {trace_id}")

        elif cmd == "test":
            # 테스트 트레이스 생성
            with TraceManager.trace_context(operation="test_operation") as trace_id:
                print(f"Test Trace ID: {trace_id}")
                log_trace_event("TEST_EVENT", {"message": "테스트 이벤트"})
            print("Test trace created successfully!")

        else:
            print("Usage: python trace_manager.py [list|show <trace_id>|test]")
    else:
        print("Usage: python trace_manager.py [list|show <trace_id>|test]")
