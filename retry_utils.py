"""
재시도 유틸리티
API 호출, 이미지 생성 등 실패 시 자동 재시도
"""
import time
import functools


def retry(max_attempts=3, delay=2, backoff=2, exceptions=(Exception,)):
    """
    재시도 데코레이터
    
    Args:
        max_attempts: 최대 시도 횟수 (기본 3회)
        delay: 첫 재시도 대기 시간 (초)
        backoff: 대기 시간 증가 배수 (지수 백오프)
        exceptions: 재시도할 예외 종류
    
    Usage:
        @retry(max_attempts=3, delay=2)
        def risky_function():
            ...
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(1, max_attempts + 1):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    last_exception = e
                    
                    if attempt < max_attempts:
                        print(f"   ⚠️ [{func.__name__}] 시도 {attempt}/{max_attempts} 실패: {str(e)[:50]}...")
                        print(f"   🔄 {current_delay}초 후 재시도...")
                        time.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        print(f"   ❌ [{func.__name__}] 최대 재시도 횟수 초과")
            
            raise last_exception
        
        return wrapper
    return decorator


def retry_call(func, *args, max_attempts=3, delay=2, **kwargs):
    """
    함수 호출 시 재시도 (데코레이터 대신 직접 호출)
    
    Usage:
        result = retry_call(risky_function, arg1, arg2, max_attempts=3)
    """
    last_exception = None
    current_delay = delay
    
    for attempt in range(1, max_attempts + 1):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            last_exception = e
            
            if attempt < max_attempts:
                print(f"   ⚠️ 시도 {attempt}/{max_attempts} 실패: {str(e)[:50]}...")
                print(f"   🔄 {current_delay}초 후 재시도...")
                time.sleep(current_delay)
                current_delay *= 2
            else:
                print(f"   ❌ 최대 재시도 횟수 초과")
    
    raise last_exception
