#!/usr/bin/env python3
"""
WO-2026-0206-012 작업 5: 전체 자동화 파이프라인

[전체 파이프라인]
1. 콘텐츠 폴더에 파일 생성/수정
      ↓
2. git commit (pre-commit hook) 또는 수동 실행
      ↓
3. sync_local_to_sheet.py 실행 → 기본 상태 동기화
      ↓
4. check_folder_contents.py 실행 → P/Q/R열 자동 체크
      ↓
5. (PD가 구글시트에서 "승인" 체크)
      ↓
6. auto_cloudinary_upload.py 실행
   - 승인 완료 → 상태 approved 변경
   - Cloudinary 업로드
   - S열 "완료" 업데이트

사용법:
    python full_sync_pipeline.py           # 전체 파이프라인 실행
    python full_sync_pipeline.py --dry-run # 테스트 모드
    python full_sync_pipeline.py --watch   # 감시 모드 (30초 간격)
"""

import sys
import time
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 개별 스크립트 임포트
from services.scripts.sync_local_to_sheet import sync_to_sheet
from services.scripts.check_folder_contents import sync_pqr_columns
from services.scripts.auto_cloudinary_upload import process_approved_rows


def run_full_pipeline(dry_run=False):
    """전체 파이프라인 실행"""
    print("=" * 70)
    print(f"🚀 전체 동기화 파이프라인 시작 [{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}]")
    print("=" * 70)

    # Step 1: 기본 상태 동기화 (로컬 → 시트)
    print("\n📁 [Step 1] 기본 상태 동기화 (sync_local_to_sheet)")
    print("-" * 50)
    sync_to_sheet(dry_run=dry_run)

    # Step 2: P/Q/R열 자동 체크
    print("\n📝 [Step 2] P~R열 자동 체크 (check_folder_contents)")
    print("-" * 50)
    sync_pqr_columns(dry_run=dry_run)

    # Step 3: 승인 → approved → Cloudinary
    print("\n☁️ [Step 3] 승인 처리 + Cloudinary 업로드")
    print("-" * 50)
    process_approved_rows(dry_run=dry_run)

    # 완료
    print("\n" + "=" * 70)
    print(f"✅ 파이프라인 완료 [{datetime.now().strftime('%H:%M:%S')}]")
    print("=" * 70)


def watch_mode(interval=30):
    """감시 모드: 주기적으로 전체 파이프라인 실행"""
    print(f"👁️ 감시 모드 시작 ({interval}초 간격)")
    print("   Ctrl+C로 종료")
    print("-" * 70)

    try:
        while True:
            run_full_pipeline(dry_run=False)
            print(f"\n⏰ 다음 실행: {interval}초 후...\n")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n\n감시 모드 종료")


def main():
    args = sys.argv[1:]

    if '--watch' in args:
        watch_mode()
    elif '--dry-run' in args:
        run_full_pipeline(dry_run=True)
    else:
        run_full_pipeline(dry_run=False)


if __name__ == "__main__":
    main()
