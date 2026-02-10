#!/usr/bin/env python3
"""
커버 이미지 소스 자동 처리 v1.0

기능:
- 03_cover_sources/ 폴더의 이미지를 02_ready/로 이동
- 매핑 파일 기반 리네이밍 (cover_{번호}_{한글명}_{영문명}.png)
- 매핑 없는 파일은 대기 목록에 추가
- 매일 오전 9시 launchd로 자동 실행

사용법:
    python cover_processor.py              # 매핑된 파일만 처리
    python cover_processor.py --all        # 미매핑 파일도 순차 처리
    python cover_processor.py --status     # 현황 확인
    python cover_processor.py --init       # 매핑 파일 템플릿 생성

Author: 김대리
Date: 2026-01-30
"""

import os
import sys
import json
import shutil
import argparse
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

# 프로젝트 루트
ROOT = Path(__file__).parent.parent.parent

# 경로 설정
COVER_DIR = ROOT / "content/images/000_cover"
SOURCE_DIR = COVER_DIR / "03_cover_sources"
READY_DIR = COVER_DIR / "02_ready"
PUBLISHED_DIR = COVER_DIR / "01_published"
MAPPING_FILE = SOURCE_DIR / "cover_mapping.json"
LOG_DIR = ROOT / "config/logs"

