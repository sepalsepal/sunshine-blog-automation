#!/usr/bin/env python3
"""
batch_runner.py - 플랫폼별 배치 처리 실행기
WO-038 v2: 레드2 R4 리스크 차단 + 플랫폼별 콘텐츠 차이 반영

사용법: python3 batch_runner.py [플랫폼] [작업] [대상]
예시: python3 batch_runner.py insta cover 060-070
"""

import sys
import os
import re
from pathlib import Path
from typing import List, Tuple, Optional
from datetime import datetime

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
LOG_DIR = PROJECT_ROOT / "config" / "logs" / "batch"

# 플랫폼 설정
PLATFORMS = ["insta", "threads", "blog"]

# 작업별 플랫폼 지원 여부
PLATFORM_ACTIONS = {
    "insta": ["cover", "body", "caption", "pipeline", "publish", "validate"],
    "threads": ["caption", "publish", "validate"],  # cover, body, pipeline 불가
    "blog": ["cover", "body", "caption", "pipeline", "publish", "validate"],
}

# 2026-02-13: 플랫 구조 - FOLDER_MAP 제거
# 폴더 매핑
# FOLDER_MAP = {
#     "1_cover_only": "1_cover_only",
#     "2_body_ready": "2_body_ready",
#     "3_approved": "3_approved",
#     "4_posted": "4_posted",
#     "cover_only": "1_cover_only",
#     "body_ready": "2_body_ready",
#     "approved": "3_approved",
#     "posted": "4_posted",
# }
FOLDER_MAP = {}


def print_banner(text: str):
    """배너 출력"""
    print("━" * 50)
    print(text)
    print("━" * 50)


def print_error(msg: str):
    """에러 메시지 출력"""
    print(f"\n❌ 에러: {msg}\n")


def print_usage():
    """사용법 출력"""
    print("""
사용법: /batch [플랫폼] [작업] [대상]

플랫폼:
  insta     인스타그램
  threads   쓰레드 (이미지는 인스타 공유)
  blog      네이버 블로그

작업:
  cover     표지 생성
  body      본문 생성
  caption   캡션 작성
  pipeline  전체 (표지+본문+캡션)
  publish   게시
  validate  검증

대상:
  001-010     범위 지정
  001,005,009 목록 지정
  3_approved  폴더 지정
  all         전체

예시:
  /batch insta cover 060-070
  /batch threads caption 3_approved
  /batch blog pipeline all
""")


def parse_target(target: str) -> List[str]:
    """
    대상 문자열을 콘텐츠 번호 목록으로 파싱

    지원 형식:
    - 범위: 001-010
    - 목록: 001,005,009
    - 폴더: 3_approved
    - 전체: all
    """
    contents = []

    # 폴더 지정
    if target in FOLDER_MAP or target == "all":
        if target == "all":
            search_folders = ["1_cover_only", "2_body_ready", "3_approved"]
        else:
            search_folders = [FOLDER_MAP.get(target, target)]

        for folder_name in search_folders:
            folder_path = CONTENTS_DIR / folder_name
            if folder_path.exists():
                for item in folder_path.iterdir():
                    if item.is_dir() and not item.name.startswith('.'):
                        # 폴더명에서 번호 추출 (예: 060_fried_chicken_후라이드치킨)
                        match = re.match(r'^(\d{3})', item.name)
                        if match:
                            contents.append(match.group(1))
        return sorted(set(contents))

    # 범위 지정 (001-010)
    if '-' in target and ',' not in target:
        parts = target.split('-')
        if len(parts) == 2:
            try:
                start = int(parts[0])
                end = int(parts[1])
                return [f"{i:03d}" for i in range(start, end + 1)]
            except ValueError:
                pass

    # 목록 지정 (001,005,009)
    if ',' in target:
        items = [item.strip() for item in target.split(',')]
        return [f"{int(item):03d}" for item in items if item.isdigit()]

    # 단일 지정 (060)
    if target.isdigit():
        return [f"{int(target):03d}"]

    return []


def find_content_folder(content_num: str) -> Optional[Path]:
    """콘텐츠 번호로 폴더 찾기"""
    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    if CONTENTS_DIR.exists():
        for item in CONTENTS_DIR.iterdir():
            if item.is_dir() and item.name.startswith(content_num):
                return item
    return None


