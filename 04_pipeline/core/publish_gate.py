#!/usr/bin/env python3
"""
Publish Gate - 게시 전 승인 검증
PD 승인 없이 게시 불가

🔐 PD 봉인 운영 원칙 (2026-02-03 확정)

1. 로컬 폴더 = 상태의 결과
   - 상태의 "원인"은 metadata / Sheets / API
   - 폴더는 결과물일 뿐 판단 근거 아님

2. posted 이동은 단방향
   - posted → contents 되돌림 ❌
   - 재작업 시 새 food_id 생성

3. 동기화 우선순위
   Instagram API > Sheets > Local metadata > Folder
"""

import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent


class BlockedError(Exception):
    """게시 차단 예외"""
    pass


def get_content_metadata(food_id: str) -> dict | None:
    """콘텐츠 메타데이터 로드 (v2: contents/ + metadata.json)"""
    import re

    # v2: contents/ 폴더
    images_dir = PROJECT_ROOT / "contents"
    if not images_dir.exists():
        return None

    # 폴더 찾기
    pattern = re.compile(rf'^\d{{3}}_{food_id}_')
    for folder in images_dir.iterdir():
        if folder.is_dir() and pattern.match(folder.name):
            # v2: metadata.json
            metadata_file = folder / "metadata.json"
            # v1 호환: {food_id}_00_metadata.json
            if not metadata_file.exists():
                v1_file = folder / f"{food_id}_00_metadata.json"
                if v1_file.exists():
                    metadata_file = v1_file
            if metadata_file.exists():
                return json.loads(metadata_file.read_text())
    return None


def update_content_metadata(food_id: str, updates: dict) -> bool:
    """콘텐츠 메타데이터 업데이트 (v2: contents/ + metadata.json)"""
    import re

    # v2: contents/ 폴더
    images_dir = PROJECT_ROOT / "contents"
    if not images_dir.exists():
        return False

    # 폴더 찾기
    pattern = re.compile(rf'^\d{{3}}_{food_id}_')
    for folder in images_dir.iterdir():
        if folder.is_dir() and pattern.match(folder.name):
            # v2: metadata.json
            metadata_file = folder / "metadata.json"
            # v1 호환: 기존 파일 있으면 사용
            v1_file = folder / f"{food_id}_00_metadata.json"
            if not metadata_file.exists() and v1_file.exists():
                metadata_file = v1_file

            # 기존 메타데이터 로드 또는 새로 생성
            if metadata_file.exists():
                metadata = json.loads(metadata_file.read_text())
            else:
                metadata = {"food_id": food_id}
                # 새 파일은 v2 형식으로
                metadata_file = folder / "metadata.json"

            # 업데이트
            metadata.update(updates)

            # 저장
            metadata_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
            return True

    return False


def can_publish(food_id: str) -> tuple[bool, str]:
    """
    게시 가능 여부 확인

    Returns:
        (가능 여부, 사유)
    """
    from core.utils.block_logger import block_pd_not_approved

    metadata = get_content_metadata(food_id)

    if not metadata:
        return False, "메타데이터 없음"

    # PD 승인 확인
    if not metadata.get('pd_approved', False):
        block_pd_not_approved(food_id)
        return False, "PD 승인 필요"

    # 상태 확인
    status = metadata.get('status', 'unknown')
    if status not in ('approved', 'verified'):
        return False, f"상태 오류: {status}"

    return True, "게시 가능"


def approve_content(food_id: str, approved_by: str = "PD_telegram") -> bool:
    """콘텐츠 승인"""
    return update_content_metadata(food_id, {
        "status": "approved",
        "pd_approved": True,
        "approved_at": datetime.now().isoformat(),
        "approved_by": approved_by
    })


def reject_content(food_id: str, reason: str, rejected_by: str = "PD_telegram") -> bool:
    """콘텐츠 반려"""
    from core.utils.block_logger import block_pd_rejected

    block_pd_rejected(food_id, reason)

    return update_content_metadata(food_id, {
        "status": "rejected",
        "pd_approved": False,
        "rejected_at": datetime.now().isoformat(),
        "rejected_by": rejected_by,
        "rejected_reason": reason
    })


def get_content_status(food_id: str) -> str:
    """콘텐츠 상태 조회"""
    metadata = get_content_metadata(food_id)
    if not metadata:
        return "unknown"
    return metadata.get("status", "generated")


def set_content_verified(food_id: str) -> bool:
    """콘텐츠를 검증 완료 상태로 설정"""
    return update_content_metadata(food_id, {
        "status": "verified",
        "pd_approved": False,
        "verified_at": datetime.now().isoformat()
    })


def set_content_published(food_id: str, instagram_url: str = None, post_id: str = None) -> bool:
    """콘텐츠를 게시 완료 상태로 설정"""
    updates = {
        "status": "published",
        "published_at": datetime.now().isoformat()
    }
    if instagram_url:
        updates["instagram_url"] = instagram_url
    if post_id:
        updates["post_id"] = post_id

    return update_content_metadata(food_id, updates)


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        food_id = sys.argv[1]
        can, reason = can_publish(food_id)
        print(f"게시 가능: {can}")
        print(f"사유: {reason}")
    else:
        print("사용법: python publish_gate.py <food_id>")
