#!/usr/bin/env python3
"""
fix_forbidden_captions.py - FORBIDDEN 캡션 자동 수정
WO-PHASE2-SUPPLEMENT B-1

대상: 36개 FORBIDDEN 콘텐츠
수정 규칙:
- 헤더 교체 (영양 정보→위험 성분 등)
- 금지 키워드 교체/제거

사용법:
    python scripts/fix_forbidden_captions.py --dry-run
    python scripts/fix_forbidden_captions.py --execute
    python scripts/fix_forbidden_captions.py --target 127 --execute
"""

import os
import sys
import json
import argparse
import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
LOGS_DIR = PROJECT_ROOT / "logs" / "fix_captions"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]


# =============================================================================
# 수정 규칙
# =============================================================================

# 헤더 교체 규칙
HEADER_REPLACEMENTS = {
    "[이미지 3번: 영양 정보]": "[이미지 3번: 위험 성분]",
    "[이미지 3번: 영양정보]": "[이미지 3번: 위험 성분]",
    "[이미지 4번: 급여 방법]": "[이미지 4번: 절대 급여 금지]",
    "[이미지 5번: 급여량 표]": "[이미지 5번: 급여량 (0g)]",
    "[이미지 6번: 조리 방법]": "[이미지 6번: 응급 대처법]",
    "[이미지 6번: 주의사항]": "[이미지 6번: 응급 대처법]",
    "[이미지 7번: 주의사항]": "[이미지 7번: 수의사 상담]",
    "[이미지 7번: 조리 방법]": "[이미지 7번: 수의사 상담]",
}

# 키워드 교체 규칙
KEYWORD_REPLACEMENTS = {
    "건강에 좋은 음식인데": "사람은 먹어도 되는 음식인데",
    "건강에 좋은": "사람에게는 좋은",
    "건강에좋은": "사람에게는 좋은",
    "영양이 풍부한": "성분이 포함된",
    "영양이 풍부": "성분이 포함",
}

# 완전 제거 키워드 (해당 줄 삭제)
KEYWORDS_TO_REMOVE_LINE = [
    "좋아요!",
    "맛있어요!",
]

# 패턴 제거 (정규식)
PATTERNS_TO_REMOVE = [
    r"좋아요[!\.]*",
    r"맛있어요[!\.]*",
]


# =============================================================================
# 유틸리티
# =============================================================================

def find_content_folder(food_id: int) -> Optional[Path]:
    """콘텐츠 폴더 찾기"""
    num_str = f"{food_id:03d}"
    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    for item in CONTENTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith(num_str):
            return item
    return None


def find_caption_files(content_folder: Path) -> List[Path]:
    """캡션 파일 찾기"""
    caption_files = []

    # 플랫폼별 캡션
    for platform in ["01_Insta&Thread", "02_Blog"]:
        platform_dir = content_folder / platform
        if platform_dir.exists():
            caption_path = platform_dir / "caption.txt"
            if caption_path.exists():
                caption_files.append(caption_path)

    # 루트 캡션
    root_caption = content_folder / "caption.txt"
    if root_caption.exists():
        caption_files.append(root_caption)

    return caption_files


def get_forbidden_ids() -> List[int]:
    """FORBIDDEN 음식 ID 목록 조회"""
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    forbidden_ids = []
    for food_id, data in food_data.items():
        if data.get("safety", "").upper() == "FORBIDDEN":
            forbidden_ids.append(int(food_id))

    return sorted(forbidden_ids)


# =============================================================================
# 캡션 수정
# =============================================================================

def fix_caption(content: str) -> Tuple[str, List[str]]:
    """
    캡션 수정

    Args:
        content: 원본 캡션

    Returns:
        (수정된 캡션, 수정 내역)
    """
    changes = []
    result = content

    # 1. 헤더 교체
    for old, new in HEADER_REPLACEMENTS.items():
        if old in result:
            result = result.replace(old, new)
            changes.append(f"헤더 교체: '{old}' → '{new}'")

    # 2. 키워드 교체
    for old, new in KEYWORD_REPLACEMENTS.items():
        if old in result:
            result = result.replace(old, new)
            changes.append(f"키워드 교체: '{old}' → '{new}'")

    # 3. 패턴 제거
    for pattern in PATTERNS_TO_REMOVE:
        matches = re.findall(pattern, result)
        if matches:
            result = re.sub(pattern, "", result)
            changes.append(f"패턴 제거: {matches}")

    # 4. 빈 줄 정리 (연속 3줄 이상 → 2줄로)
    result = re.sub(r'\n{3,}', '\n\n', result)

    return result, changes


def process_caption_file(
    caption_path: Path,
    dry_run: bool = True,
) -> Dict:
    """
    단일 캡션 파일 처리

    Returns:
        {"path": str, "changes": list, "success": bool}
    """
    result = {
        "path": str(caption_path),
        "changes": [],
        "success": False,
        "error": None,
    }

    try:
        # 원본 읽기
        original = caption_path.read_text(encoding="utf-8")

        # 수정
        fixed, changes = fix_caption(original)

        if not changes:
            result["changes"] = ["변경 없음"]
            result["success"] = True
            return result

        result["changes"] = changes

        if dry_run:
            result["success"] = True
            result["dry_run"] = True
        else:
            # 백업 생성
            backup_path = caption_path.with_suffix(".txt.bak")
            backup_path.write_text(original, encoding="utf-8")

            # 수정 저장
            caption_path.write_text(fixed, encoding="utf-8")
            result["success"] = True
            result["backup"] = str(backup_path)

    except Exception as e:
        result["error"] = str(e)

    return result


