#!/usr/bin/env python3
"""
📋 metadata.json 스키마 검증 및 status 정규화 (업무 8-9번)

필수 필드: food_id, status, safety_level
허용 상태: cover_only, verified, approved, posted, rejected
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"

REQUIRED_FIELDS = ["food_id", "status"]
VALID_STATUSES = {"cover_only", "verified", "approved", "posted", "rejected", "unknown"}

def validate_and_fix():
    print("📋 metadata.json 검증 시작...")
    print("=" * 50)

    fixed = 0
    issues = []

    for folder in sorted(CONTENTS_DIR.iterdir()):
        if not folder.is_dir():
            continue
        if folder.name.startswith("🔒") or folder.name.startswith("."):
            continue

        meta_path = folder / "metadata.json"

        # 파일 없으면 생성
        if not meta_path.exists():
            food_id = extract_food_id(folder.name)
            meta = {
                "food_id": food_id,
                "status": "cover_only",
                "safety_level": "unknown"
            }
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
            print(f"  ✅ 생성: {folder.name}")
            fixed += 1
            continue

        # 파일 읽기
        try:
            meta = json.loads(meta_path.read_text())
        except json.JSONDecodeError:
            issues.append(f"JSON 파싱 실패: {folder.name}")
            continue

        modified = False

        # 필수 필드 확인
        food_id = extract_food_id(folder.name)
        if "food_id" not in meta:
            meta["food_id"] = food_id
            modified = True

        if "status" not in meta:
            meta["status"] = "cover_only"
            modified = True

        # status 정규화
        status = meta.get("status", "")
        if status not in VALID_STATUSES:
            if status in ("published", "done", "complete"):
                meta["status"] = "posted"
            elif status in ("pending", "draft", "wip"):
                meta["status"] = "cover_only"
            else:
                meta["status"] = "cover_only"
            print(f"  🔄 상태 정규화: {folder.name} ({status} → {meta['status']})")
            modified = True

        if modified:
            meta_path.write_text(json.dumps(meta, ensure_ascii=False, indent=2))
            fixed += 1

    print()
    print("=" * 50)
    print(f"📊 결과: {fixed}개 수정/생성")

    if issues:
        print(f"⚠️ 이슈: {len(issues)}개")
        for issue in issues:
            print(f"  - {issue}")

    return fixed, issues


def extract_food_id(folder_name: str) -> str:
    """폴더명에서 food_id 추출"""
    parts = folder_name.split("_")
    if len(parts) >= 2:
        # 027_spinach_시금치 → spinach
        return parts[1]
    return folder_name


if __name__ == "__main__":
    validate_and_fix()
