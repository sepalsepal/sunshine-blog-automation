#!/usr/bin/env python3
"""
# ============================================================
# Project Sunshine - Batch Processing Script
# ============================================================
#
# 여러 주제를 한번에 처리하는 배치 스크립트
#
# 사용법:
#   python scripts/batch_process.py --topics apple,banana,cherry
#   python scripts/batch_process.py --all
#   python scripts/batch_process.py --pending
#
# ============================================================
"""

import argparse
import asyncio
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Optional

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_DIR = PROJECT_ROOT / "config"
IMAGES_DIR = PROJECT_ROOT / "images"
MEDIA_BANK = PROJECT_ROOT / "media_bank" / "instagram_ready"
SCRIPTS_DIR = PROJECT_ROOT / "scripts"

# 지원하는 모든 주제
ALL_TOPICS = [
    "apple", "banana", "cherry", "blueberry", "strawberry",
    "watermelon", "carrot", "sweet_potato", "pumpkin", "grape"
]


def get_available_topics() -> List[str]:
    """텍스트 데이터가 있는 주제 목록"""
    topics = []
    for f in CONFIG_DIR.glob("*_text.json"):
        topic = f.stem.replace("_text", "")
        topics.append(topic)
    return sorted(topics)


def get_topics_with_images() -> List[str]:
    """이미지가 준비된 주제 목록"""
    topics = []
    for topic in get_available_topics():
        # 이미지 디렉토리 확인
        possible_dirs = [
            MEDIA_BANK / f"{topic}_v2",
            MEDIA_BANK / topic,
            MEDIA_BANK / f"{topic}_001",
            MEDIA_BANK / f"{topic}_final"
        ]
        for d in possible_dirs:
            if d.exists() and any(d.glob("*.jpg")) or any(d.glob("*.png")):
                topics.append(topic)
                break
    return topics


def get_pending_topics() -> List[str]:
    """아직 처리되지 않은 주제 (이미지 출력 없음)"""
    available = get_available_topics()
    pending = []
    for topic in available:
        output_dir = IMAGES_DIR / topic
        if not output_dir.exists() or not any(output_dir.glob("*.png")):
            pending.append(topic)
    return pending


def get_completed_topics() -> List[str]:
    """이미 처리 완료된 주제"""
    completed = []
    for topic in get_available_topics():
        output_dir = IMAGES_DIR / topic
        if output_dir.exists() and len(list(output_dir.glob("*.png"))) >= 10:
            completed.append(topic)
    return completed


