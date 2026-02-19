#!/usr/bin/env python3
"""
커버 이미지 관리 스크립트
- 03_cover_sources → 02_ready 이동 + 소스 자동 삭제
- 02_ready → 01_published 이동 (게시 완료 시)
- 레디 이동 시 Google Sheets 자동 동기화

사용법:
    # 소스에서 레디로 이동 (소스 자동 삭제 + 시트 동기화)
    python cover_manager.py move <source_filename> <topic_en> <topic_kr> [--number 123]

    # 소스 폴더 정리 (이미 레디에 있는 항목 삭제)
    python cover_manager.py cleanup

    # 현황 확인
    python cover_manager.py status
"""

import os
import sys
import json
import shutil
import argparse
from pathlib import Path
from datetime import datetime

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent.parent
COVER_BASE = PROJECT_ROOT / "content" / "images" / "000_cover"
SOURCE_DIR = COVER_BASE / "03_cover_sources"
READY_DIR = COVER_BASE / "02_ready"
PUBLISHED_DIR = COVER_BASE / "01_published"
MAPPING_FILE = SOURCE_DIR / "cover_mapping.json"

# Google Sheets 동기화 모듈 임포트
sys.path.insert(0, str(PROJECT_ROOT))
try:
    from core.utils.google_sheets_manager import ContentSheetManager
    SHEETS_AVAILABLE = True
except ImportError:
    SHEETS_AVAILABLE = False
    print("⚠️ Google Sheets 모듈 로드 실패 - 로컬 모드로 실행")


def normalize_topic_name(name: str) -> str:
    """영문명 정규화 (숫자 접미사 제거, 소문자)"""
    return name.lower().rstrip('0123456789').strip('_')


def check_sheet_duplicate(topic_en: str, topic_kr: str) -> bool:
    """
    Google Sheets에서 중복 확인 (정규화된 이름 + 한글명 기준)

    Returns:
        True if duplicate exists
    """
    if not SHEETS_AVAILABLE:
        return False

    try:
        manager = ContentSheetManager()
        if not manager.connect():
            return False

        contents = manager.get_all_contents()
        normalized_input = normalize_topic_name(topic_en)

        for c in contents:
            existing_en = c.get('영문명', '')
            existing_kr = c.get('한글명', '')
            normalized_existing = normalize_topic_name(existing_en)

            # 정규화된 영문명 또는 한글명이 일치하면 중복
            if normalized_input == normalized_existing:
                print(f"⚠️ 시트 중복: {topic_en} ↔ {existing_en} ({existing_kr})")
                return True
            if topic_kr == existing_kr:
                print(f"⚠️ 시트 중복 (한글명): {topic_kr} ↔ {existing_en}")
                return True

        return False
    except:
        return False


def sync_to_sheets(number: int, topic_en: str, topic_kr: str, safety: str = 'SAFE') -> bool:
    """
    Google Sheets에 커버 정보 동기화

    Args:
        number: 커버 번호
        topic_en: 영문 주제명
        topic_kr: 한글 주제명
        safety: 안전도 (SAFE/CAUTION/DANGER)

    Returns:
        성공 여부
    """
    if not SHEETS_AVAILABLE:
        print("⚠️ Google Sheets 동기화 스킵 (모듈 미로드)")
        return False

    try:
        manager = ContentSheetManager()

        # 연결 시도
        if not manager.connect():
            print("⚠️ Google Sheets 연결 실패 - 로컬 캐시에만 저장")
            return False

        # 🔒 중복 체크 (정규화 + 한글명)
        if check_sheet_duplicate(topic_en, topic_kr):
            print(f"❌ 시트 동기화 스킵: 중복 항목 존재")
            return False

        # 시트에 추가 (표지대기 상태로)
        success = manager.add_content(
            number=f"{number:03d}",
            topic_en=topic_en,
            topic_kr=topic_kr,
            safety=safety,
            status='표지대기',
            publish_date=None,
            instagram_url=''
        )

        if success:
            print(f"📊 Google Sheets 동기화 완료: {topic_kr} ({topic_en})")

        return success

    except Exception as e:
        print(f"❌ Google Sheets 동기화 실패: {e}")
        return False


def load_mapping() -> dict:
    """매핑 파일 로드"""
    if MAPPING_FILE.exists():
        with open(MAPPING_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"description": "커버 이미지 매핑", "mappings": {}, "processed": []}


def save_mapping(mapping: dict):
    """매핑 파일 저장"""
    mapping['last_updated'] = datetime.now().isoformat()
    with open(MAPPING_FILE, 'w', encoding='utf-8') as f:
        json.dump(mapping, f, ensure_ascii=False, indent=2)


