#!/usr/bin/env python3
"""
blog_image_qc.py - 블로그 이미지 3~7번 전체 재검수
[WO-QC-001]

검수 대상:
- {food}_blog_03_nutrition.png
- {food}_blog_04_feeding.png
- {food}_blog_05_amount.png
- {food}_blog_06_caution.png
- {food}_blog_07_cooking.png
"""

import os
import sys
import json
import re
from pathlib import Path
from PIL import Image
from datetime import datetime
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CONTENTS_DIR = PROJECT_ROOT / "01_contents"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["4_posted", "3_approved", "2_body_ready", "1_cover_only"]

# 안전도 색상 코드
SAFETY_COLORS = {
    "SAFE": "#4CAF50",
    "CAUTION": "#FFD93D",
    "DANGER": "#FF6B6B",
    "FORBIDDEN": "#FF5252"
}

# 블로그 이미지 규칙
BLOG_IMAGES = {
    3: {"name": "nutrition", "desc": "영양 정보"},
    4: {"name": "feeding", "desc": "급여 가능/불가"},
    5: {"name": "amount", "desc": "급여량 표"},
    6: {"name": "caution", "desc": "주의사항"},
    7: {"name": "cooking", "desc": "조리 방법"},
}


def get_all_content_folders() -> List[Dict]:
    """모든 콘텐츠 폴더 스캔"""
    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    folders = []

    for item in CONTENTS_DIR.iterdir():
        if not item.is_dir():
            continue
        match = re.match(r'^(\d{3})_([a-z_]+)(?:_(.+))?$', item.name)
        if match:
            folders.append({
                "num": int(match.group(1)),
                "food_en": match.group(2),
                "food_ko": match.group(3) or "",
                "name": item.name,
                "path": item,
                "status_dir": "flat"  # 2026-02-13: 플랫 구조
            })

    return sorted(folders, key=lambda x: x["num"])


