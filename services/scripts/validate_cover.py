#!/usr/bin/env python3
"""
표지 규칙 검증 스크립트 (2026-02-09 PD 지시)

규칙 미준수 표지는 즉시 삭제됨.

사용법:
    python validate_cover.py <image_path> [cover_type]
    python validate_cover.py cover.png korean
    python validate_cover.py cover.png english
"""

from PIL import Image
from pathlib import Path
import sys
import os
from datetime import datetime


# 규칙 정의 (2026-02-09 PD 확정)
RULES = {
    "korean": {
        "name": "표지(한글) - 블로그용",
        "target_y": 80,
        "tolerance": 10,
        "font_size": 120,
        "allowed_fonts": ["NotoSansCJK-Black"],
    },
    "english": {
        "name": "표지(영어) - 인스타그램용",
        "target_y": 194,
        "tolerance": 10,
        "font_size": 114,
        "allowed_fonts": ["NotoSansCJK-Black", "Arial Black"],
    },
}


def find_text_y(img_path: str) -> int | None:
    """이미지에서 텍스트 시작 Y 위치 찾기"""
    img = Image.open(img_path).convert("RGBA")
    pixels = img.load()

    for y in range(300):
        white_count = 0
        for x in range(img.width):
            r, g, b, a = pixels[x, y]
            if r > 240 and g > 240 and b > 240 and a > 200:
                white_count += 1
        if white_count > 100:
            return y
    return None


def validate_cover(image_path: str, cover_type: str = "korean") -> tuple[bool, str]:
    """
    표지 규칙 검증

    Args:
        image_path: 검증할 이미지 경로
        cover_type: "korean" (블로그) / "english" (인스타그램)

    Returns:
        (통과 여부, 상세 메시지)
    """
    if cover_type not in RULES:
        return False, f"알 수 없는 cover_type: {cover_type}"

    rule = RULES[cover_type]

    # 파일 존재 확인
    if not Path(image_path).exists():
        return False, f"파일 없음: {image_path}"

    # 텍스트 Y 위치 측정
    text_y = find_text_y(image_path)

    if text_y is None:
        return False, "텍스트 감지 실패 (흰색 텍스트 없음)"

    # Y 위치 검증
    target_y = rule["target_y"]
    tolerance = rule["tolerance"]
    diff = abs(text_y - target_y)

    if diff > tolerance:
        return False, f"Y 위치 위반: {text_y}px (허용: {target_y}±{tolerance}px, 차이: {diff}px)"

    return True, f"PASS - Y={text_y}px (목표: {target_y}px, 차이: {diff}px)"


def log_violation(image_path: str, violation: str):
    """위반 로그 기록"""
    log_dir = Path(__file__).parent.parent.parent / "config" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_file = log_dir / "cover_violations.log"

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[COVER_VIOLATION] {timestamp}\n- 파일: {image_path}\n- 위반 내용: {violation}\n- 조치: 삭제됨\n\n"

    with open(log_file, "a", encoding="utf-8") as f:
        f.write(log_entry)


def validate_and_delete(image_path: str, cover_type: str = "korean", dry_run: bool = False) -> bool:
    """
    검증 후 위반 시 삭제

    Args:
        image_path: 검증할 이미지 경로
        cover_type: "korean" / "english"
        dry_run: True면 삭제하지 않고 결과만 출력

    Returns:
        통과 여부
    """
    passed, message = validate_cover(image_path, cover_type)

    rule = RULES.get(cover_type, {})
    print(f"\n{'=' * 60}")
    print(f"표지 검증: {rule.get('name', cover_type)}")
    print(f"{'=' * 60}")
    print(f"파일: {image_path}")
    print(f"결과: {'✅ PASS' if passed else '❌ FAIL'}")
    print(f"상세: {message}")

    if not passed:
        log_violation(image_path, message)
        if dry_run:
            print(f"\n⚠️ [DRY-RUN] 삭제 대상이지만 dry_run 모드로 유지됨")
        else:
            try:
                os.remove(image_path)
                print(f"\n🗑️ 삭제됨: {image_path}")
            except Exception as e:
                print(f"\n❌ 삭제 실패: {e}")

    print(f"{'=' * 60}\n")
    return passed


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("사용법: python validate_cover.py <image_path> [cover_type] [--dry-run]")
        print("  cover_type: korean (기본) / english")
        print("  --dry-run: 삭제하지 않고 결과만 출력")
        print("\n예시:")
        print("  python validate_cover.py cover_고구마.png korean")
        print("  python validate_cover.py cover_SWEETPOTATO.png english --dry-run")
        sys.exit(1)

    image_path = sys.argv[1]
    cover_type = sys.argv[2] if len(sys.argv) > 2 and not sys.argv[2].startswith("--") else "korean"
    dry_run = "--dry-run" in sys.argv

    validate_and_delete(image_path, cover_type, dry_run)