def get_next_cover_number() -> int:
    """다음 커버 번호 계산"""
    max_num = 0
    for f in READY_DIR.glob("cover_*.png"):
        try:
            parts = f.stem.split('_')
            if len(parts) >= 2:
                num = int(parts[1])
                max_num = max(max_num, num)
        except (ValueError, IndexError):
            continue

    for f in PUBLISHED_DIR.glob("cover_*.png"):
        try:
            parts = f.stem.split('_')
            if len(parts) >= 2:
                num = int(parts[1])
                max_num = max(max_num, num)
        except (ValueError, IndexError):
            continue

    return max_num + 1


def check_duplicate(topic_en: str) -> list:
    """
    레디/퍼블리시 폴더에서 중복 확인

    Returns:
        중복 파일 경로 리스트 (없으면 빈 리스트)
    """
    duplicates = []
    topic_lower = topic_en.lower()

    # 레디 폴더 확인
    for f in READY_DIR.glob("cover_*.png"):
        parts = f.stem.split('_')
        if len(parts) >= 4:
            existing_topic = parts[-1].lower()
            # DANGER 접미사 처리
            if existing_topic in ['danger', 'danger2']:
                existing_topic = parts[-2].lower()
            if existing_topic == topic_lower:
                duplicates.append(f)

    # 퍼블리시 폴더 확인
    for f in PUBLISHED_DIR.glob("cover_*.png"):
        parts = f.stem.split('_')
        if len(parts) >= 4:
            existing_topic = parts[-1].lower()
            if existing_topic in ['danger', 'danger2']:
                existing_topic = parts[-2].lower()
            if existing_topic == topic_lower:
                duplicates.append(f)

    return duplicates


def move_to_ready(source_filename: str, topic_en: str, topic_kr: str, number: int = None) -> bool:
    """
    소스에서 레디로 이동 + 소스 삭제

    Args:
        source_filename: 소스 파일명 (hf_xxx.png)
        topic_en: 영문 주제명
        topic_kr: 한글 주제명
        number: 커버 번호 (없으면 자동 계산)

    Returns:
        성공 여부
    """
    source_path = SOURCE_DIR / source_filename

    if not source_path.exists():
        print(f"❌ 소스 파일 없음: {source_filename}")
        return False

    # 🔒 중복 체크 (먼저 있는 파일 우선)
    duplicates = check_duplicate(topic_en)
    if duplicates:
        print(f"⚠️ 중복 발견! '{topic_en}' 이미 존재:")
        for dup in duplicates:
            print(f"   - {dup.name}")
        print(f"❌ 이동 취소. 기존 파일 우선 정책.")
        return False

    # 번호 계산
    if number is None:
        number = get_next_cover_number()

    # 대상 파일명: cover_{번호}_{한글명}_{영문명}.png
    target_filename = f"cover_{number}_{topic_kr}_{topic_en}.png"
    target_path = READY_DIR / target_filename

    # 이동 (복사 후 삭제)
    try:
        shutil.copy2(source_path, target_path)
        print(f"✅ 복사 완료: {target_filename}")

        # 소스 삭제
        source_path.unlink()
        print(f"🗑️  소스 삭제: {source_filename}")

        # 매핑 업데이트
        mapping = load_mapping()
        if source_filename in mapping.get('mappings', {}):
            del mapping['mappings'][source_filename]

        mapping.setdefault('processed', []).append({
            'source': source_filename,
            'target': target_filename,
            'topic_en': topic_en,
            'topic_kr': topic_kr,
            'date': datetime.now().strftime('%Y-%m-%d')
        })
        save_mapping(mapping)

        # 🔥 Google Sheets 자동 동기화 (레디 이동 시 즉시)
        sync_to_sheets(number, topic_en, topic_kr)

        return True

    except Exception as e:
        print(f"❌ 이동 실패: {e}")
        return False


def cleanup_sources() -> int:
    """레디에 이미 존재하는 소스 파일 삭제"""
    mapping = load_mapping()

    # 레디 폴더의 topic_en 목록
    ready_topics = set()
    for f in READY_DIR.glob("cover_*.png"):
        parts = f.stem.split('_')
        if len(parts) >= 4:
            ready_topics.add(parts[-1].lower())

    deleted = 0
    to_delete = []

    for source_file, info in list(mapping.get('mappings', {}).items()):
        topic_en = info.get('topic_en', '').lower()
        source_path = SOURCE_DIR / source_file

        if topic_en in ready_topics and source_path.exists():
            to_delete.append((source_file, info.get('topic_kr', ''), source_path))

    if not to_delete:
        print("✅ 정리할 파일 없음")
        return 0

    print(f"🗑️  {len(to_delete)}건 삭제 예정:")
    for source_file, topic_kr, source_path in to_delete:
        print(f"  - {topic_kr} ({source_file[:40]}...)")
        source_path.unlink()

        # 매핑에서 제거
        if source_file in mapping.get('mappings', {}):
            del mapping['mappings'][source_file]

        deleted += 1

    save_mapping(mapping)
    print(f"\n✅ {deleted}건 삭제 완료")
    return deleted