def process_food_id(
    food_id: int,
    dry_run: bool = True,
) -> Dict:
    """
    단일 음식 ID 처리

    Returns:
        {"food_id": int, "files": list, "total_changes": int}
    """
    result = {
        "food_id": food_id,
        "folder": None,
        "files": [],
        "total_changes": 0,
        "success": True,
    }

    # 폴더 찾기
    folder = find_content_folder(food_id)
    if not folder:
        result["success"] = False
        result["error"] = "폴더 없음"
        return result

    result["folder"] = str(folder)

    # 캡션 파일 찾기
    caption_files = find_caption_files(folder)
    if not caption_files:
        result["success"] = True
        result["files"] = [{"path": "없음", "changes": ["캡션 파일 없음"]}]
        return result

    # 각 캡션 파일 처리
    for caption_path in caption_files:
        file_result = process_caption_file(caption_path, dry_run)
        result["files"].append(file_result)

        if file_result["changes"] and file_result["changes"][0] != "변경 없음":
            result["total_changes"] += len(file_result["changes"])

        if not file_result["success"]:
            result["success"] = False

    return result


# =============================================================================
# 메인 실행
# =============================================================================

def run_fix(
    target: Optional[int] = None,
    dry_run: bool = True,
    verbose: bool = True,
) -> Dict:
    """
    FORBIDDEN 캡션 수정 실행

    Args:
        target: 특정 food_id (None이면 전체 FORBIDDEN)
        dry_run: True면 미리보기만
        verbose: 상세 출력

    Returns:
        {"total": int, "fixed": int, "failed": int, "results": list}
    """
    print("=" * 60)
    print(f"FORBIDDEN 캡션 자동 수정 {'(DRY-RUN)' if dry_run else '(EXECUTE)'}")
    print("=" * 60)

    # 대상 결정
    if target:
        food_ids = [target]
    else:
        food_ids = get_forbidden_ids()

    print(f"\n대상: {len(food_ids)}개 FORBIDDEN 콘텐츠")

    if not dry_run:
        print("\n⚠️ 실제 파일이 수정됩니다!")
        print("백업 파일이 .txt.bak으로 생성됩니다.\n")

    stats = {
        "total": len(food_ids),
        "fixed": 0,
        "no_change": 0,
        "failed": 0,
        "results": [],
    }

    for food_id in food_ids:
        result = process_food_id(food_id, dry_run)
        stats["results"].append(result)

        if result["success"]:
            if result["total_changes"] > 0:
                stats["fixed"] += 1
            else:
                stats["no_change"] += 1
        else:
            stats["failed"] += 1

        if verbose:
            status = "FIXED" if result["total_changes"] > 0 else "NO_CHANGE"
            if not result["success"]:
                status = "FAILED"

            print(f"  #{food_id:03d}: {status} ({result['total_changes']} changes)")

            if result["total_changes"] > 0:
                for file_result in result["files"]:
                    rel_path = Path(file_result["path"]).name if file_result["path"] != "없음" else "없음"
                    for change in file_result["changes"][:3]:
                        print(f"      - {change}")

    # 로그 저장
    log_path = save_fix_log(stats, dry_run)

    # 요약
    print("\n" + "=" * 60)
    print("결과 요약")
    print("=" * 60)
    print(f"총 대상: {stats['total']}개")
    print(f"수정됨: {stats['fixed']}개")
    print(f"변경 없음: {stats['no_change']}개")
    print(f"실패: {stats['failed']}개")
    print(f"\n로그: {log_path}")

    if dry_run and stats["fixed"] > 0:
        print("\n💡 실제 적용하려면: --execute 옵션 사용")

    return stats


def save_fix_log(stats: Dict, dry_run: bool) -> Path:
    """수정 로그 저장"""
    date_str = datetime.now().strftime("%Y%m%d")
    time_str = datetime.now().strftime("%H%M%S")
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    mode = "dryrun" if dry_run else "execute"
    log_path = LOGS_DIR / f"{date_str}_{time_str}_{mode}.log"

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"{'='*60}\n")
        f.write(f"FORBIDDEN Caption Fix Log\n")
        f.write(f"{'='*60}\n\n")

        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}\n")
        f.write(f"Total: {stats['total']}\n")
        f.write(f"Fixed: {stats['fixed']}\n")
        f.write(f"No Change: {stats['no_change']}\n")
        f.write(f"Failed: {stats['failed']}\n\n")

        # 수정된 항목 상세
        f.write("[FIXED ITEMS]\n")
        for result in stats["results"]:
            if result["total_changes"] > 0:
                f.write(f"\n#{result['food_id']:03d}:\n")
                for file_result in result["files"]:
                    f.write(f"  {file_result['path']}:\n")
                    for change in file_result["changes"]:
                        f.write(f"    - {change}\n")

        f.write("\n" + "=" * 60 + "\n")

    return log_path


def main():
    parser = argparse.ArgumentParser(
        description="FORBIDDEN 캡션 자동 수정"
    )
    parser.add_argument(
        "--target",
        type=int,
        help="특정 food_id만 수정 (미지정 시 전체 FORBIDDEN)"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="미리보기 모드 (파일 수정 안 함)"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="실제 수정 실행"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="간략 출력"
    )

    args = parser.parse_args()

    # dry-run이 기본, --execute 시에만 실제 실행
    dry_run = not args.execute

    run_fix(
        target=args.target,
        dry_run=dry_run,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
