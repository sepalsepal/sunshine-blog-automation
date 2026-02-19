#!/usr/bin/env python3
"""
기존 표지에 메타데이터 일괄 생성
- _00.png 있고 _00_metadata.json 없는 폴더 대상
- cover_v1 규칙 적용
"""

import json
import hashlib
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent
IMAGES_DIR = PROJECT_ROOT / "content/images"
COVER_RULES_PATH = PROJECT_ROOT / "config/cover_rules.json"


def get_rule_hash() -> str:
    """cover_rules.json의 cover_v1 규칙 해시 생성"""
    if not COVER_RULES_PATH.exists():
        return "no_rules_file"

    rules = json.loads(COVER_RULES_PATH.read_text())
    cover_v1 = rules.get("rules", {}).get("cover_v1", {})
    rule_str = json.dumps(cover_v1, sort_keys=True)
    return hashlib.sha256(rule_str.encode()).hexdigest()[:16]


def generate_metadata_for_folder(folder: Path, rule_hash: str) -> dict | None:
    """폴더에 메타데이터 생성"""

    # 실제 *_00.png 파일 찾기 (복합키 지원: coca_cola_00.png 등)
    cover_files = list(folder.glob("*_00.png"))
    if not cover_files:
        return None

    cover_file = cover_files[0]

    # 파일명에서 food_key 추출: "coca_cola_00.png" → "coca_cola"
    food_key = cover_file.stem.replace("_00", "")

    # 메타데이터 파일 확인 (이미 있으면 스킵)
    metadata_file = folder / f"{food_key}_00_metadata.json"
    if metadata_file.exists():
        return {"status": "skip", "reason": "already exists"}

    # 파일 크기
    file_size_kb = round(cover_file.stat().st_size / 1024)

    # 메타데이터 생성
    metadata = {
        "rule_name": "cover_v1",
        "rule_hash": rule_hash,
        "generated_at": datetime.now().isoformat() + "Z",
        "input_image": f"{food_key}_00_cover.png",
        "title_text": food_key.upper(),
        "output_file": f"{food_key}_00.png",
        "file_size_kb": file_size_kb,
        "note": "batch_generated_from_existing_cover"
    }

    # 저장
    metadata_file.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))

    return {"status": "created", "file": str(metadata_file)}


def main():
    print("=" * 50)
    print("📋 기존 표지 메타데이터 일괄 생성")
    print("=" * 50)

    # 규칙 해시 계산
    rule_hash = get_rule_hash()
    print(f"📌 Rule Hash: {rule_hash}")

    # 결과 집계
    created = 0
    skipped = 0
    failed = 0

    # 폴더 스캔
    for folder in sorted(IMAGES_DIR.iterdir()):
        if not folder.is_dir():
            continue

        # 숫자로 시작하는 폴더만 (000_cover 등 제외)
        if not folder.name[0].isdigit():
            continue

        # 특수 폴더 제외
        if folder.name.startswith("000_") or "archive" in folder.name or "test" in folder.name:
            continue

        result = generate_metadata_for_folder(folder, rule_hash)

        if result is None:
            failed += 1
        elif result["status"] == "skip":
            skipped += 1
        elif result["status"] == "created":
            created += 1
            print(f"  ✅ {folder.name}")

    print()
    print("=" * 50)
    print(f"📊 결과: 생성 {created}개 | 스킵 {skipped}개 | 실패 {failed}개")
    print("=" * 50)

    return created


if __name__ == "__main__":
    main()
