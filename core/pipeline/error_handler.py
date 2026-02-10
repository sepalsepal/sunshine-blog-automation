"""
Error Handler - 중앙 집중식 에러 처리 시스템
Project Sunshine Pipeline System

기능:
- 전역 예외 처리
- 에러 분류 및 로깅
- 복구 전략 실행
- 알림 시스템 연동
"""

import asyncio
import json
import traceback
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union
import functools


class ErrorSeverity(Enum):
    """에러 심각도"""
    DEBUG = "debug"
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """에러 카테고리"""
    NETWORK = "network"
    API = "api"
    FILE_IO = "file_io"
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    RATE_LIMIT = "rate_limit"
    TIMEOUT = "timeout"
    RESOURCE = "resource"
    CONFIGURATION = "configuration"
    UNKNOWN = "unknown"


class PipelineError(Exception):
    """파이프라인 커스텀 예외"""

    def __init__(
        self,
        message: str,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        severity: ErrorSeverity = ErrorSeverity.ERROR,
        context: Optional[Dict] = None,
        recoverable: bool = True
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.context = context or {}
        self.recoverable = recoverable
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "message": self.message,
            "category": self.category.value,
            "severity": self.severity.value,
            "context": self.context,
            "recoverable": self.recoverable,
            "timestamp": self.timestamp.isoformat()
        }


class ErrorHandler:
    """
    중앙 집중식 에러 처리기

    사용법:
        handler = ErrorHandler()

        # 데코레이터로 사용
        @handler.catch_errors
        async def my_function():
            ...

        # 컨텍스트 매니저로 사용
        async with handler.error_context("작업명"):
            ...
    """

    # 에러 패턴 → 카테고리 매핑
    ERROR_PATTERNS = {
        ErrorCategory.NETWORK: [
            "connection", "network", "dns", "socket", "unreachable",
            "ConnectionError", "ConnectionRefusedError"
        ],
        ErrorCategory.API: [
            "api", "response", "status code", "json", "parse"
        ],
        ErrorCategory.RATE_LIMIT: [
            "rate limit", "429", "too many requests", "throttle", "quota"
        ],
        ErrorCategory.AUTHENTICATION: [
            "401", "403", "unauthorized", "forbidden", "token", "auth"
        ],
        ErrorCategory.TIMEOUT: [
            "timeout", "timed out", "deadline"
        ],
        ErrorCategory.FILE_IO: [
            "file", "permission", "directory", "path", "not found",
            "FileNotFoundError", "PermissionError", "IOError"
        ],
        ErrorCategory.VALIDATION: [
            "validation", "invalid", "required", "missing", "format"
        ],
        ErrorCategory.RESOURCE: [
            "memory", "disk", "space", "resource", "limit"
        ],
        ErrorCategory.CONFIGURATION: [
            "config", "setting", "environment", "variable"
        ]
    }

    def __init__(self, log_dir: Optional[Path] = None):
        self._log_dir = log_dir or Path(__file__).parent.parent / "logs"
        self._log_dir.mkdir(parents=True, exist_ok=True)

        self._error_log_file = self._log_dir / "errors.json"
        self._error_history: List[Dict] = []
        self._callbacks: Dict[ErrorSeverity, List[Callable]] = {
            severity: [] for severity in ErrorSeverity
        }
        self._recovery_strategies: Dict[ErrorCategory, Callable] = {}

        self._load_history()

    def _load_history(self) -> None:
        """에러 히스토리 로드"""
        if self._error_log_file.exists():
            try:
                with open(self._error_log_file, 'r', encoding='utf-8') as f:
                    self._error_history = json.load(f)
            except Exception:
                self._error_history = []

    def _save_error(self, error_data: Dict) -> None:
        """에러 저장"""
        self._error_history.append(error_data)

        # 최근 1000개만 유지
        if len(self._error_history) > 1000:
            self._error_history = self._error_history[-1000:]

        try:
            with open(self._error_log_file, 'w', encoding='utf-8') as f:
                json.dump(self._error_history, f, ensure_ascii=False, indent=2, default=str)
        except Exception as e:
            print(f"에러 로그 저장 실패: {e}")

    def classify_error(self, error: Union[Exception, str]) -> ErrorCategory:
        """에러를 카테고리로 분류"""
        error_str = str(error).lower()
        error_type = type(error).__name__.lower() if isinstance(error, Exception) else ""

        for category, patterns in self.ERROR_PATTERNS.items():
            for pattern in patterns:
                if pattern.lower() in error_str or pattern.lower() in error_type:
                    return category

        return ErrorCategory.UNKNOWN

    def determine_severity(
        self,
        error: Exception,
        category: ErrorCategory
    ) -> ErrorSeverity:
        """에러 심각도 결정"""
        # CRITICAL 조건
        critical_categories = [
            ErrorCategory.AUTHENTICATION,
            ErrorCategory.CONFIGURATION
        ]
        if category in critical_categories:
            return ErrorSeverity.CRITICAL

        # ERROR 조건 (기본)
        if isinstance(error, (RuntimeError, SystemError)):
            return ErrorSeverity.ERROR

        # WARNING 조건
        warning_categories = [
            ErrorCategory.RATE_LIMIT,
            ErrorCategory.TIMEOUT
        ]
        if category in warning_categories:
            return ErrorSeverity.WARNING

        return ErrorSeverity.ERROR

    def handle_error(
        self,
        error: Exception,
        context: Optional[Dict] = None,
        reraise: bool = False
    ) -> Dict:
        """
        에러 처리 메인 함수

        Args:
            error: 발생한 예외
            context: 추가 컨텍스트 정보
            reraise: 에러 재발생 여부

        Returns:
            처리된 에러 정보
        """
        # PipelineError인 경우 그대로 사용
        if isinstance(error, PipelineError):
            category = error.category
            severity = error.severity
            error_data = error.to_dict()
        else:
            # 일반 에러 분류
            category = self.classify_error(error)
            severity = self.determine_severity(error, category)

            error_data = {
                "message": str(error),
                "type": type(error).__name__,
                "category": category.value,
                "severity": severity.value,
                "context": context or {},
                "traceback": traceback.format_exc(),
                "timestamp": datetime.now().isoformat()
            }

        # 로그 저장
        self._save_error(error_data)

        # 콜백 실행
        for callback in self._callbacks.get(severity, []):
            try:
                callback(error_data)
            except Exception as cb_error:
                print(f"에러 콜백 실패: {cb_error}")

        # 복구 전략 실행
        if category in self._recovery_strategies:
            try:
                self._recovery_strategies[category](error, context)
            except Exception as recovery_error:
                print(f"복구 전략 실패: {recovery_error}")

        # 에러 재발생
        if reraise:
            raise error

        return error_data

    def register_callback(
        self,
        severity: ErrorSeverity,
        callback: Callable[[Dict], None]
    ) -> None:
        """특정 심각도에 콜백 등록"""
        self._callbacks[severity].append(callback)

    def register_recovery_strategy(
        self,
        category: ErrorCategory,
        strategy: Callable[[Exception, Optional[Dict]], None]
    ) -> None:
        """카테고리별 복구 전략 등록"""
        self._recovery_strategies[category] = strategy

    def catch_errors(self, func: Callable) -> Callable:
        """
        에러 캐칭 데코레이터

        사용법:
            @error_handler.catch_errors
            async def my_function():
                ...
        """
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                self.handle_error(e, context={"function": func.__name__, "args": str(args)[:200]})
                raise

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                self.handle_error(e, context={"function": func.__name__, "args": str(args)[:200]})
                raise

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    class ErrorContext:
        """에러 컨텍스트 매니저"""

        def __init__(self, handler: 'ErrorHandler', operation: str, context: Optional[Dict] = None):
            self.handler = handler
            self.operation = operation
            self.context = context or {}

        async def __aenter__(self):
            return self

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            if exc_val is not None:
                self.handler.handle_error(
                    exc_val,
                    context={**self.context, "operation": self.operation}
                )
            return False  # 에러 전파

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            if exc_val is not None:
                self.handler.handle_error(
                    exc_val,
                    context={**self.context, "operation": self.operation}
                )
            return False

    def error_context(self, operation: str, context: Optional[Dict] = None):
        """에러 컨텍스트 매니저 생성"""
        return self.ErrorContext(self, operation, context)

    def get_recent_errors(
        self,
        count: int = 10,
        severity: Optional[ErrorSeverity] = None,
        category: Optional[ErrorCategory] = None
    ) -> List[Dict]:
        """최근 에러 조회"""
        errors = self._error_history

        if severity:
            errors = [e for e in errors if e.get("severity") == severity.value]

        if category:
            errors = [e for e in errors if e.get("category") == category.value]

        return errors[-count:]

    def get_error_statistics(self) -> Dict:
        """에러 통계"""
        if not self._error_history:
            return {"total": 0, "by_severity": {}, "by_category": {}}

        by_severity = {}
        by_category = {}

        for error in self._error_history:
            sev = error.get("severity", "unknown")
            cat = error.get("category", "unknown")

            by_severity[sev] = by_severity.get(sev, 0) + 1
            by_category[cat] = by_category.get(cat, 0) + 1

        return {
            "total": len(self._error_history),
            "by_severity": by_severity,
            "by_category": by_category
        }

    def clear_history(self) -> int:
        """에러 히스토리 초기화"""
        count = len(self._error_history)
        self._error_history = []
        self._save_error({})  # 빈 파일로 저장
        return count