class BatchProcessor:
    """배치 처리 클래스"""

    def __init__(self, dry_run: bool = False, verbose: bool = True):
        self.dry_run = dry_run
        self.verbose = verbose
        self.results: List[Dict] = []

    def log(self, message: str):
        """로그 출력"""
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] {message}")

    def run_text_overlay(self, topic: str) -> bool:
        """텍스트 오버레이 실행"""
        self.log(f"  📝 텍스트 오버레이 생성: {topic}")

        if self.dry_run:
            self.log(f"  ⏭️  [DRY-RUN] 스킵됨")
            return True

        try:
            result = subprocess.run(
                ["node", str(SCRIPTS_DIR / "add_text_overlay_puppeteer.js"), topic],
                cwd=str(SCRIPTS_DIR),
                capture_output=True,
                text=True,
                timeout=120
            )

            if result.returncode == 0:
                self.log(f"  ✅ 완료")
                return True
            else:
                self.log(f"  ❌ 실패: {result.stderr[:200]}")
                return False

        except subprocess.TimeoutExpired:
            self.log(f"  ❌ 타임아웃")
            return False
        except Exception as e:
            self.log(f"  ❌ 오류: {e}")
            return False

    async def generate_caption(self, topic: str) -> Optional[Dict]:
        """캡션 생성"""
        self.log(f"  📝 캡션 생성: {topic}")

        if self.dry_run:
            self.log(f"  ⏭️  [DRY-RUN] 스킵됨")
            return {"topic": topic, "status": "dry-run"}

        try:
            sys.path.insert(0, str(PROJECT_ROOT))
            from core.agents.caption import CaptionAgent

            agent = CaptionAgent()
            result = await agent.run({"topic": topic})

            if result.success:
                caption_data = result.data.get("caption", {})
                self.log(f"  ✅ 캡션 {caption_data.get('character_count', 0)}자, 해시태그 {caption_data.get('hashtag_count', 0)}개")

                # 캡션 저장
                caption_file = CONFIG_DIR / f"{topic}_caption.txt"
                with open(caption_file, 'w', encoding='utf-8') as f:
                    f.write(caption_data.get('full', ''))

                return result.data
            else:
                self.log(f"  ❌ 캡션 생성 실패: {result.error}")
                return None

        except Exception as e:
            self.log(f"  ❌ 오류: {e}")
            return None

    async def fact_check(self, topic: str) -> Optional[Dict]:
        """팩트체크"""
        self.log(f"  🔍 팩트체크: {topic}")

        if self.dry_run:
            self.log(f"  ⏭️  [DRY-RUN] 스킵됨")
            return {"topic": topic, "status": "dry-run"}

        try:
            sys.path.insert(0, str(PROJECT_ROOT))
            from core.agents.fact_checker import FactCheckerAgent

            agent = FactCheckerAgent()
            safety = agent.check_food_safety(topic)

            level = safety.get('safety_level', 'UNKNOWN')
            self.log(f"  ✅ 안전 등급: {level}")

            return safety

        except Exception as e:
            self.log(f"  ❌ 오류: {e}")
            return None

    async def process_topic(self, topic: str) -> Dict:
        """단일 주제 처리"""
        self.log(f"\n{'='*50}")
        self.log(f"📌 [{topic.upper()}] 처리 시작")
        self.log(f"{'='*50}")

        result = {
            "topic": topic,
            "timestamp": datetime.now().isoformat(),
            "steps": {}
        }

        # 1. 텍스트 데이터 확인
        text_file = CONFIG_DIR / f"{topic}_text.json"
        if not text_file.exists():
            self.log(f"  ❌ 텍스트 데이터 없음: {text_file}")
            result["status"] = "failed"
            result["error"] = "no_text_data"
            return result

        self.log(f"  ✅ 텍스트 데이터 확인됨")
        result["steps"]["text_data"] = True

        # 2. 이미지 소스 확인
        has_images = topic in get_topics_with_images()
        result["steps"]["has_images"] = has_images

        if has_images:
            self.log(f"  ✅ 이미지 소스 확인됨")
        else:
            self.log(f"  ⚠️  이미지 소스 없음 (텍스트 오버레이 스킵)")

        # 3. 팩트체크
        fact_result = await self.fact_check(topic)
        result["steps"]["fact_check"] = fact_result

        # 4. 캡션 생성
        caption_result = await self.generate_caption(topic)
        result["steps"]["caption"] = caption_result is not None

        # 5. 텍스트 오버레이 (이미지가 있는 경우만)
        if has_images:
            overlay_result = self.run_text_overlay(topic)
            result["steps"]["text_overlay"] = overlay_result
        else:
            result["steps"]["text_overlay"] = None

        # 결과 판정
        if has_images and result["steps"].get("text_overlay"):
            result["status"] = "completed"
        elif result["steps"].get("caption"):
            result["status"] = "partial"  # 캡션만 완료
        else:
            result["status"] = "failed"

        self.log(f"\n  📊 결과: {result['status'].upper()}")
        return result

    async def process_batch(self, topics: List[str]) -> List[Dict]:
        """배치 처리"""
        self.log(f"\n{'='*60}")
        self.log(f"🚀 배치 처리 시작 - {len(topics)}개 주제")
        self.log(f"{'='*60}")
        self.log(f"주제: {', '.join(topics)}")

        results = []
        for i, topic in enumerate(topics, 1):
            self.log(f"\n[{i}/{len(topics)}] 처리 중...")
            result = await self.process_topic(topic)
            results.append(result)
            self.results.append(result)

        return results

    def print_summary(self):
        """결과 요약 출력"""
        print(f"\n{'='*60}")
        print(f"📊 배치 처리 결과 요약")
        print(f"{'='*60}")

        completed = [r for r in self.results if r.get("status") == "completed"]
        partial = [r for r in self.results if r.get("status") == "partial"]
        failed = [r for r in self.results if r.get("status") == "failed"]

        print(f"\n✅ 완료: {len(completed)}개")
        for r in completed:
            print(f"   - {r['topic']}")

        print(f"\n⚠️  부분 완료 (캡션만): {len(partial)}개")
        for r in partial:
            print(f"   - {r['topic']}")

        print(f"\n❌ 실패: {len(failed)}개")
        for r in failed:
            print(f"   - {r['topic']}: {r.get('error', 'unknown')}")

        print(f"\n{'='*60}")

    def save_report(self, filename: str = None):
        """결과 리포트 저장"""
        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"batch_report_{timestamp}.json"

        report_path = PROJECT_ROOT / "logs" / filename
        report_path.parent.mkdir(exist_ok=True)

        report = {
            "timestamp": datetime.now().isoformat(),
            "total": len(self.results),
            "completed": len([r for r in self.results if r.get("status") == "completed"]),
            "partial": len([r for r in self.results if r.get("status") == "partial"]),
            "failed": len([r for r in self.results if r.get("status") == "failed"]),
            "results": self.results
        }

        with open(report_path, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"\n📄 리포트 저장: {report_path}")


