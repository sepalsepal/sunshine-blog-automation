#!/usr/bin/env python3
"""
[F-FOLDER-CLEAN] 콘텐츠 폴더 정리 유틸리티

규칙:
- 메인 폴더 = 파이널 이미지 4장만 존재
- _bg.png → archive/ 이동
- _draft, _temp, _test → archive/ 이동
- 게시 완료 후 archive/ 삭제 가능
"""

import os
import shutil
import re
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent


def clean_content_folder(folder_path: str | Path, food_id: str) -> dict:
    """
    폴더 정리 - 파이널 4장만 남기고 나머지 아카이빙

    Args:
        folder_path: 콘텐츠 폴더 경로
        food_id: 음식 영문 키 (예: duck, spinach)

    Returns:
        {"moved": [...], "kept": [...], "errors": [...]}
    """
    folder_path = Path(folder_path)
    if not folder_path.exists():
        return {"error": f"폴더 없음: {folder_path}"}

    archive_path = folder_path / "archive"
    archive_path.mkdir(exist_ok=True)

    # 파이널 파일명 패턴
    final_files = {
        f"{food_id}_00.png",
        f"{food_id}_01.png",
        f"{food_id}_02.png",
        f"{food_id}_03.png",
    }

    # 보존할 파일 패턴 (캡션 등)
    keep_patterns = [
        r"caption.*\.txt$",
        r"caption.*\.json$",
        r"cloudinary.*\.json$",
        r".*_metadata\.json$",
    ]

    result = {
        "moved": [],
        "kept": [],
        "errors": []
    }

    # 폴더 내 모든 파일 검사
    for item in folder_path.iterdir():
        if item.name == "archive" or item.is_dir():
            continue

        filename = item.name

        # 파이널 파일은 유지
        if filename in final_files:
            result["kept"].append(filename)
            continue

        # 보존 패턴 검사
        should_keep = False
        for pattern in keep_patterns:
            if re.match(pattern, filename, re.IGNORECASE):
                should_keep = True
                result["kept"].append(filename)
                break

        if should_keep:
            continue

        # 나머지는 아카이빙
        try:
            src = item
            dst = archive_path / filename
            if dst.exists():
                # 중복 시 타임스탬프 추가
                stem = dst.stem
                suffix = dst.suffix
                timestamp = datetime.now().strftime("%H%M%S")
                dst = archive_path / f"{stem}_{timestamp}{suffix}"
            shutil.move(str(src), str(dst))
            result["moved"].append(filename)
        except Exception as e:
            result["errors"].append(f"{filename}: {str(e)}")

    return result


def find_content_folder(food_id: str) -> Path | None:
    """음식 ID로 콘텐츠 폴더 찾기"""
    images_dir = PROJECT_ROOT / "content/images"

    if not images_dir.exists():
        return None

    pattern = re.compile(rf'^\d{{3}}_{food_id}_')
    for folder in images_dir.iterdir():
        if folder.is_dir() and pattern.match(folder.name):
            return folder

    return None


def clean_by_food_id(food_id: str) -> dict:
    """음식 ID로 폴더 찾아서 정리"""
    folder = find_content_folder(food_id)
    if not folder:
        return {"error": f"폴더 없음: {food_id}"}

    return clean_content_folder(folder, food_id)


def clean_all_folders() -> dict:
    """모든 콘텐츠 폴더 정리"""
    images_dir = PROJECT_ROOT / "content/images"
    results = {}

    for folder in sorted(images_dir.iterdir()):
        if not folder.is_dir():
            continue

        # 특수 폴더 제외
        if folder.name.startswith("000_") or "archive" in folder.name.lower():
            continue

        # 폴더명에서 food_id 추출
        parts = folder.name.split("_")
        if len(parts) < 2:
            continue

        food_id = parts[1]
        result = clean_content_folder(folder, food_id)
        if result.get("moved"):
            results[folder.name] = result

    return results


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1:
        food_id = sys.argv[1]
        print(f"🧹 폴더 정리: {food_id}")
        result = clean_by_food_id(food_id)
        print(f"   이동: {len(result.get('moved', []))}개")
        print(f"   유지: {len(result.get('kept', []))}개")
        if result.get("errors"):
            print(f"   오류: {result['errors']}")
    else:
        print("사용법: python folder_cleaner.py <food_id>")
        print("예: python folder_cleaner.py duck")
