"""
SunFlow Token Monitor (P1)
- Instagram 토큰 만료 모니터링
- 60일 전 알림
- 갱신 가이드 제공
"""

import os
import json
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Optional
from dataclasses import dataclass

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent


@dataclass
class TokenStatus:
    """토큰 상태"""
    is_valid: bool
    expires_at: Optional[datetime]
    days_until_expiry: Optional[int]
    needs_renewal: bool
    message: str


class TokenMonitor:
    """토큰 모니터링"""

    # 갱신 알림 기준 (일)
    RENEWAL_WARNING_DAYS = 60
    RENEWAL_URGENT_DAYS = 14
    RENEWAL_CRITICAL_DAYS = 7

    def __init__(self):
        self.project_root = PROJECT_ROOT
        self.token_file = self.project_root / "config" / "data" / "token_info.json"
        self._load_token_info()

    def _load_token_info(self):
        """토큰 정보 로드"""
        if self.token_file.exists():
            with open(self.token_file, 'r', encoding='utf-8') as f:
                self.token_info = json.load(f)
        else:
            self.token_info = {
                "instagram": {
                    "last_refresh": None,
                    "expires_at": None,
                    "refresh_count": 0
                }
            }

    def _save_token_info(self):
        """토큰 정보 저장"""
        self.token_file.parent.mkdir(parents=True, exist_ok=True)
        with open(self.token_file, 'w', encoding='utf-8') as f:
            json.dump(self.token_info, f, ensure_ascii=False, indent=2)

    def update_token_expiry(self, expires_at: datetime):
        """토큰 만료일 업데이트"""
        self.token_info["instagram"]["expires_at"] = expires_at.isoformat()
        self.token_info["instagram"]["last_refresh"] = datetime.now().isoformat()
        self.token_info["instagram"]["refresh_count"] += 1
        self._save_token_info()

    def get_token_status(self) -> TokenStatus:
        """토큰 상태 조회"""
        expires_at_str = self.token_info.get("instagram", {}).get("expires_at")

        if not expires_at_str:
            # 토큰 만료일 미설정 - 기본 60일 가정
            return TokenStatus(
                is_valid=True,
                expires_at=None,
                days_until_expiry=None,
                needs_renewal=False,
                message="토큰 만료일 미설정 (수동 확인 필요)"
            )

        expires_at = datetime.fromisoformat(expires_at_str)
        now = datetime.now()
        days_until = (expires_at - now).days

        if days_until <= 0:
            return TokenStatus(
                is_valid=False,
                expires_at=expires_at,
                days_until_expiry=days_until,
                needs_renewal=True,
                message="❌ 토큰 만료됨! 즉시 갱신 필요"
            )
        elif days_until <= self.RENEWAL_CRITICAL_DAYS:
            return TokenStatus(
                is_valid=True,
                expires_at=expires_at,
                days_until_expiry=days_until,
                needs_renewal=True,
                message=f"🚨 긴급! {days_until}일 후 만료"
            )
        elif days_until <= self.RENEWAL_URGENT_DAYS:
            return TokenStatus(
                is_valid=True,
                expires_at=expires_at,
                days_until_expiry=days_until,
                needs_renewal=True,
                message=f"⚠️ 주의! {days_until}일 후 만료"
            )
        elif days_until <= self.RENEWAL_WARNING_DAYS:
            return TokenStatus(
                is_valid=True,
                expires_at=expires_at,
                days_until_expiry=days_until,
                needs_renewal=True,
                message=f"📢 알림: {days_until}일 후 만료 예정"
            )
        else:
            return TokenStatus(
                is_valid=True,
                expires_at=expires_at,
                days_until_expiry=days_until,
                needs_renewal=False,
                message=f"✅ 정상 ({days_until}일 남음)"
            )

    def get_renewal_guide(self) -> str:
        """토큰 갱신 가이드"""
        return """
═══════════════════════════════════════════════════════════
              Instagram 토큰 갱신 가이드
═══════════════════════════════════════════════════════════

📋 갱신 방법 (장기 토큰 → 장기 토큰)

1. 현재 토큰으로 갱신 API 호출:

   GET https://graph.instagram.com/refresh_access_token
     ?grant_type=ig_refresh_token
     &access_token={현재_토큰}

2. 응답에서 새 토큰 및 만료일 확인:
   {
     "access_token": "새_토큰",
     "token_type": "Bearer",
     "expires_in": 5184000  // 60일 (초)
   }

3. .env 파일 업데이트:
   INSTAGRAM_ACCESS_TOKEN="새_토큰"

4. 토큰 만료일 등록:
   python core/utils/token_monitor.py set-expiry 60

═══════════════════════════════════════════════════════════

⚠️ 주의사항:
- 만료 전에만 갱신 가능 (만료 후 불가)
- 갱신 후 이전 토큰은 즉시 무효화
- 60일 장기 토큰 기준

📞 문제 발생 시:
- Meta Developer Console 확인
- 새 토큰 발급 필요할 수 있음

═══════════════════════════════════════════════════════════
"""

    async def check_and_notify(self) -> Optional[Dict]:
        """토큰 상태 확인 및 알림"""
        status = self.get_token_status()

        if status.needs_renewal:
            # 텔레그램 알림 전송 (옵션)
            try:
                from .telegram_notifier import TelegramNotifier
                notifier = TelegramNotifier()

                message = f"""
🔐 Instagram 토큰 알림

{status.message}

만료일: {status.expires_at.strftime('%Y-%m-%d %H:%M') if status.expires_at else '미설정'}
남은 일수: {status.days_until_expiry if status.days_until_expiry else '미확인'}일

👉 갱신 방법: python core/utils/token_monitor.py guide
"""
                await notifier.send_message(message)

                return {
                    "notified": True,
                    "status": status.message
                }
            except Exception as e:
                return {
                    "notified": False,
                    "error": str(e),
                    "status": status.message
                }

        return None

    def set_expiry_from_now(self, days: int = 60):
        """현재 시점 기준 만료일 설정"""
        expires_at = datetime.now() + timedelta(days=days)
        self.update_token_expiry(expires_at)
        return expires_at


# CLI 실행
if __name__ == "__main__":
    import sys

    monitor = TokenMonitor()

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "status":
            status = monitor.get_token_status()
            print("\n=== Instagram 토큰 상태 ===\n")
            print(f"  상태: {status.message}")
            if status.expires_at:
                print(f"  만료일: {status.expires_at.strftime('%Y-%m-%d %H:%M')}")
            if status.days_until_expiry is not None:
                print(f"  남은 일수: {status.days_until_expiry}일")
            print(f"  유효: {'예' if status.is_valid else '아니오'}")
            print(f"  갱신 필요: {'예' if status.needs_renewal else '아니오'}")

        elif cmd == "guide":
            print(monitor.get_renewal_guide())

        elif cmd == "set-expiry" and len(sys.argv) > 2:
            days = int(sys.argv[2])
            expires_at = monitor.set_expiry_from_now(days)
            print(f"\n✅ 만료일 설정 완료: {expires_at.strftime('%Y-%m-%d %H:%M')}")
            print(f"   ({days}일 후)")

        elif cmd == "check":
            result = asyncio.run(monitor.check_and_notify())
            if result:
                print(f"\n📢 알림 전송: {result}")
            else:
                print("\n✅ 알림 불필요 (토큰 상태 정상)")

        else:
            print("Usage: python token_monitor.py [status|guide|set-expiry <days>|check]")
    else:
        # 기본: 상태 표시
        status = monitor.get_token_status()
        print(f"\n토큰 상태: {status.message}")
