#!/usr/bin/env python3
"""
🔐 PD 봉인 규칙 - 신고 시스템 (2026-02-03 확정)

1. 신고는 상태를 직접 바꾸지 않는다
   - 신고 = 사실 전달
   - 상태 변경은: 자동 조치 결과 / PD 승인 / 명시적 파이프라인
   - ❌ "신고했으니까 자동으로 반려" 같은 로직 금지

2. 처리 방식
   - SYNC_ERROR: 완전 자동 (3중 동기화)
   - IMAGE_ERROR: 반자동 (확인 + 알림)
   - INFO_ERROR: PD 확인 필요
   - OTHER: PD 확인 필요

3. 신고 버튼은 모든 콘텐츠에 상시 표시
   - 상태와 무관
   - 승인/게시와 독립
   - 신고는 권한이 아니라 안전밸브

신고 유형:
- SYNC_ERROR: 이미 게시됨 (동기화 오류) → 완전 자동
- IMAGE_ERROR: 이미지 문제 → 반자동 + 알림
- INFO_ERROR: 정보 오류 → PD 확인 필요
- OTHER: 기타 → PD 확인 필요
"""

import json
import re
from datetime import datetime
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
REPORTS_DIR = PROJECT_ROOT / "config" / "logs" / "reports"


def log_report(report_data: dict) -> dict:
    """
    신고 로그 기록

    Args:
        report_data: 신고 데이터
            - food_id: 콘텐츠 ID
            - report_code: SYNC_ERROR, IMAGE_ERROR, INFO_ERROR, OTHER
            - report_detail: 상세 내용
            - reported_by: 신고자
            - auto_action: 자동 조치 내용
            - action_result: 조치 결과

    Returns:
        기록된 로그 데이터
    """
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    report_entry = {
        "type": "pd_report",
        "food_id": report_data.get("food_id"),
        "report_code": report_data.get("report_code"),
        "report_detail": report_data.get("report_detail"),
        "reported_by": report_data.get("reported_by", "PD_telegram"),
        "reported_at": report_data.get("reported_at", datetime.now().isoformat()),
        "auto_action": report_data.get("auto_action", "none"),
        "action_result": report_data.get("action_result"),
        "resolved_at": report_data.get("resolved_at"),
    }

    # 파일에 기록
    log_file = REPORTS_DIR / f"report_{datetime.now().strftime('%Y%m%d')}.jsonl"
    with open(log_file, 'a', encoding='utf-8') as f:
        f.write(json.dumps(report_entry, ensure_ascii=False) + '\n')

    print(f"⚠️ REPORT: {report_entry['report_code']} - {report_entry['food_id']}")
    return report_entry


def handle_sync_error(food_id: str) -> dict:
    """
    SYNC_ERROR 처리 - 완전 자동

    1. 3중 동기화 실행
    2. 결과에 따라 자동 이동
    3. 결과 반환
    """
    from utils.sync_status import sync_content_status

    # 3중 동기화 실행
    result = sync_content_status(food_id)

    # 로그 기록
    log_report({
        "food_id": food_id,
        "report_code": "SYNC_ERROR",
        "report_detail": "이미 게시된 콘텐츠가 목록에 표시됨",
        "auto_action": "sync_check",
        "action_result": result,
        "resolved_at": datetime.now().isoformat() if result["final_status"] == "published" else None
    })

    return {
        "success": True,
        "food_id": food_id,
        "final_status": result["final_status"],
        "source": result["source"],
        "auto_resolved": result["final_status"] == "published"
    }


def handle_image_error(food_id: str) -> dict:
    """
    IMAGE_ERROR 처리 - 반자동 (확인 + 알림)
    """
    from utils.sync_status import find_content_folder

    folder = find_content_folder(food_id)

    if not folder:
        return {
            "success": False,
            "food_id": food_id,
            "all_valid": False,
            "issues": "폴더를 찾을 수 없음"
        }

    # 이미지 파일 확인
    issues = []
    images = [
        folder / f"{food_id}_00.png",
        folder / f"{food_id}_01.png",
        folder / f"{food_id}_02.png",
        folder / f"{food_id}_03.png",
    ]

    for img in images:
        if not img.exists():
            issues.append(f"{img.name} 없음")
        elif img.stat().st_size < 1000:  # 1KB 미만 = 손상 가능성
            issues.append(f"{img.name} 손상 의심 (크기 너무 작음)")

    result = {
        "success": True,
        "food_id": food_id,
        "all_valid": len(issues) == 0,
        "issues": issues if issues else None,
        "folder": str(folder)
    }

    # 로그 기록
    log_report({
        "food_id": food_id,
        "report_code": "IMAGE_ERROR",
        "report_detail": "이미지 문제 신고",
        "auto_action": "image_check",
        "action_result": result
    })

    return result


