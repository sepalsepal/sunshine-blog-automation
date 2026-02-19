"""
📊 콘텐츠 상태 Enum (v3 통일)

로컬 상태와 Google Sheets 상태 매핑 통일

변경 이력:
- 2026-02-04: cover_done → cover_only, body_done → body_ready 통일
"""

from enum import Enum
from typing import Dict


class ContentStatus(str, Enum):
    """콘텐츠 상태 열거형"""
    COVER_ONLY = "cover_only"      # 표지만 완료
    BODY_READY = "body_ready"      # 본문까지 완료 (승인 대기)
    APPROVED = "approved"          # PD 승인 완료 (게시 대기)
    POSTED = "posted"              # 게시 완료
    REJECTED = "rejected"          # 반려됨


# 한글 라벨 (UI/보고용)
STATUS_LABELS_KR: Dict[str, str] = {
    ContentStatus.COVER_ONLY: "표지완료",
    ContentStatus.BODY_READY: "본문완료",
    ContentStatus.APPROVED: "승인완료",
    ContentStatus.POSTED: "게시완료",
    ContentStatus.REJECTED: "반려됨",
}

# 이모지 라벨 (텔레그램/대시보드용)
STATUS_LABELS_EMOJI: Dict[str, str] = {
    ContentStatus.COVER_ONLY: "📁 표지완료",
    ContentStatus.BODY_READY: "🟡 본문완료",
    ContentStatus.APPROVED: "🟢 승인완료",
    ContentStatus.POSTED: "📤 게시완료",
    ContentStatus.REJECTED: "❌ 반려됨",
}

# 구버전 호환 매핑 (마이그레이션용)
LEGACY_STATUS_MAP: Dict[str, str] = {
    # 구버전 → 신버전
    "cover_done": ContentStatus.COVER_ONLY,
    "body_done": ContentStatus.BODY_READY,
    "verified": ContentStatus.BODY_READY,  # verified → body_ready
    "표지완료": ContentStatus.COVER_ONLY,
    "검증완료": ContentStatus.BODY_READY,
    "승인완료": ContentStatus.APPROVED,
    "게시완료": ContentStatus.POSTED,
}


def normalize_status(status: str) -> str:
    """상태값 정규화 (구버전 → 신버전 변환)

    Args:
        status: 원본 상태값

    Returns:
        정규화된 상태값 (ContentStatus enum 값)
    """
    if not status:
        return ContentStatus.COVER_ONLY

    status_lower = status.lower().strip()

    # 이미 신버전 형식이면 그대로 반환
    if status_lower in [s.value for s in ContentStatus]:
        return status_lower

    # 구버전 매핑
    if status in LEGACY_STATUS_MAP:
        return LEGACY_STATUS_MAP[status]

    if status_lower in LEGACY_STATUS_MAP:
        return LEGACY_STATUS_MAP[status_lower]

    # 기본값
    return ContentStatus.COVER_ONLY


def get_status_label(status: str, emoji: bool = True) -> str:
    """상태 라벨 반환

    Args:
        status: 상태값
        emoji: 이모지 포함 여부

    Returns:
        한글 라벨
    """
    normalized = normalize_status(status)
    labels = STATUS_LABELS_EMOJI if emoji else STATUS_LABELS_KR

    return labels.get(normalized, f"❓ {status}")


def get_status_for_sheets(status: str) -> str:
    """Google Sheets용 상태값 반환

    Args:
        status: 로컬 상태값

    Returns:
        시트용 한글 상태값
    """
    normalized = normalize_status(status)
    return STATUS_LABELS_KR.get(normalized, status)


def get_status_from_sheets(sheet_status: str) -> str:
    """Google Sheets 상태값을 로컬 상태로 변환

    Args:
        sheet_status: 시트의 한글 상태값

    Returns:
        로컬 상태값 (enum)
    """
    return normalize_status(sheet_status)


# 폴더명 ↔ 상태 매핑
FOLDER_STATUS_MAP: Dict[str, str] = {
    "1_cover_only": ContentStatus.COVER_ONLY,
    "2_body_ready": ContentStatus.BODY_READY,
    "3_approved": ContentStatus.APPROVED,
    "4_posted": ContentStatus.POSTED,
}

STATUS_FOLDER_MAP: Dict[str, str] = {v: k for k, v in FOLDER_STATUS_MAP.items()}


def get_folder_for_status(status: str) -> str:
    """상태에 해당하는 폴더명 반환"""
    normalized = normalize_status(status)
    return STATUS_FOLDER_MAP.get(normalized, "1_cover_only")


def get_status_for_folder(folder_name: str) -> str:
    """폴더명에 해당하는 상태 반환"""
    return FOLDER_STATUS_MAP.get(folder_name, ContentStatus.COVER_ONLY)
