#!/usr/bin/env python3
"""
conditional_pass_expiry.py - 조건부 PASS 30일 자동 제재 로직
RULES.md §22.14.5

타임라인:
- Day 0: 조건부 PASS 부여
- Day 21: 경고 알림 (7일 남음)
- Day 30: 자동 FAIL 전환
- Day 30+: 해당 카테고리 신규 배치 차단
"""

import json
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass

PROJECT_ROOT = Path(__file__).parent.parent.parent

# 설정 파일 경로
PD_MANUAL_CHECK_PATH = PROJECT_ROOT / "박PD_확인용" / "PD_MANUAL_CHECK.json"
BLOCKED_CATEGORIES_PATH = PROJECT_ROOT / "config" / "blocked_categories.json"


@dataclass
class ExpiryStatus:
    """만료 상태"""
    url: str
    category: str
    expiry_date: str
    days_remaining: int
    status: str  # ACTIVE, WARNING, EXPIRED


def load_json(path: Path) -> Dict:
    """JSON 파일 로드"""
    if not path.exists():
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict):
    """JSON 파일 저장"""
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def check_expiry_status(expiry_date_str: str) -> Tuple[int, str]:
    """
    만료 상태 확인

    Returns:
        (days_remaining, status)
    """
    try:
        expiry_date = datetime.strptime(expiry_date_str, "%Y-%m-%d")
    except ValueError:
        return -1, "INVALID_DATE"

    today = datetime.now().replace(hour=0, minute=0, second=0, microsecond=0)
    delta = expiry_date - today
    days_remaining = delta.days

    if days_remaining < 0:
        return days_remaining, "EXPIRED"
    elif days_remaining <= 7:
        return days_remaining, "WARNING"
    else:
        return days_remaining, "ACTIVE"


def get_all_conditional_passes() -> List[ExpiryStatus]:
    """모든 조건부 PASS 항목 조회"""
    check_data = load_json(PD_MANUAL_CHECK_PATH)
    items = check_data.get("items", [])

    results = []
    for item in items:
        if not item.get("conditional_pass", False):
            continue
        if item.get("resolved", False):
            continue

        expiry_date = item.get("expiry_date", "")
        if not expiry_date:
            continue

        days_remaining, status = check_expiry_status(expiry_date)

        results.append(ExpiryStatus(
            url=item.get("url", ""),
            category=item.get("category", ""),
            expiry_date=expiry_date,
            days_remaining=days_remaining,
            status=status
        ))

    return results


def get_warning_items() -> List[ExpiryStatus]:
    """경고 대상 항목 조회 (7일 이내 만료)"""
    all_items = get_all_conditional_passes()
    return [item for item in all_items if item.status == "WARNING"]


def get_expired_items() -> List[ExpiryStatus]:
    """만료된 항목 조회"""
    all_items = get_all_conditional_passes()
    return [item for item in all_items if item.status == "EXPIRED"]


def block_category(category: str, reason: str):
    """
    카테고리 차단 (§22.14.5)

    차단 범위:
    - 차단 대상: 해당 카테고리 "신규 배치"만
    - 기존 게시물: 영향 없음
    """
    blocked = load_json(BLOCKED_CATEGORIES_PATH)

    if "blocked" not in blocked:
        blocked["blocked"] = {}

    blocked["blocked"][category] = {
        "reason": reason,
        "blocked_at": datetime.now().isoformat(),
        "scope": "new_batch_only",
        "existing_posts_affected": False
    }

    blocked["updated_at"] = datetime.now().isoformat()
    save_json(BLOCKED_CATEGORIES_PATH, blocked)

    return True


def unblock_category(category: str):
    """카테고리 차단 해제"""
    blocked = load_json(BLOCKED_CATEGORIES_PATH)

    if "blocked" not in blocked:
        return False

    if category in blocked["blocked"]:
        del blocked["blocked"][category]
        blocked["updated_at"] = datetime.now().isoformat()
        save_json(BLOCKED_CATEGORIES_PATH, blocked)
        return True

    return False


def is_category_blocked(category: str) -> Tuple[bool, Optional[Dict]]:
    """카테고리 차단 여부 확인"""
    blocked = load_json(BLOCKED_CATEGORIES_PATH)

    if "blocked" not in blocked:
        return False, None

    if category in blocked["blocked"]:
        return True, blocked["blocked"][category]

    return False, None


