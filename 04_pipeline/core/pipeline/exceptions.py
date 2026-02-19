"""
Project Sunshine - 커스텀 예외 클래스
파이프라인 전체에서 사용되는 예외 타입 정의

Author: 최과장
Date: 2026-01-27
"""

from typing import Optional, Dict, Any


class SunshineException(Exception):
    """Project Sunshine 기본 예외"""

    def __init__(self, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.message = message
        self.details = details or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "type": self.__class__.__name__,
            "message": self.message,
            "details": self.details
        }


# ============================================================
# 파이프라인 관련 예외
# ============================================================

class PipelineError(SunshineException):
    """파이프라인 실행 에러"""

    def __init__(self, message: str, stage: str = None, details: Dict = None):
        super().__init__(message, details)
        self.stage = stage
        if stage:
            self.details["stage"] = stage


class StageFailedError(PipelineError):
    """특정 단계 실패"""

    def __init__(self, stage: str, reason: str, score: int = None):
        super().__init__(f"Stage '{stage}' failed: {reason}", stage)
        self.score = score
        if score is not None:
            self.details["score"] = score


class MaxRetriesExceededError(PipelineError):
    """최대 재시도 횟수 초과"""

    def __init__(self, stage: str, attempts: int, last_score: int = None):
        super().__init__(
            f"Maximum retries ({attempts}) exceeded at stage '{stage}'",
            stage
        )
        self.attempts = attempts
        self.last_score = last_score
        self.details["attempts"] = attempts
        if last_score is not None:
            self.details["last_score"] = last_score


# ============================================================
# 에이전트 관련 예외
# ============================================================

class AgentError(SunshineException):
    """에이전트 실행 에러"""

    def __init__(self, agent_name: str, message: str, details: Dict = None):
        super().__init__(f"[{agent_name}] {message}", details)
        self.agent_name = agent_name
        self.details["agent"] = agent_name


class ValidationError(AgentError):
    """입력 데이터 검증 실패"""

    def __init__(self, agent_name: str, field: str = None, reason: str = None):
        message = "Validation failed"
        if field:
            message += f" for field '{field}'"
        if reason:
            message += f": {reason}"
        super().__init__(agent_name, message)
        if field:
            self.details["field"] = field


class ExecutionError(AgentError):
    """에이전트 실행 중 에러"""

    def __init__(self, agent_name: str, message: str, original_error: Exception = None):
        super().__init__(agent_name, message)
        if original_error:
            self.details["original_error"] = str(original_error)
            self.details["error_type"] = type(original_error).__name__


# ============================================================
# API 관련 예외
# ============================================================

class APIError(SunshineException):
    """외부 API 에러"""

    def __init__(self, service: str, message: str, status_code: int = None, response: str = None):
        super().__init__(f"[{service}] API Error: {message}")
        self.service = service
        self.status_code = status_code
        self.response_body = response
        self.details["service"] = service
        if status_code:
            self.details["status_code"] = status_code


class RateLimitError(APIError):
    """API 레이트 제한"""

    def __init__(self, service: str, retry_after: int = None):
        super().__init__(service, "Rate limit exceeded")
        self.retry_after = retry_after
        if retry_after:
            self.details["retry_after_seconds"] = retry_after


class TimeoutError(APIError):
    """API 타임아웃"""

    def __init__(self, service: str, timeout_seconds: float):
        super().__init__(service, f"Request timed out after {timeout_seconds}s")
        self.timeout = timeout_seconds
        self.details["timeout_seconds"] = timeout_seconds


class AuthenticationError(APIError):
    """API 인증 실패"""

    def __init__(self, service: str, reason: str = "Invalid or missing credentials"):
        super().__init__(service, reason)


# ============================================================
# 이미지 관련 예외
# ============================================================

class ImageError(SunshineException):
    """이미지 처리 에러"""
    pass


class ImageGenerationError(ImageError):
    """이미지 생성 실패"""

    def __init__(self, prompt_index: int, reason: str, provider: str = None):
        super().__init__(f"Failed to generate image {prompt_index}: {reason}")
        self.prompt_index = prompt_index
        self.provider = provider
        self.details["prompt_index"] = prompt_index
        if provider:
            self.details["provider"] = provider


class ImageDownloadError(ImageError):
    """이미지 다운로드 실패"""

    def __init__(self, url: str, reason: str):
        super().__init__(f"Failed to download image: {reason}")
        self.url = url
        self.details["url"] = url


class ImageProcessingError(ImageError):
    """이미지 가공 실패 (리사이즈, 오버레이 등)"""

    def __init__(self, operation: str, image_path: str, reason: str):
        super().__init__(f"Failed to {operation} image: {reason}")
        self.operation = operation
        self.image_path = image_path
        self.details["operation"] = operation
        self.details["image_path"] = image_path


# ============================================================
# 게시 관련 예외
# ============================================================

class PublishError(SunshineException):
    """게시 에러"""
    pass


class InstagramAPIError(PublishError):
    """Instagram API 에러"""

    def __init__(self, message: str, error_code: str = None, error_subcode: str = None):
        super().__init__(f"Instagram API Error: {message}")
        if error_code:
            self.details["error_code"] = error_code
        if error_subcode:
            self.details["error_subcode"] = error_subcode


class CloudinaryError(PublishError):
    """Cloudinary 업로드 에러"""

    def __init__(self, message: str, public_id: str = None):
        super().__init__(f"Cloudinary Error: {message}")
        if public_id:
            self.details["public_id"] = public_id


# ============================================================
# 품질 검수 예외
# ============================================================

class QualityError(SunshineException):
    """품질 검수 에러"""
    pass


class QualityGateFailedError(QualityError):
    """품질 게이트 미통과"""

    def __init__(self, gate: str, score: int, threshold: int, issues: list = None):
        super().__init__(
            f"{gate} quality gate failed: {score} < {threshold}"
        )
        self.gate = gate
        self.score = score
        self.threshold = threshold
        self.issues = issues or []
        self.details["gate"] = gate
        self.details["score"] = score
        self.details["threshold"] = threshold
        if issues:
            self.details["issues"] = issues


# ============================================================
# 유틸리티 함수
# ============================================================

def format_exception_chain(exc: Exception) -> str:
    """예외 체인을 문자열로 포맷팅"""
    messages = []
    current = exc
    while current:
        if isinstance(current, SunshineException):
            messages.append(f"{type(current).__name__}: {current.message}")
        else:
            messages.append(f"{type(current).__name__}: {str(current)}")
        current = current.__cause__
    return " -> ".join(messages)


def wrap_exception(exc: Exception, context: str) -> SunshineException:
    """일반 예외를 SunshineException으로 래핑"""
    wrapped = SunshineException(f"{context}: {str(exc)}")
    wrapped.__cause__ = exc
    wrapped.details["original_type"] = type(exc).__name__
    return wrapped