def show_status():
    """현황 표시"""
    mapping = load_mapping()

    source_files = list(SOURCE_DIR.glob("hf_*.png"))
    ready_files = list(READY_DIR.glob("cover_*.png"))
    published_files = list(PUBLISHED_DIR.glob("cover_*.png"))

    print("=" * 60)
    print("📊 커버 이미지 현황")
    print("=" * 60)
    print(f"  03_cover_sources: {len(source_files)}건")
    print(f"  02_ready:         {len(ready_files)}건")
    print(f"  01_published:     {len(published_files)}건")
    print()

    if source_files:
        print("📁 소스 파일 (미처리):")
        for f in source_files[:10]:
            info = mapping.get('mappings', {}).get(f.name, {})
            topic_kr = info.get('topic_kr', '미지정')
            print(f"  - {topic_kr}: {f.name[:45]}...")
        if len(source_files) > 10:
            print(f"  ... 외 {len(source_files) - 10}건")

    print("=" * 60)


def batch_move_all():
    """모든 소스 파일을 레디로 이동 (매핑 정보 사용)"""
    mapping = load_mapping()

    moved = 0
    for source_file, info in list(mapping.get('mappings', {}).items()):
        source_path = SOURCE_DIR / source_file
        if not source_path.exists():
            continue

        topic_en = info.get('topic_en', '')
        topic_kr = info.get('topic_kr', '')

        if not topic_en or not topic_kr:
            print(f"⚠️  매핑 정보 불완전: {source_file}")
            continue

        if move_to_ready(source_file, topic_en, topic_kr):
            moved += 1

    print(f"\n✅ 총 {moved}건 이동 완료")
    return moved


def sync_ready_to_sheets():
    """
    레디 폴더의 모든 커버를 Google Sheets에 동기화
    (기존 항목은 스킵)
    """
    if not SHEETS_AVAILABLE:
        print("❌ Google Sheets 모듈 미로드")
        return 0

    try:
        manager = ContentSheetManager()
        if not manager.connect():
            print("❌ Google Sheets 연결 실패")
            return 0

        # 기존 시트 데이터 가져오기
        existing = {c.get('영문명', '').lower() for c in manager.get_all_contents()}

        synced = 0
        skipped = 0

        for f in READY_DIR.glob("cover_*.png"):
            # cover_{번호}_{한글명}_{영문명}.png 파싱
            parts = f.stem.split('_')
            if len(parts) < 4:
                continue

            try:
                number = int(parts[1])
                topic_kr = parts[2]
                topic_en = parts[-1].lower()

                # DANGER 파일 감지
                safety = 'SAFE'
                if 'DANGER' in f.stem.upper():
                    safety = 'DANGER'
                    topic_en = parts[-2].lower()  # DANGER 앞의 영문명

                # 이미 존재하면 스킵
                if topic_en in existing:
                    skipped += 1
                    continue

                # 시트에 추가
                success = manager.add_content(
                    number=f"{number:03d}",
                    topic_en=topic_en,
                    topic_kr=topic_kr,
                    safety=safety,
                    status='표지대기',
                    publish_date=None,
                    instagram_url=''
                )

                if success:
                    synced += 1
                    print(f"  ✅ {topic_kr} ({topic_en})")

            except (ValueError, IndexError) as e:
                print(f"  ⚠️ 파싱 실패: {f.name} - {e}")
                continue

        print(f"\n📊 동기화 결과: 추가 {synced}건, 스킵 {skipped}건 (이미 존재)")
        return synced

    except Exception as e:
        print(f"❌ 동기화 실패: {e}")
        return 0


def main():
    parser = argparse.ArgumentParser(description='커버 이미지 관리')
    subparsers = parser.add_subparsers(dest='command', help='명령')

    # move 명령
    move_parser = subparsers.add_parser('move', help='소스에서 레디로 이동')
    move_parser.add_argument('source', help='소스 파일명')
    move_parser.add_argument('topic_en', help='영문 주제명')
    move_parser.add_argument('topic_kr', help='한글 주제명')
    move_parser.add_argument('--number', type=int, help='커버 번호')

    # cleanup 명령
    subparsers.add_parser('cleanup', help='소스 폴더 정리')

    # status 명령
    subparsers.add_parser('status', help='현황 확인')

    # batch 명령
    subparsers.add_parser('batch', help='모든 소스 파일 이동')

    # sync 명령 (레디 → 구글시트)
    subparsers.add_parser('sync', help='레디 폴더 → Google Sheets 동기화')

    args = parser.parse_args()

    if args.command == 'move':
        move_to_ready(args.source, args.topic_en, args.topic_kr, args.number)
    elif args.command == 'cleanup':
        cleanup_sources()
    elif args.command == 'status':
        show_status()
    elif args.command == 'batch':
        batch_move_all()
    elif args.command == 'sync':
        sync_ready_to_sheets()
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
