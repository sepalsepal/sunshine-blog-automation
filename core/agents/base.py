"""
BaseAgent - 모든 에이전트가 상속받는 기본 클래스
Project Sunshine Agent System
Author: 최기술 대리
"""

import asyncio
import logging
from abc import ABC, abstractmethod
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional
import json
import yaml


class AgentStatus(Enum):
    """에이전트 상태"""
    IDLE = "idle"
    RUNNING = "running"
    SUCCESS = "success"
    FAILED = "failed"
    WAITING = "waiting"


class AgentResult:
    """에이전트 실행 결과를 담는 클래스"""

    def __init__(
        self,
        success: bool,
        data: Any = None,
        error: Optional[str] = None,
        metadata: Optional[Dict] = None
    ):
        self.success = success
        self.data = data
        self.error = error
        self.metadata = metadata or {}
        self.timestamp = datetime.now()

    def to_dict(self) -> Dict:
        return {
            "success": self.success,
            "data": self.data,
            "error": self.error,
            "metadata": self.metadata,
            "timestamp": self.timestamp.isoformat()
        }

    def __repr__(self):
        status = "SUCCESS" if self.success else "FAILED"
        return f"<AgentResult {status} at {self.timestamp}>"


class BaseAgent(ABC):
    """
    모든 에이전트의 기본 클래스

    사용법:
        class MyAgent(BaseAgent):
            @property
            def name(self) -> str:
                return "MyAgent"

            async def execute(self, input_data: Any) -> AgentResult:
                # 실제 작업 수행
                return AgentResult(success=True, data=result)
    """

    def __init__(self, config_path: Optional[str] = None):
        self._status = AgentStatus.IDLE
        self._config = {}
        self._logger = self._setup_logger()
        self._history = []

        # 설정 로드
        if config_path:
            self.load_config(config_path)
        else:
            # Try multiple config paths
            possible_paths = [
                Path(__file__).parent.parent.parent / "config" / "settings" / "config.yaml",  # project_sunshine/config/settings/
                Path(__file__).parent.parent / "config" / "config.yaml",  # legacy path
            ]
            for default_config in possible_paths:
                if default_config.exists():
                    self.load_config(str(default_config))
                    break

    @property
    @abstractmethod
    def name(self) -> str:
        """에이전트 이름 (하위 클래스에서 반드시 구현)"""
        pass

    @property
    def status(self) -> AgentStatus:
        """현재 에이전트 상태"""
        return self._status

    @property
    def config(self) -> Dict:
        """에이전트 설정"""
        return self._config

    @property
    def history(self) -> list:
        """실행 히스토리"""
        return self._history

    def _setup_logger(self) -> logging.Logger:
        """로거 설정"""
        logger = logging.getLogger(f"agent.{self.__class__.__name__}")

        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '[%(asctime)s] %(name)s | %(levelname)s | %(message)s',
                datefmt='%H:%M:%S'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)

        return logger

    def load_config(self, config_path: str) -> None:
        """YAML 설정 파일 로드"""
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                full_config = yaml.safe_load(f)

            # 에이전트별 설정 추출
            agent_key = self.name.lower().replace(" ", "_")
            self._config = full_config.get("agents", {}).get(agent_key, {})

            # 전역 설정도 포함
            self._config["_global"] = full_config.get("global", {})

            self._logger.debug(f"Config loaded for {self.name}")
        except Exception as e:
            self._logger.warning(f"Config load failed: {e}")

    def log(self, message: str, level: str = "info") -> None:
        """로그 출력"""
        log_func = getattr(self._logger, level.lower(), self._logger.info)
        log_func(message)

    @abstractmethod
    async def execute(self, input_data: Any) -> AgentResult:
        """
        실제 작업 수행 (하위 클래스에서 반드시 구현)

        Args:
            input_data: 입력 데이터

        Returns:
            AgentResult: 실행 결과
        """
        pass

    def validate_input(self, input_data: Any) -> bool:
        """
        입력 데이터 검증 (필요시 하위 클래스에서 오버라이드)

        Args:
            input_data: 검증할 입력 데이터

        Returns:
            bool: 유효하면 True
        """
        return input_data is not None

    def pre_execute(self, input_data: Any) -> Any:
        """
        실행 전 전처리 (필요시 하위 클래스에서 오버라이드)

        Args:
            input_data: 입력 데이터

        Returns:
            전처리된 데이터
        """
        return input_data

    def post_execute(self, result: AgentResult) -> AgentResult:
        """
        실행 후 후처리 (필요시 하위 클래스에서 오버라이드)

        Args:
            result: 실행 결과

        Returns:
            후처리된 결과
        """
        return result

    async def run(self, input_data: Any) -> AgentResult:
        """
        에이전트 실행 (메인 진입점)

        전체 실행 흐름:
        1. 입력 검증
        2. 전처리
        3. 실행
        4. 후처리
        5. 히스토리 저장

        Args:
            input_data: 입력 데이터

        Returns:
            AgentResult: 최종 실행 결과
        """
        start_time = datetime.now()
        self._status = AgentStatus.RUNNING
        self.log(f"▶ {self.name} 시작")

        try:
            # 1. 입력 검증
            if not self.validate_input(input_data):
                raise ValueError(f"Invalid input for {self.name}")

            # 2. 전처리
            processed_input = self.pre_execute(input_data)

            # 3. 실행
            result = await self.execute(processed_input)

            # 4. 후처리
            result = self.post_execute(result)

            # 상태 업데이트
            self._status = AgentStatus.SUCCESS if result.success else AgentStatus.FAILED

        except Exception as e:
            self._status = AgentStatus.FAILED
            result = AgentResult(
                success=False,
                error=str(e),
                metadata={"exception_type": type(e).__name__}
            )
            self.log(f"✗ {self.name} 실패: {e}", level="error")

        # 실행 시간 계산
        elapsed = (datetime.now() - start_time).total_seconds()
        result.metadata["elapsed_seconds"] = elapsed
        result.metadata["agent_name"] = self.name

        # 히스토리 저장
        self._history.append(result.to_dict())

        # 로그
        status_icon = "✓" if result.success else "✗"
        self.log(f"{status_icon} {self.name} 완료 ({elapsed:.2f}s)")

        return result

    def run_sync(self, input_data: Any) -> AgentResult:
        """
        동기 실행 (async 환경이 아닐 때 사용)

        Args:
            input_data: 입력 데이터

        Returns:
            AgentResult: 실행 결과
        """
        return asyncio.run(self.run(input_data))

    def reset(self) -> None:
        """에이전트 상태 초기화"""
        self._status = AgentStatus.IDLE
        self._history = []
        self.log(f"{self.name} 초기화됨")

    def get_last_result(self) -> Optional[Dict]:
        """마지막 실행 결과 반환"""
        return self._history[-1] if self._history else None

    def __repr__(self):
        return f"<{self.name} status={self.status.value}>"


# 편의를 위한 데코레이터
def retry(max_attempts: int = 3, delay: float = 1.0):
    """
    재시도 데코레이터

    사용법:
        @retry(max_attempts=3, delay=1.0)
        async def my_method(self, data):
            ...
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_error = None
            for attempt in range(max_attempts):
                try:
                    return await func(*args, **kwargs)
                except Exception as e:
                    last_error = e
                    if attempt < max_attempts - 1:
                        await asyncio.sleep(delay)
            raise last_error
        return wrapper
    return decorator
