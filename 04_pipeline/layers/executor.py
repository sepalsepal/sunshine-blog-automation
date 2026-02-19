#!/usr/bin/env python3
"""
executor.py - Layer 3: 배치 실행 계층
WO-LIGHTWEIGHT-SEPARATION + WO-PERFORMANCE-LOOP

책임:
- 배치 실행
- 게시 처리
- 저장 처리
- 성과 기록 초기화 (WO-PERFORMANCE-LOOP)

제한:
- Validator PASS 없으면 실행 차단
- Generator 직접 호출 불가
- Validator 결과 수정 불가
"""

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional

import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.interfaces.layer_contract import (
    ValidationResult,
    ValidationStatus,
    ExecutionResult,
    ExecutionStatus,
    LayerAccessControl,
    PermissionDeniedError,
    ExecutionBlockedError,
)
from pipeline.performance_logger import PerformanceLogger


class Executor:
    """
    Layer 3: 배치 실행 전담

    Validator PASS 없으면 실행 차단
    Generator, Validator 직접 수정 불가
    """

    LAYER_NAME = "executor"

    def __init__(self):
        self.contents_dir = PROJECT_ROOT / "contents"
        self.performance_logger = PerformanceLogger()
        self._enable_performance_tracking = True

    def execute(self, validation: ValidationResult) -> ExecutionResult:
        """
        배치 실행

        Args:
            validation: Validator에서 전달받은 검증 결과

        Returns:
            ExecutionResult 객체

        Raises:
            ExecutionBlockedError: Validator PASS가 아닌 경우
        """
        # 권한 확인
        LayerAccessControl.check_permission(self.LAYER_NAME, "execute")

        # 핵심: PASS가 아니면 실행 불가
        if validation.status != ValidationStatus.PASS:
            raise ExecutionBlockedError(
                f"Validator PASS 필수. 현재: {validation.status.value}. "
                f"사유: {validation.reason}"
            )

        # 실행 진행
        return self._do_execute(validation, action="batch")

    def publish(self, validation: ValidationResult) -> ExecutionResult:
        """
        게시 실행

        Args:
            validation: Validator에서 전달받은 검증 결과

        Returns:
            ExecutionResult 객체
        """
        # 권한 확인
        LayerAccessControl.check_permission(self.LAYER_NAME, "publish")

        # 핵심: PASS가 아니면 실행 불가
        if validation.status != ValidationStatus.PASS:
            raise ExecutionBlockedError(
                f"Validator PASS 필수. 현재: {validation.status.value}. "
                f"사유: {validation.reason}"
            )

        return self._do_execute(validation, action="publish")

    def save(self, validation: ValidationResult) -> ExecutionResult:
        """
        저장 실행

        Args:
            validation: Validator에서 전달받은 검증 결과

        Returns:
            ExecutionResult 객체
        """
        # 권한 확인
        LayerAccessControl.check_permission(self.LAYER_NAME, "batch")

        # 핵심: PASS가 아니면 실행 불가
        if validation.status != ValidationStatus.PASS:
            raise ExecutionBlockedError(
                f"Validator PASS 필수. 현재: {validation.status.value}. "
                f"사유: {validation.reason}"
            )

        return self._do_execute(validation, action="save")

    def _do_execute(
        self,
        validation: ValidationResult,
        action: str,
        platform: str = "insta",
        strategic_meta: Optional[Dict] = None,
        post_url: Optional[str] = None
    ) -> ExecutionResult:
        """
        실제 실행 로직

        Args:
            validation: 검증 결과
            action: 실행 유형 (batch, publish, save)
            platform: 플랫폼 (blog/insta/thread)
            strategic_meta: 전략 메타데이터
            post_url: 게시물 URL

        Returns:
            ExecutionResult 객체
        """
        # 실행 로직 (실제 구현은 기존 코드 활용)
        details = f"Action '{action}' executed for food_id={validation.food_id}"

        result = ExecutionResult(
            layer=self.LAYER_NAME,
            food_id=validation.food_id,
            food_name=validation.food_name,
            action=action,
            status=ExecutionStatus.EXECUTED,
            details=details,
            executed_at=datetime.now().isoformat()
        )

        # 성과 기록 초기화 (WO-PERFORMANCE-LOOP)
        if self._enable_performance_tracking and action in ["publish", "batch"]:
            self._init_performance_record(
                result=result,
                platform=platform,
                strategic_meta=strategic_meta,
                post_url=post_url
            )

        return result

    def _init_performance_record(
        self,
        result: ExecutionResult,
        platform: str,
        strategic_meta: Optional[Dict] = None,
        post_url: Optional[str] = None
    ) -> None:
        """
        게시 완료 후 성과 레코드 초기화 (WO-PERFORMANCE-LOOP)

        Args:
            result: 실행 결과
            platform: 플랫폼
            strategic_meta: 전략 메타데이터
            post_url: 게시물 URL
        """
        try:
            # 기본 strategic_meta
            if strategic_meta is None:
                strategic_meta = {
                    "safety": "SAFE",
                    "intent": "AUTHORITY",
                    "format": "DATA",
                    "emotion_axis": "trust"
                }

            # content_id 생성
            content_id = f"FOOD_{result.food_id}"

            self.performance_logger.create_record(
                content_id=content_id,
                food_id=result.food_id,
                food_name=result.food_name,
                platform=platform,
                strategic_meta=strategic_meta,
                post_url=post_url
            )
        except Exception as e:
            # 성과 기록 실패는 실행을 차단하지 않음
            pass

    def execute_batch(
        self,
        validations: List[ValidationResult]
    ) -> List[ExecutionResult]:
        """
        배치 실행 (여러 항목)

        Args:
            validations: 검증 결과 목록

        Returns:
            ExecutionResult 목록
        """
        results = []
        for validation in validations:
            try:
                result = self.execute(validation)
                results.append(result)
            except ExecutionBlockedError as e:
                # 블록된 항목은 스킵
                results.append(ExecutionResult(
                    layer=self.LAYER_NAME,
                    food_id=validation.food_id,
                    food_name=validation.food_name,
                    action="batch",
                    status=ExecutionStatus.SKIPPED,
                    details=str(e),
                    executed_at=datetime.now().isoformat()
                ))

        return results

    # =========================================================================
    # 금지 메서드 (계층 침범 방지)
    # =========================================================================

    def _blocked_direct_generate(self):
        """Generator 직접 호출 시도 시 차단"""
        raise PermissionDeniedError(
            "Executor는 Generator 직접 호출 불가 (계층 분리 원칙)"
        )

    def _blocked_modify_validation(self):
        """Validation 결과 수정 시도 시 차단"""
        raise PermissionDeniedError(
            "Executor는 Validation 결과 수정 불가 (계층 분리 원칙)"
        )

    def _blocked_override(self):
        """override 시도 시 차단"""
        raise PermissionDeniedError(
            "Executor는 override 권한 없음 (계층 분리 원칙)"
        )

    # 금지 작업 래퍼 (테스트용)
    def generate(self, *args, **kwargs):
        """금지: generate"""
        LayerAccessControl.check_permission(self.LAYER_NAME, "generate")

    def validate(self, *args, **kwargs):
        """금지: validate"""
        LayerAccessControl.check_permission(self.LAYER_NAME, "validate")

    def modify_validation(self, *args, **kwargs):
        """금지: modify_validation"""
        LayerAccessControl.check_permission(self.LAYER_NAME, "modify_validation")

    def override(self, *args, **kwargs):
        """금지: override"""
        LayerAccessControl.check_permission(self.LAYER_NAME, "override")
