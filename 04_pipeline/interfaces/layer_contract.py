#!/usr/bin/env python3
"""
layer_contract.py - 계층 간 인터페이스 정의
WO-LIGHTWEIGHT-SEPARATION

3계층 분리:
- Layer 1: Generator (생성)
- Layer 2: Validator (검증)
- Layer 3: Executor (실행)

각 계층은 정해진 인터페이스로만 통신하며,
다른 계층의 내부 로직에 직접 접근할 수 없다.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


# =============================================================================
# 예외 클래스
# =============================================================================

class LayerError(Exception):
    """계층 관련 기본 예외"""
    pass


class PermissionDeniedError(LayerError):
    """계층 간 권한 침범 시 발생"""
    pass


class ExecutionBlockedError(LayerError):
    """Validator PASS 없이 실행 시도 시 발생"""
    pass


class AutoBlockedError(LayerError):
    """금지 코드로 자동 차단 시 발생"""
    pass


class ValidationFailedError(LayerError):
    """검증 실패 시 발생"""
    pass


# =============================================================================
# 상태 Enum
# =============================================================================

class ContentStatus(Enum):
    """생성 콘텐츠 상태"""
    GENERATED = "GENERATED"
    PENDING = "PENDING"
    ERROR = "ERROR"


class ValidationStatus(Enum):
    """검증 결과 상태"""
    PASS = "PASS"
    FAIL = "FAIL"
    BLOCKED = "BLOCKED"  # 금지 코드로 자동 차단


class ExecutionStatus(Enum):
    """실행 결과 상태"""
    EXECUTED = "EXECUTED"
    SKIPPED = "SKIPPED"
    ERROR = "ERROR"


# =============================================================================
# 데이터 전송 객체 (DTO)
# =============================================================================

@dataclass
class GeneratedContent:
    """
    Layer 1 → Layer 2 전달용 데이터
    Generator에서 생성한 콘텐츠
    """
    layer: str = "generator"
    food_id: int = 0
    food_name: str = ""
    content_type: str = ""  # caption, image, template
    content: str = ""
    safety: str = ""  # SAFE, CAUTION, FORBIDDEN
    generated_at: str = field(default_factory=lambda: datetime.now().isoformat())
    status: ContentStatus = ContentStatus.GENERATED
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict:
        return {
            "layer": self.layer,
            "food_id": self.food_id,
            "food_name": self.food_name,
            "content_type": self.content_type,
            "content": self.content[:100] + "..." if len(self.content) > 100 else self.content,
            "safety": self.safety,
            "generated_at": self.generated_at,
            "status": self.status.value,
            "metadata": self.metadata
        }


@dataclass
class ValidationResult:
    """
    Layer 2 → Layer 3 전달용 데이터
    Validator에서 산출한 검증 결과
    """
    layer: str = "validator"
    food_id: int = 0
    food_name: str = ""
    score: Dict[str, int] = field(default_factory=dict)
    total: int = 0
    status: ValidationStatus = ValidationStatus.PASS
    fail_codes: List[str] = field(default_factory=list)
    allow_override: bool = False
    requires_approval: Optional[str] = None  # "김부장" 등
    reason: str = ""
    validated_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "layer": self.layer,
            "food_id": self.food_id,
            "food_name": self.food_name,
            "score": self.score,
            "total": self.total,
            "status": self.status.value,
            "fail_codes": self.fail_codes,
            "allow_override": self.allow_override,
            "requires_approval": self.requires_approval,
            "reason": self.reason,
            "validated_at": self.validated_at
        }


@dataclass
class ExecutionResult:
    """
    Layer 3 결과 데이터
    Executor에서 실행한 결과
    """
    layer: str = "executor"
    food_id: int = 0
    food_name: str = ""
    action: str = ""  # publish, batch, save
    status: ExecutionStatus = ExecutionStatus.EXECUTED
    details: str = ""
    executed_at: str = field(default_factory=lambda: datetime.now().isoformat())

    def to_dict(self) -> Dict:
        return {
            "layer": self.layer,
            "food_id": self.food_id,
            "food_name": self.food_name,
            "action": self.action,
            "status": self.status.value,
            "details": self.details,
            "executed_at": self.executed_at
        }


# =============================================================================
# 계층 접근 제어
# =============================================================================

class LayerAccessControl:
    """
    계층 간 접근 제어 관리
    각 계층이 허용된 작업만 수행하도록 강제
    """

    # 금지 코드: override 불가, 자동 차단
    BLOCKED_CODES = frozenset(["ACCURACY_ERROR", "SAFETY_MISMATCH"])

    # 계층별 허용 작업
    LAYER_PERMISSIONS = {
        "generator": {
            "allowed": ["generate_caption", "generate_image", "apply_template"],
            "blocked": ["validate", "override", "execute", "modify_validation"]
        },
        "validator": {
            "allowed": ["validate", "score", "check_fail_codes", "auto_block"],
            "blocked": ["generate", "execute", "modify_generator", "bypass_block"]
        },
        "executor": {
            "allowed": ["execute", "publish", "batch"],
            "blocked": ["generate", "validate", "modify_validation", "override"]
        }
    }

    @classmethod
    def check_permission(cls, layer: str, action: str) -> bool:
        """권한 확인"""
        perms = cls.LAYER_PERMISSIONS.get(layer, {})
        blocked = perms.get("blocked", [])

        if action in blocked:
            raise PermissionDeniedError(
                f"{layer}에서 '{action}' 작업은 금지됨 (계층 분리 원칙)"
            )

        return True

    @classmethod
    def is_blocked_code(cls, code: str) -> bool:
        """금지 코드 여부 확인"""
        return code in cls.BLOCKED_CODES

    @classmethod
    def can_override(cls, fail_codes: List[str]) -> bool:
        """override 가능 여부 확인"""
        return not any(cls.is_blocked_code(code) for code in fail_codes)
