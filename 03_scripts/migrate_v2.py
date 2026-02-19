#!/usr/bin/env python3
"""
🚀 폴더 구조 v2 마이그레이션 스크립트

v1: content/images/{번호}_{food_id}_{한글명}/
    - metadata: {food_id}_00_metadata.json

v2: contents/{번호}_{food_id}_{한글명}/
    - metadata: metadata.json

변경사항:
1. content/images → contents
2. {food_id}_00_metadata.json → metadata.json
3. SSOT: Instagram API → 로컬 폴더
"""

import os
import shutil
import json
import re
from datetime import datetime
from pathlib import Path

# 설정
PROJECT_ROOT = Path(__file__).parent.parent
V1_PATH = PROJECT_ROOT / "content" / "images"
V2_PATH = PROJECT_ROOT / "01_contents"
POSTED_PATH = PROJECT_ROOT / "posted"
FOOD_SAFETY_PATH = PROJECT_ROOT / "config" / "settings" / "food_safety.json"


def load_food_names() -> dict:
    """food_safety.json에서 한글명 로드"""
    # 이미 폴더명에 한글명이 있으므로 추출
    return {}


def get_korean_name_from_folder(folder_name: str) -> str:
    """폴더명에서 한글명 추출"""
    # 예: 026_kale_케일 → 케일
    parts = folder_name.split("_")
    if len(parts) >= 3:
        return "_".join(parts[2:])
    return parts[-1] if parts else folder_name


def get_food_id_from_folder(folder_name: str) -> str:
    """폴더명에서 food_id 추출"""
    # 예: 026_kale_케일 → kale
    parts = folder_name.split("_")
    if len(parts) >= 2:
        return parts[1]
    return parts[0] if parts else folder_name


def migrate_content_folder():
    """v1 → v2 폴더 이동"""

    migrated = []
    errors = []
    skipped = []

    # v1 폴더 스캔
    if not V1_PATH.exists():
        print(f"⚠️ v1 경로 없음: {V1_PATH}")
        return

    # v2 폴더 생성
    V2_PATH.mkdir(parents=True, exist_ok=True)

    folders = sorted([f for f in V1_PATH.iterdir() if f.is_dir()])

    for folder in folders:
        folder_name = folder.name

        # 특수 폴더 스킵
        if folder_name.startswith("000_") or "archive" in folder_name.lower():
            skipped.append(folder_name)
            print(f"⏭️ 스킵: {folder_name}")
            continue

        try:
            # food_id와 한글명 추출
            food_id = get_food_id_from_folder(folder_name)
            name_ko = get_korean_name_from_folder(folder_name)

            # 기존 번호 유지 (폴더명에서 추출)
            match = re.match(r'^(\d{3})_', folder_name)
            if match:
                number = match.group(1)
                new_folder_name = f"{number}_{food_id}_{name_ko}"
            else:
                # 번호 없으면 새로 부여
                new_folder_name = folder_name

            dst_path = V2_PATH / new_folder_name

            # 이미 존재하면 스킵
            if dst_path.exists():
                skipped.append(folder_name)
                print(f"⏭️ 이미 존재: {new_folder_name}")
                continue

            # 폴더 복사
            shutil.copytree(folder, dst_path)

            # 메타데이터 변환
            convert_metadata(dst_path, food_id, name_ko)

            migrated.append({
                "food_id": food_id,
                "from": str(folder),
                "to": str(dst_path)
            })

            print(f"✅ {folder_name} → {new_folder_name}")

        except Exception as e:
            errors.append({
                "folder": folder_name,
                "error": str(e)
            })
            print(f"❌ {folder_name}: {e}")

    # 결과 저장
    save_migration_report(migrated, errors, skipped)

    print(f"\n{'='*50}")
    print(f"📊 마이그레이션 완료")
    print(f"✅ 성공: {len(migrated)}개")
    print(f"⏭️ 스킵: {len(skipped)}개")
    print(f"❌ 실패: {len(errors)}개")


def convert_metadata(folder_path: Path, food_id: str, name_ko: str):
    """
    메타데이터 파일명 변환

    v1: {food_id}_00_metadata.json
    v2: metadata.json
    """

    # v1 메타데이터 패턴 찾기
    v1_patterns = [
        f"{food_id}_00_metadata.json",
        f"{food_id}_metadata.json",
    ]

    v1_meta_path = None
    for pattern in v1_patterns:
        check_path = folder_path / pattern
        if check_path.exists():
            v1_meta_path = check_path
            break

    v2_meta_path = folder_path / "metadata.json"

    if v1_meta_path and v1_meta_path != v2_meta_path:
        # v1 메타데이터 로드
        with open(v1_meta_path, "r", encoding="utf-8") as f:
            meta = json.load(f)

        # v2 필드 추가/변환
        meta["food_id"] = food_id
        meta["food_name_ko"] = name_ko

        if "status" not in meta:
            meta["status"] = determine_status(folder_path, food_id)

        if "pd_approved" not in meta:
            meta["pd_approved"] = False

        # v2 형식으로 저장
        with open(v2_meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        # v1 파일 삭제
        v1_meta_path.unlink()
        print(f"   📄 메타데이터 변환: {v1_meta_path.name} → metadata.json")

    elif not v2_meta_path.exists():
        # 메타데이터 없으면 생성
        status = determine_status(folder_path, food_id)

        meta = {
            "food_id": food_id,
            "food_name_ko": name_ko,
            "status": status,
            "pd_approved": False,
            "created_at": datetime.now().isoformat(),
            "rule_name": "cover_v1",
            "rule_version": "1.0.0"
        }

        with open(v2_meta_path, "w", encoding="utf-8") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        print(f"   📄 메타데이터 생성: metadata.json (status={status})")


def determine_status(folder_path: Path, food_id: str) -> str:
    """파일 존재 여부로 상태 판단"""
    cover = folder_path / f"{food_id}_00.png"
    body1 = folder_path / f"{food_id}_01.png"
    body2 = folder_path / f"{food_id}_02.png"

    if not cover.exists():
        return "unknown"
    elif not body1.exists() or not body2.exists():
        return "cover_only"
    else:
        return "verified"


def save_migration_report(migrated: list, errors: list, skipped: list):
    """마이그레이션 리포트 저장"""

    report = {
        "timestamp": datetime.now().isoformat(),
        "version": "v1 → v2",
        "summary": {
            "migrated": len(migrated),
            "skipped": len(skipped),
            "errors": len(errors)
        },
        "migrated": migrated,
        "skipped": skipped,
        "errors": errors
    }

    logs_dir = PROJECT_ROOT / "logs" / "migrations"
    logs_dir.mkdir(parents=True, exist_ok=True)

    filepath = logs_dir / f"migrate_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"📄 리포트 저장: {filepath}")


if __name__ == "__main__":
    print("🚀 폴더 구조 v2 마이그레이션 시작")
    print("="*50)
    print(f"v1 경로: {V1_PATH}")
    print(f"v2 경로: {V2_PATH}")
    print("="*50)
    migrate_content_folder()
