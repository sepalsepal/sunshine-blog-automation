#!/usr/bin/env python3
"""
caption_safety_validator.py - §22.11~13 캡션 안전도 분기 검증
v3.1: ENUM 단일 판정, 금지 키워드 차단, 이미지-캡션 일치 검증

사용법:
    python3 scripts/caption_safety_validator.py --check 127
    python3 scripts/caption_safety_validator.py --scan-all
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
LOGS_DIR = PROJECT_ROOT / "logs" / "validation"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]


# =============================================================================
# §22.11.1 ENUM 단일 판정 원칙
# =============================================================================
class Safety(Enum):
    SAFE = "SAFE"
    CAUTION = "CAUTION"
    FORBIDDEN = "FORBIDDEN"


def get_safety_from_source(food_id: int) -> Safety:
    """
    §22.11.1: 단일 source에서 1회만 판정
    food_data.json이 유일한 source
    """
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    data = food_data.get(str(food_id), {})
    safety_str = data.get("safety", "SAFE").upper()

    try:
        return Safety(safety_str)
    except ValueError:
        raise ValueError(f"§22.11.1 위반: 허용되지 않은 안전도 값 '{safety_str}'")


# =============================================================================
# §22.11.2 안전도별 캡션 구조
# =============================================================================
CAPTION_STRUCTURE = {
    "SAFE_CAUTION": {
        3: "영양 정보",
        4: "급여 방법",
        5: "급여량 표",
        6: "주의사항",
        7: "조리 방법",
    },
    "FORBIDDEN": {
        3: "위험 성분",
        4: "절대 급여 금지",
        5: "0g 강조",
        6: "응급 대처법",
        7: "수의사 상담",
    }
}


def get_expected_caption_structure(safety: Safety) -> Dict[int, str]:
    """안전도에 따른 예상 캡션 구조 반환"""
    if safety == Safety.FORBIDDEN:
        return CAPTION_STRUCTURE["FORBIDDEN"]
    return CAPTION_STRUCTURE["SAFE_CAUTION"]


# =============================================================================
# §22.12 금지 키워드 차단
# =============================================================================
FORBIDDEN_KEYWORDS = [
    "급여 방법",
    "조리 방법",
    "권장량",
    "좋아요",
    "맛있어요",
    "체중별 급여량",
    "소형견 급여량",
    "중형견 급여량",
    "대형견 급여량",
    "영양 가득",
    "건강에 좋",
    "드셔도 됩니다",
    "먹여도 됩니다",
    "영양 정보",  # FORBIDDEN은 "위험 성분" 사용
    "영양정보",
]

# 캡션 헤더 패턴 (FORBIDDEN에서 금지)
FORBIDDEN_HEADER_PATTERNS = [
    "[이미지 4번: 급여 방법]",
    "[이미지 6번: 조리 방법]",
    "[이미지 3번: 영양 정보]",
    "[이미지 3번: 영양정보]",
]

# FORBIDDEN 캡션 필수 헤더
FORBIDDEN_REQUIRED_HEADERS = {
    3: "[이미지 3번: 위험 성분]",
    4: "[이미지 4번: 절대 급여 금지]",
    5: "[이미지 5번: 급여량 표]",  # 0g 강조 내용
    6: "[이미지 6번: 응급 대처법]",
    7: "[이미지 7번: 수의사 상담]",
}


def check_forbidden_keywords(caption: str, safety: Safety) -> Tuple[bool, List[str]]:
    """
    §22.12: FORBIDDEN 캡션에서 금지 키워드 감지
    Returns: (통과여부, 감지된 키워드 목록)
    """
    if safety != Safety.FORBIDDEN:
        return True, []

    detected = []

    # 금지 키워드 체크
    for keyword in FORBIDDEN_KEYWORDS:
        if keyword in caption:
            detected.append(f"금지 키워드: '{keyword}'")

    # 금지 헤더 패턴 체크
    for pattern in FORBIDDEN_HEADER_PATTERNS:
        if pattern in caption:
            detected.append(f"금지 헤더: '{pattern}'")

    return len(detected) == 0, detected


def check_required_headers(caption: str, safety: Safety) -> Tuple[bool, List[str]]:
    """
    §22.11.2: FORBIDDEN 캡션 필수 헤더 확인
    Returns: (통과여부, 누락된 헤더 목록)
    """
    if safety != Safety.FORBIDDEN:
        return True, []

    missing = []
    for slide_num, header in FORBIDDEN_REQUIRED_HEADERS.items():
        # 헤더 또는 유사 패턴 확인
        header_pattern = header.replace("[이미지 ", "").replace("]", "")
        alt_pattern = f"{slide_num}번"

        # 필수 키워드 확인
        required_content = {
            3: ["위험", "독성"],
            4: ["금지", "절대"],
            5: ["0g", "금지"],
            6: ["응급", "병원", "대처"],
            7: ["수의사", "상담"],
        }

        keywords = required_content.get(slide_num, [])
        has_content = any(kw in caption for kw in keywords)

        if not has_content:
            missing.append(f"슬라이드 {slide_num}: {header} 관련 내용 필요 (키워드: {keywords})")

    return len(missing) == 0, missing


# =============================================================================
# §22.13 이미지-캡션 일치 검증
# =============================================================================
def generate_structure_id(food_id: int, safety: Safety, version: str = "v3.1") -> str:
    """
    §22.13.1 구조 ID 생성 규칙
    형식: {food_id}_{safety}_{template_version}_{timestamp}
    """
    timestamp = datetime.now().strftime("%Y%m%d")
    return f"{food_id}_{safety.value}_{version}_{timestamp}"


def validate_image_caption_match(
    food_id: int,
    caption: str,
    safety: Safety
) -> Dict:
    """
    §22.13: 이미지-캡션 일치 검증
    """
    results = {
        "food_id": food_id,
        "safety": safety.value,
        "structure_id": generate_structure_id(food_id, safety),
        "valid": True,
        "errors": [],
        "warnings": [],
    }

    # §22.12 금지 키워드 검증 (가장 중요)
    keyword_pass, detected = check_forbidden_keywords(caption, safety)
    if not keyword_pass:
        results["valid"] = False
        for item in detected:
            results["errors"].append(f"§22.12 위반: {item}")

    # §22.11.2 필수 헤더/내용 검증
    if safety == Safety.FORBIDDEN:
        header_pass, missing = check_required_headers(caption, safety)
        if not header_pass:
            for item in missing:
                results["warnings"].append(f"§22.11.2: {item}")

    return results


def save_validation_log(results: Dict, food_id: int):
    """
    §22.13.2 로그 저장
    위치: /logs/validation/{date}/{food_id}_validation.log
    """
    date_str = datetime.now().strftime("%Y%m%d")
    log_dir = LOGS_DIR / date_str
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / f"{food_id:03d}_caption_validation.log"

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"=== §22.11-13 Caption Validation Log ===\n")
        f.write(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n")
        f.write(f"Food ID: {results['food_id']}\n")
        f.write(f"Safety: {results['safety']}\n")
        f.write(f"Structure ID: {results['structure_id']}\n")
        f.write(f"\n")
        f.write(f"Valid: {'PASS' if results['valid'] else 'FAIL'}\n")
        f.write(f"\n")

        if results['errors']:
            f.write(f"[ERRORS]\n")
            for err in results['errors']:
                f.write(f"  - {err}\n")
            f.write(f"\n")

        if results['warnings']:
            f.write(f"[WARNINGS]\n")
            for warn in results['warnings']:
                f.write(f"  - {warn}\n")
            f.write(f"\n")

        f.write(f"=== End of Log ===\n")

    return log_path


# =============================================================================
# 콘텐츠 폴더 유틸리티
# =============================================================================
def find_content_folder(food_id: int) -> Optional[Path]:
    """번호로 콘텐츠 폴더 찾기"""
    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    num_str = f"{food_id:03d}"
    for item in CONTENTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith(num_str):
            return item
    return None


def load_caption(content_folder: Path, platform: str = "insta") -> Optional[str]:
    """캡션 파일 로드"""
    # 2026-02-13: 플랫 구조 반영 - 플랫폼 폴더 매핑
    platform_folder_map = {
        "insta": "01_Insta&Thread",
        "blog": "02_Blog"
    }
    platform_folder = platform_folder_map.get(platform, platform)

    # 다양한 캡션 파일 위치 확인
    possible_paths = [
        content_folder / f"caption_{platform}.txt",
        content_folder / platform_folder / "caption.txt",
        content_folder / "caption.txt",
    ]

    for path in possible_paths:
        if path.exists():
            return path.read_text(encoding="utf-8")

    return None


def load_all_captions(content_folder: Path) -> Dict[str, str]:
    """모든 캡션 파일 로드"""
    captions = {}

    # 플랫폼별 캡션
    for platform in ["insta", "blog"]:
        caption = load_caption(content_folder, platform)
        if caption:
            captions[platform] = caption

    return captions


# =============================================================================
# 메인 검증 함수
# =============================================================================
def validate_content(food_id: int, verbose: bool = True) -> Dict:
    """
    단일 콘텐츠 검증
    §22.11~13 전체 적용
    """
    results = {
        "food_id": food_id,
        "valid": False,
        "safety": None,
        "structure_id": None,
        "caption_found": False,
        "platforms_checked": [],
        "errors": [],
        "warnings": [],
    }

    # 1. 안전도 판정 (단일 source)
    try:
        safety = get_safety_from_source(food_id)
        results["safety"] = safety.value
    except ValueError as e:
        results["errors"].append(str(e))
        return results

    # 2. 콘텐츠 폴더 찾기
    folder = find_content_folder(food_id)
    if not folder:
        results["errors"].append(f"콘텐츠 폴더 없음: #{food_id:03d}")
        return results

    # 3. 모든 캡션 로드 및 검증
    captions = load_all_captions(folder)

    if not captions:
        results["warnings"].append("캡션 파일 없음 - 검증 스킵")
        results["structure_id"] = generate_structure_id(food_id, safety)
        return results

    results["caption_found"] = True
    results["structure_id"] = generate_structure_id(food_id, safety)
    all_valid = True

    # 4. 각 플랫폼별 §22.11~13 검증
    for platform, caption in captions.items():
        results["platforms_checked"].append(platform)
        validation = validate_image_caption_match(food_id, caption, safety)

        if validation["errors"]:
            all_valid = False
            for err in validation["errors"]:
                results["errors"].append(f"[{platform}] {err}")

        for warn in validation["warnings"]:
            results["warnings"].append(f"[{platform}] {warn}")

    results["valid"] = all_valid

    # 5. 로그 저장
    log_path = save_validation_log(results, food_id)

    if verbose:
        status = "PASS" if results["valid"] else "FAIL"
        platforms = ", ".join(results["platforms_checked"])
        print(f"   #{food_id:03d} [{safety.value}] ({platforms}): {status}")
        if results["errors"]:
            for err in results["errors"]:
                print(f"      ERROR: {err}")
        if results["warnings"]:
            for warn in results["warnings"]:
                print(f"      WARN: {warn}")
        print(f"      Log: {log_path}")

    return results


def scan_all(start: int = 1, end: int = 999, verbose: bool = True):
    """전체 콘텐츠 스캔"""
    print("=" * 60)
    print("§22.11~13 Caption Safety Validator")
    print("=" * 60)

    stats = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "no_caption": 0,
        "by_safety": {"SAFE": 0, "CAUTION": 0, "FORBIDDEN": 0}
    }

    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    for food_id in range(start, end + 1):
        if str(food_id) not in food_data:
            continue

        folder = find_content_folder(food_id)
        if not folder:
            continue

        stats["total"] += 1
        result = validate_content(food_id, verbose=verbose)

        if result["safety"]:
            stats["by_safety"][result["safety"]] += 1

        if not result["caption_found"]:
            stats["no_caption"] += 1
        elif result["valid"]:
            stats["passed"] += 1
        else:
            stats["failed"] += 1

    print("\n" + "=" * 60)
    print("검증 결과 요약")
    print("=" * 60)
    print(f"총 검사: {stats['total']}개")
    print(f"  PASS: {stats['passed']}개")
    print(f"  FAIL: {stats['failed']}개")
    print(f"  캡션 없음: {stats['no_caption']}개")
    print(f"\n안전도별 분포:")
    print(f"  SAFE: {stats['by_safety']['SAFE']}개")
    print(f"  CAUTION: {stats['by_safety']['CAUTION']}개")
    print(f"  FORBIDDEN: {stats['by_safety']['FORBIDDEN']}개")
    print("=" * 60)

    return stats


def main():
    parser = argparse.ArgumentParser(description="§22.11~13 캡션 안전도 분기 검증")
    parser.add_argument("--check", type=int, help="특정 콘텐츠 검증")
    parser.add_argument("--scan-all", action="store_true", help="전체 스캔")
    parser.add_argument("--start", type=int, default=1, help="시작 번호")
    parser.add_argument("--end", type=int, default=999, help="종료 번호")
    parser.add_argument("-q", "--quiet", action="store_true", help="간략 출력")
    args = parser.parse_args()

    if args.check:
        validate_content(args.check, verbose=not args.quiet)
    elif args.scan_all:
        scan_all(args.start, args.end, verbose=not args.quiet)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