def print_status():
    """현재 상태 출력"""
    print(f"\n{'='*60}")
    print(f"📊 Project Sunshine 현재 상태")
    print(f"{'='*60}")

    available = get_available_topics()
    with_images = get_topics_with_images()
    completed = get_completed_topics()
    pending = get_pending_topics()

    print(f"\n📁 텍스트 데이터 있음: {len(available)}개")
    print(f"   {', '.join(available)}")

    print(f"\n🖼️  이미지 준비됨: {len(with_images)}개")
    print(f"   {', '.join(with_images) if with_images else '없음'}")

    print(f"\n✅ 처리 완료: {len(completed)}개")
    print(f"   {', '.join(completed) if completed else '없음'}")

    print(f"\n⏳ 처리 대기: {len(pending)}개")
    print(f"   {', '.join(pending) if pending else '없음'}")

    print(f"\n{'='*60}")


async def main():
    parser = argparse.ArgumentParser(description="Project Sunshine 배치 처리")
    parser.add_argument("--topics", type=str, help="처리할 주제 (콤마 구분)")
    parser.add_argument("--all", action="store_true", help="모든 주제 처리")
    parser.add_argument("--pending", action="store_true", help="미처리 주제만")
    parser.add_argument("--with-images", action="store_true", help="이미지 있는 주제만")
    parser.add_argument("--dry-run", action="store_true", help="실제 실행 안함")
    parser.add_argument("--status", action="store_true", help="현재 상태 확인")
    parser.add_argument("--quiet", action="store_true", help="간략한 출력")

    args = parser.parse_args()

    # 상태 확인
    if args.status:
        print_status()
        return

    # 주제 선택
    topics = []
    if args.topics:
        topics = [t.strip() for t in args.topics.split(",")]
    elif args.all:
        topics = get_available_topics()
    elif args.pending:
        topics = get_pending_topics()
    elif args.with_images:
        topics = get_topics_with_images()
    else:
        print("사용법:")
        print("  python batch_process.py --status          # 현재 상태")
        print("  python batch_process.py --topics apple,banana")
        print("  python batch_process.py --all             # 모든 주제")
        print("  python batch_process.py --pending         # 미처리만")
        print("  python batch_process.py --with-images     # 이미지 있는 것만")
        print("  python batch_process.py --dry-run --all   # 테스트")
        return

    if not topics:
        print("처리할 주제가 없습니다.")
        return

    # 배치 처리 실행
    processor = BatchProcessor(
        dry_run=args.dry_run,
        verbose=not args.quiet
    )

    await processor.process_batch(topics)
    processor.print_summary()
    processor.save_report()


if __name__ == "__main__":
    asyncio.run(main())
