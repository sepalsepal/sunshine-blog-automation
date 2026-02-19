"""
파이프라인 로깅 시스템
- 콘솔 출력 (컬러)
- 파일 저장 (일별)
- 구조화된 JSON 로그

Phase 3: 로깅 시스템
"""

import logging
import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

ROOT = Path(__file__).parent.parent


class ColorFormatter(logging.Formatter):
    """컬러 로그 포맷터"""

    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'
    }

    def format(self, record):
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # 레벨명 컬러 적용
        record.levelname = f"{color}{record.levelname}{reset}"

        return super().format(record)


class PipelineLogger:
    """
    파이프라인 로깅 시스템

    Features:
    - 콘솔 출력 (컬러)
    - 파일 로그 (일별)
    - 구조화된 JSON 로그
    - Phase/Crew 단위 로깅
    """

    def __init__(self, log_dir: str = "logs", name: str = "sunshine_pipeline"):
        self.log_dir = ROOT / log_dir
        self.log_dir.mkdir(exist_ok=True)
        self.name = name

        # 로거 설정
        self.logger = logging.getLogger(name)
        self.logger.setLevel(logging.DEBUG)

        # 기존 핸들러 제거 (중복 방지)
        self.logger.handlers.clear()

        # 콘솔 핸들러 (컬러)
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_format = ColorFormatter(
            '%(asctime)s │ %(levelname)s │ %(message)s',
            datefmt='%H:%M:%S'
        )
        console_handler.setFormatter(console_format)
        self.logger.addHandler(console_handler)

        # 파일 핸들러 (일별)
        today = datetime.now().strftime("%Y-%m-%d")
        file_handler = logging.FileHandler(
            self.log_dir / f"pipeline_{today}.log",
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        file_format = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(name)s | %(message)s'
        )
        file_handler.setFormatter(file_format)
        self.logger.addHandler(file_handler)

        # JSON 로그 파일 경로
        self.json_log_path = self.log_dir / f"structured_{today}.jsonl"

    def info(self, message: str, **kwargs):
        """INFO 레벨 로그"""
        self.logger.info(message)
        self._write_structured("INFO", message, **kwargs)

    def warning(self, message: str, **kwargs):
        """WARNING 레벨 로그"""
        self.logger.warning(message)
        self._write_structured("WARNING", message, **kwargs)

    def error(self, message: str, **kwargs):
        """ERROR 레벨 로그"""
        self.logger.error(message)
        self._write_structured("ERROR", message, **kwargs)

    def debug(self, message: str, **kwargs):
        """DEBUG 레벨 로그"""
        self.logger.debug(message)

    def _write_structured(self, level: str, message: str, **kwargs):
        """구조화된 JSON 로그 저장"""
        log_entry = {
            "timestamp": datetime.now().isoformat(),
            "level": level,
            "message": message,
            **kwargs
        }

        with open(self.json_log_path, "a", encoding="utf-8") as f:
            f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

    def log_phase_start(self, phase: str, food_name: str, **kwargs):
        """Phase 시작 로그"""
        self.info(
            f"🚀 Phase 시작: {phase} ({food_name})",
            event="phase_start",
            phase=phase,
            food_name=food_name,
            **kwargs
        )

    def log_phase_end(
        self,
        phase: str,
        food_name: str,
        duration: float,
        success: bool = True,
        **kwargs
    ):
        """Phase 완료 로그"""
        status = "✅ 완료" if success else "❌ 실패"
        self.info(
            f"{status} Phase: {phase} ({duration:.2f}초)",
            event="phase_end",
            phase=phase,
            food_name=food_name,
            duration=duration,
            success=success,
            **kwargs
        )

    def log_crew_execution(
        self,
        crew_name: str,
        duration: float,
        success: bool,
        result: Optional[Dict] = None
    ):
        """Crew 실행 로그"""
        status = "성공" if success else "실패"
        self.info(
            f"⚙️ {crew_name} 실행 {status} ({duration:.2f}초)",
            event="crew_execution",
            crew=crew_name,
            duration=duration,
            success=success,
            result_summary=result
        )

    def log_approval_request(
        self,
        phase: str,
        food_name: str,
        approver: str = "PD"
    ):
        """승인 요청 로그"""
        self.info(
            f"⏳ {approver} 승인 대기: {phase} ({food_name})",
            event="approval_request",
            phase=phase,
            food_name=food_name,
            approver=approver
        )

    def log_approval_result(
        self,
        phase: str,
        food_name: str,
        approved: bool,
        reason: Optional[str] = None
    ):
        """승인 결과 로그"""
        status = "✅ 승인" if approved else "❌ 반려"
        self.info(
            f"{status}: {phase} ({food_name})",
            event="approval_result",
            phase=phase,
            food_name=food_name,
            approved=approved,
            reason=reason
        )

    def log_pipeline_summary(
        self,
        food_name: str,
        status: str,
        tech_score: float,
        creative_score: float,
        total_duration: float,
        instagram_url: Optional[str] = None
    ):
        """파이프라인 요약 로그"""
        self.info(
            f"📊 파이프라인 완료: {food_name} ({status})",
            event="pipeline_summary",
            food_name=food_name,
            status=status,
            tech_score=tech_score,
            creative_score=creative_score,
            total_duration=total_duration,
            instagram_url=instagram_url
        )


# 테스트
if __name__ == "__main__":
    logger = PipelineLogger()

    logger.info("테스트 INFO 메시지")
    logger.warning("테스트 WARNING 메시지")
    logger.error("테스트 ERROR 메시지")

    logger.log_phase_start("storyboard", "watermelon")
    logger.log_phase_end("storyboard", "watermelon", 5.23, success=True)

    print(f"\n로그 파일: {logger.log_dir}")
