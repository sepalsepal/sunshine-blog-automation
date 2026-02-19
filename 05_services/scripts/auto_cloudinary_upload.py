#!/usr/bin/env python3
"""
WO-2026-0206-012 작업 3~4: 승인 → approved 자동 변경 + Cloudinary 자동 업로드

파이프라인:
1. 구글시트에서 "승인" 열이 "완료"인 행 찾기
2. 해당 행의 "상태" 열을 "approved"로 변경
3. S열(Cloudinary)이 비어있으면 이미지 업로드
4. 업로드 성공 시 S열 "완료"로 업데이트

보완 규칙 (레드2 판정 반영):
① Cloudinary public_id: sunshine/{번호}_{영문명}/{파일명} (결정적 경로)
② 승인 취소 시: Cloudinary 파일 삭제 안함, 상태 유지
③ 업로드 실패 시: 상태=upload_failed, S열="실패", 로그 기록

사용법:
    python auto_cloudinary_upload.py           # 실행
    python auto_cloudinary_upload.py --dry-run # 테스트 모드
    python auto_cloudinary_upload.py --watch   # 감시 모드
"""

import os
import sys
import json
import time
import logging
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

import gspread
from google.oauth2.service_account import Credentials

# Cloudinary 설정
try:
    import cloudinary
    import cloudinary.uploader
    from dotenv import load_dotenv
    load_dotenv(PROJECT_ROOT / ".env")

    cloudinary.config(
        cloud_name=os.getenv("CLOUDINARY_CLOUD_NAME"),
        api_key=os.getenv("CLOUDINARY_API_KEY"),
        api_secret=os.getenv("CLOUDINARY_API_SECRET")
    )
    CLOUDINARY_AVAILABLE = True
except ImportError:
    CLOUDINARY_AVAILABLE = False
    print("⚠️ cloudinary 라이브러리 없음 - 업로드 기능 비활성화")

