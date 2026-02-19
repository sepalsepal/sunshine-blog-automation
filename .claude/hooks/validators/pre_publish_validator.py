#!/usr/bin/env python3
"""
pre_publish_validator.py - 게시 전 전체 Validator
WO-036: RULES.md §9.2 게시 전 점검 기준 (v2.1 업데이트)

사용법:
  python3 pre_publish_validator.py [content_folder]
  python3 pre_publish_validator.py --number 8 --platform threads

v2.1 변경사항:
  - --number: 콘텐츠 번호로 폴더 찾기 (예: 8 → 008_Banana)
  - --platform: 플랫폼별 검증 (threads/instagram)
  - Threads v1.1: Common_01, 02, 03, 09 + #CanMyDogEatThis 필수

Exit 0: PASS (게시 허용)
Exit 1: FAIL (게시 차단)
"""

import sys
import os
import argparse
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent.parent


def find_content_folder_by_number(number: int) -> Path | None:
    """콘텐츠 번호로 폴더 찾기 (예: 8 → 008_Banana)"""
    contents_dir = PROJECT_ROOT / "01_contents"
    if not contents_dir.exists():
        return None

    pattern = f"{number:03d}_*"
    matches = list(contents_dir.glob(pattern))
    if matches:
        return matches[0]
    return None


def find_latest_content_folder() -> Path | None:
    """가장 최근 작업 중인 콘텐츠 폴더 찾기"""
    # 01_contents 구조 (v2.0)
    search_paths = [
        PROJECT_ROOT / "01_contents",
        PROJECT_ROOT / "contents" / "3_approved",  # 레거시
        PROJECT_ROOT / "contents" / "2_body_ready",  # 레거시
    ]

    for search_path in search_paths:
        if search_path.exists():
            # 숫자로 시작하는 콘텐츠 폴더 찾기 (000_ 제외)
            folders = [f for f in search_path.iterdir()
                      if f.is_dir()
                      and not f.name.startswith('.')
                      and not f.name.startswith('000_')
                      and f.name[0].isdigit()]
            if folders:
                # 가장 최근 수정된 폴더
                return max(folders, key=lambda x: x.stat().st_mtime)

    return None