# 로깅 설정
LOG_DIR.mkdir(parents=True, exist_ok=True)
log_file = LOG_DIR / f"cover_processor_{datetime.now().strftime('%Y%m%d')}.log"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - [CoverProcessor] %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class CoverProcessor:
    """커버 이미지 소스 처리기"""

    def __init__(self):
        self.source_dir = SOURCE_DIR
        self.ready_dir = READY_DIR
        self.published_dir = PUBLISHED_DIR
        self.mapping_file = MAPPING_FILE

        # 디렉토리 확인
        self.source_dir.mkdir(parents=True, exist_ok=True)
        self.ready_dir.mkdir(parents=True, exist_ok=True)

    def get_next_cover_number(self) -> int:
        """다음 커버 번호 조회"""
        max_num = 0

        # ready 폴더 확인
        for f in self.ready_dir.glob("cover_*.png"):
            try:
                num = int(f.name.split("_")[1])
                max_num = max(max_num, num)
            except (IndexError, ValueError):
                continue

        # published 폴더도 확인
        for f in self.published_dir.glob("cover_*.png"):
            try:
                num = int(f.name.split("_")[1])
                max_num = max(max_num, num)
            except (IndexError, ValueError):
                continue

        return max_num + 1

    def get_source_files(self) -> List[Path]:
        """소스 폴더의 이미지 파일 목록"""
        extensions = {'.png', '.jpg', '.jpeg', '.webp'}
        files = []

        for f in self.source_dir.iterdir():
            if f.is_file() and f.suffix.lower() in extensions:
                files.append(f)

        # 파일명 기준 정렬 (날짜순)
        files.sort(key=lambda x: x.name)
        return files

    def load_mapping(self) -> Dict[str, Dict]:
        """매핑 파일 로드"""
        if self.mapping_file.exists():
            with open(self.mapping_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {"mappings": {}, "processed": [], "last_updated": None}

    def save_mapping(self, data: Dict):
        """매핑 파일 저장"""
        data["last_updated"] = datetime.now().isoformat()
        with open(self.mapping_file, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def init_mapping_template(self):
        """매핑 파일 템플릿 생성"""
        source_files = self.get_source_files()

        mapping_data = {
            "description": "커버 이미지 매핑 파일. source_filename에 topic_kr, topic_en을 매핑하세요.",
            "mappings": {},
            "processed": [],
            "last_updated": datetime.now().isoformat()
        }

        for f in source_files:
            mapping_data["mappings"][f.name] = {
                "topic_kr": "",
                "topic_en": "",
                "danger": False,
                "note": ""
            }

        self.save_mapping(mapping_data)
        logger.info(f"매핑 템플릿 생성: {self.mapping_file}")
        logger.info(f"총 {len(source_files)}개 파일에 대해 topic_kr, topic_en을 입력하세요.")

        return mapping_data

    def process_file(
        self,
        source_file: Path,
        topic_kr: str,
        topic_en: str,
        danger: bool = False,
        cover_num: Optional[int] = None
    ) -> Tuple[bool, str]:
        """
        단일 파일 처리

        Returns:
            (성공여부, 새 파일명 또는 에러 메시지)
        """
        if cover_num is None:
            cover_num = self.get_next_cover_number()

        # 파일명 생성
        danger_suffix = "_DANGER" if danger else ""
        new_name = f"cover_{cover_num:02d}_{topic_kr}_{topic_en}{danger_suffix}.png"
        dest_path = self.ready_dir / new_name

        # 중복 체크
        if dest_path.exists():
            return False, f"이미 존재: {new_name}"

        try:
            # 이동 (PNG가 아니면 복사 후 원본 삭제)
            if source_file.suffix.lower() == '.png':
                shutil.move(str(source_file), str(dest_path))
            else:
                # 다른 포맷은 그대로 이동 (확장자 유지하거나 변환 필요시 별도 처리)
                shutil.move(str(source_file), str(dest_path))

            logger.info(f"처리 완료: {source_file.name} -> {new_name}")
            return True, new_name

        except Exception as e:
            return False, str(e)

    def process_mapped_files(self) -> Dict[str, any]:
        """매핑된 파일만 처리"""
        mapping_data = self.load_mapping()
        mappings = mapping_data.get("mappings", {})
        processed = mapping_data.get("processed", [])

        results = {
            "processed": [],
            "skipped": [],
            "errors": []
        }

        source_files = self.get_source_files()

        for source_file in source_files:
            filename = source_file.name

            # 이미 처리된 파일 스킵
            if filename in processed:
                results["skipped"].append({"file": filename, "reason": "이미 처리됨"})
                continue

            # 매핑 확인
            if filename not in mappings:
                results["skipped"].append({"file": filename, "reason": "매핑 없음"})
                continue

            file_mapping = mappings[filename]
            topic_kr = file_mapping.get("topic_kr", "").strip()
            topic_en = file_mapping.get("topic_en", "").strip()
            danger = file_mapping.get("danger", False)

            # 매핑 정보 유효성 검사
            if not topic_kr or not topic_en:
                results["skipped"].append({"file": filename, "reason": "topic 미입력"})
                continue

            # 처리
            success, result = self.process_file(source_file, topic_kr, topic_en, danger)

            if success:
                results["processed"].append({"file": filename, "new_name": result})
                processed.append(filename)
            else:
                results["errors"].append({"file": filename, "error": result})

        # 매핑 파일 업데이트
        mapping_data["processed"] = processed
        self.save_mapping(mapping_data)

        return results

    def process_all_files(self, default_prefix: str = "미분류") -> Dict[str, any]:
        """
        모든 파일 처리 (매핑 없는 파일은 순차 번호로)

        Args:
            default_prefix: 매핑 없는 파일의 기본 접두사
        """
        mapping_data = self.load_mapping()
        mappings = mapping_data.get("mappings", {})
        processed = mapping_data.get("processed", [])

        results = {
            "processed": [],
            "skipped": [],
            "errors": []
        }

        source_files = self.get_source_files()
        unmapped_count = 0

        for source_file in source_files:
            filename = source_file.name

            # 이미 처리된 파일 스킵
            if filename in processed:
                results["skipped"].append({"file": filename, "reason": "이미 처리됨"})
                continue

            # 매핑 확인
            if filename in mappings:
                file_mapping = mappings[filename]
                topic_kr = file_mapping.get("topic_kr", "").strip()
                topic_en = file_mapping.get("topic_en", "").strip()
                danger = file_mapping.get("danger", False)

                if not topic_kr or not topic_en:
                    # 매핑 있지만 정보 없음 -> 미분류로 처리
                    unmapped_count += 1
                    topic_kr = f"{default_prefix}{unmapped_count:02d}"
                    topic_en = f"unknown{unmapped_count:02d}"
                    danger = False
            else:
                # 매핑 없음 -> 미분류로 처리
                unmapped_count += 1
                topic_kr = f"{default_prefix}{unmapped_count:02d}"
                topic_en = f"unknown{unmapped_count:02d}"
                danger = False

            # 처리
            success, result = self.process_file(source_file, topic_kr, topic_en, danger)

            if success:
                results["processed"].append({"file": filename, "new_name": result})
                processed.append(filename)
            else:
                results["errors"].append({"file": filename, "error": result})

        # 매핑 파일 업데이트
        mapping_data["processed"] = processed
        self.save_mapping(mapping_data)

        return results

    def get_status(self) -> Dict[str, any]:
        """현황 조회"""
        source_files = self.get_source_files()
        mapping_data = self.load_mapping()
        mappings = mapping_data.get("mappings", {})
        processed = set(mapping_data.get("processed", []))

        # 분류
        pending_mapped = []
        pending_unmapped = []
        already_processed = []

        for f in source_files:
            if f.name in processed:
                already_processed.append(f.name)
            elif f.name in mappings:
                m = mappings[f.name]
                if m.get("topic_kr") and m.get("topic_en"):
                    pending_mapped.append({
                        "file": f.name,
                        "topic_kr": m["topic_kr"],
                        "topic_en": m["topic_en"]
                    })
                else:
                    pending_unmapped.append(f.name)
            else:
                pending_unmapped.append(f.name)

        # ready 폴더 현황
        ready_count = len(list(self.ready_dir.glob("cover_*.png")))
        published_count = len(list(self.published_dir.glob("cover_*.png")))
        next_num = self.get_next_cover_number()

        return {
            "source_folder": str(self.source_dir),
            "total_source_files": len(source_files),
            "pending_mapped": pending_mapped,
            "pending_unmapped": pending_unmapped,
            "already_processed": already_processed,
            "ready_count": ready_count,
            "published_count": published_count,
            "next_cover_number": next_num,
            "mapping_file": str(self.mapping_file)
        }

    def print_status(self):
        """현황 출력"""
        status = self.get_status()

        print("\n" + "=" * 60)
        print("커버 이미지 소스 처리 현황")
        print("=" * 60)
        print(f"소스 폴더: {status['source_folder']}")
        print(f"매핑 파일: {status['mapping_file']}")
        print()
        print(f"소스 파일 총: {status['total_source_files']}개")
        print(f"  - 처리 대기 (매핑됨): {len(status['pending_mapped'])}개")
        print(f"  - 처리 대기 (미매핑): {len(status['pending_unmapped'])}개")
        print(f"  - 이미 처리됨: {len(status['already_processed'])}개")
        print()
        print(f"02_ready 폴더: {status['ready_count']}개")
        print(f"01_published 폴더: {status['published_count']}개")
        print(f"다음 커버 번호: {status['next_cover_number']}")

        if status['pending_mapped']:
            print("\n--- 처리 대기 (매핑됨) ---")
            for item in status['pending_mapped'][:10]:
                print(f"  {item['file'][:30]}... -> {item['topic_kr']} ({item['topic_en']})")
            if len(status['pending_mapped']) > 10:
                print(f"  ... 외 {len(status['pending_mapped']) - 10}개")

        if status['pending_unmapped']:
            print("\n--- 매핑 필요 ---")
            for f in status['pending_unmapped'][:5]:
                print(f"  {f}")
            if len(status['pending_unmapped']) > 5:
                print(f"  ... 외 {len(status['pending_unmapped']) - 5}개")

        print("=" * 60 + "\n")


def send_telegram_notification(results: Dict):
    """텔레그램 알림 전송"""
    try:
        sys.path.insert(0, str(ROOT))
        from core.pipeline.telegram_notifier import TelegramNotifier

        notifier = TelegramNotifier()
        if not notifier.is_configured():
            return

        processed_count = len(results.get("processed", []))
        error_count = len(results.get("errors", []))

        if processed_count == 0 and error_count == 0:
            return  # 처리할 것 없으면 알림 안함

        message = f"""
<b>커버 소스 자동 처리 완료</b>

처리 시간: {datetime.now().strftime('%Y-%m-%d %H:%M')}
처리됨: <b>{processed_count}개</b>
오류: {error_count}개

02_ready 폴더에서 확인하세요.
        """.strip()

        notifier._send_message(message)
        logger.info("텔레그램 알림 전송 완료")

    except Exception as e:
        logger.warning(f"텔레그램 알림 실패: {e}")


def main():
    parser = argparse.ArgumentParser(
        description="커버 이미지 소스 자동 처리",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  python cover_processor.py              # 매핑된 파일만 처리
  python cover_processor.py --all        # 모든 파일 처리 (미매핑은 순차번호)
  python cover_processor.py --status     # 현황 확인
  python cover_processor.py --init       # 매핑 템플릿 생성

매핑 파일 위치:
  content/images/000_cover/03_cover_sources/cover_mapping.json

매핑 파일 형식:
  {
    "mappings": {
      "hf_20260129_xxx.png": {
        "topic_kr": "포도",
        "topic_en": "grape",
        "danger": true
      }
    }
  }
        """
    )

    parser.add_argument("--all", action="store_true", help="미매핑 파일도 순차 처리")
    parser.add_argument("--status", action="store_true", help="현황 확인")
    parser.add_argument("--init", action="store_true", help="매핑 템플릿 생성")
    parser.add_argument("--notify", action="store_true", help="처리 후 텔레그램 알림")
    parser.add_argument("--dry-run", action="store_true", help="실제 파일 이동 없이 테스트")

    args = parser.parse_args()

    processor = CoverProcessor()

    if args.status:
        processor.print_status()
        return

    if args.init:
        processor.init_mapping_template()
        print(f"\n매핑 파일이 생성되었습니다: {processor.mapping_file}")
        print("파일을 열어 각 이미지의 topic_kr, topic_en을 입력하세요.")
        return

    if args.dry_run:
        logger.info("[DRY-RUN] 실제 파일 이동 없이 테스트")
        processor.print_status()
        return

    # 처리 실행
    logger.info("=" * 60)
    logger.info("커버 이미지 소스 처리 시작")
    logger.info("=" * 60)

    if args.all:
        results = processor.process_all_files()
    else:
        results = processor.process_mapped_files()

    # 결과 출력
    logger.info(f"처리 완료: {len(results['processed'])}개")
    logger.info(f"스킵: {len(results['skipped'])}개")
    logger.info(f"오류: {len(results['errors'])}개")

    for item in results['processed']:
        logger.info(f"  ✅ {item['file'][:30]}... -> {item['new_name']}")

    for item in results['errors']:
        logger.error(f"  ❌ {item['file']}: {item['error']}")

    # 텔레그램 알림
    if args.notify:
        send_telegram_notification(results)

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
