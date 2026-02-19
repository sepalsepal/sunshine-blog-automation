#!/usr/bin/env python3
"""
Block Logger - 실패/차단 로그 기록 유틸리티
BLOCK_LOG_SCHEMA.json 형식 준수
"""

import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
BLOCK_LOG_DIR = PROJECT_ROOT / "config/logs/blocks"


def log_block(
    reason_code: str,
    food_id: str = None,
    detected_by: str = "unknown",
    reason_detail: str = None,
    rule_name: str = None,
    rule_version: str = None,
    recovery_action: str = "none",
    retry_count: int = 0
) -> dict:
    """
    차단/실패 로그 기록

    Args:
        reason_code: 차단 사유 코드 (BLOCK_LOG_SCHEMA 참조)
        food_id: 콘텐츠 식별자
        detected_by: 차단을 감지한 모듈
        reason_detail: 상세 설명
        rule_name: 적용된 규칙 이름
        rule_version: 적용된 규칙 버전
        recovery_action: 복구 조치 (auto_retry, regenerate, manual_fix, skip, none)
        retry_count: 재시도 횟수

    Returns:
        기록된 로그 객체
    """
    BLOCK_LOG_DIR.mkdir(parents=True, exist_ok=True)

    log_entry = {
        "blocked": True,
        "reason_code": reason_code,
        "reason_detail": reason_detail,
        "food_id": food_id,
        "rule_name": rule_name,
        "rule_version": rule_version,
        "detected_by": detected_by,
        "timestamp": datetime.now().isoformat(),
        "recovery_action": recovery_action,
        "recovery_status": "pending",
        "retry_count": retry_count
    }

    # 파일에 기록
    log_file = BLOCK_LOG_DIR / f"block_{datetime.now().strftime('%Y%m%d')}.jsonl"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

    print(f"🚫 BLOCK: {reason_code} - {food_id or 'unknown'}")
    return log_entry


def get_recent_blocks(limit: int = 10) -> list:
    """최근 차단 로그 조회"""
    if not BLOCK_LOG_DIR.exists():
        return []

    blocks = []
    for log_file in sorted(BLOCK_LOG_DIR.glob("block_*.jsonl"), reverse=True):
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    blocks.append(json.loads(line))
                    if len(blocks) >= limit:
                        return blocks
    return blocks


def get_blocks_by_food(food_id: str) -> list:
    """특정 음식의 차단 이력 조회"""
    if not BLOCK_LOG_DIR.exists():
        return []

    blocks = []
    for log_file in BLOCK_LOG_DIR.glob("block_*.jsonl"):
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    entry = json.loads(line)
                    if entry.get("food_id") == food_id:
                        blocks.append(entry)
    return blocks


# 편의 함수들
def block_missing_metadata(food_id: str, field: str, detected_by: str = "pre_check"):
    return log_block(
        reason_code="MISSING_METADATA",
        food_id=food_id,
        detected_by=detected_by,
        reason_detail=f"필수 필드 누락: {field}",
        recovery_action="regenerate"
    )


def block_rule_mismatch(food_id: str, expected: str, actual: str, detected_by: str = "verifier"):
    return log_block(
        reason_code="RULE_MISMATCH",
        food_id=food_id,
        detected_by=detected_by,
        reason_detail=f"규칙 불일치: 기대 {expected}, 실제 {actual}",
        recovery_action="regenerate"
    )


def block_pd_not_approved(food_id: str):
    return log_block(
        reason_code="PD_NOT_APPROVED",
        food_id=food_id,
        detected_by="publish_gate",
        reason_detail="PD 승인 없이 게시 시도",
        recovery_action="none"
    )


def block_pd_rejected(food_id: str, reason: str):
    return log_block(
        reason_code="PD_REJECTED",
        food_id=food_id,
        detected_by="pd_approval",
        reason_detail=f"PD 반려: {reason}",
        recovery_action="regenerate"
    )