# 로깅 설정
LOG_DIR = PROJECT_ROOT / "logs"
LOG_DIR.mkdir(exist_ok=True)
logging.basicConfig(
    filename=LOG_DIR / "cloudinary_errors.log",
    level=logging.ERROR,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# 열 인덱스 (1-based, 구글시트 기준)
COL_NUM = 1           # A열: 번호
COL_ENG_NAME = 2      # B열: 영문명
COL_STATUS = 6        # F열: 게시상태
COL_APPROVAL = 15     # O열: 승인(수동검수)
COL_CAPTION_INSTA = 16   # P열: 인스타 캡션
COL_CAPTION_THREADS = 17  # Q열: 쓰레드 캡션
COL_METADATA = 18     # R열: 메타데이터
COL_CLOUDINARY = 19   # S열: 클라우디너리
COL_FOLDER_STATUS = 21  # U열: 폴더상태


def get_sheet():
    """구글시트 연결"""
    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_path = PROJECT_ROOT / "config" / "google-credentials.json"
    creds = Credentials.from_service_account_file(str(creds_path), scopes=scopes)
    client = gspread.authorize(creds)
    return client.open("Sunshine").worksheet("게시콘텐츠")


def get_content_folder(num: str) -> Path:
    """번호로 콘텐츠 폴더 찾기"""
    body_ready = PROJECT_ROOT / "contents" / "2_body_ready"
    for folder in body_ready.iterdir():
        if folder.is_dir() and folder.name.startswith(f"{num}_"):
            return folder
    return None


def get_images_to_upload(folder: Path) -> list:
    """업로드할 이미지 목록 (00~06 또는 00~03)"""
    images = []
    for i in range(7):  # 00~06
        pattern = f"*_{i:02d}.png"
        matches = list(folder.glob(pattern))
        if matches:
            images.append(matches[0])
    return images


def upload_to_cloudinary(folder: Path, num: str, eng_name: str, dry_run=False) -> dict:
    """Cloudinary에 이미지 업로드

    public_id 규칙: sunshine/{번호}_{영문명}/{파일명}
    예: sunshine/060_fried_chicken/fried_chicken_00
    """
    if not CLOUDINARY_AVAILABLE:
        return {'success': False, 'error': 'cloudinary library not available'}

    images = get_images_to_upload(folder)
    if not images:
        return {'success': False, 'error': 'no images found'}

    results = []
    errors = []

    for img_path in images:
        # public_id 생성 (확장자 제외)
        filename_base = img_path.stem  # e.g., fried_chicken_00
        public_id = f"sunshine/{num}_{eng_name}/{filename_base}"

        if dry_run:
            print(f"  [DRY-RUN] 업로드 예정: {img_path.name} → {public_id}")
            results.append({'file': img_path.name, 'public_id': public_id})
            continue

        try:
            result = cloudinary.uploader.upload(
                str(img_path),
                public_id=public_id,
                overwrite=True,  # 동일 파일 덮어쓰기 (중복 방지)
                resource_type="image"
            )
            results.append({
                'file': img_path.name,
                'public_id': public_id,
                'url': result.get('secure_url')
            })
            print(f"  ✅ {img_path.name} → {public_id}")

        except Exception as e:
            error_msg = f"Upload failed for {img_path.name}: {str(e)}"
            errors.append(error_msg)
            logging.error(f"[{num}_{eng_name}] {error_msg}")
            print(f"  ❌ {img_path.name}: {str(e)}")

    if errors:
        return {
            'success': False,
            'error': '; '.join(errors),
            'uploaded': results
        }

    return {
        'success': True,
        'uploaded': results,
        'count': len(results)
    }


def get_body_ready_numbers():
    """2_body_ready 폴더에 있는 콘텐츠 번호 목록"""
    body_ready = PROJECT_ROOT / "contents" / "2_body_ready"
    numbers = set()
    if not body_ready.exists():
        return numbers
    for folder in body_ready.iterdir():
        if folder.is_dir() and not folder.name.startswith('.'):
            parts = folder.name.split('_')
            if parts[0].isdigit():
                numbers.add(parts[0])
    return numbers


def can_approve(row: list) -> tuple:
    """approved 가능 여부 검증 (WO-2026-0206-013 규칙)

    approved = 다음 4가지 모두 충족:
    1. P열 (인스타 캡션) = 완료
    2. Q열 (쓰레드 캡션) = 완료
    3. R열 (메타데이터) = 완료
    4. S열 (Cloudinary) = 완료

    Returns:
        (bool, list): (승인 가능 여부, 미충족 항목 목록)
    """
    missing = []

    p = row[COL_CAPTION_INSTA - 1] if len(row) >= COL_CAPTION_INSTA else ""
    q = row[COL_CAPTION_THREADS - 1] if len(row) >= COL_CAPTION_THREADS else ""
    r = row[COL_METADATA - 1] if len(row) >= COL_METADATA else ""
    s = row[COL_CLOUDINARY - 1] if len(row) >= COL_CLOUDINARY else ""

    if p != "완료":
        missing.append("P열(인스타캡션)")
    if q != "완료":
        missing.append("Q열(쓰레드캡션)")
    if r != "완료":
        missing.append("R열(메타데이터)")
    if s != "완료":
        missing.append("S열(Cloudinary)")

    return (len(missing) == 0, missing)


def move_to_approved(folder_name: str, dry_run=False) -> dict:
    """폴더 이동: body_ready → approved (WO-2026-0206-013)"""
    import shutil

    src = PROJECT_ROOT / "contents" / "2_body_ready" / folder_name
    dst = PROJECT_ROOT / "contents" / "3_approved" / folder_name

    if not src.exists():
        return {'error': f'Source not found: {src}'}

    if dst.exists():
        return {'skipped': f'Already exists: {dst}'}

    if not dry_run:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.move(str(src), str(dst))

    return {'moved': f'{src.name} → 3_approved/'}


def process_approved_rows(dry_run=False):
    """승인된 행 처리: approved 상태 변경 + Cloudinary 업로드

    대상: 2_body_ready 폴더에 있는 콘텐츠만 (body_ready 상태)
    """
    print(f"[{datetime.now().strftime('%H:%M:%S')}] 자동화 프로세스 시작...")

    # 2_body_ready에 있는 콘텐츠만 대상
    body_ready_nums = get_body_ready_numbers()
    print(f"대상 콘텐츠 (2_body_ready): {sorted(body_ready_nums)}")

    sheet = get_sheet()
    all_data = sheet.get_all_values()

    updates = []
    processed = []

    for idx, row in enumerate(all_data[1:], start=2):
        if len(row) < COL_CLOUDINARY:
            continue

        num = row[COL_NUM - 1]

        # 2_body_ready에 없는 콘텐츠는 건너뜀
        if num not in body_ready_nums:
            continue

        eng_name = row[COL_ENG_NAME - 1] if len(row) >= COL_ENG_NAME else ""
        current_status = row[COL_STATUS - 1] if len(row) >= COL_STATUS else ""
        approval = row[COL_APPROVAL - 1] if len(row) >= COL_APPROVAL else ""
        cloudinary_status = row[COL_CLOUDINARY - 1] if len(row) >= COL_CLOUDINARY else ""

        # 조건 1: 승인 완료 + Cloudinary 미완료 → 먼저 업로드
        if approval == "완료" and cloudinary_status not in ["완료", "실패"]:
            folder = get_content_folder(num)
            if folder:
                print(f"\n[{num}] {eng_name}: Cloudinary 업로드 시작 (승인 대기)")
                result = upload_to_cloudinary(folder, num, eng_name, dry_run=dry_run)

                if result['success'] or dry_run:
                    updates.append({
                        'row': idx,
                        'col': COL_CLOUDINARY,
                        'old': cloudinary_status,
                        'new': '완료',
                        'field': 'S열(Cloudinary)',
                        'num': num
                    })
                    cloudinary_status = '완료'  # 재검증용
                    processed.append({
                        'num': num,
                        'eng_name': eng_name,
                        'uploaded_count': result.get('count', 0)
                    })
                else:
                    updates.append({
                        'row': idx,
                        'col': COL_CLOUDINARY,
                        'old': cloudinary_status,
                        'new': '실패',
                        'field': 'S열(Cloudinary)',
                        'num': num
                    })
                    continue  # 업로드 실패 시 approved 불가

        # 조건 2: 승인 완료 + 상태가 approved 아닌 경우 → P/Q/R/S 검증 후 approved
        if approval == "완료" and current_status != "approved":
            # WO-2026-0206-013: approved 전환 전 P/Q/R/S 검증
            # 업데이트 후 상태로 row 재구성
            check_row = list(row)
            if cloudinary_status == '완료':
                check_row[COL_CLOUDINARY - 1] = '완료'

            can_approve_result, missing = can_approve(check_row)

            if not can_approve_result:
                print(f"\n[{num}] {eng_name}: approved 불가 - 미충족: {', '.join(missing)}")
                continue

            print(f"\n[{num}] {eng_name}: 승인 완료 → approved 변경")
            updates.append({
                'row': idx,
                'col': COL_STATUS,
                'old': current_status,
                'new': 'approved',
                'field': 'F열(게시상태)',
                'num': num
            })

            # 폴더 이동
            folder = get_content_folder(num)
            if folder:
                move_result = move_to_approved(folder.name, dry_run=dry_run)
                if move_result.get('moved'):
                    print(f"  📁 {move_result['moved']}")
                    updates.append({
                        'row': idx,
                        'col': COL_FOLDER_STATUS,
                        'old': row[COL_FOLDER_STATUS - 1] if len(row) >= COL_FOLDER_STATUS else "",
                        'new': 'approved',
                        'field': 'U열(폴더상태)',
                        'num': num
                    })

            current_status = 'approved'

        # 조건 3: body_ready 상태 + Cloudinary 미완료 (승인 전) → 업로드만
        if approval != "완료" and cloudinary_status not in ["완료", "실패"]:
            folder = get_content_folder(num)
            if not folder:
                print(f"\n[{num}] 폴더 없음 - 건너뜀")
                continue

            print(f"\n[{num}] {eng_name}: Cloudinary 업로드 시작")
            result = upload_to_cloudinary(folder, num, eng_name, dry_run=dry_run)

            if result['success'] or dry_run:
                updates.append({
                    'row': idx,
                    'col': COL_CLOUDINARY,
                    'old': cloudinary_status,
                    'new': '완료',
                    'field': 'S열(Cloudinary)',
                    'num': num
                })
                processed.append({
                    'num': num,
                    'eng_name': eng_name,
                    'uploaded_count': result.get('count', 0)
                })
            else:
                # 실패 시: 상태를 upload_failed로, S열을 "실패"로
                updates.append({
                    'row': idx,
                    'col': COL_STATUS,
                    'old': current_status,
                    'new': 'upload_failed',
                    'field': 'F열(게시상태)',
                    'num': num
                })
                updates.append({
                    'row': idx,
                    'col': COL_CLOUDINARY,
                    'old': cloudinary_status,
                    'new': '실패',
                    'field': 'S열(Cloudinary)',
                    'num': num
                })

    # 결과 요약 및 업데이트
    if updates:
        print(f"\n{'='*60}")
        print(f"변경 필요: {len(updates)}건")
        print("-" * 60)
        for u in updates:
            print(f"  [{u['num']}] {u['field']}: '{u['old']}' → '{u['new']}'")

        if not dry_run:
            cells = []
            for u in updates:
                cells.append(gspread.Cell(u['row'], u['col'], u['new']))

            sheet.update_cells(cells)
            print(f"\n✅ {len(updates)}건 구글시트 업데이트 완료")

            if processed:
                print(f"\n📤 Cloudinary 업로드 완료: {len(processed)}건")
                for p in processed:
                    print(f"  - {p['num']}_{p['eng_name']}: {p['uploaded_count']}개 이미지")
        else:
            print("\n(--dry-run 모드: 실제 업데이트/업로드 안함)")
    else:
        print("\n✅ 처리할 항목 없음")

    return updates


def watch_mode(interval=30):
    """감시 모드: 주기적으로 체크"""
    print(f"👁️ 감시 모드 시작 ({interval}초 간격)")
    print("   Ctrl+C로 종료")
    print("-" * 60)

    try:
        while True:
            process_approved_rows(dry_run=False)
            print(f"\n다음 체크: {interval}초 후...")
            time.sleep(interval)
    except KeyboardInterrupt:
        print("\n감시 모드 종료")


def main():
    args = sys.argv[1:]

    if '--watch' in args:
        watch_mode()
    elif '--dry-run' in args:
        process_approved_rows(dry_run=True)
    else:
        process_approved_rows(dry_run=False)


if __name__ == "__main__":
    main()
