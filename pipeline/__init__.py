"""
pipeline - §22 안전도 분기 파이프라인
v3.1: ENUM 단일 판정, 금지 키워드 차단, 이미지-캡션 일치 검증
"""

from .enums.safety import Safety, get_safety, SafetyError

__all__ = ["Safety", "get_safety", "SafetyError"]
__version__ = "3.1"
