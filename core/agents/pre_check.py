#!/usr/bin/env python3
"""
PRE-CHECK 차단기

목적: 생성 전에 차단 → 삭제/재제작 루프 제거
원칙: 하나라도 실패하면 생성 진입 금지
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Tuple

# 프로젝트 루트
ROOT = Path(__file__).parent.parent.parent


class PreCheckError(Exception):
    """PRE-CHECK 실패 예외"""
    pass


def log_violation(food_name: str, content_type: str, reason: str):
    """PRE-CHECK 위반 로그 기록"""
    log_dir = ROOT / "config/logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    log_file = log_dir / "pre_check_violations.log"

    entry = {
        "timestamp": datetime.now().isoformat(),
        "food_name": food_name,
        "content_type": content_type,
        "reason": reason
    }

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry, ensure_ascii=False) + "\n")


def pre_check(food_name: str, content_type: str) -> Tuple[bool, str]:
    """
    생성 전 차단기
    하나라도 실패하면 생성 진입 금지

    Args:
        food_name: 음식 영문명 (예: duck)
        content_type: "cover" 또는 "body"

    Returns:
        (통과 여부, 실패 사유)
    """

    # 1. rule_name 존재 확인
    if content_type == "cover":
        rules_path = ROOT / "config/cover_rules.json"
        rule_name = "cover_v1"
    elif content_type == "body":
        rules_path = ROOT / "config/body_rules.json"
        rule_name = "body_v1"
    else:
        return False, f"알 수 없는 content_type: {content_type}"

    if not rules_path.exists():
        return False, f"규칙 파일 없음: {rules_path.name}"

    try:
        rules = json.loads(rules_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, f"규칙 파일 파싱 오류: {e}"

    # rules 구조 확인 (rules 키 아래에 있을 수 있음)
    rules_dict = rules.get("rules", rules)
    if rule_name not in rules_dict:
        return False, f"규칙 없음: {rule_name}"

    # 2. food → safety 매핑 존재 확인
    safety_path = ROOT / "config/settings/food_safety.json"
    if not safety_path.exists():
        return False, f"안전도 DB 없음: {safety_path.name}"

    try:
        safety_db = json.loads(safety_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as e:
        return False, f"안전도 DB 파싱 오류: {e}"

    # 안전도 DB 구조: {"safe": [...], "caution": [...], "danger": [...]}
    all_foods = []
    for category in ["safe", "caution", "danger"]:
        all_foods.extend(safety_db.get(category, []))

    if food_name not in all_foods:
        return False, f"음식 안전도 없음: {food_name}"

    # 3. 모두 통과
    return True, "PRE-CHECK 통과"


def enforce_pre_check(food_name: str, content_type: str) -> bool:
    """
    PRE-CHECK 강제 실행
    실패 시 예외 발생 → 생성 진입 불가

    Args:
        food_name: 음식 영문명
        content_type: "cover" 또는 "body"

    Returns:
        True (통과 시)

    Raises:
        PreCheckError: 실패 시
    """
    passed, reason = pre_check(food_name, content_type)

    if not passed:
        # 로그 기록
        log_violation(food_name, content_type, reason)

        # 예외 발생 → 생성 중단
        raise PreCheckError(f"PRE-CHECK 실패: {reason}")

    print(f"✅ PRE-CHECK 통과: {food_name} ({content_type})")
    return True


def pre_check_all(food_name: str) -> Tuple[bool, str]:
    """
    cover + body 모두 PRE-CHECK

    Returns:
        (통과 여부, 메시지)
    """
    # Cover 체크
    cover_passed, cover_reason = pre_check(food_name, "cover")
    if not cover_passed:
        return False, f"[cover] {cover_reason}"

    # Body 체크
    body_passed, body_reason = pre_check(food_name, "body")
    if not body_passed:
        return False, f"[body] {body_reason}"

    return True, "PRE-CHECK 전체 통과"


# CLI 실행
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python pre_check.py <food_name> [content_type]")
        print("Example: python pre_check.py duck cover")
        sys.exit(1)

    food = sys.argv[1]
    ctype = sys.argv[2] if len(sys.argv) > 2 else None

    print("=" * 50)
    print(f"🔍 PRE-CHECK: {food}")
    print("=" * 50)

    if ctype:
        passed, reason = pre_check(food, ctype)
        print(f"   [{ctype}] {'✅ PASS' if passed else '❌ FAIL'}: {reason}")
    else:
        passed, reason = pre_check_all(food)
        print(f"   {'✅ PASS' if passed else '❌ FAIL'}: {reason}")

    print("=" * 50)
    sys.exit(0 if passed else 1)