def validate_platform_action(platform: str, action: str) -> Tuple[bool, str]:
    """플랫폼-작업 조합 유효성 검사"""
    if platform not in PLATFORMS:
        return False, f"지원하지 않는 플랫폼: {platform}"

    allowed_actions = PLATFORM_ACTIONS.get(platform, [])
    if action not in allowed_actions:
        if platform == "threads" and action in ["cover", "body", "pipeline"]:
            return False, f"쓰레드는 인스타 이미지 공유. /batch insta {action} 사용"
        return False, f"'{platform}'에서 '{action}' 작업 불가"

    return True, ""


def execute_action(platform: str, action: str, content_num: str) -> Tuple[bool, str]:
    """단일 콘텐츠에 대해 작업 실행"""
    folder = find_content_folder(content_num)
    if not folder:
        return False, f"콘텐츠 폴더 없음: {content_num}"

    # 실제 작업 실행 (시뮬레이션)
    # 실제 구현에서는 각 플랫폼/작업별 스크립트 호출

    action_map = {
        "cover": f"표지 생성: {folder.name}",
        "body": f"본문 생성: {folder.name}",
        "caption": f"캡션 작성: {folder.name}",
        "pipeline": f"파이프라인 실행: {folder.name}",
        "publish": f"게시 준비: {folder.name}",
        "validate": f"검증 실행: {folder.name}",
    }

    print(f"  [{platform}] {action_map.get(action, action)}")

    # Validator 호출 (실제 구현)
    if action == "validate":
        validator_path = PROJECT_ROOT / ".claude" / "hooks" / "validators" / "pre_publish_validator.py"
        if validator_path.exists():
            import subprocess
            result = subprocess.run(
                ["python3", str(validator_path), str(folder)],
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                return False, "Validator FAIL"

    return True, "성공"


def run_batch(platform: str, action: str, target: str):
    """배치 작업 실행"""

    # 1. 플랫폼-작업 검증
    valid, error_msg = validate_platform_action(platform, action)
    if not valid:
        print_error(error_msg)
        return

    # 2. 대상 파싱
    contents = parse_target(target)
    if not contents:
        print_error(f"해당 콘텐츠를 찾을 수 없음: {target}")
        return

    # 3. 대량 작업 확인 (10개 초과)
    if len(contents) > 10:
        print(f"\n⚠️  {len(contents)}개 콘텐츠를 처리합니다.")
        print(f"   대상: {contents[0]} ~ {contents[-1]}")
        confirm = input("   계속하시겠습니까? (y/n): ")
        if confirm.lower() != 'y':
            print("   취소되었습니다.")
            return

    # 4. 배너 출력
    print_banner(f"📦 /batch {platform} {action} {target}")
    print(f"플랫폼: {platform}")
    print(f"작업: {action}")
    print(f"대상: {len(contents)}개")
    print("")

    # 5. 순차 실행
    results = {"success": [], "fail": [], "skip": []}

    for content_num in contents:
        success, msg = execute_action(platform, action, content_num)
        if success:
            results["success"].append(content_num)
        else:
            results["fail"].append((content_num, msg))
            print(f"    ❌ {content_num}: {msg}")

    # 6. 요약 보고
    print("")
    print_banner("📊 /batch 완료 보고")
    print(f"플랫폼: {platform}")
    print(f"작업: {action}")
    print(f"대상: {target}")
    print("")
    print(f"✅ 성공: {len(results['success'])}개")
    print(f"❌ 실패: {len(results['fail'])}개")

    if results["fail"]:
        print("")
        print("실패 목록:")
        for num, reason in results["fail"]:
            print(f"  - {num}: {reason}")

    print("━" * 50)

    # 7. 로그 저장
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    log_file = LOG_DIR / f"batch_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
    with open(log_file, 'w', encoding='utf-8') as f:
        f.write(f"Platform: {platform}\n")
        f.write(f"Action: {action}\n")
        f.write(f"Target: {target}\n")
        f.write(f"Success: {results['success']}\n")
        f.write(f"Fail: {results['fail']}\n")


def main():
    if len(sys.argv) < 4:
        print_usage()
        sys.exit(1)

    platform = sys.argv[1].lower()
    action = sys.argv[2].lower()
    target = sys.argv[3]

    run_batch(platform, action, target)


if __name__ == "__main__":
    main()
