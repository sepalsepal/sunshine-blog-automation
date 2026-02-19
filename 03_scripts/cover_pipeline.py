#!/usr/bin/env python3
"""
📂 커버 소스 파이프라인 (v1)
STEP 1: 0_cover_sources/ → 1_cover_only/ 자동 처리

기능:
- 0_cover_sources/ 스캔
- 리네이밍 (cover_YYYYMMDD_순번.png)
- 1_cover_only/ 폴더 생성 + 이동
- 텔레그램 알림

사용법:
    python scripts/cover_pipeline.py           # 실행
    python scripts/cover_pipeline.py --dry-run # 테스트 (실제 이동 없음)

크론 등록 (하루 2번):
    0 9 * * * cd /path/to/project_sunshine && python scripts/cover_pipeline.py
    0 21 * * * cd /path/to/project_sunshine && python scripts/cover_pipeline.py
"""

import os
import sys
import json
import shutil
import re
from pathlib import Path
from datetime import datetime

# 프로젝트 루트
ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

# 경로 설정
CONTENTS_DIR = ROOT / "01_contents"
COVER_SOURCES = CONTENTS_DIR / "0_cover_sources"
COVER_ONLY = CONTENTS_DIR / "1_cover_only"

# 지원 확장자
SUPPORTED_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.webp'}


def get_next_content_number() -> int:
    """전체 contents 폴더에서 다음 번호 계산"""
    max_num = 0

    # 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
    # 모든 상태 폴더 스캔
    # status_folders = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]

    for folder in CONTENTS_DIR.iterdir():
        if folder.is_dir() and not folder.name.startswith('.'):
            # 폴더명에서 번호 추출 (예: 151_cabbage_양배추 → 151)
            match = re.match(r'^(\d+)_', folder.name)
            if match:
                num = int(match.group(1))
                max_num = max(max_num, num)

    # 2026-02-13: 플랫 구조 - 월별 폴더 스캔 제거
    # 4_posted 하위 월별 폴더도 확인
    # posted_dir = CONTENTS_DIR / "4_posted"
    # if posted_dir.exists():
    #     for month_dir in posted_dir.iterdir():
    #         if month_dir.is_dir():
    #             for folder in month_dir.iterdir():
    #                 if folder.is_dir():
    #                     match = re.match(r'^(\d+)_', folder.name)
    #                     if match:
    #                         num = int(match.group(1))
    #                         max_num = max(max_num, num)

    return max_num + 1


def scan_cover_sources() -> list[Path]:
    """0_cover_sources/ 에서 이미지 파일 스캔"""
    if not COVER_SOURCES.exists():
        print(f"⚠️ 소스 폴더 없음: {COVER_SOURCES}")
        return []

    images = []
    for f in COVER_SOURCES.iterdir():
        if f.is_file() and f.suffix.lower() in SUPPORTED_EXTENSIONS:
            images.append(f)

    # 파일명 기준 정렬 (생성 시간순 대체)
    images.sort(key=lambda x: x.name)
    return images


def create_metadata(folder_path: Path, cover_filename: str):
    """metadata.json 생성"""
    metadata = {
        "food_id": "미지정",
        "food_name_kr": "미지정",
        "food_name_en": "unknown",
        "status": "cover_only",
        "cover_file": cover_filename,
        "created_at": datetime.now().isoformat(),
        "source": "cover_pipeline_v1"
    }

    metadata_path = folder_path / "metadata.json"
    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

    return metadata_path


def send_telegram_notification(processed_items: list[str], count: int):
    """텔레그램 알림 전송"""
    import requests

    bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    chat_id = os.environ.get('TELEGRAM_CHAT_ID', '5360443525')

    if not bot_token:
        print("⚠️ TELEGRAM_BOT_TOKEN 없음 - 알림 스킵")
        return

    now = datetime.now().strftime("%Y-%m-%d %H:%M")
    items_text = "\n".join([f"- {item}" for item in processed_items[:10]])
    if len(processed_items) > 10:
        items_text += f"\n... 외 {len(processed_items) - 10}개"

    message = f"""🆕 커버 소스 처리 완료

처리: {count}개
시간: {now}

등록된 항목:
{items_text}

👉 /생성 에서 확인 가능"""

    try:
        url = f"https://api.telegram.org/bot{bot_token}/sendMessage"
        response = requests.post(url, data={
            'chat_id': chat_id,
            'text': message,
            'parse_mode': 'HTML'
        }, timeout=10)

        if response.status_code == 200:
            print("✅ 텔레그램 알림 전송 완료")
        else:
            print(f"⚠️ 텔레그램 응답 오류: {response.status_code}")

    except Exception as e:
        print(f"⚠️ 텔레그램 알림 실패: {e}")


def process_cover_sources(dry_run: bool = False) -> dict:
    """커버 소스 처리 메인 함수"""
    print("=" * 60)
    print("📂 커버 소스 파이프라인 v1")
    print("=" * 60)

    # 1. 소스 스캔
    images = scan_cover_sources()
    if not images:
        print("ℹ️ 처리할 이미지 없음")
        return {"processed": 0, "items": []}

    print(f"\n📁 발견된 이미지: {len(images)}개")

    # 2. 다음 번호 계산
    next_num = get_next_content_number()
    print(f"📊 시작 번호: {next_num}")

    # 3. 오늘 날짜
    today = datetime.now().strftime("%Y%m%d")

    # 4. 대상 폴더 확인
    COVER_ONLY.mkdir(exist_ok=True)

    processed_items = []

    for idx, src_file in enumerate(images, start=1):
        # 순번 (001, 002, ...)
        seq = f"{idx:03d}"

        # 새 파일명: cover_YYYYMMDD_001.png
        new_filename = f"cover_{today}_{seq}.png"

        # 폴더명: {번호}_cover_{날짜}_{순번}_미지정
        folder_name = f"{next_num:03d}_cover_{today}_{seq}_미지정"

        # 폴더 경로
        dest_folder = COVER_ONLY / folder_name
        dest_file = dest_folder / new_filename

        print(f"\n[{idx}/{len(images)}] {src_file.name}")
        print(f"  → 폴더: {folder_name}/")
        print(f"  → 파일: {new_filename}")

        if not dry_run:
            # 폴더 생성
            dest_folder.mkdir(exist_ok=True)

            # 파일 이동 + 리네이밍
            shutil.copy2(src_file, dest_file)

            # 원본 삭제
            src_file.unlink()

            # metadata.json 생성
            create_metadata(dest_folder, new_filename)

            print(f"  ✅ 완료")
        else:
            print(f"  🔍 [DRY-RUN] 실제 처리 안함")

        processed_items.append(folder_name)
        next_num += 1

    # 5. 결과 출력
    print("\n" + "=" * 60)
    print(f"✅ 처리 완료: {len(processed_items)}개")

    # 6. 텔레그램 알림 (dry-run이 아닐 때만)
    if not dry_run and processed_items:
        send_telegram_notification(processed_items, len(processed_items))

    return {
        "processed": len(processed_items),
        "items": processed_items
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="커버 소스 파이프라인")
    parser.add_argument('--dry-run', action='store_true', help='테스트 모드 (실제 이동 없음)')

    args = parser.parse_args()

    result = process_cover_sources(dry_run=args.dry_run)

    if args.dry_run:
        print("\n⚠️ DRY-RUN 모드: 실제 파일 이동 없음")

    return result


if __name__ == "__main__":
    main()
