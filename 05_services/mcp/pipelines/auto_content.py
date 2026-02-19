#!/usr/bin/env python3
"""
MCP 자동 콘텐츠 파이프라인

목표: PD 복사-붙여넣기 제거
하나의 명령 → 전체 자동화 → 텔레그램 보고

안정화 기능 (Day 14):
  - PRE-CHECK: 생성 전 규칙/매핑 검증
  - rule_hash: 동기화 검증
  - max_retry: 2회 초과 시 중단 + 알림

사용법:
  python mcp/pipelines/auto_content.py duck
  python mcp/pipelines/auto_content.py --test  # 연결 테스트만
"""

import os
import sys
import ssl
import json
import urllib.request
import urllib.parse
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict, Any

# 프로젝트 루트
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

# .env 로드
from dotenv import load_dotenv
load_dotenv(ROOT / '.env')

# 안정화 모듈 임포트
from core.agents.pre_check import pre_check_all, PreCheckError
from core.agents.rule_sync_checker import verify_rule_sync, RuleSyncError
from core.agents.retry_controller import RetryController, MaxRetryExceededError


class AutoContentPipeline:
    """자동 콘텐츠 파이프라인"""

    def __init__(self):
        self.root = ROOT
        self.telegram_token = os.environ.get('TELEGRAM_BOT_TOKEN')
        self.telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID', '5360443525')
        self.ssl_ctx = self._create_ssl_context()

    def _create_ssl_context(self):
        """SSL 컨텍스트 생성 (프록시 환경용)"""
        ctx = ssl.create_default_context()
        ctx.check_hostname = False
        ctx.verify_mode = ssl.CERT_NONE
        return ctx

    def send_telegram(self, message: str, image_path: Optional[Path] = None) -> bool:
        """텔레그램 메시지 전송"""
        if not self.telegram_token:
            print("⚠️ TELEGRAM_BOT_TOKEN 없음, 알림 스킵")
            return False

        try:
            if image_path and image_path.exists():
                return self._send_telegram_photo(message, image_path)
            else:
                return self._send_telegram_text(message)
        except Exception as e:
            print(f"⚠️ 텔레그램 전송 실패: {e}")
            return False

    def _send_telegram_text(self, message: str) -> bool:
        """텍스트 메시지 전송"""
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = urllib.parse.urlencode({
            'chat_id': self.telegram_chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }).encode('utf-8')

        req = urllib.request.Request(url, data=data)
        with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=30) as response:
            result = json.loads(response.read().decode('utf-8'))

        return result.get('ok', False)

    def _send_telegram_photo(self, caption: str, image_path: Path) -> bool:
        """이미지 + 캡션 전송"""
        import mimetypes

        url = f"https://api.telegram.org/bot{self.telegram_token}/sendPhoto"
        boundary = '----WebKitFormBoundary7MA4YWxkTrZu0gW'

        # 멀티파트 폼 데이터 구성
        body = b''

        # chat_id
        body += f'--{boundary}\r\n'.encode()
        body += b'Content-Disposition: form-data; name="chat_id"\r\n\r\n'
        body += f'{self.telegram_chat_id}\r\n'.encode()

        # caption
        body += f'--{boundary}\r\n'.encode()
        body += b'Content-Disposition: form-data; name="caption"\r\n\r\n'
        body += f'{caption}\r\n'.encode()

        # parse_mode
        body += f'--{boundary}\r\n'.encode()
        body += b'Content-Disposition: form-data; name="parse_mode"\r\n\r\n'
        body += b'HTML\r\n'

        # photo
        mime_type = mimetypes.guess_type(str(image_path))[0] or 'image/png'
        body += f'--{boundary}\r\n'.encode()
        body += f'Content-Disposition: form-data; name="photo"; filename="{image_path.name}"\r\n'.encode()
        body += f'Content-Type: {mime_type}\r\n\r\n'.encode()
        body += image_path.read_bytes()
        body += b'\r\n'

        body += f'--{boundary}--\r\n'.encode()

        req = urllib.request.Request(url, data=body)
        req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')

        with urllib.request.urlopen(req, context=self.ssl_ctx, timeout=60) as response:
            result = json.loads(response.read().decode('utf-8'))

        return result.get('ok', False)

    def find_content_folder(self, food_name: str) -> Optional[Path]:
        """콘텐츠 폴더 찾기"""
        import re
        images_dir = self.root / 'content/images'

        # 정확한 매칭: {번호}_{foodName}_ 패턴
        exact_pattern = re.compile(rf'^\d{{3}}_{food_name}_')
        for folder in sorted(images_dir.iterdir()):
            if folder.is_dir() and exact_pattern.match(folder.name):
                return folder

        return None

    def verify_cover(self, content_folder: Path, food_name: str) -> Dict[str, Any]:
        """표지 검증 (메타데이터 기반)"""
        metadata_path = content_folder / f"{food_name}_00_metadata.json"
        cover_path = content_folder / f"{food_name}_00.png"

        result = {
            'passed': False,
            'cover_exists': cover_path.exists(),
            'metadata_exists': metadata_path.exists(),
            'rule_name': None,
            'rule_hash': None,
            'message': ''
        }

        if not result['cover_exists']:
            result['message'] = '표지 이미지 없음'
            return result

        if not result['metadata_exists']:
            result['message'] = '메타데이터 없음'
            return result

        try:
            metadata = json.loads(metadata_path.read_text(encoding='utf-8'))
            result['rule_name'] = metadata.get('rule_name')
            result['rule_hash'] = metadata.get('rule_hash')

            if result['rule_name'] == 'cover_v1' and result['rule_hash']:
                result['passed'] = True
                result['message'] = f"✅ {result['rule_name']} 규칙으로 생성됨"
            else:
                result['message'] = '유효하지 않은 규칙'

        except Exception as e:
            result['message'] = f'메타데이터 파싱 오류: {e}'

        return result

    def run(self, food_name: str, dry_run: bool = False) -> bool:
        """파이프라인 실행"""
        start_time = datetime.now()
        retry_ctrl = RetryController()

        print("=" * 60)
        print(f"🚀 MCP 자동 콘텐츠 파이프라인")
        print(f"   음식: {food_name}")
        print(f"   시작: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"   모드: {'DRY RUN' if dry_run else 'LIVE'}")
        print("=" * 60)

        # 🔴 0. PRE-CHECK (생성 진입 전 차단기)
        print("\n🔒 Step 0: PRE-CHECK (규칙/매핑 검증)")
        try:
            passed, reason = pre_check_all(food_name)
            if not passed:
                msg = f"❌ PRE-CHECK 실패: {reason}"
                print(f"   {msg}")
                self.send_telegram(f"🚨 <b>PRE-CHECK 실패</b>\n\n음식: {food_name}\n사유: {reason}")
                return False
            print(f"   ✅ {reason}")
        except PreCheckError as e:
            msg = f"❌ PRE-CHECK 예외: {e}"
            print(f"   {msg}")
            self.send_telegram(f"🚨 <b>PRE-CHECK 예외</b>\n\n{e}")
            return False

        # 1. 콘텐츠 폴더 찾기
        print("\n📁 Step 1: 콘텐츠 폴더 확인")
        content_folder = self.find_content_folder(food_name)
        if not content_folder:
            msg = f"❌ 콘텐츠 폴더 없음: {food_name}"
            print(msg)
            self.send_telegram(f"🚨 <b>파이프라인 실패</b>\n{msg}")
            return False

        print(f"   ✅ {content_folder.name}")

        # 2. 표지 검증
        print("\n🔍 Step 2: 표지 검증 (메타데이터)")
        cover_result = self.verify_cover(content_folder, food_name)
        print(f"   표지 존재: {'✅' if cover_result['cover_exists'] else '❌'}")
        print(f"   메타데이터: {'✅' if cover_result['metadata_exists'] else '❌'}")
        print(f"   규칙: {cover_result['rule_name'] or 'N/A'}")
        print(f"   결과: {cover_result['message']}")

        if not cover_result['passed']:
            print("\n   ⚠️ 표지 재생성 필요")
            # 표지 재생성 로직 (render_cover_v1.js 호출) with retry
            if not dry_run:
                task_id = f"{food_name}_cover_regen"
                try:
                    def regen_cover():
                        self._regenerate_cover(content_folder, food_name)
                        result = self.verify_cover(content_folder, food_name)
                        if not result['passed']:
                            raise Exception(result['message'])
                        return result

                    cover_result = retry_ctrl.execute_with_retry(
                        task_id, food_name, regen_cover
                    )
                except MaxRetryExceededError as e:
                    print(f"   🚨 {e}")
                    return False

        # 🔴 2.5. rule_hash 동기화 검증
        print("\n🔗 Step 2.5: rule_hash 동기화 검증")
        metadata_path = content_folder / f"{food_name}_00_metadata.json"
        rule_file = ROOT / "config/cover_rules.json"
        synced, sync_msg = verify_rule_sync(metadata_path, rule_file, "cover_v1")
        if synced:
            print(f"   ✅ {sync_msg}")
        else:
            msg = f"⚠️ rule_hash 동기화 실패: {sync_msg}"
            print(f"   {msg}")
            # 동기화 실패 시 재생성 필요 (규칙 파일이 변경됨)
            self.send_telegram(f"🚨 <b>rule_hash 동기화 실패</b>\n\n{sync_msg}")

        # 3. 본문 이미지 확인
        print("\n📷 Step 3: 본문 이미지 확인")
        content_images = list(content_folder.glob(f"{food_name}_0[1-9].png"))
        content_images.extend(list(content_folder.glob(f"{food_name}_1*.png")))
        print(f"   본문 이미지: {len(content_images)}장")

        for img in sorted(content_images):
            size_kb = img.stat().st_size / 1024
            status = "✅" if size_kb > 500 else "⚠️ 크기 작음"
            print(f"   - {img.name} ({size_kb:.0f}KB) {status}")

        # 4. 최종 보고
        end_time = datetime.now()
        duration = (end_time - start_time).total_seconds()

        print("\n" + "=" * 60)
        print("📊 파이프라인 완료 보고")
        print("=" * 60)
        print(f"   음식: {food_name.upper()}")
        print(f"   폴더: {content_folder.name}")
        print(f"   표지: {'✅ PASS' if cover_result['passed'] else '❌ FAIL'}")
        print(f"   본문: {len(content_images)}장")
        print(f"   소요: {duration:.1f}초")
        print("=" * 60)

        # 텔레그램 보고
        cover_path = content_folder / f"{food_name}_00.png"
        report = f"""
📦 <b>MCP 파이프라인 완료</b>

🍽️ 음식: <b>{food_name.upper()}</b>
📁 폴더: {content_folder.name}
🎨 표지: {'✅ PASS' if cover_result['passed'] else '❌ FAIL'}
📷 본문: {len(content_images)}장
⏱️ 소요: {duration:.1f}초
"""
        if not dry_run:
            self.send_telegram(report.strip(), cover_path if cover_path.exists() else None)
        else:
            print("\n[DRY RUN] 텔레그램 알림 스킵")

        return True

    def _regenerate_cover(self, content_folder: Path, food_name: str):
        """표지 재생성"""
        import subprocess

        title = food_name.upper()
        script = self.root / 'services/scripts/text_overlay/render_cover_v1.js'

        print(f"   🔄 표지 재생성: {food_name} → {title}")

        try:
            result = subprocess.run(
                ['node', str(script), food_name, title],
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                print("   ✅ 표지 재생성 완료")
            else:
                print(f"   ❌ 재생성 실패: {result.stderr}")

        except Exception as e:
            print(f"   ❌ 재생성 오류: {e}")


def test_connections():
    """연결 테스트"""
    print("=" * 60)
    print("🔍 MCP 연결 테스트")
    print("=" * 60)

    results = []

    # Google Sheets 테스트
    print("\n📊 Google Sheets...")
    try:
        from google.oauth2.service_account import Credentials
        from googleapiclient.discovery import build

        creds_path = os.environ.get('GOOGLE_CREDENTIALS_PATH')
        sheet_id = os.environ.get('GOOGLE_SHEET_ID')

        if creds_path and sheet_id:
            if not os.path.isabs(creds_path):
                creds_path = str(ROOT / creds_path)

            creds = Credentials.from_service_account_file(
                creds_path,
                scopes=['https://www.googleapis.com/auth/spreadsheets']
            )
            service = build('sheets', 'v4', credentials=creds)
            result = service.spreadsheets().get(spreadsheetId=sheet_id).execute()
            print(f"   ✅ 연결 성공: {result.get('properties', {}).get('title')}")
            results.append(('Google Sheets', True))
        else:
            print("   ⚠️ 환경변수 누락")
            results.append(('Google Sheets', False))
    except Exception as e:
        print(f"   ❌ 연결 실패: {e}")
        results.append(('Google Sheets', False))

    # Telegram 테스트
    print("\n📱 Telegram...")
    pipeline = AutoContentPipeline()
    try:
        success = pipeline._send_telegram_text("🧪 [테스트] MCP 연결 테스트")
        if success:
            print("   ✅ 연결 성공")
            results.append(('Telegram', True))
        else:
            print("   ❌ 연결 실패")
            results.append(('Telegram', False))
    except Exception as e:
        print(f"   ❌ 연결 실패: {e}")
        results.append(('Telegram', False))

    # 결과 요약
    print("\n" + "=" * 60)
    print("📋 연결 테스트 결과")
    print("=" * 60)
    all_passed = True
    for name, passed in results:
        status = "✅" if passed else "❌"
        print(f"   {status} {name}")
        if not passed:
            all_passed = False

    print("=" * 60)
    if all_passed:
        print("✅ 모든 연결 성공!")
    else:
        print("⚠️ 일부 연결 실패")

    return all_passed


def main():
    import argparse

    parser = argparse.ArgumentParser(description='MCP 자동 콘텐츠 파이프라인')
    parser.add_argument('food_name', nargs='?', help='음식 영문명 (예: duck)')
    parser.add_argument('--test', action='store_true', help='연결 테스트만 실행')
    parser.add_argument('--dry-run', action='store_true', help='실제 게시/알림 없이 실행')

    args = parser.parse_args()

    if args.test:
        success = test_connections()
        sys.exit(0 if success else 1)

    if not args.food_name:
        parser.print_help()
        sys.exit(1)

    pipeline = AutoContentPipeline()
    success = pipeline.run(args.food_name, dry_run=args.dry_run)
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
