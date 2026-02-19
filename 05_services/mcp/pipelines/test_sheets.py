#!/usr/bin/env python3
"""Google Sheets 연결 테스트"""

import os
import sys
from pathlib import Path

# 프로젝트 루트
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

# .env 로드
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')


def test_sheets():
    creds_path = os.environ.get('GOOGLE_CREDENTIALS_PATH')
    sheet_id = os.environ.get('GOOGLE_SHEET_ID')

    print("=" * 50)
    print("🔍 Google Sheets 연결 테스트")
    print("=" * 50)

    if not creds_path:
        print("❌ GOOGLE_CREDENTIALS_PATH 없음")
        return False

    if not sheet_id:
        print("❌ GOOGLE_SHEET_ID 없음")
        return False

    # 절대 경로로 변환
    if not os.path.isabs(creds_path):
        creds_path = str(ROOT / creds_path)

    if not os.path.exists(creds_path):
        print(f"❌ 인증 파일 없음: {creds_path}")
        return False

    print(f"✅ 인증 파일: {os.path.basename(creds_path)}")
    print(f"✅ 시트 ID: {sheet_id[:10]}...")

    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        creds = Credentials.from_service_account_file(
            creds_path,
            scopes=['https://www.googleapis.com/auth/spreadsheets']
        )
        service = build('sheets', 'v4', credentials=creds)

        # 시트 메타데이터 읽기
        result = service.spreadsheets().get(
            spreadsheetId=sheet_id
        ).execute()

        title = result.get('properties', {}).get('title', 'Unknown')
        sheets = [s['properties']['title'] for s in result.get('sheets', [])]

        print(f"✅ 시트 제목: {title}")
        print(f"✅ 워크시트: {', '.join(sheets[:3])}")
        print("=" * 50)
        print("✅ Google Sheets 연결 성공!")
        print("=" * 50)
        return True

    except Exception as e:
        print(f"❌ Google Sheets 연결 실패: {e}")
        return False


if __name__ == "__main__":
    success = test_sheets()
    sys.exit(0 if success else 1)