def handle_info_error(food_id: str, detail: str = None) -> dict:
    """
    INFO_ERROR 처리 - PD 확인 필요 (자동 수정 금지)
    """
    result = {
        "success": True,
        "food_id": food_id,
        "status": "pending_pd_review",
        "detail": detail
    }

    # 로그 기록만
    log_report({
        "food_id": food_id,
        "report_code": "INFO_ERROR",
        "report_detail": detail or "정보/텍스트 오류 신고",
        "auto_action": "none",
        "action_result": result
    })

    return result


def handle_other_error(food_id: str, detail: str = None) -> dict:
    """
    OTHER 처리 - PD 확인 필요
    """
    result = {
        "success": True,
        "food_id": food_id,
        "status": "pending_pd_review",
        "detail": detail
    }

    log_report({
        "food_id": food_id,
        "report_code": "OTHER",
        "report_detail": detail or "기타 문제 신고",
        "auto_action": "none",
        "action_result": result
    })

    return result


def handle_text_overlap_error(food_id: str, detail: str = None) -> dict:
    """
    TEXT_OVERLAP 처리 - 텍스트 중첩 오류 신고

    텍스트가 이미지나 다른 텍스트와 겹치는 경우

    🔐 상태 Enum v1.0 규칙:
    - TEXT_OVERLAP → reoverlay (텍스트 오버레이만 재작업)
    - 이미지 유지, body_ready 상태 유지
    - ❌ regenerate (이미지 재생성) 아님!

    Returns:
        신고 결과 (reoverlay 권장)
    """
    from utils.sync_status import find_content_folder
    from core.status_enum import ReportType, ActionType, get_action_for_report

    folder = find_content_folder(food_id)

    # 신고 유형에 따른 액션 결정
    report_type = ReportType.TEXT_OVERLAP
    action_type = get_action_for_report(report_type)  # REOVERLAY

    result = {
        "success": True,
        "food_id": food_id,
        "status": "body_ready",  # 상태 유지!
        "issue_type": report_type.value,
        "action_type": action_type.value,  # reoverlay
        "detail": detail or "텍스트 중첩 문제",
        "folder": str(folder) if folder else None,
        "recommendation": "텍스트 오버레이 재작업 (이미지 유지)"
    }

    # 로그 기록
    log_report({
        "food_id": food_id,
        "report_code": "TEXT_OVERLAP",
        "report_detail": detail or "텍스트 중첩 문제 신고",
        "auto_action": action_type.value,  # reoverlay
        "action_result": result
    })

    return result


def get_recent_reports(limit: int = 10) -> list:
    """최근 신고 로그 조회"""
    if not REPORTS_DIR.exists():
        return []

    reports = []
    for log_file in sorted(REPORTS_DIR.glob("report_*.jsonl"), reverse=True):
        with open(log_file, 'r', encoding='utf-8') as f:
            for line in f:
                if line.strip():
                    reports.append(json.loads(line))
                    if len(reports) >= limit:
                        return reports
    return reports


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "sync" and len(sys.argv) > 2:
            food_id = sys.argv[2]
            result = handle_sync_error(food_id)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif cmd == "image" and len(sys.argv) > 2:
            food_id = sys.argv[2]
            result = handle_image_error(food_id)
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif cmd == "list":
            reports = get_recent_reports()
            for r in reports:
                print(f"{r['reported_at'][:16]} | {r['report_code']} | {r['food_id']}")

    else:
        print("사용법:")
        print("  python report_handler.py sync <food_id>  - 동기화 오류 처리")
        print("  python report_handler.py image <food_id> - 이미지 오류 처리")
        print("  python report_handler.py list            - 최근 신고 목록")