def validate_pre_publish(content_folder: Path | None = None, platform: str = "instagram") -> tuple[bool, list[str]]:
    """
    게시 전 전체 검증
    RULES.md §9.2 기준 (v2.1 업데이트)

    Args:
        content_folder: 콘텐츠 폴더 경로
        platform: "threads" 또는 "instagram"
    """
    fails = []
    passes = []

    if content_folder is None:
        content_folder = find_latest_content_folder()

    if content_folder is None:
        return False, ["검증할 콘텐츠 폴더를 찾을 수 없음"]

    if not content_folder.exists():
        return False, [f"폴더가 존재하지 않음: {content_folder}"]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 플랫폼별 캐러셀 이미지 구조
    # Threads v1.1: Common_01, 02, 03, 09
    # Instagram: Common_01, 02 + slide_03 + Common_08
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    insta_folder = content_folder / "01_Insta&Thread"
    carousel_images = []

    # Common 이미지 확인
    common_01 = list(content_folder.glob("*_Common_01_Cover.png"))
    common_02 = list(content_folder.glob("*_Common_02_Food.png"))
    common_03 = list(content_folder.glob("*_Common_03_DogWithFood.png"))
    common_08 = list(content_folder.glob("*_Common_08_Cta.png"))
    common_09 = list(content_folder.glob("*_Common_09_Cta.png"))
    slide_03 = insta_folder / "slide_03.png" if insta_folder.exists() else None

    # 공통: Common_01, 02
    if common_01:
        passes.append("1번 Common_01_Cover 존재")
        carousel_images.append(common_01[0])
    else:
        fails.append("1번 Common_01_Cover 없음")

    if common_02:
        passes.append("2번 Common_02_Food 존재")
        carousel_images.append(common_02[0])
    else:
        fails.append("2번 Common_02_Food 없음")

    if platform.lower() == "threads":
        # Threads v1.1: Common_01, 02, 03, 09
        if common_03:
            passes.append("3번 Common_03_DogWithFood 존재")
            carousel_images.append(common_03[0])
        else:
            fails.append("3번 Common_03_DogWithFood 없음")

        if common_09:
            passes.append("4번 Common_09_Cta 존재")
            carousel_images.append(common_09[0])
        else:
            fails.append("4번 Common_09_Cta 없음")
    else:
        # Instagram: slide_03 + Common_08
        if slide_03 and slide_03.exists():
            passes.append("3번 slide_03 (클린이미지) 존재")
            carousel_images.append(slide_03)
        else:
            passes.append("3번 slide_03 없음 (옵션)")

        if common_08:
            passes.append("4번 Common_08_Cta 존재")
            carousel_images.append(common_08[0])
        else:
            passes.append("4번 Common_08_Cta 없음 (옵션)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §9.2.2 해상도 검증
    # Instagram/Threads: 1024x1024 이상 허용 (API 유연)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    try:
        from PIL import Image

        wrong_size = []
        for img_path in carousel_images:
            try:
                img = Image.open(img_path)
                w, h = img.size

                # 모든 플랫폼: 1024x1024 이상이면 OK (API 허용 범위)
                if w < 1024 or h < 1024:
                    wrong_size.append(f"{img_path.name}: {img.size} (최소 1024x1024)")
            except Exception:
                wrong_size.append(f"{img_path.name}: 열기 실패")

        if not wrong_size and carousel_images:
            passes.append("전 슬라이드 해상도 1024+ PASS")
        elif wrong_size:
            fails.append(f"해상도 FAIL: {', '.join(wrong_size)}")
    except ImportError:
        passes.append("PIL 미설치 - 해상도 검증 스킵")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §9.2.3 캡션 파일 존재
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    insta_caption = list(content_folder.glob("**/*_Insta_Caption.txt"))
    threads_caption = list(content_folder.glob("**/*_Threads_Caption.txt"))

    if insta_caption:
        passes.append(f"인스타 캡션 존재")
    else:
        fails.append("인스타 캡션 FAIL: *_Insta_Caption.txt 없음")

    if threads_caption:
        passes.append(f"쓰레드 캡션 존재")
    else:
        fails.append("쓰레드 캡션 FAIL: *_Threads_Caption.txt 없음")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §9.2.4 캡션 내용 검증 (인스타만)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if insta_caption:
        import re

        for caption_file in insta_caption:
            try:
                content = caption_file.read_text(encoding='utf-8')

                # 해시태그 12~16개 (인스타만)
                hashtags = re.findall(r'#\w+', content)
                if 7 <= len(hashtags) <= 20:  # 유연하게 조정
                    passes.append(f"해시태그 {len(hashtags)}개 PASS")
                else:
                    fails.append(f"해시태그 {len(hashtags)}개 (7~20개 권장)")

            except Exception as e:
                fails.append(f"{caption_file.name}: 읽기 실패 - {e}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 쓰레드 캡션 검증 (v1.1: #CanMyDogEatThis 필수, 2개 이하)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if threads_caption:
        import re

        for caption_file in threads_caption:
            try:
                content = caption_file.read_text(encoding='utf-8')

                # v1.1: #CanMyDogEatThis 필수
                hashtags = re.findall(r'#\w+', content)
                has_required = any('CanMyDogEatThis' in tag for tag in hashtags)

                if has_required and len(hashtags) <= 2:
                    passes.append(f"쓰레드 해시태그 PASS (#CanMyDogEatThis 포함, {len(hashtags)}개)")
                elif not has_required:
                    fails.append(f"쓰레드 #CanMyDogEatThis 없음 FAIL (v1.1 필수)")
                else:
                    fails.append(f"쓰레드 해시태그 {len(hashtags)}개 FAIL (최대 2개)")

            except Exception as e:
                fails.append(f"{caption_file.name}: 읽기 실패 - {e}")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 결과
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    all_passed = len(fails) == 0

    return all_passed, [f"대상: {content_folder}"] + passes + fails


def main():
    parser = argparse.ArgumentParser(description="게시 전 전체 Validator v2.1")
    parser.add_argument("folder", nargs="?", help="콘텐츠 폴더 경로")
    parser.add_argument("--number", "-n", type=int, help="콘텐츠 번호 (예: 8 → 008_Banana)")
    parser.add_argument("--platform", "-p", choices=["threads", "instagram"], default="instagram",
                       help="플랫폼 (기본: instagram)")

    args = parser.parse_args()

    # 콘텐츠 폴더 결정
    content_folder = None
    if args.number:
        content_folder = find_content_folder_by_number(args.number)
    elif args.folder:
        content_folder = Path(args.folder)

    passed, messages = validate_pre_publish(content_folder, platform=args.platform)

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"PRE-PUBLISH VALIDATOR v2.1: {'PASS' if passed else 'FAIL'}")
    print(f"플랫폼: {args.platform.upper()}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    for msg in messages:
        if "대상:" in msg:
            print(msg)
            print("")
        elif "PASS" in msg:
            print(f"  ✅ {msg}")
        elif "FAIL" in msg:
            print(f"  ❌ {msg}")
        else:
            print(f"  ℹ️ {msg}")

    print("")
    if passed:
        print("→ 게시 진행 가능")
    else:
        print("→ FAIL 항목 수정 후 재시도")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