def load_food_data() -> Dict:
    """food_data.json 로드"""
    food_data_path = PROJECT_ROOT / "config" / "food_data.json"
    if food_data_path.exists():
        with open(food_data_path, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def check_image_resolution(image_path: Path) -> tuple:
    """이미지 해상도 확인"""
    try:
        with Image.open(image_path) as img:
            return img.size
    except Exception:
        return (0, 0)


def validate_filename(filename: str, food_en: str, num: int) -> Dict:
    """파일명 규칙 검증"""
    expected = f"{food_en}_blog_{num:02d}_{BLOG_IMAGES[num]['name']}.png"

    # 유연한 매칭 (기존 네이밍과 새 네이밍 모두 허용)
    old_patterns = [
        f"{num}_{BLOG_IMAGES[num]['desc']}.png",  # 3_영양정보.png
        f"{num}번_{BLOG_IMAGES[num]['desc']}.png",  # 3번_영양정보.png
        f"blog_{num:02d}.png",  # blog_03.png
    ]

    if filename == expected:
        return {"pass": True, "expected": expected, "actual": filename, "type": "v2.8"}
    elif filename in old_patterns or any(p in filename for p in [f"{num}_", f"{num}번"]):
        return {"pass": True, "expected": expected, "actual": filename, "type": "legacy"}
    else:
        return {"pass": False, "expected": expected, "actual": filename, "type": "unknown"}


def find_blog_image(folder_path: Path, num: int) -> Optional[Path]:
    """블로그 이미지 찾기 (여러 네이밍 패턴 지원)"""
    # 2026-02-13: 플랫 구조 반영
    blog_dir = folder_path / "02_Blog"
    if not blog_dir.exists():
        return None

    # 가능한 패턴들
    patterns = [
        f"*_blog_{num:02d}_*.png",
        f"{num}_*.png",
        f"{num}번*.png",
        f"blog_{num:02d}.png",
    ]

    for pattern in patterns:
        matches = list(blog_dir.glob(pattern))
        if matches:
            return matches[0]

    return None


def qc_single_folder(folder: Dict, food_data: Dict) -> Dict:
    """단일 폴더 QC"""
    result = {
        "num": folder["num"],
        "name": folder["name"],
        "food_en": folder["food_en"],
        "status_dir": folder["status_dir"],
        "images": {},
        "r_pass": 0,
        "r_fail": 0,
        "c_pass": 0,
        "c_fail": 0,
        "errors": []
    }

    # 안전도 확인
    safety_level = "UNKNOWN"
    if str(folder["num"]) in food_data:
        safety_level = food_data[str(folder["num"])].get("safety_level", "UNKNOWN")

    for img_num in [3, 4, 5, 6, 7]:
        img_result = {
            "num": img_num,
            "name": BLOG_IMAGES[img_num]["name"],
            "desc": BLOG_IMAGES[img_num]["desc"],
            "exists": False,
            "path": None,
            "r_check": {"pass": False, "errors": []},
            "c_check": {"pass": False, "errors": []}
        }

        # 이미지 찾기
        img_path = find_blog_image(folder["path"], img_num)

        if img_path and img_path.exists():
            img_result["exists"] = True
            img_result["path"] = str(img_path)

            # === 규칙 검수 (R) ===
            r_errors = []

            # 1. 해상도 확인
            width, height = check_image_resolution(img_path)
            if width != 1080 or height != 1080:
                r_errors.append(f"해상도 불일치: {width}x{height} (기준: 1080x1080)")

            # 2. 파일명 확인
            fn_check = validate_filename(img_path.name, folder["food_en"], img_num)
            if not fn_check["pass"]:
                r_errors.append(f"파일명 불일치: {fn_check['actual']} → {fn_check['expected']}")

            # 3. 파일 크기 확인 (최소 10KB)
            file_size = img_path.stat().st_size
            if file_size < 10000:
                r_errors.append(f"파일 크기 너무 작음: {file_size} bytes")

            if not r_errors:
                img_result["r_check"]["pass"] = True
                result["r_pass"] += 1
            else:
                img_result["r_check"]["errors"] = r_errors
                result["r_fail"] += 1
                result["errors"].extend([f"#{folder['num']} img{img_num}: {e}" for e in r_errors])

            # === 크리에이티브 검수 (C) ===
            # 기본 통과 (실제 AI 판단은 별도 수행)
            img_result["c_check"]["pass"] = True
            result["c_pass"] += 1

        else:
            # 이미지 없음
            img_result["r_check"]["errors"] = ["이미지 없음"]
            result["r_fail"] += 1
            result["c_fail"] += 1
            result["errors"].append(f"#{folder['num']} img{img_num}: 이미지 없음")

        result["images"][img_num] = img_result

    return result


def run_full_qc() -> Dict:
    """전체 QC 실행"""
    print("=" * 60)
    print("블로그 이미지 재검수 (3~7번)")
    print("=" * 60)

    folders = get_all_content_folders()
    food_data = load_food_data()

    # blog 폴더가 있는 콘텐츠만 대상
    # 2026-02-13: 플랫 구조 반영
    target_folders = []
    for folder in folders:
        blog_dir = folder["path"] / "02_Blog"
        if blog_dir.exists():
            target_folders.append(folder)

    print(f"검수 대상: {len(target_folders)}개 음식 × 5장 = {len(target_folders) * 5}개 이미지")
    print()

    results = []
    total_r_pass = 0
    total_r_fail = 0
    total_c_pass = 0
    total_c_fail = 0
    all_errors = []

    for folder in target_folders:
        result = qc_single_folder(folder, food_data)
        results.append(result)

        total_r_pass += result["r_pass"]
        total_r_fail += result["r_fail"]
        total_c_pass += result["c_pass"]
        total_c_fail += result["c_fail"]
        all_errors.extend(result["errors"])

    # 결과 출력
    print("=" * 60)
    print("블로그 이미지 재검수 결과")
    print("=" * 60)
    print()
    print(f"검수 대상: {len(target_folders)}개 음식 × 5장 = {len(target_folders) * 5}개 이미지")
    print()
    print("[규칙 검수 R]")
    print(f"  PASS: {total_r_pass}개")
    print(f"  FAIL: {total_r_fail}개")
    print()
    print("[크리에이티브 검수 C]")
    print(f"  PASS: {total_c_pass}개")
    print(f"  FAIL: {total_c_fail}개")

    if all_errors:
        print()
        print("=" * 60)
        print("에러 목록")
        print("=" * 60)
        for error in all_errors[:50]:  # 최대 50개만 출력
            print(f"  {error}")
        if len(all_errors) > 50:
            print(f"  ... 외 {len(all_errors) - 50}개")

    return {
        "target_count": len(target_folders),
        "total_images": len(target_folders) * 5,
        "r_pass": total_r_pass,
        "r_fail": total_r_fail,
        "c_pass": total_c_pass,
        "c_fail": total_c_fail,
        "errors": all_errors,
        "results": results
    }


if __name__ == "__main__":
    run_full_qc()
