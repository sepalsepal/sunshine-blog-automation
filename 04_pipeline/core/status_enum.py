#!/usr/bin/env python3
"""
Project Sunshine — 상태 Enum 정의
버전: v1.0
작성: 김부장 + 레드2
승인: 박세준 PD
일시: 2026-02-04

목적:
- 상태 간 전이 규칙 명확화
- 시스템 오류 ≠ PD 판단 분리
- 자동화 신뢰도 향상
"""

from enum import Enum
from typing import Optional
from datetime import datetime


class ContentStatus(Enum):
    """콘텐츠 상태 정의 (6개)"""

    # ═══════════════════════════════════════════
    # 제작 단계
    # ═══════════════════════════════════════════

    COVER_ONLY = "cover_only"
    """
    표지만 완료
    - 표지 이미지 1장 존재
    - 본문 이미지 없음
    - 다음: body_ready (본문 생성 후)
    - 폴더: 1_cover_only/
    """

    BODY_READY = "body_ready"
    """
    본문 완료 (PD 승인 대기)
    - 이미지 4장 존재 (표지 + 본문 3장)
    - 텍스트 오버레이 완료
    - 다음: approved (승인) / cover_only (반려)
    - 폴더: 2_body_ready/
    """

    # ═══════════════════════════════════════════
    # 승인 단계
    # ═══════════════════════════════════════════

    APPROVED = "approved"
    """
    PD 승인 완료 (게시 대기)
    - PD가 명시적으로 승인
    - 게시 가능 상태
    - 다음: posted (게시 성공) / approved 유지 (게시 실패)
    - 폴더: 3_approved/
    """

    REJECTED = "rejected"
    """
    PD 반려
    - PD가 명시적으로 반려 (시스템 오류 아님!)
    - 사유 기록 필수
    - 다음: cover_only (수정 후 재작업)
    - 폴더: 1_cover_only/ (복귀)
    """

    # ═══════════════════════════════════════════
    # 게시 단계
    # ═══════════════════════════════════════════

    POSTED = "posted"
    """
    게시 완료
    - Instagram 업로드 성공
    - media_id 존재
    - 최종 상태
    - 폴더: 4_posted/YYYY-MM/
    """

    POST_FAILED = "post_failed"
    """
    게시 실패 (시스템 오류)
    - Instagram API 오류
    - 네트워크 오류
    - 모듈 오류 등
    - 상태: approved 유지 (post_failed는 임시 상태)
    - 다음: 재시도 → posted / approved
    - ⚠️ 반려(rejected)와 절대 혼동 금지
    """


class ReportType(Enum):
    """신고 유형 정의 (3개)"""

    TEXT_OVERLAP = "text_overlap"
    """
    텍스트 중첩/오류
    - 처리: reoverlay (텍스트 오버레이만 재작업)
    - 이미지: 유지
    - 상태: body_ready 유지
    """

    IMAGE_ERROR = "image_error"
    """
    이미지 깨짐/오류
    - 처리: regenerate (이미지 전체 재생성)
    - 상태: cover_only로 복귀
    """

    OTHER = "other"
    """
    기타 문제
    - 처리: 로그 기록만
    - 상태: 유지
    """


class ActionType(Enum):
    """재작업 유형 정의 (2개)"""

    REOVERLAY = "reoverlay"
    """
    텍스트 오버레이만 재작업
    - 배경 이미지: 유지
    - 텍스트 레이아웃: 재작업
    - 비용: 무료 (API 호출 없음)
    - 시간: ~10초
    """

    REGENERATE = "regenerate"
    """
    이미지 전체 재생성
    - 배경 이미지: 재생성 (Flux 2.0 Pro)
    - 텍스트 레이아웃: 재작업
    - 비용: 유료 (API 호출)
    - 시간: ~30초
    """


# ═══════════════════════════════════════════
# 상태 ↔ 폴더 매핑
# ═══════════════════════════════════════════

STATUS_TO_FOLDER = {
    ContentStatus.COVER_ONLY: "1_cover_only",
    ContentStatus.BODY_READY: "2_body_ready",
    ContentStatus.APPROVED: "3_approved",
    ContentStatus.POSTED: "4_posted",
    ContentStatus.REJECTED: "1_cover_only",  # 복귀
}

FOLDER_TO_STATUS = {
    "1_cover_only": ContentStatus.COVER_ONLY,
    "2_body_ready": ContentStatus.BODY_READY,
    "3_approved": ContentStatus.APPROVED,
    "4_posted": ContentStatus.POSTED,
}


# ═══════════════════════════════════════════
# 상태 전이 규칙
# ═══════════════════════════════════════════

VALID_TRANSITIONS = {
    # cover_only
    (ContentStatus.COVER_ONLY, "make_body"): ContentStatus.BODY_READY,

    # body_ready
    (ContentStatus.BODY_READY, "approve"): ContentStatus.APPROVED,
    (ContentStatus.BODY_READY, "reject"): ContentStatus.REJECTED,
    (ContentStatus.BODY_READY, "reoverlay"): ContentStatus.BODY_READY,  # 유지
    (ContentStatus.BODY_READY, "regenerate"): ContentStatus.COVER_ONLY,

    # approved
    (ContentStatus.APPROVED, "post_success"): ContentStatus.POSTED,
    (ContentStatus.APPROVED, "post_fail"): ContentStatus.APPROVED,  # 유지!
    (ContentStatus.APPROVED, "reject"): ContentStatus.REJECTED,

    # rejected → 수정 후 재작업
    (ContentStatus.REJECTED, "rework"): ContentStatus.COVER_ONLY,
}