def process_expirations() -> Dict:
    """
    만료 처리 실행

    Returns:
        처리 결과 요약
    """
    results = {
        "processed_at": datetime.now().isoformat(),
        "warnings": [],
        "expired": [],
        "blocked_categories": []
    }

    # 경고 항목
    warnings = get_warning_items()
    for item in warnings:
        results["warnings"].append({
            "url": item.url,
            "category": item.category,
            "days_remaining": item.days_remaining,
            "expiry_date": item.expiry_date
        })

    # 만료 항목 처리
    expired = get_expired_items()
    categories_to_block = set()

    for item in expired:
        results["expired"].append({
            "url": item.url,
            "category": item.category,
            "expiry_date": item.expiry_date
        })
        categories_to_block.add(item.category)

    # 카테고리 차단
    for category in categories_to_block:
        is_blocked, _ = is_category_blocked(category)
        if not is_blocked:
            block_category(
                category,
                f"조건부 PASS 30일 만료 - 자동 차단 (§22.14.5)"
            )
            results["blocked_categories"].append(category)

    return results


def resolve_conditional_pass(url: str):
    """
    조건부 PASS 해결 (URL 업데이트 완료 시)

    만료 해제 조건:
    - URL 업데이트 완료
    - 새 URL 검증 PASS
    - PD_MANUAL_CHECK에서 제거
    """
    check_data = load_json(PD_MANUAL_CHECK_PATH)
    items = check_data.get("items", [])

    category_to_unblock = None

    for item in items:
        if item.get("url") == url:
            item["resolved"] = True
            item["resolved_at"] = datetime.now().isoformat()
            category_to_unblock = item.get("category")
            break

    check_data["items"] = items
    check_data["updated_at"] = datetime.now().isoformat()
    save_json(PD_MANUAL_CHECK_PATH, check_data)

    # 해당 카테고리의 다른 미해결 항목 확인
    if category_to_unblock:
        unresolved = [
            item for item in items
            if item.get("category") == category_to_unblock
            and item.get("conditional_pass", False)
            and not item.get("resolved", False)
        ]

        # 미해결 항목 없으면 차단 해제
        if not unresolved:
            unblock_category(category_to_unblock)
            return True, category_to_unblock

    return True, None


def daily_check():
    """
    일일 점검 (cron 또는 스케줄러에서 호출)

    - Day 21: 경고 알림 생성
    - Day 30: 자동 FAIL 전환 + 카테고리 차단
    """
    results = process_expirations()

    # 로그 저장
    log_dir = PROJECT_ROOT / "logs" / "expiry"
    log_dir.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    log_file = log_dir / f"expiry_check_{date_str}.json"
    save_json(log_file, results)

    return results


# CLI
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="조건부 PASS 만료 관리 (§22.14.5)")
    parser.add_argument("--check", action="store_true", help="일일 점검 실행")
    parser.add_argument("--list-warnings", action="store_true", help="경고 항목 조회")
    parser.add_argument("--list-expired", action="store_true", help="만료 항목 조회")
    parser.add_argument("--list-blocked", action="store_true", help="차단 카테고리 조회")
    parser.add_argument("--resolve", type=str, help="URL 해결 처리")

    args = parser.parse_args()

    if args.check:
        results = daily_check()
        print("=== 일일 점검 결과 ===")
        print(f"처리 시각: {results['processed_at']}")
        print(f"경고: {len(results['warnings'])}건")
        print(f"만료: {len(results['expired'])}건")
        print(f"신규 차단: {len(results['blocked_categories'])}개 카테고리")

        if results["warnings"]:
            print("\n[경고 항목]")
            for w in results["warnings"]:
                print(f"  - {w['category']}: {w['days_remaining']}일 남음")

        if results["expired"]:
            print("\n[만료 항목]")
            for e in results["expired"]:
                print(f"  - {e['category']}: {e['url'][:50]}...")

        if results["blocked_categories"]:
            print("\n[신규 차단 카테고리]")
            for c in results["blocked_categories"]:
                print(f"  - {c}")

    elif args.list_warnings:
        warnings = get_warning_items()
        print(f"=== 경고 항목 ({len(warnings)}건) ===")
        for w in warnings:
            print(f"  [{w.category}] {w.days_remaining}일 남음: {w.url[:60]}...")

    elif args.list_expired:
        expired = get_expired_items()
        print(f"=== 만료 항목 ({len(expired)}건) ===")
        for e in expired:
            print(f"  [{e.category}] 만료: {e.url[:60]}...")

    elif args.list_blocked:
        blocked = load_json(BLOCKED_CATEGORIES_PATH)
        blocked_cats = blocked.get("blocked", {})
        print(f"=== 차단 카테고리 ({len(blocked_cats)}개) ===")
        for cat, info in blocked_cats.items():
            print(f"  - {cat}: {info.get('reason', '')}")

    elif args.resolve:
        success, unblocked = resolve_conditional_pass(args.resolve)
        if success:
            print(f"URL 해결 완료: {args.resolve}")
            if unblocked:
                print(f"카테고리 차단 해제: {unblocked}")
        else:
            print("URL을 찾을 수 없습니다.")

    else:
        parser.print_help()
