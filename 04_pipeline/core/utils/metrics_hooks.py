"""
SunFlow Metrics Hooks
- 파이프라인 이벤트에 메트릭 수집 자동 연동
- 데코레이터 및 컨텍스트 매니저 제공
"""

import functools
import time
from datetime import datetime
from typing import Callable, Optional
from contextlib import contextmanager

from .metrics_collector import (
    get_collector,
    record_health_check,
    record_publish,
    record_instagram_stats,
    record_api_cost,
    record_error,
    record_quality_gate
)


def track_health_check(func: Callable) -> Callable:
    """헬스체크 결과 자동 기록 데코레이터"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            result = func(*args, **kwargs)
            # 결과가 딕셔너리면 status 확인
            if isinstance(result, dict):
                success = result.get('status') == 'HEALTHY'
            else:
                success = bool(result)
            record_health_check(success)
            return result
        except Exception as e:
            record_health_check(False)
            raise
    return wrapper


def track_publish(func: Callable) -> Callable:
    """게시 결과 자동 기록 데코레이터"""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        retry_count = kwargs.get('retry_count', 0)
        try:
            result = func(*args, **kwargs)
            # 결과 판정
            if isinstance(result, dict):
                success = result.get('success', False)
            elif isinstance(result, tuple):
                success = result[0] if result else False
            else:
                success = bool(result)
            record_publish(success, retry_count)
            return result
        except Exception as e:
            record_publish(False, retry_count)
            raise
    return wrapper


def track_api_call(service: str, cost_per_call: float = 0.0):
    """API 호출 비용 자동 기록 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            record_api_cost(service, 1, cost_per_call)
            return result
        return wrapper
    return decorator


def track_quality_gate(gate: str):
    """품질 게이트 결과 자동 기록 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            result = func(*args, **kwargs)
            # 결과 판정 (점수 기반)
            if isinstance(result, (int, float)):
                if gate == 'G1':
                    passed = result >= 90
                else:  # G2, G3
                    passed = result >= 85
            elif isinstance(result, dict):
                passed = result.get('passed', False)
            else:
                passed = bool(result)
            record_quality_gate(gate, passed)
            return result
        return wrapper
    return decorator


def track_error(severity: str = 'P3'):
    """에러 자동 기록 데코레이터"""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                record_error(severity)
                raise
        return wrapper
    return decorator


@contextmanager
def track_operation(operation_type: str, **metadata):
    """작업 추적 컨텍스트 매니저"""
    start_time = time.time()
    collector = get_collector()

    try:
        yield
        elapsed = time.time() - start_time
        # 성공 로깅
        if operation_type == 'health_check':
            record_health_check(True)
        elif operation_type == 'publish':
            record_publish(True, metadata.get('retry_count', 0))
    except Exception as e:
        elapsed = time.time() - start_time
        # 실패 로깅
        if operation_type == 'health_check':
            record_health_check(False)
        elif operation_type == 'publish':
            record_publish(False, metadata.get('retry_count', 0))
        record_error(metadata.get('severity', 'P3'))
        raise


class MetricsMiddleware:
    """파이프라인 미들웨어"""

    def __init__(self):
        self.collector = get_collector()

    def on_pipeline_start(self, topic: str):
        """파이프라인 시작 시"""
        pass  # 향후 확장

    def on_pipeline_end(self, topic: str, success: bool):
        """파이프라인 종료 시"""
        pass  # 향후 확장

    def on_image_generated(self, count: int, cost: float):
        """이미지 생성 완료 시"""
        record_api_cost('fal_ai', count, cost)

    def on_cloudinary_upload(self, count: int):
        """Cloudinary 업로드 완료 시"""
        record_api_cost('cloudinary', count, 0)

    def on_instagram_publish(self, success: bool, retry_count: int = 0):
        """Instagram 게시 완료 시"""
        record_publish(success, retry_count)

    def on_quality_gate(self, gate: str, score: float):
        """품질 게이트 통과 시"""
        if gate == 'G1':
            passed = score >= 90
        else:
            passed = score >= 85
        record_quality_gate(gate, passed)

    def on_error(self, error: Exception, severity: str = 'P3'):
        """에러 발생 시"""
        record_error(severity)

    def update_instagram_stats(self, followers: int, **engagement):
        """Instagram 통계 업데이트"""
        record_instagram_stats(followers, **engagement)


# 전역 미들웨어 인스턴스
middleware = MetricsMiddleware()


# ===== 연동 예시 =====
"""
# 1. 데코레이터 사용
@track_publish
def publish_to_instagram(content):
    # 게시 로직
    return {'success': True, 'post_id': '123'}

# 2. 컨텍스트 매니저 사용
with track_operation('publish', retry_count=1):
    result = instagram_api.publish(content)

# 3. 미들웨어 사용
from core.utils.metrics_hooks import middleware

middleware.on_image_generated(count=4, cost=0.20)
middleware.on_quality_gate('G2', score=92)
middleware.on_instagram_publish(success=True)
"""
