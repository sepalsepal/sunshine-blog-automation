#!/usr/bin/env python3
"""
max_retry 제한 컨트롤러

목적: 야간 자동화 무한루프 방지
원칙: 2회 초과 시 중단 + 텔레그램 알림
"""

import os
import ssl
import json
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Optional, Callable, Any

# 프로젝트 루트
ROOT = Path(__file__).parent.parent.parent


class MaxRetryExceededError(Exception):
    """최대 재시도 초과 예외"""
    pass


def log_max_retry(task_id: str, food_name: str, retry_count: int, error: str):
    """최대 재시도 초과 로그 기록"""
    log_dir = ROOT / "config/logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "max_retry_exceeded.log"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "task_id": task_id,
        "food_name": food_name,
        "retry_count": retry_count,
        "error": error
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


class RetryController:
    """재시도 컨트롤러"""

    def __init__(self):
        self.settings = self._load_settings()
        self.retry_count = {}
        self.last_error = {}
        self._ssl_ctx = self._create_ssl_context()

    def _load_settings(self) -> dict:
        """설정 로드"""
        path = ROOT / "config/pipeline_settings.json"
        if path.exists():
            try:
                return json.loads(path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {
            "retry": {"max_retry": 2, "on_exceed": "STOP_AND_REPORT"},
            "notification": {"on_max_retry": True, "telegram_alert": True}
        }

    def _create_ssl_context(self):
        """SSL 컨텍스트 생성 (프록시 환경용)"""
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    @property
    def max_retry(self) -> int:
        """최대 재시도 횟수"""
        return self.settings.get("retry", {}).get("max_retry", 2)

    def can_retry(self, task_id: str) -> bool:
        """재시도 가능 여부 확인"""
        current = self.retry_count.get(task_id, 0)
        return current < self.max_retry

    def get_retry_count(self, task_id: str) -> int:
        """현재 재시도 횟수"""
        return self.retry_count.get(task_id, 0)

    def increment(self, task_id: str, error: str = ""):
        """재시도 횟수 증가"""
        self.retry_count[task_id] = self.retry_count.get(task_id, 0) + 1
        if error:
            self.last_error[task_id] = error

    def reset(self, task_id: str):
        """재시도 횟수 초기화"""
        self.retry_count.pop(task_id, None)
        self.last_error.pop(task_id, None)

    def on_exceed(self, task_id: str, food_name: str):
        """
        최대 재시도 초과 시 처리

        Raises:
            MaxRetryExceededError
        """
        count = self.retry_count.get(task_id, 0)
        error = self.last_error.get(task_id, "알 수 없는 오류")

        # 로그 기록
        log_max_retry(task_id, food_name, count, error)

        # 텔레그램 알림
        if self.settings.get("notification", {}).get("telegram_alert", True):
            self._send_telegram_alert(task_id, food_name, count, error)

        # 예외 발생 → 중단
        raise MaxRetryExceededError(f"최대 재시도 초과: {task_id} ({count}회)")

    def _send_telegram_alert(self, task_id: str, food_name: str, count: int, error: str):
        """텔레그램 알림 전송"""
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        chat_id = os.environ.get("TELEGRAM_CHAT_ID", "5360443525")

        if not token:
            print("⚠️ TELEGRAM_BOT_TOKEN 없음, 알림 스킵")
            return

        message = f"""
🚨 <b>최대 재시도 초과!</b>

📦 음식: <b>{food_name.upper()}</b>
🔢 시도 횟수: {count}회
⛔ 상태: 중단됨
❌ 오류: {error[:100]}

PD님 확인 필요합니다.
"""

        try:
            url = f"https://api.telegram.org/bot{token}/sendMessage"
            data = urllib.parse.urlencode({
                "chat_id": chat_id,
                "text": message.strip(),
                "parse_mode": "HTML"
            }).encode("utf-8")

            req = urllib.request.Request(url, data=data)
            with urllib.request.urlopen(req, context=self._ssl_ctx, timeout=30) as response:
                result = json.loads(response.read().decode("utf-8"))
                if result.get("ok"):
                    print(f"📱 텔레그램 알림 전송됨 (메시지 ID: {result['result'].get('message_id')})")
                else:
                    print(f"⚠️ 텔레그램 알림 실패: {result}")

        except Exception as e:
            print(f"⚠️ 텔레그램 알림 오류: {e}")

    def execute_with_retry(
        self,
        task_id: str,
        food_name: str,
        step_func: Callable[[], Any],
        on_retry: Optional[Callable[[int, str], None]] = None
    ) -> Any:
        """
        재시도 로직이 포함된 실행

        Args:
            task_id: 작업 식별자
            food_name: 음식명
            step_func: 실행할 함수
            on_retry: 재시도 시 호출될 콜백 (retry_count, error)

        Returns:
            step_func의 반환값

        Raises:
            MaxRetryExceededError: 최대 재시도 초과 시
        """
        while True:
            try:
                result = step_func()
                # 성공 시 카운트 초기화
                self.reset(task_id)
                return result

            except Exception as e:
                error_msg = str(e)

                if self.can_retry(task_id):
                    self.increment(task_id, error_msg)
                    count = self.get_retry_count(task_id)
                    print(f"⚠️ 재시도 {count}/{self.max_retry}: {error_msg}")

                    if on_retry:
                        on_retry(count, error_msg)

                    continue
                else:
                    # 최대 초과 → 중단 + 알림
                    self.increment(task_id, error_msg)
                    self.on_exceed(task_id, food_name)
                    break


# 전역 인스턴스
_retry_controller = None


def get_retry_controller() -> RetryController:
    """전역 RetryController 인스턴스 반환"""
    global _retry_controller
    if _retry_controller is None:
        _retry_controller = RetryController()
    return _retry_controller


# CLI 테스트
if __name__ == "__main__":
    import sys

    print("=" * 60)
    print("🔍 RetryController 테스트")
    print("=" * 60)

    ctrl = RetryController()
    print(f"   max_retry: {ctrl.max_retry}")

    # 시뮬레이션: 3번 실패
    task_id = "test_task"
    food_name = "test_food"

    for i in range(4):
        print(f"\n[시도 {i+1}]")
        if ctrl.can_retry(task_id):
            ctrl.increment(task_id, f"테스트 오류 {i+1}")
            print(f"   현재 카운트: {ctrl.get_retry_count(task_id)}")
        else:
            print(f"   ❌ 재시도 불가 (최대 {ctrl.max_retry}회 초과)")
            try:
                ctrl.on_exceed(task_id, food_name)
            except MaxRetryExceededError as e:
                print(f"   🚨 예외 발생: {e}")
            break

    print("\n" + "=" * 60)
