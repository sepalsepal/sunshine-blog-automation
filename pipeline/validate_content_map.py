#!/usr/bin/env python3
"""
CONTENT_MAP 검증 스크립트
Day 12 HARD FAIL 시스템 - HARD FAIL #1

사용법:
    python pipeline/validate_content_map.py <topic>
    python pipeline/validate_content_map.py beef
    python pipeline/validate_content_map.py --all
"""

import json
import sys
import os
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 경로
ROOT = Path(__file__).parent.parent
CONTENT_MAP_PATH = ROOT / "config" / "data" / "content_map.json"
IMAGES_PATH = ROOT / "content" / "images"
TOPICS_PATH = ROOT / "config" / "settings" / "topics_expanded.json"

# 텔레그램 알림 (선택적)
TELEGRAM_ENABLED = os.getenv("TELEGRAM_ENABLED", "false").lower() == "true"


class ValidationResult:
    """검증 결과 클래스"""

    def __init__(self, topic: str):
        self.topic = topic
        self.passed = False
        self.errors = []
        self.warnings = []
        self.info = {}

    def add_error(self, msg: str):
        self.errors.append(msg)
        self.passed = False

    def add_warning(self, msg: str):
        self.warnings.append(msg)

    def to_dict(self):
        return {
            "topic": self.topic,
            "passed": self.passed,
            "errors": self.errors,
            "warnings": self.warnings,
            "info": self.info,
            "timestamp": datetime.now().isoformat()
        }


def load_content_map() -> dict:
    """content_map.json 로드"""
    if not CONTENT_MAP_PATH.exists():
        raise FileNotFoundError(f"CONTENT_MAP not found: {CONTENT_MAP_PATH}")

    with open(CONTENT_MAP_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def load_topics_expanded() -> dict:
    """topics_expanded.json 로드"""
    if not TOPICS_PATH.exists():
        return {}

    with open(TOPICS_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def get_topic_safety(topic: str, topics_data: dict) -> str:
    """주제의 안전 분류 조회"""
    categories = topics_data.get("categories", {})

    # categories가 dict인 경우 (실제 구조)
    if isinstance(categories, dict):
        for cat_key, cat_value in categories.items():
            if isinstance(cat_value, dict):
                for t in cat_value.get("topics", []):
                    if t.get("id") == topic:
                        return t.get("safety", "unknown")
    # categories가 list인 경우 (대비용)
    elif isinstance(categories, list):
        for category in categories:
            for t in category.get("topics", []):
                if t.get("id") == topic:
                    return t.get("safety", "unknown")

    return "unknown"


def validate_topic(topic: str) -> ValidationResult:
    """
    단일 토픽 검증

    HARD FAIL #1 조건:
    1. topic이 CONTENT_MAP에 존재
    2. 폴더 경로가 유효함
    3. status가 blocked가 아님
    """
    result = ValidationResult(topic)

    try:
        content_map = load_content_map()
        topics_data = load_topics_expanded()
    except FileNotFoundError as e:
        result.add_error(f"설정 파일 없음: {e}")
        return result

    contents = content_map.get("contents", {})

    # 조건 1: topic이 CONTENT_MAP에 존재
    if topic not in contents:
        result.add_error(f"CONTENT_MAP에 topic 없음: {topic}")
        return result

    entry = contents[topic]
    result.info["folder"] = entry.get("folder")
    result.info["status"] = entry.get("status")
    result.info["safety"] = entry.get("safety")

    # 조건 2: 폴더 경로가 유효함
    folder_path = IMAGES_PATH / entry.get("folder", "")
    if not folder_path.exists():
        result.add_error(f"폴더 경로 없음: {folder_path}")
        return result

    result.info["folder_exists"] = True

    # 조건 3: status가 blocked가 아님
    status = entry.get("status", "unknown")
    if status == "blocked":
        block_reason = entry.get("block_reason", "사유 없음")
        result.add_error(f"status=blocked: {block_reason}")
        return result

    # 추가 검증: safety 분류 확인
    safety = entry.get("safety")
    topic_safety = get_topic_safety(topic, topics_data)

    if topic_safety != "unknown" and safety != topic_safety:
        result.add_warning(f"safety 불일치: CONTENT_MAP={safety}, topics_expanded={topic_safety}")

    # 모든 조건 통과
    result.passed = True
    return result


def validate_all() -> list:
    """모든 토픽 검증"""
    content_map = load_content_map()
    contents = content_map.get("contents", {})

    results = []
    for topic in contents.keys():
        result = validate_topic(topic)
        results.append(result)

    return results


def send_telegram_alert(result: ValidationResult):
    """HARD FAIL 시 텔레그램 알림"""
    if not TELEGRAM_ENABLED:
        return

    try:
        from services.scripts.telegram_notifier import TelegramNotifier
        notifier = TelegramNotifier()

        message = f"⛔ HARD FAIL: {result.topic} CONTENT_MAP 검증 실패\n\n"
        message += f"오류:\n"
        for error in result.errors:
            message += f"• {error}\n"

        notifier._send_message(message)
    except Exception as e:
        print(f"[WARN] 텔레그램 알림 실패: {e}")


def main():
    """메인 실행"""
    if len(sys.argv) < 2:
        print("사용법: python validate_content_map.py <topic>")
        print("        python validate_content_map.py --all")
        sys.exit(1)

    arg = sys.argv[1]

    if arg == "--all":
        results = validate_all()

        passed = [r for r in results if r.passed]
        failed = [r for r in results if not r.passed]

        print(f"\n{'='*60}")
        print(f"CONTENT_MAP 전체 검증 결과")
        print(f"{'='*60}")
        print(f"총 {len(results)}건 / PASS {len(passed)}건 / FAIL {len(failed)}건")
        print(f"{'='*60}\n")

        if failed:
            print("❌ FAIL 목록:")
            for r in failed:
                print(f"  - {r.topic}: {r.errors}")
            print()

        print("✅ PASS 목록:")
        for r in passed:
            status = r.info.get("status", "unknown")
            print(f"  - {r.topic} ({status})")

        sys.exit(0 if not failed else 1)

    else:
        topic = arg
        result = validate_topic(topic)

        print(f"\n{'='*60}")
        print(f"CONTENT_MAP 검증: {topic}")
        print(f"{'='*60}")

        if result.passed:
            print(f"✅ PASS")
            print(f"  폴더: {result.info.get('folder')}")
            print(f"  상태: {result.info.get('status')}")
            print(f"  안전: {result.info.get('safety')}")
            sys.exit(0)
        else:
            print(f"❌ HARD FAIL")
            for error in result.errors:
                print(f"  오류: {error}")

            # 텔레그램 알림
            send_telegram_alert(result)

            sys.exit(1)


if __name__ == "__main__":
    main()