# 전역 에러 핸들러 인스턴스
error_handler = ErrorHandler()


# 편의 함수들
def handle_error(error: Exception, context: Optional[Dict] = None) -> Dict:
    """전역 에러 처리"""
    return error_handler.handle_error(error, context)


def catch_errors(func: Callable) -> Callable:
    """에러 캐칭 데코레이터"""
    return error_handler.catch_errors(func)


def get_error_stats() -> Dict:
    """에러 통계 조회"""
    return error_handler.get_error_statistics()


# 테스트 코드
if __name__ == "__main__":
    async def test():
        handler = ErrorHandler()

        # 콜백 등록 테스트
        def critical_callback(error_data):
            print(f"CRITICAL 에러 발생: {error_data['message']}")

        handler.register_callback(ErrorSeverity.CRITICAL, critical_callback)

        # 에러 분류 테스트
        test_errors = [
            "Connection refused",
            "Rate limit exceeded",
            "401 Unauthorized",
            "File not found: /path/to/file",
            "Timeout after 30 seconds"
        ]

        for err in test_errors:
            category = handler.classify_error(err)
            print(f"'{err}' -> {category.value}")

        # 데코레이터 테스트
        @handler.catch_errors
        async def failing_function():
            raise ValueError("Test error")

        try:
            await failing_function()
        except ValueError:
            pass

        # 통계 확인
        print("\n에러 통계:", handler.get_error_statistics())

    asyncio.run(test())
