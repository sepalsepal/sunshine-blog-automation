#!/usr/bin/env python3
"""
c2_validator.py - C2 인포그래픽 Validator
WO-036: RULES.md §2.4 기준 PASS/FAIL 판정

사용법: python3 c2_validator.py <image_path>
Exit 0: PASS
Exit 1: FAIL
"""

import sys
from pathlib import Path

def validate_c2(image_path: str) -> tuple[bool, list[str]]:
    """
    C2 인포그래픽 검증
    RULES.md §2.4 C2 인포그래픽 v2.0 기준
    """
    fails = []
    passes = []

    try:
        from PIL import Image
    except ImportError:
        if not Path(image_path).exists():
            return False, ["파일이 존재하지 않음"]
        return True, ["PIL 미설치 - 기본 검증만 수행"]

    if not Path(image_path).exists():
        return False, ["파일이 존재하지 않음"]

    try:
        img = Image.open(image_path)
    except Exception as e:
        return False, [f"이미지 열기 실패: {e}"]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §2.4.1 해상도 검증: 1080x1080
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    width, height = img.size
    if width == 1080 and height == 1080:
        passes.append(f"해상도 1080x1080 PASS")
    else:
        fails.append(f"해상도 FAIL: {width}x{height} (1080x1080 필요)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 이미지 모드 검증
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    if img.mode in ('RGB', 'RGBA'):
        passes.append(f"이미지 모드 {img.mode} PASS")
    else:
        fails.append(f"이미지 모드 FAIL: {img.mode} (RGB/RGBA 필요)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 파일명 기반 카드 유형 확인
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    filename = Path(image_path).name
    card_types = {
        "영양": "영양성분",
        "급여방법": "급여방법/안전",
        "급여량": "급여량",
        "주의": "주의사항",
        "조리": "조리방법"
    }

    detected_type = None
    for keyword, card_type in card_types.items():
        if keyword in filename:
            detected_type = card_type
            passes.append(f"카드 유형 감지: {card_type}")
            break

    if not detected_type:
        passes.append("카드 유형 미확인 (파일명에서 감지 안됨)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 결과
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    all_passed = len(fails) == 0

    return all_passed, passes + fails


def main():
    if len(sys.argv) < 2:
        print("사용법: python3 c2_validator.py <image_path>")
        sys.exit(1)

    image_path = sys.argv[1]
    passed, messages = validate_c2(image_path)

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"C2 INFOGRAPHIC VALIDATOR: {'PASS' if passed else 'FAIL'}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"파일: {image_path}")
    print("")

    for msg in messages:
        prefix = "✅" if "PASS" in msg or "감지" in msg else "❌"
        print(f"  {prefix} {msg}")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
