#!/usr/bin/env python3
"""Telegram 연결 테스트"""

import os
import sys
import ssl
import urllib.request
import urllib.parse
import json
from pathlib import Path

# 프로젝트 루트
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

# .env 로드
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')


def test_telegram():
    token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '5360443525')

    print("=" * 50)
    print("🔍 Telegram 연결 테스트")
    print("=" * 50)

    if not token:
        print("❌ TELEGRAM_BOT_TOKEN 없음")
        return False

    print(f"✅ 봇 토큰: {token[:10]}...{token[-5:]}")
    print(f"✅ 채팅 ID: {chat_id}")

    # SSL 컨텍스트 (프록시 환경용)
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    # 테스트 메시지 전송
    message = "🧪 [테스트] MCP Telegram 연결 테스트 성공!"

    try:
        url = f"https://api.telegram.org/bot{token}/sendMessage"
        data = urllib.parse.urlencode({
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }).encode('utf-8')

        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, context=ctx, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))

        if result.get('ok'):
            print("=" * 50)
            print("✅ Telegram 메시지 전송 성공!")
            print(f"   메시지 ID: {result['result'].get('message_id')}")
            print("=" * 50)
            return True
        else:
            print(f"❌ Telegram API 오류: {result}")
            return False

    except Exception as e:
        print(f"❌ Telegram 연결 실패: {e}")
        return False


if __name__ == "__main__":
    success = test_telegram()
    sys.exit(0 if success else 1)
