#!/usr/bin/env python3
"""
일괄 콘텐츠 제작 스크립트
- 13개 토픽 순차 제작
- AI 이미지 비용 관리
- 진행 상황 저장

작성: 2026-01-30
"""

import asyncio
import json
import sys
from pathlib import Path
from datetime import datetime

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from services.scripts.auto_content_producer import ContentProducer

# 제작 대상 토픽 (스케줄 순서)
TOPICS = [
    {"en": "spinach", "kr": "시금치", "num": 26, "safety": "safe"},
    {"en": "zucchini", "kr": "애호박", "num": 27, "safety": "safe"},
    {"en": "chicken", "kr": "닭고기", "num": 28, "safety": "safe"},
    {"en": "beef", "kr": "소고기", "num": 29, "safety": "safe"},
    {"en": "salmon", "kr": "연어", "num": 30, "safety": "safe"},
    {"en": "tuna", "kr": "참치", "num": 31, "safety": "safe"},
    {"en": "yogurt", "kr": "요거트", "num": 32, "safety": "safe"},
    {"en": "tofu", "kr": "두부", "num": 33, "safety": "safe"},
    {"en": "boiled_egg", "kr": "삶은달걀", "num": 34, "safety": "safe"},
    {"en": "mackerel", "kr": "고등어", "num": 35, "safety": "safe"},
    {"en": "potato", "kr": "감자", "num": 36, "safety": "safe"},
    {"en": "chocolate", "kr": "초콜릿", "num": 37, "safety": "dangerous"},
    {"en": "blackberry", "kr": "블랙베리", "num": 38, "safety": "safe"},
]

PROGRESS_FILE = ROOT / "config/data/batch_progress.json"


def load_progress() -> dict:
    """진행 상황 로드"""
    if PROGRESS_FILE.exists():
        return json.loads(PROGRESS_FILE.read_text(encoding='utf-8'))
    return {"completed": [], "failed": [], "started_at": None}


def save_progress(progress: dict):
    """진행 상황 저장"""
    PROGRESS_FILE.parent.mkdir(parents=True, exist_ok=True)
    PROGRESS_FILE.write_text(json.dumps(progress, indent=2, ensure_ascii=False), encoding='utf-8')


async def produce_all(start_from: int = 0, dry_run: bool = False):
    """모든 토픽 일괄 제작"""

    progress = load_progress()

    if not progress.get("started_at"):
        progress["started_at"] = datetime.now().isoformat()

    print("="*60)
    print("📦 일괄 콘텐츠 제작 시작")
    print(f"   대상: {len(TOPICS)}개 토픽")
    print(f"   시작점: {start_from}")
    print(f"   드라이런: {dry_run}")
    print("="*60)

    producer = ContentProducer()

    for i, topic in enumerate(TOPICS[start_from:], start=start_from):
        topic_en = topic["en"]
        topic_kr = topic["kr"]

        # 이미 완료된 토픽 스킵
        if topic_en in progress["completed"]:
            print(f"\n⏭️  [{i+1}/{len(TOPICS)}] {topic_kr} - 이미 완료됨, 스킵")
            continue

        print(f"\n\n{'='*60}")
        print(f"📦 [{i+1}/{len(TOPICS)}] {topic_kr} ({topic_en})")
        print(f"{'='*60}")

        # 텍스트 설정 로드
        text_config_path = ROOT / f"config/settings/{topic_en}_text.json"

        if text_config_path.exists():
            text_config = json.loads(text_config_path.read_text(encoding='utf-8'))
        else:
            print(f"❌ 텍스트 설정 없음: {text_config_path}")
            progress["failed"].append(topic_en)
            save_progress(progress)
            continue

        if dry_run:
            print(f"   [DRY RUN] 실제 제작 안 함")
            continue

        try:
            result = await producer.produce_content(
                topic_en=topic_en,
                topic_kr=topic_kr,
                folder_number=topic["num"],
                text_config=text_config,
                safety=topic["safety"]
            )

            if result.get("success"):
                progress["completed"].append(topic_en)
                print(f"✅ {topic_kr} 제작 완료!")
            else:
                progress["failed"].append(topic_en)
                print(f"❌ {topic_kr} 제작 실패: {result.get('error')}")

        except Exception as e:
            progress["failed"].append(topic_en)
            print(f"❌ {topic_kr} 제작 오류: {e}")

        save_progress(progress)

        # API 레이트 리밋 방지
        if i < len(TOPICS) - 1:
            print("\n⏳ 다음 토픽까지 5초 대기...")
            await asyncio.sleep(5)

    # 최종 요약
    print("\n\n" + "="*60)
    print("📊 일괄 제작 완료")
    print("="*60)
    print(f"✅ 성공: {len(progress['completed'])}개")
    print(f"❌ 실패: {len(progress['failed'])}개")

    if progress["failed"]:
        print(f"\n실패 목록: {', '.join(progress['failed'])}")

    return progress


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="일괄 콘텐츠 제작")
    parser.add_argument("--start-from", type=int, default=0, help="시작 인덱스 (0부터)")
    parser.add_argument("--dry-run", action="store_true", help="테스트 모드")
    parser.add_argument("--status", action="store_true", help="진행 상황 확인")

    args = parser.parse_args()

    if args.status:
        progress = load_progress()
        print("📊 진행 상황")
        print(f"  완료: {len(progress.get('completed', []))}개")
        print(f"  실패: {len(progress.get('failed', []))}개")
        print(f"  남음: {len(TOPICS) - len(progress.get('completed', []))}개")

        if progress.get("completed"):
            print(f"\n완료 목록: {', '.join(progress['completed'])}")
        sys.exit(0)

    asyncio.run(produce_all(start_from=args.start_from, dry_run=args.dry_run))
