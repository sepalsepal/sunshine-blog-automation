"""
pipeline/validators - §22.11~13 검증기 모듈
v3.1: pre_validator, post_validator, gate_controller
"""

from .pre_validator import (
    validate_before_generation,
    PreValidationError,
    PreValidationResult,
    load_and_validate,
)

from .post_validator import (
    validate_after_generation,
    PostValidationError,
    PostValidationResult,
    generate_structure_id,
    check_forbidden_keywords,
    # A-1, A-3: 버전/구조 ID 검증
    validate_version,
    validate_structure_ids,
    VersionMismatchError,
    TEMPLATE_VERSION,
)

from .gate_controller import (
    GateController,
    GateStatus,
    GateError,
    gate_check,
    can_save,
    # A-2: 3회 위반 자동 중단
    BatchLockError,
    ViolationTracker,
    reset_violation_tracker,
    get_violation_count,
)

__all__ = [
    # Pre-validator
    "validate_before_generation",
    "PreValidationError",
    "PreValidationResult",
    "load_and_validate",
    # Post-validator
    "validate_after_generation",
    "PostValidationError",
    "PostValidationResult",
    "generate_structure_id",
    "check_forbidden_keywords",
    # Gate Controller
    "GateController",
    "GateStatus",
    "GateError",
    "gate_check",
    "can_save",
]