class TransitionError(Exception):
    """잘못된 상태 전이 예외"""
    pass


def transition_status(
    current: ContentStatus,
    action: str,
    reason: str = None
) -> ContentStatus:
    """
    상태 전이 규칙

    Args:
        current: 현재 상태
        action: 수행할 액션
        reason: 사유 (reject 시 필수)

    Returns:
        새 상태

    Raises:
        TransitionError: 잘못된 전이
    """
    key = (current, action)

    if key not in VALID_TRANSITIONS:
        raise TransitionError(f"Invalid transition: {current.value} + {action}")

    # 반려 시 사유 필수
    if action == "reject" and not reason:
        raise TransitionError("Reject requires a reason")

    return VALID_TRANSITIONS[key]


def get_folder_for_status(status: ContentStatus) -> str:
    """상태에 해당하는 폴더명 반환"""
    return STATUS_TO_FOLDER.get(status, "1_cover_only")


def get_status_from_folder(folder_name: str) -> Optional[ContentStatus]:
    """폴더명에서 상태 추출"""
    # 4_posted/YYYY-MM 패턴 처리
    if folder_name.startswith("4_posted") or "4_posted" in folder_name:
        return ContentStatus.POSTED

    return FOLDER_TO_STATUS.get(folder_name)


def get_action_for_report(report_type: ReportType) -> ActionType:
    """신고 유형에 따른 재작업 타입 반환"""
    mapping = {
        ReportType.TEXT_OVERLAP: ActionType.REOVERLAY,
        ReportType.IMAGE_ERROR: ActionType.REGENERATE,
        ReportType.OTHER: None,  # 로그만
    }
    return mapping.get(report_type)


def get_allowed_actions(status: ContentStatus) -> list[str]:
    """상태별 허용 액션 목록"""
    actions = {
        ContentStatus.COVER_ONLY: ["make_body"],
        ContentStatus.BODY_READY: ["approve", "reject", "reoverlay", "regenerate"],
        ContentStatus.APPROVED: ["post_success", "post_fail", "reject"],
        ContentStatus.POSTED: [],  # 최종 상태
        ContentStatus.REJECTED: ["rework"],
    }
    return actions.get(status, [])


# ═══════════════════════════════════════════
# metadata 스키마 생성
# ═══════════════════════════════════════════

def create_metadata_schema(food_id: str, status: ContentStatus = ContentStatus.COVER_ONLY) -> dict:
    """표준 metadata.json 스키마 생성"""
    now = datetime.now().isoformat()

    return {
        "food_id": food_id,
        "status": status.value,
        "created_at": now,
        "updated_at": now,

        "pd_approved": False,
        "approved_at": None,
        "approved_by": None,
        "rejected_at": None,
        "rejected_by": None,
        "rejected_reason": None,

        "posted_at": None,
        "instagram_media_id": None,
        "instagram_url": None,

        "post_failed": False,
        "post_failed_reason": None,
        "post_failed_at": None,

        "reports": []
    }


def add_report_to_metadata(metadata: dict, report_type: ReportType, detail: str = None) -> dict:
    """metadata에 신고 기록 추가"""
    if "reports" not in metadata:
        metadata["reports"] = []

    metadata["reports"].append({
        "type": report_type.value,
        "detail": detail,
        "reported_at": datetime.now().isoformat(),
        "resolved": False
    })

    metadata["updated_at"] = datetime.now().isoformat()
    return metadata


# ═══════════════════════════════════════════
# 테스트
# ═══════════════════════════════════════════

if __name__ == "__main__":
    print("=" * 50)
    print("상태 Enum 테스트")
    print("=" * 50)

    # 정상 전이 테스트
    print("\n1. 정상 전이 테스트:")
    status = ContentStatus.COVER_ONLY
    print(f"  시작: {status.value}")

    status = transition_status(status, "make_body")
    print(f"  → make_body: {status.value}")

    status = transition_status(status, "approve")
    print(f"  → approve: {status.value}")

    status = transition_status(status, "post_success")
    print(f"  → post_success: {status.value}")

    # 게시 실패 테스트
    print("\n2. 게시 실패 테스트 (approved 유지):")
    status = ContentStatus.APPROVED
    status = transition_status(status, "post_fail")
    print(f"  approved + post_fail = {status.value}")
    assert status == ContentStatus.APPROVED, "게시 실패 시 approved 유지해야 함!"

    # 텍스트 중첩 테스트
    print("\n3. 텍스트 중첩 테스트 (body_ready 유지):")
    status = ContentStatus.BODY_READY
    status = transition_status(status, "reoverlay")
    print(f"  body_ready + reoverlay = {status.value}")
    assert status == ContentStatus.BODY_READY, "reoverlay 시 body_ready 유지해야 함!"

    # 신고 → 액션 매핑 테스트
    print("\n4. 신고 → 액션 매핑:")
    for rt in ReportType:
        action = get_action_for_report(rt)
        print(f"  {rt.value} → {action.value if action else 'log_only'}")

    # 잘못된 전이 테스트
    print("\n5. 잘못된 전이 테스트:")
    try:
        transition_status(ContentStatus.POSTED, "approve")
    except TransitionError as e:
        print(f"  예상된 오류: {e}")

    print("\n✅ 모든 테스트 통과!")
