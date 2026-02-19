#!/usr/bin/env python3
"""
🔐 PD 봉인 운영 원칙 - SSOT v2 (2026-02-03 확정)

핵심 변경: 로컬 폴더 = 진실의 원천 (SSOT)

동기화 우선순위 (v2):
1순위: 폴더 위치 (contents/ vs posted/)
2순위: metadata.json (로컬 상태)
3순위: Google Sheets (리포트)
4순위: Instagram API (사실 확인용)

→ metadata.json, Sheets, Instagram은 전부 보조 정보
→ 충돌 시 로컬 폴더 위치가 정답
"""

import os
import json
import re
from datetime import datetime
from pathlib import Path

# 상태 Enum 임포트
import sys
sys.path.insert(0, str(Path(__file__).parent.parent))
from core.utils.status_enum import (
    ContentStatus, normalize_status, get_status_from_sheets,
    STATUS_LABELS_KR
)

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "contents"
POSTED_DIR = CONTENTS_DIR / "4_posted"    # v3: posted → contents/4_posted
HISTORY_PATH = PROJECT_ROOT / "config" / "data" / "publishing_history.csv"

# v3 상태 폴더
STATUS_FOLDERS = ["3_approved", "2_body_ready", "1_cover_only"]


def find_in_contents(food_id: str, status_filter: str = None) -> Path | None:
    """contents/ 폴더에서 food_id 찾기 (v3 구조 지원)

    Args:
        food_id: 콘텐츠 ID
        status_filter: 특정 상태만 검색 ("3_approved" 등)
    """
    if not CONTENTS_DIR.exists():
        return None

    # v3: 상태 폴더 내 검색
    search_folders = [status_filter] if status_filter else STATUS_FOLDERS
    for status in search_folders:
        status_dir = CONTENTS_DIR / status
        if status_dir.exists():
            for folder in status_dir.iterdir():
                if folder.is_dir() and food_id in folder.name:
                    return folder

    # v2 호환: contents/ 루트 검색
    for folder in CONTENTS_DIR.iterdir():
        if folder.is_dir() and folder.name not in STATUS_FOLDERS and food_id in folder.name:
            return folder

    return None


def find_in_posted(food_id: str) -> Path | None:
    """posted/ 폴더에서 food_id 찾기"""
    if not POSTED_DIR.exists():
        return None

    for month_dir in POSTED_DIR.iterdir():
        if month_dir.is_dir():
            for folder in month_dir.iterdir():
                if folder.is_dir() and food_id in folder.name:
                    return folder
    return None


def find_content_folder(food_id: str) -> Path | None:
    """food_id로 콘텐츠 폴더 찾기 (v2: contents/ 또는 posted/)"""

    # 1. contents/ 검색
    folder = find_in_contents(food_id)
    if folder:
        return folder

    # 2. posted/ 검색
    folder = find_in_posted(food_id)
    if folder:
        return folder

    return None


def get_folder_status(food_id: str) -> str:
    """
    폴더 위치 기반 상태 판단 (v3 SSOT)

    1순위: 폴더 위치 (posted/ > 3_approved > 2_body_ready > 1_cover_only)
    """
    if find_in_posted(food_id):
        return "posted"

    # v3: 상태 폴더 기반 판단
    for status in STATUS_FOLDERS:
        folder = find_in_contents(food_id, status_filter=status)
        if folder:
            if status == "3_approved":
                return "approved"
            elif status == "2_body_ready":
                return "body_ready"
            elif status == "1_cover_only":
                return "cover_only"

    # v2 호환: contents/ 루트
    if find_in_contents(food_id):
        return "in_contents"

    return "not_found"


