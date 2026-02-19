#!/usr/bin/env python3
"""
📂 contents 폴더 구조 개편 스크립트
STEP 2: 상태별 분류 및 이동

분류 기준:
- 1_cover_only: 커버(_00.png)만 있고 본문(_01~_03) 없음
- 2_body_ready: 본문 있지만 pd_approved != true
- 3_approved: pd_approved == true (게시 대기)
"""

import json
import shutil
from pathlib import Path
from typing import Literal

# 프로젝트 루트
ROOT = Path(__file__).parent.parent
CONTENTS_DIR = ROOT / "01_contents"

# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = {
#     "cover_only": CONTENTS_DIR / "1_cover_only",
#     "body_ready": CONTENTS_DIR / "2_body_ready",
#     "approved": CONTENTS_DIR / "3_approved",
# }


def get_folder_status(folder: Path) -> Literal["cover_only", "body_ready", "approved", "skip"]:
    """폴더 상태 판별"""

    # 특수 폴더 스킵
    skip_folders = ["1_cover_only", "2_body_ready", "3_approved", "test_visual_guard", "🔒_views"]
    if folder.name in skip_folders:
        return "skip"

    # 숫자로 시작하지 않는 폴더 스킵
    if not folder.name[0].isdigit():
        return "skip"

    # metadata.json 읽기
    metadata_path = folder / "metadata.json"
    metadata = {}
    if metadata_path.exists():
        try:
            metadata = json.loads(metadata_path.read_text())
        except json.JSONDecodeError:
            print(f"  ⚠️ JSON 파싱 오류: {metadata_path}")

    # 1. pd_approved == true → approved
    if metadata.get("pd_approved") is True:
        return "approved"

    # 2. 본문 이미지 존재 여부 확인 (_01, _02, _03 패턴)
    has_body_images = False
    for f in folder.iterdir():
        if f.is_file() and f.suffix.lower() == ".png":
            # 패턴: {name}_01.png, {name}_02.png, {name}_03.png
            stem = f.stem  # 파일명에서 확장자 제거
            # 끝이 _01, _02, _03으로 끝나는지 확인
            if any(stem.endswith(f"_{i:02d}") or stem.endswith(f"_0{i}") for i in range(1, 4)):
                has_body_images = True
                break

    # 3. 본문 있으면 body_ready, 없으면 cover_only
    if has_body_images:
        return "body_ready"
    else:
        return "cover_only"


def analyze_folders() -> dict:
    """모든 폴더 분석 (dry-run)"""
    results = {
        "cover_only": [],
        "body_ready": [],
        "approved": [],
        "skip": [],
    }

    for folder in sorted(CONTENTS_DIR.iterdir()):
        if not folder.is_dir():
            continue

        status = get_folder_status(folder)
        results[status].append(folder.name)

    return results


def move_folders(dry_run: bool = True) -> dict:
    """폴더 이동 실행"""
    results = analyze_folders()
    moved = {"cover_only": 0, "body_ready": 0, "approved": 0}

    for status in ["cover_only", "body_ready", "approved"]:
        target_dir = STATUS_DIRS[status]
        target_dir.mkdir(exist_ok=True)

        for folder_name in results[status]:
            src = CONTENTS_DIR / folder_name
            dst = target_dir / folder_name

            if dry_run:
                print(f"  [DRY] {folder_name} → {status}/")
            else:
                if dst.exists():
                    print(f"  ⚠️ 이미 존재: {dst}")
                    continue
                shutil.move(str(src), str(dst))
                print(f"  ✅ 이동: {folder_name} → {status}/")

            moved[status] += 1

    return moved


def main():
    print("=" * 60)
    print("📂 CONTENTS 폴더 구조 개편")
    print("=" * 60)

    # 1. 분석
    print("\n📊 현재 상태 분석...")
    results = analyze_folders()

    print(f"\n📋 분류 결과:")
    print(f"  - 1_cover_only: {len(results['cover_only'])}개")
    print(f"  - 2_body_ready: {len(results['body_ready'])}개")
    print(f"  - 3_approved: {len(results['approved'])}개")
    print(f"  - skip: {len(results['skip'])}개")

    # 2. 상세 목록 출력
    print("\n" + "=" * 60)
    print("📁 상세 분류 목록")
    print("=" * 60)

    print("\n🔵 [1_cover_only] 커버만 있음:")
    for name in results["cover_only"][:10]:  # 처음 10개만
        print(f"  - {name}")
    if len(results["cover_only"]) > 10:
        print(f"  ... 외 {len(results['cover_only']) - 10}개")

    print("\n🟡 [2_body_ready] 본문 있음 (미승인):")
    for name in results["body_ready"][:10]:
        print(f"  - {name}")
    if len(results["body_ready"]) > 10:
        print(f"  ... 외 {len(results['body_ready']) - 10}개")

    print("\n🟢 [3_approved] PD 승인됨:")
    for name in results["approved"]:
        print(f"  - {name}")

    # 3. 드라이런 먼저
    print("\n" + "=" * 60)
    print("🧪 DRY RUN (이동 미리보기)")
    print("=" * 60)
    move_folders(dry_run=True)

    # 4. 사용자 확인
    print("\n" + "=" * 60)
    response = input("🔄 실제로 이동하시겠습니까? (y/N): ").strip().lower()

    if response == "y":
        print("\n📦 이동 실행 중...")
        moved = move_folders(dry_run=False)
        print(f"\n✅ 완료: cover_only={moved['cover_only']}, body_ready={moved['body_ready']}, approved={moved['approved']}")
    else:
        print("❌ 취소됨")


if __name__ == "__main__":
    main()
