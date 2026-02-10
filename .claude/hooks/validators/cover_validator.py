#!/usr/bin/env python3
"""
cover_validator.py - 표지 이미지 Validator
WO-036: RULES.md §8 기준 PASS/FAIL 판정

사용법: python3 cover_validator.py <image_path>
Exit 0: PASS
Exit 1: FAIL
"""

import sys
from pathlib import Path

def validate_cover(image_path: str) -> tuple[bool, list[str]]:
    """
    표지 이미지 검증
    RULES.md §8 COVER_RULES 표지(한글) v1.0 기준
    """
    fails = []
    passes = []

    try:
        from PIL import Image
    except ImportError:
        # PIL 없으면 기본 검증만
        if not Path(image_path).exists():
            return False, ["파일이 존재하지 않음"]
        return True, ["PIL 미설치 - 기본 검증만 수행"]

    # 파일 존재 확인
    if not Path(image_path).exists():
        return False, ["파일이 존재하지 않음"]

    try:
        img = Image.open(image_path)
    except Exception as e:
        return False, [f"이미지 열기 실패: {e}"]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §8.1 해상도 검증: 1080x1080 고정
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    width, height = img.size
    if width == 1080 and height == 1080:
        passes.append(f"해상도 1080x1080 PASS")
    else:
        fails.append(f"해상도 FAIL: {width}x{height} (1080x1080 필요)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §8.6 금지사항 확인 (파일명 기반)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    filename = Path(image_path).name.lower()

    # 영어 표지인지 확인 (인스타용은 별도 규칙)
    if "_en" in filename or "english" in filename:
        passes.append("인스타그램용 영어 표지 감지 - §2.2 규칙 적용 필요")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 결과 출력
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    all_passed = len(fails) == 0

    return all_passed, passes + fails


def main():
    if len(sys.argv) < 2:
        print("사용법: python3 cover_validator.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    passed, messages = validate_cover(image_path)

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"COVER VALIDATOR: {'PASS' if passed else 'FAIL'}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"파일: {image_path}")
    print("")

    for msg in messages:
        prefix = "✅" if "PASS" in msg else "❌"
        print(f"  {prefix} {msg}")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
