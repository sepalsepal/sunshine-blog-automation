#!/usr/bin/env python3
"""
pipeline/enums/safety.py - Safety ENUM 클래스
§22.11.1 ENUM 단일 판정 원칙

문자열 직접 사용 금지 - ENUM만 허용
잘못된 값 입력 시 예외 발생
"""

from enum import Enum
from typing import Union


class Safety(Enum):
    """안전도 ENUM - 3가지 상태만 허용"""
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    FORBIDDEN = "FORBIDDEN"

    def __str__(self) -> str:
        return self.value

    @property
    def is_dangerous(self) -> bool:
        """위험 여부 (CAUTION 이상)"""
        return self in (Safety.CAUTION, Safety.FORBIDDEN)

    @property
    def is_forbidden(self) -> bool:
        """절대 금지 여부"""
        return self == Safety.FORBIDDEN


class SafetyError(ValueError):
    """Safety 관련 예외"""
    pass


def get_safety(value: Union[str, Safety]) -> Safety:
    """
    문자열 → ENUM 변환 (오타 방지)

    Args:
        value: 안전도 문자열 또는 Safety ENUM

    Returns:
        Safety ENUM

    Raises:
        SafetyError: 유효하지 않은 값
    """
    # 이미 ENUM이면 그대로 반환
    if isinstance(value, Safety):
        return value

    # 문자열 변환
    if not isinstance(value, str):
        raise SafetyError(f"Invalid safety type: {type(value)}")

    try:
        return Safety(value.upper().strip())
    except ValueError:
        valid_values = [s.value for s in Safety]
        raise SafetyError(
            f"Invalid safety value: '{value}'. "
            f"Must be one of: {valid_values}"
        )


def validate_safety(value: str) -> bool:
    """
    안전도 값 유효성 검증

    Returns:
        True if valid, raises SafetyError if invalid
    """
    get_safety(value)
    return True


# 편의 함수
def is_safe(value: Union[str, Safety]) -> bool:
    """SAFE 여부 확인"""
    return get_safety(value) == Safety.SAFE


def is_caution(value: Union[str, Safety]) -> bool:
    """CAUTION 여부 확인"""
    return get_safety(value) == Safety.CAUTION


def is_forbidden(value: Union[str, Safety]) -> bool:
    """FORBIDDEN 여부 확인"""
    return get_safety(value) == Safety.FORBIDDEN
