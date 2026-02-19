"""
Logger - 고급 로깅 시스템
Project Sunshine Logging System

기능:
- 구조화된 JSON 로깅
- 자동 로그 로테이션
- 레벨별 필터링
- 성능 추적
"""

import json
import logging
import os
import sys
from datetime import datetime
from logging.handlers import RotatingFileHandler, TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional
import functools
import time
import asyncio


class JSONFormatter(logging.Formatter):
    """JSON 포맷 로거"""

    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # 추가 데이터가 있으면 포함
        if hasattr(record, 'extra_data'):
            log_data["data"] = record.extra_data

        # 예외 정보가 있으면 포함
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info)
            }

        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """컬러 콘솔 포맷터"""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'

    def format(self, record: logging.LogRecord) -> str:
        color = self.COLORS.get(record.levelname, self.RESET)
        timestamp = datetime.now().strftime("%H:%M:%S")

        formatted = f"{color}[{timestamp}] {record.levelname:<8}{self.RESET} | {record.name} | {record.getMessage()}"

        if hasattr(record, 'extra_data'):
            formatted += f" | {record.extra_data}"

        return formatted


class SunshineLogger:
    """
    Project Sunshine 전용 로거

    사용법:
        logger = SunshineLogger("MyAgent")
        logger.info("작업 시작", data={"topic": "banana"})
        logger.error("에러 발생", exc_info=True)

        # 성능 측정
        with logger.timer("이미지 생성"):
            generate_image()

        # 데코레이터
        @logger.log_execution
        def my_function():
            ...
    """

    _instances: Dict[str, 'SunshineLogger'] = {}

    def __new__(cls, name: str, *args, **kwargs):
        """싱글톤 패턴 - 같은 이름의 로거는 재사용"""
        if name not in cls._instances:
            instance = super().__new__(cls)
            cls._instances[name] = instance
        return cls._instances[name]

    def __init__(
        self,
        name: str,
        log_dir: Optional[Path] = None,
        level: int = logging.INFO,
        json_logging: bool = True,
        console_logging: bool = True,
        file_logging: bool = True,
        max_bytes: int = 10 * 1024 * 1024,  # 10MB
        backup_count: int = 5
    ):
        # 이미 초기화된 경우 스킵
        if hasattr(self, '_initialized') and self._initialized:
            return

        self.name = name
        self.log_dir = log_dir or Path(__file__).parent.parent / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.logger = logging.getLogger(f"sunshine.{name}")
        self.logger.setLevel(level)
        self.logger.handlers = []  # 기존 핸들러 제거

        # 콘솔 핸들러
        if console_logging:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(ColoredFormatter())
            console_handler.setLevel(level)
            self.logger.addHandler(console_handler)

        # 파일 핸들러 (JSON 또는 일반)
        if file_logging:
            if json_logging:
                file_path = self.log_dir / f"{name.lower()}.json.log"
                file_handler = RotatingFileHandler(
                    file_path,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.setFormatter(JSONFormatter())
            else:
                file_path = self.log_dir / f"{name.lower()}.log"
                file_handler = RotatingFileHandler(
                    file_path,
                    maxBytes=max_bytes,
                    backupCount=backup_count,
                    encoding='utf-8'
                )
                file_handler.setFormatter(logging.Formatter(
                    '[%(asctime)s] %(levelname)s | %(name)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S'
                ))

            file_handler.setLevel(level)
            self.logger.addHandler(file_handler)

        # 전역 로그 파일 (모든 로거가 공유)
        global_log = self.log_dir / "sunshine.log"
        global_handler = TimedRotatingFileHandler(
            global_log,
            when='midnight',
            interval=1,
            backupCount=7,
            encoding='utf-8'
        )
        global_handler.setFormatter(logging.Formatter(
            '[%(asctime)s] %(levelname)s | %(name)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        ))
        global_handler.setLevel(logging.INFO)
        self.logger.addHandler(global_handler)

        self._initialized = True

    def _log(self, level: int, message: str, data: Optional[Dict] = None, **kwargs):
        """내부 로깅 함수"""
        extra = {'extra_data': data} if data else {}
        self.logger.log(level, message, extra=extra, **kwargs)

    def debug(self, message: str, data: Optional[Dict] = None, **kwargs):
        """DEBUG 레벨 로깅"""
        self._log(logging.DEBUG, message, data, **kwargs)

    def info(self, message: str, data: Optional[Dict] = None, **kwargs):
        """INFO 레벨 로깅"""
        self._log(logging.INFO, message, data, **kwargs)

    def warning(self, message: str, data: Optional[Dict] = None, **kwargs):
        """WARNING 레벨 로깅"""
        self._log(logging.WARNING, message, data, **kwargs)

    def error(self, message: str, data: Optional[Dict] = None, **kwargs):
        """ERROR 레벨 로깅"""
        self._log(logging.ERROR, message, data, **kwargs)

    def critical(self, message: str, data: Optional[Dict] = None, **kwargs):
        """CRITICAL 레벨 로깅"""
        self._log(logging.CRITICAL, message, data, **kwargs)

    def exception(self, message: str, data: Optional[Dict] = None):
        """예외 정보와 함께 ERROR 로깅"""
        self._log(logging.ERROR, message, data, exc_info=True)

    class Timer:
        """성능 측정용 타이머 컨텍스트 매니저"""

        def __init__(self, logger: 'SunshineLogger', operation: str):
            self.logger = logger
            self.operation = operation
            self.start_time = None

        def __enter__(self):
            self.start_time = time.time()
            self.logger.debug(f"⏱ {self.operation} 시작")
            return self

        def __exit__(self, exc_type, exc_val, exc_tb):
            elapsed = time.time() - self.start_time
            if exc_type is None:
                self.logger.info(
                    f"✓ {self.operation} 완료",
                    data={"elapsed_seconds": round(elapsed, 3)}
                )
            else:
                self.logger.error(
                    f"✗ {self.operation} 실패",
                    data={"elapsed_seconds": round(elapsed, 3), "error": str(exc_val)}
                )
            return False

        async def __aenter__(self):
            return self.__enter__()

        async def __aexit__(self, exc_type, exc_val, exc_tb):
            return self.__exit__(exc_type, exc_val, exc_tb)

    def timer(self, operation: str):
        """성능 측정 타이머"""
        return self.Timer(self, operation)

    def log_execution(self, func):
        """실행 로깅 데코레이터"""
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            with self.timer(func.__name__):
                return await func(*args, **kwargs)

        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            with self.timer(func.__name__):
                return func(*args, **kwargs)

        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        return sync_wrapper

    def agent_start(self, agent_name: str, input_summary: str = ""):
        """에이전트 시작 로깅"""
        self.info(f"▶ {agent_name} 시작", data={"input": input_summary[:100]})

    def agent_end(self, agent_name: str, success: bool, result_summary: str = ""):
        """에이전트 종료 로깅"""
        icon = "✓" if success else "✗"
        level = logging.INFO if success else logging.ERROR
        self._log(level, f"{icon} {agent_name} {'완료' if success else '실패'}",
                 data={"result": result_summary[:100]})

    def pipeline_progress(self, step: int, total: int, step_name: str):
        """파이프라인 진행 상황 로깅"""
        progress = round(step / total * 100)
        self.info(f"[{step}/{total}] {step_name} ({progress}%)")


# 전역 로거들
main_logger = SunshineLogger("Main")
pipeline_logger = SunshineLogger("Pipeline")
agent_logger = SunshineLogger("Agent")
api_logger = SunshineLogger("API")


def get_logger(name: str) -> SunshineLogger:
    """로거 인스턴스 가져오기"""
    return SunshineLogger(name)


# 로그 디렉토리 정리 유틸리티
def cleanup_old_logs(log_dir: Optional[Path] = None, days: int = 30) -> int:
    """오래된 로그 파일 정리"""
    import glob
    from datetime import timedelta

    log_dir = log_dir or Path(__file__).parent.parent / "logs"
    cutoff = datetime.now() - timedelta(days=days)
    removed = 0

    for log_file in log_dir.glob("*.log*"):
        try:
            mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
            if mtime < cutoff:
                log_file.unlink()
                removed += 1
        except Exception:
            pass

    return removed


# 테스트 코드
if __name__ == "__main__":
    async def test():
        logger = get_logger("TestModule")

        logger.info("테스트 시작", data={"version": "3.0"})

        # 타이머 테스트
        with logger.timer("작업 1"):
            time.sleep(0.1)

        # async 타이머
        async with logger.timer("비동기 작업"):
            await asyncio.sleep(0.1)

        # 에이전트 로깅
        logger.agent_start("TestAgent", "입력 데이터...")
        logger.agent_end("TestAgent", True, "처리 완료")

        # 파이프라인 진행
        for i in range(1, 6):
            logger.pipeline_progress(i, 5, f"단계 {i}")

        # 에러 로깅
        try:
            raise ValueError("테스트 에러")
        except ValueError:
            logger.exception("에러 발생")

        logger.warning("경고 메시지")
        logger.critical("치명적 오류")

    asyncio.run(test())