def get_local_metadata(food_id: str) -> dict | None:
    """로컬 metadata.json에서 상태 조회 (v2: metadata.json)"""
    folder = find_content_folder(food_id)

    if not folder:
        return None

    # v2: metadata.json
    metadata_path = folder / "metadata.json"

    # v1 호환: {food_id}_00_metadata.json
    if not metadata_path.exists():
        v1_path = folder / f"{food_id}_00_metadata.json"
        if v1_path.exists():
            metadata_path = v1_path

    if not metadata_path.exists():
        return None

    try:
        with open(metadata_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return None


def get_local_status(food_id: str) -> str:
    """
    로컬 상태 조회 (v2)

    1순위: 폴더 위치
    2순위: metadata.json
    3순위: 파일 존재 여부
    """
    folder = find_content_folder(food_id)

    if not folder:
        return "unknown"

    # 1순위: posted/ 폴더에 있으면 무조건 posted
    if "posted" in str(folder):
        return "posted"

    # 2순위: metadata.json 확인
    metadata = get_local_metadata(food_id)
    if metadata:
        status = metadata.get("status", "cover_only")
        pd_approved = metadata.get("pd_approved", False)

        if status == "posted":
            return "posted"
        elif status == "rejected":
            return "rejected"
        elif status == "approved" or pd_approved:
            return "approved"
        elif status == "verified":
            return "verified"
        else:
            return status

    # 3순위: 파일 존재 여부로 판단
    cover = folder / f"{food_id}_00.png"
    body1 = folder / f"{food_id}_01.png"

    if not cover.exists():
        return "unknown"
    elif not body1.exists():
        return "cover_only"
    else:
        return "verified"


def check_instagram_posted(food_id: str) -> bool:
    """
    Instagram API로 게시 여부 확인 (v2: 확인용, SSOT 아님)

    현재는 publishing_history.csv 기반으로 대체
    """
    if not HISTORY_PATH.exists():
        return False

    try:
        lines = HISTORY_PATH.read_text().strip().split('\n')
        for line in lines[1:]:  # 헤더 스킵
            parts = line.split(',')
            if len(parts) >= 8:
                content_id = parts[1].strip()
                status = parts[7].strip()
                # v3: status_enum 사용하여 정규화
                normalized = normalize_status(status)
                if content_id == food_id and normalized == ContentStatus.POSTED:
                    return True
    except Exception as e:
        print(f"⚠️ Instagram 상태 확인 오류: {e}")

    return False


def get_sheet_status(food_id: str) -> str | None:
    """
    Google Sheets에서 상태 조회 (v3: status_enum 사용)

    현재는 publishing_history.csv 기반으로 대체
    """
    if not HISTORY_PATH.exists():
        return None

    try:
        lines = HISTORY_PATH.read_text().strip().split('\n')
        for line in lines[1:]:
            parts = line.split(',')
            if len(parts) >= 8:
                content_id = parts[1].strip()
                status = parts[7].strip()
                if content_id == food_id:
                    # v3: status_enum 사용하여 정규화
                    return normalize_status(status)
    except Exception as e:
        print(f"⚠️ Sheets 상태 확인 오류: {e}")

    return None


def sync_content_status(food_id: str) -> dict:
    """
    콘텐츠 상태 동기화 - v2 SSOT (로컬 폴더 기준)

    우선순위:
    1순위: 폴더 위치 (contents/ vs posted/)
    2순위: metadata.json
    3순위: Google Sheets
    4순위: Instagram API

    예외: Instagram에 실제 게시된 경우만 폴더 이동
    """

    # 1순위: 폴더 위치 확인
    folder_status = get_folder_status(food_id)

    if folder_status == "not_found":
        return {
            "food_id": food_id,
            "final_status": "unknown",
            "source": "not_found",
            "synced_at": datetime.now().isoformat()
        }

    if folder_status == "posted":
        # posted/ 폴더에 있으면 무조건 posted
        return {
            "food_id": food_id,
            "final_status": "posted",
            "source": "folder_location",
            "synced_at": datetime.now().isoformat()
        }

    # 2순위: metadata.json 확인
    local_status = get_local_status(food_id)
    source = "local_metadata"

    # 예외 처리: Instagram에 게시됐지만 폴더가 contents/에 있는 경우
    if check_instagram_posted(food_id):
        # 폴더를 posted/로 이동
        apply_sync_result(food_id, {"final_status": "posted"})
        return {
            "food_id": food_id,
            "final_status": "posted",
            "source": "instagram_verified",
            "synced_at": datetime.now().isoformat()
        }

    result = {
        "food_id": food_id,
        "final_status": local_status,
        "source": source,
        "synced_at": datetime.now().isoformat()
    }

    return result


def apply_sync_result(food_id: str, sync_result: dict):
    """동기화 결과 적용 - 폴더 이동 (v2)"""
    from utils.move_to_posted import move_to_posted

    final_status = sync_result["final_status"]

    # 1. Local metadata 업데이트
    update_local_metadata(food_id, final_status)

    # 2. 폴더 이동 (posted인 경우)
    if final_status == "posted":
        folder_path = find_in_contents(food_id)
        if folder_path:
            move_to_posted(food_id, str(folder_path))


def update_local_metadata(food_id: str, status: str):
    """로컬 메타데이터 상태 업데이트 (v2: metadata.json)"""
    folder = find_content_folder(food_id)

    if not folder:
        return

    # v2: metadata.json
    metadata_path = folder / "metadata.json"

    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
    else:
        metadata = {"food_id": food_id}

    metadata["status"] = status
    metadata["synced_at"] = datetime.now().isoformat()

    with open(metadata_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)


def get_all_content_ids() -> list:
    """모든 콘텐츠 ID 목록 (v3 구조 지원)"""
    ids = set()

    # v3: contents/ 상태 폴더 스캔
    if CONTENTS_DIR.exists():
        for status in STATUS_FOLDERS:
            status_dir = CONTENTS_DIR / status
            if status_dir.exists():
                for folder in status_dir.iterdir():
                    if folder.is_dir() and not folder.name.startswith("000_"):
                        parts = folder.name.split("_")
                        if len(parts) >= 2:
                            ids.add(parts[1])

        # v2 호환: contents/ 루트 스캔
        for folder in CONTENTS_DIR.iterdir():
            if folder.is_dir() and folder.name not in STATUS_FOLDERS:
                if not folder.name.startswith("000_") and not folder.name.startswith("🔒"):
                    parts = folder.name.split("_")
                    if len(parts) >= 2:
                        ids.add(parts[1])

    # posted/ 스캔
    if POSTED_DIR.exists():
        for month_dir in POSTED_DIR.iterdir():
            if month_dir.is_dir():
                for folder in month_dir.iterdir():
                    if folder.is_dir():
                        # food_id_한글명 형식
                        parts = folder.name.split("_")
                        if parts:
                            ids.add(parts[0])

    return list(ids)


def sync_all_contents() -> dict:
    """
    전체 콘텐츠 동기화 (v2)
    """

    print("🔄 전체 동기화 시작 (v2 SSOT: 로컬 폴더 기준)")

    stats = {
        "synced": 0,
        "moved_to_posted": 0,
        "errors": 0
    }

    for food_id in get_all_content_ids():
        try:
            result = sync_content_status(food_id)
            stats["synced"] += 1

            if result["final_status"] == "posted" and result["source"] == "instagram_verified":
                stats["moved_to_posted"] += 1

            print(f"  {food_id}: {result['final_status']} (from {result['source']})")

        except Exception as e:
            print(f"  ❌ {food_id}: 오류 - {e}")
            stats["errors"] += 1

    print(f"✅ 전체 동기화 완료: {stats['synced']}개 처리, {stats['moved_to_posted']}개 이동")
    return stats


def get_contents_by_status() -> dict:
    """
    상태별 콘텐츠 분류 (v2)
    """
    result = {
        "cover_only": [],
        "verified": [],
        "approved": [],
        "rejected": [],
        "posted": []
    }

    for food_id in get_all_content_ids():
        status_info = sync_content_status(food_id)
        status = status_info["final_status"]
        if status in result:
            result[status].append(food_id)
        elif status == "unknown":
            result["cover_only"].append(food_id)

    return result


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        cmd = sys.argv[1]

        if cmd == "sync":
            if len(sys.argv) > 2:
                food_id = sys.argv[2]
                result = sync_content_status(food_id)
                print(json.dumps(result, indent=2, ensure_ascii=False))
            else:
                sync_all_contents()

        elif cmd == "status":
            result = get_contents_by_status()
            print(json.dumps(result, indent=2, ensure_ascii=False))

        elif cmd == "check":
            if len(sys.argv) < 3:
                print("사용법: python sync_status.py check <food_id>")
            else:
                food_id = sys.argv[2]
                print(f"폴더 위치: {get_folder_status(food_id)}")
                print(f"로컬 상태: {get_local_status(food_id)}")
                print(f"Instagram: {check_instagram_posted(food_id)}")
                print(f"Sheets: {get_sheet_status(food_id)}")

    else:
        print("사용법 (v2 SSOT):")
        print("  python sync_status.py sync           - 전체 동기화")
        print("  python sync_status.py sync <food_id> - 특정 콘텐츠 동기화")
        print("  python sync_status.py status         - 상태별 분류")
        print("  python sync_status.py check <food_id> - 상태 확인")
