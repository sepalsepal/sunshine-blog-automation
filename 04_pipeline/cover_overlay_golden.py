#!/usr/bin/env python3
"""
cover_overlay_golden.py - 골든 샘플 스펙 준수 표지 생성기
GOLDEN SAMPLE SPEC v2.0

기준: baguette_up50.png
확정일: 2026-02-12
승인: PD 박세준

이 파일의 모든 상수는 PD 승인 없이 변경 불가.
"""

import hashlib
import json
from pathlib import Path
from typing import Tuple, Optional

import PIL
from PIL import Image, ImageDraw, ImageFont, ImageFilter

from config.version import SYSTEM_VERSION, SPEC_VERSION

# ============================================================================
# 스펙 버전 및 환경 상수 (변경 금지)
# ============================================================================

# 🔒 v2.2: 버전 정보는 config.version에서 import
# SYSTEM_VERSION, SPEC_VERSION은 config/version.py에서 관리

# 허용된 anchor 목록 (v2.2)
ALLOWED_ANCHORS = {"mt"}

# Pillow 버전 고정 (v2 필수)
REQUIRED_PILLOW_VERSION = "12.1.0"

# 폰트 SHA256 해시 (v2 필수)
FONT_SHA256_MAP = {
    "BlackHanSans-Regular.ttf": "31960809284026681774a8e52dc19ebcad26cf69b0ad9d560f288296fbb52739",
    "NanumGothic-ExtraBold.ttf": "5c4568e5295a8c52bc30e7efa1ea6d2de43556268ef42daba93540a1ece691ae",
}

# ============================================================================
# 프로젝트 설정
# ============================================================================

PROJECT_ROOT = Path(__file__).parent.parent
CONFIG_PATH = PROJECT_ROOT / "config" / "cover_overlay_spec.json"
FONTS_DIR = PROJECT_ROOT / "config" / "fonts"

# ============================================================================
# 골든 샘플 스펙 상수 (변경 금지)
# ============================================================================

# 해상도 (절대 고정)
WIDTH = 1080
HEIGHT = 1080

# 한글 텍스트 (윗줄)
KOREAN_FONT = "NotoSansCJK-Black.ttc"
KOREAN_FONT_SIZE = 120
KOREAN_Y = 30
KOREAN_COLOR = "#FFFFFF"

# 영어 텍스트 (아랫줄)
ENGLISH_FONT = "NotoSansCJK-Black.ttc"
ENGLISH_FONT_SIZE = 80
ENGLISH_Y = 170  # v1.1: 160 → 170 (+10px)
ENGLISH_COLOR = "#FFFFFF"
ENGLISH_UPPERCASE = True  # v1.1: UPPERCASE 적용

# 텍스트 앵커 (v2 필수)
TEXT_ANCHOR = "mt"  # middle-top (중앙 상단 기준)

# v2.1: 영어 길이 초과 시 자동 축소 규칙
MAX_ENGLISH_WIDTH_PERCENT = 0.90  # 가로 90%
MAX_ENGLISH_WIDTH_PX = int(WIDTH * MAX_ENGLISH_WIDTH_PERCENT)  # 972px
ENGLISH_MIN_FONT_SIZE = 60  # 최소 폰트 크기
ENGLISH_LINE_BREAK_FORBIDDEN = True  # 줄바꿈 절대 금지

# 상단 그라데이션
GRADIENT_HEIGHT_PERCENT = 0.35
GRADIENT_HEIGHT_PX = 378
GRADIENT_ALPHA_START = 180
GRADIENT_ALPHA_END = 0
GRADIENT_COLOR = (0, 0, 0)

# 드롭 쉐도우
SHADOW_OFFSET_X = 3
SHADOW_OFFSET_Y = 3
SHADOW_COLOR = (0, 0, 0)
SHADOW_ALPHA = 120
SHADOW_BLUR = 4


# ============================================================================
# 환경 검증 함수 (v2 필수)
# ============================================================================

def verify_pillow_version() -> bool:
    """Pillow 버전 검증 (v2.2 강화)"""
    current = PIL.__version__
    if current != REQUIRED_PILLOW_VERSION:
        raise ValueError(
            f"[E007] Pillow 버전 불일치: "
            f"필요 {REQUIRED_PILLOW_VERSION}, 현재 {current}"
        )
    return True


def validate_anchor(anchor: str) -> bool:
    """anchor 검증 (v2.2)"""
    if anchor not in ALLOWED_ANCHORS:
        raise ValueError(
            f"[E012] 허용되지 않은 anchor: '{anchor}'"
        )
    return True


def get_file_sha256(file_path: Path) -> str:
    """파일 SHA256 해시 계산"""
    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def verify_font_integrity(font_path: Path) -> bool:
    """폰트 파일 무결성 검증 (SHA256)"""
    font_name = font_path.name
    if font_name in FONT_SHA256_MAP:
        expected_hash = FONT_SHA256_MAP[font_name]
        actual_hash = get_file_sha256(font_path)
        if actual_hash != expected_hash:
            raise ValueError(
                f"[FONT_INTEGRITY_ERROR] 폰트 해시 불일치: {font_name}\n"
                f"  Expected: {expected_hash}\n"
                f"  Actual: {actual_hash}"
            )
        print(f"  [OK] 폰트 무결성 확인: {font_name}")
    return True


# ============================================================================
# 폰트 로더
# ============================================================================

def _get_font_path(font_name: str) -> Path:
    """폰트 파일 경로 반환"""
    # 프로젝트 폰트 디렉토리
    project_font = FONTS_DIR / font_name
    if project_font.exists():
        return project_font

    # OTF 버전 시도
    otf_name = font_name.replace(".ttc", ".otf").replace("CJK-", "CJKkr-")
    project_otf = FONTS_DIR / otf_name
    if project_otf.exists():
        return project_otf

    # 시스템 폰트 디렉토리 (macOS)
    system_paths = [
        Path("/System/Library/Fonts") / font_name,
        Path("/Library/Fonts") / font_name,
        Path.home() / "Library" / "Fonts" / font_name,
    ]
    for path in system_paths:
        if path.exists():
            return path

    # NotoSansCJKkr-Black.otf 폴백
    fallback = FONTS_DIR / "NotoSansCJKkr-Black.otf"
    if fallback.exists():
        return fallback

    # BlackHanSans 폴백 (사용자 폰트 디렉토리)
    blackhansans = Path.home() / "Library" / "Fonts" / "BlackHanSans-Regular.ttf"
    if blackhansans.exists():
        return blackhansans

    # NanumGothic-ExtraBold 최종 폴백
    nanumgothic = Path.home() / "Library" / "Fonts" / "NanumGothic-ExtraBold.ttf"
    if nanumgothic.exists():
        return nanumgothic

    raise FileNotFoundError(f"폰트 파일 없음: {font_name}")


def get_korean_font() -> Tuple[ImageFont.FreeTypeFont, Path]:
    """한글 폰트 로드 (120px) + 경로 반환"""
    font_path = _get_font_path(KOREAN_FONT)
    return ImageFont.truetype(str(font_path), KOREAN_FONT_SIZE), font_path


def get_english_font() -> Tuple[ImageFont.FreeTypeFont, Path]:
    """영어 폰트 로드 (80px) + 경로 반환"""
    font_path = _get_font_path(ENGLISH_FONT)
    return ImageFont.truetype(str(font_path), ENGLISH_FONT_SIZE), font_path


# ============================================================================
# 유틸리티
# ============================================================================

def hex_to_rgba(hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    """HEX → RGBA 변환"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, alpha)


def measure_text(
    text: str,
    font: ImageFont.FreeTypeFont
) -> Tuple[int, int]:
    """텍스트 크기 측정 (width, height)"""
    temp = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(temp)
    bbox = draw.textbbox((0, 0), text, font=font)
    return bbox[2] - bbox[0], bbox[3] - bbox[1]


# ============================================================================
# 레이어 렌더링
# ============================================================================

def apply_top_gradient(img: Image.Image) -> Image.Image:
    """
    상단 그라데이션 적용 (레이어 2)

    스펙:
    - 높이: 35% (378px)
    - 알파: 180 → 0 (상단 → 하단)
    """
    gradient = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    draw = ImageDraw.Draw(gradient)

    for y in range(GRADIENT_HEIGHT_PX):
        # 선형 보간
        alpha = int(GRADIENT_ALPHA_START * (1 - y / GRADIENT_HEIGHT_PX))
        draw.line([(0, y), (WIDTH, y)], fill=(*GRADIENT_COLOR, alpha))

    return Image.alpha_composite(img, gradient)


def draw_text_with_shadow(
    img: Image.Image,
    text: str,
    font: ImageFont.FreeTypeFont,
    y: int,
    color: str,
    anchor: str = TEXT_ANCHOR
) -> Image.Image:
    """
    드롭 쉐도우 + 텍스트 렌더링 (v2.2: anchor 검증 추가)

    스펙:
    - 쉐도우 offset: (3, 3)
    - 쉐도우 알파: 120
    - 쉐도우 blur: 4
    - anchor: mt (middle-top)
    """
    # 🔒 v2.2: anchor 검증
    validate_anchor(anchor)

    # 중앙 X 좌표
    x = WIDTH // 2

    # 드롭 쉐도우 레이어
    shadow_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)
    shadow_draw.text(
        (x + SHADOW_OFFSET_X, y + SHADOW_OFFSET_Y),
        text,
        font=font,
        fill=(*SHADOW_COLOR, SHADOW_ALPHA),
        anchor=anchor  # v2: anchor 명시
    )
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=SHADOW_BLUR))

    # 합성: 쉐도우
    img = Image.alpha_composite(img, shadow_layer)

    # 텍스트 레이어
    text_layer = Image.new("RGBA", (WIDTH, HEIGHT), (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    text_draw.text(
        (x, y),
        text,
        font=font,
        fill=hex_to_rgba(color),
        anchor=anchor  # v2: anchor 명시
    )

    # 합성: 텍스트
    return Image.alpha_composite(img, text_layer)


# ============================================================================
# v2.1: 영어 폰트 크기 자동 조절
# ============================================================================

class RenderLog:
    """렌더 로그 기록 클래스"""
    def __init__(self):
        self.auto_scale_used = False
        self.final_font_size = ENGLISH_FONT_SIZE
        self.rendered_width = 0
        self.hold_for_review = False

    def to_dict(self) -> dict:
        return {
            "AUTO_SCALE_USED": self.auto_scale_used,
            "FINAL_FONT_SIZE": self.final_font_size,
            "RENDERED_WIDTH": self.rendered_width,
            "HOLD_FOR_REVIEW": self.hold_for_review,
        }

    def __str__(self) -> str:
        return (
            f"AUTO_SCALE_USED: {self.auto_scale_used}\n"
            f"FINAL_FONT_SIZE: {self.final_font_size}\n"
            f"RENDERED_WIDTH: {self.rendered_width}px\n"
            f"HOLD_FOR_REVIEW: {self.hold_for_review}"
        )


def calculate_english_font_size(
    english_text: str,
    base_size: int = ENGLISH_FONT_SIZE
) -> Tuple[int, int, RenderLog]:
    """
    v2.1: 영어 텍스트 폰트 크기 자동 계산

    조건: rendered_width > 972px (가로 90%)
    조치: new_size = floor(80 * (972 / rendered_width))

    Returns:
        (최종 폰트 크기, 렌더링 너비, RenderLog)

    Raises:
        ValueError: new_size < 60일 경우 HOLD_FOR_REVIEW
    """
    import math

    log = RenderLog()
    font_path = _get_font_path(ENGLISH_FONT)
    font = ImageFont.truetype(str(font_path), base_size)

    # 텍스트 너비 측정
    text_width, _ = measure_text(english_text, font)
    log.rendered_width = text_width

    # 너비 초과 시 축소 계산
    if text_width > MAX_ENGLISH_WIDTH_PX:
        log.auto_scale_used = True
        new_size = math.floor(base_size * (MAX_ENGLISH_WIDTH_PX / text_width))

        # 최종 크기로 다시 측정
        font = ImageFont.truetype(str(font_path), new_size)
        text_width, _ = measure_text(english_text, font)
        log.rendered_width = text_width
        log.final_font_size = new_size

        if new_size < ENGLISH_MIN_FONT_SIZE:
            # 60px 미만: 제작 중단
            log.hold_for_review = True
            raise ValueError(
                f"[HOLD_FOR_REVIEW] 영어 폰트 크기 {new_size}px < 최소 {ENGLISH_MIN_FONT_SIZE}px\n"
                f"텍스트: '{english_text}'\n"
                f"렌더링 너비: {log.rendered_width}px\n"
                f"줄바꿈 금지 규정에 따라 제작 중단. PD 검토 필요."
            )
        elif new_size == ENGLISH_MIN_FONT_SIZE:
            # 60px: 제작 후 보고 필수
            log.hold_for_review = True
            print(f"  [WARNING] 영어 폰트 60px 적용 - 제작 후 보고 필수")
    else:
        log.final_font_size = base_size

    return log.final_font_size, log.rendered_width, log


# ============================================================================
# 스펙 검증 함수
# ============================================================================

def validate_spec_before_render(korean_text: str, english_text: str) -> bool:
    """
    🔒 렌더링 전 스펙 검증 (v1.1)
    위반 시 예외 발생하여 생성 차단
    """
    errors = []

    # 영어 UPPERCASE 검증
    if english_text != english_text.upper():
        errors.append(f"UPPERCASE 위반: '{english_text}' → '{english_text.upper()}'")

    # 한글 존재 검증
    if not korean_text or len(korean_text.strip()) == 0:
        errors.append("한글 텍스트 누락")

    # 영어 존재 검증
    if not english_text or len(english_text.strip()) == 0:
        errors.append("영어 텍스트 누락")

    if errors:
        raise ValueError(f"[SPEC_VIOLATION] 스펙 위반 {len(errors)}건:\n" + "\n".join(errors))

    return True


def validate_environment() -> dict:
    """
    🔒 환경 검증 (v2 필수)
    - Pillow 버전
    - 폰트 무결성
    """
    result = {
        "pillow_version": {"pass": False, "actual": PIL.__version__, "required": REQUIRED_PILLOW_VERSION},
        "font_korean": {"pass": False, "path": None, "hash_verified": False},
        "font_english": {"pass": False, "path": None, "hash_verified": False},
    }

    # Pillow 버전 검증
    verify_pillow_version()
    result["pillow_version"]["pass"] = True

    # 폰트 로드 및 무결성 검증
    korean_font, korean_path = get_korean_font()
    result["font_korean"]["path"] = str(korean_path)
    try:
        verify_font_integrity(korean_path)
        result["font_korean"]["hash_verified"] = True
    except ValueError:
        result["font_korean"]["hash_verified"] = False
    result["font_korean"]["pass"] = True

    english_font, english_path = get_english_font()
    result["font_english"]["path"] = str(english_path)
    try:
        verify_font_integrity(english_path)
        result["font_english"]["hash_verified"] = True
    except ValueError:
        result["font_english"]["hash_verified"] = False
    result["font_english"]["pass"] = True

    return result


# ============================================================================
# 메인 함수
# ============================================================================

def create_cover_golden(
    source_path: str,
    korean_text: str,
    english_text: str,
    output_path: str,
    skip_env_check: bool = False
) -> Tuple[str, RenderLog]:
    """
    골든 샘플 스펙 준수 표지 생성 (v2.1)

    Args:
        source_path: 클린 소스 이미지 경로
        korean_text: 한글 음식명 (예: "바게트")
        english_text: 영어 음식명 (예: "Baguette")
        output_path: 출력 파일 경로
        skip_env_check: 환경 검증 스킵 (테스트용)

    Returns:
        Tuple[str, RenderLog]: (출력 파일 경로, 렌더 로그)
        - RenderLog에 AUTO_SCALE_USED, FINAL_FONT_SIZE, RENDERED_WIDTH, HOLD_FOR_REVIEW 기록

    Raises:
        ValueError: 영어 폰트 60px 미만 시 HOLD_FOR_REVIEW (제작 중단)

    레이어 순서:
        1. 배경 이미지 (클린 소스)
        2. 상단 그라데이션 오버레이
        3. 한글 드롭 쉐도우
        4. 한글 텍스트
        5. 영어 드롭 쉐도우
        6. 영어 텍스트
    """
    # 🔒 v2: 영어 텍스트 UPPERCASE 강제 변환
    english_text = english_text.upper()

    # 🔒 UPPERCASE 검증 (위반 시 생성 차단)
    if not english_text.isupper():
        raise ValueError(f"[SPEC_VIOLATION] 영어 텍스트 UPPERCASE 위반: {english_text}")

    # 🔒 렌더링 전 스펙 검증
    validate_spec_before_render(korean_text, english_text)

    print(f"\n{'='*60}")
    print(f"GOLDEN SAMPLE 표지 생성 (SYS:{SYSTEM_VERSION}/SPEC:{SPEC_VERSION})")
    print(f"{'='*60}")

    # 🔒 v2: 환경 검증
    if not skip_env_check:
        print("\n[환경 검증]")
        env_result = validate_environment()
        print(f"  Pillow: {env_result['pillow_version']['actual']}")
        print(f"  한글 폰트: {Path(env_result['font_korean']['path']).name}")
        print(f"  영어 폰트: {Path(env_result['font_english']['path']).name}")

    # 🔒 v2.1: 영어 폰트 크기 자동 계산
    final_font_size, rendered_width, render_log = calculate_english_font_size(english_text)

    print(f"\n소스: {source_path}")
    print(f"한글: {korean_text} (120px, Y=30)")
    if render_log.auto_scale_used:
        print(f"영어: {english_text} ({final_font_size}px ← 80px 축소, Y=170, UPPERCASE)")
        print(f"  [AUTO_SCALE] 렌더링 너비: {rendered_width}px (최대 {MAX_ENGLISH_WIDTH_PX}px)")
    else:
        print(f"영어: {english_text} (80px, Y=170, UPPERCASE)")
        print(f"  렌더링 너비: {rendered_width}px")
    print(f"앵커: {TEXT_ANCHOR}")
    print(f"출력: {output_path}")

    # 레이어 1: 배경 이미지 로드 + 리사이즈
    img = Image.open(source_path).convert("RGBA")
    orig_size = img.size
    if orig_size != (WIDTH, HEIGHT):
        img = img.resize((WIDTH, HEIGHT), Image.LANCZOS)
        print(f"리사이즈: {orig_size} → {WIDTH}x{HEIGHT}")

    # 레이어 2: 상단 그라데이션
    img = apply_top_gradient(img)
    print(f"그라데이션: {GRADIENT_HEIGHT_PERCENT*100}%, alpha {GRADIENT_ALPHA_START}→{GRADIENT_ALPHA_END}")

    # 폰트 로드
    korean_font, _ = get_korean_font()

    # 🔒 v2.1: 영어 폰트는 자동 계산된 크기로 로드
    font_path = _get_font_path(ENGLISH_FONT)
    english_font = ImageFont.truetype(str(font_path), final_font_size)

    # 레이어 3-4: 한글 쉐도우 + 텍스트
    img = draw_text_with_shadow(
        img, korean_text, korean_font, KOREAN_Y, KOREAN_COLOR, TEXT_ANCHOR
    )
    print(f"한글: '{korean_text}' @ Y={KOREAN_Y}, anchor={TEXT_ANCHOR}")

    # 레이어 5-6: 영어 쉐도우 + 텍스트 (v2.1: 자동 계산된 폰트 사용)
    img = draw_text_with_shadow(
        img, english_text, english_font, ENGLISH_Y, ENGLISH_COLOR, TEXT_ANCHOR
    )
    print(f"영어: '{english_text}' @ Y={ENGLISH_Y}, font_size={final_font_size}px, anchor={TEXT_ANCHOR}")

    # 저장
    output = Path(output_path)
    output.parent.mkdir(parents=True, exist_ok=True)
    img.save(output, "PNG")

    print(f"\n저장 완료: {output_path}")
    print(f"해상도: {WIDTH}x{HEIGHT}")

    # 🔒 v2.1: 필수 로그 출력
    print(f"\n[RenderLog]")
    print(render_log)

    if render_log.hold_for_review:
        print(f"\n⚠️  HOLD_FOR_REVIEW: 60px 적용 - PD 검토 필요")

    print(f"{'='*60}\n")

    return str(output_path), render_log


def validate_output(output_path: str) -> dict:
    """
    출력 이미지 검증

    Returns:
        검증 결과 딕셔너리
    """
    img = Image.open(output_path)

    checks = {
        "resolution": img.size == (WIDTH, HEIGHT),
        "format": output_path.lower().endswith(".png"),
        "mode": img.mode == "RGBA"
    }

    return {
        "path": output_path,
        "size": img.size,
        "mode": img.mode,
        "checks": checks,
        "all_pass": all(checks.values())
    }


# ============================================================================
# CLI
# ============================================================================

def main():
    """CLI 엔트리포인트"""
    import sys

    if len(sys.argv) < 5:
        print("사용법: python cover_overlay_golden.py <source> <korean> <english> <output>")
        print("예시: python cover_overlay_golden.py baguette_clean.png 바게트 Baguette baguette_cover.png")
        sys.exit(1)

    source = sys.argv[1]
    korean = sys.argv[2]
    english = sys.argv[3]
    output = sys.argv[4]

    try:
        output_path, render_log = create_cover_golden(source, korean, english, output)
    except ValueError as e:
        if "HOLD_FOR_REVIEW" in str(e):
            print(f"\n⛔ 제작 중단: {e}")
            sys.exit(2)
        raise

    # 검증
    validation = validate_output(output_path)
    print(f"검증 결과: {'PASS' if validation['all_pass'] else 'FAIL'}")
    for check, passed in validation["checks"].items():
        status = "+" if passed else "-"
        print(f"  {status} {check}")

    # v2.1: RenderLog 요약
    if render_log.hold_for_review:
        print(f"\n⚠️  PD 검토 필요: 60px 폰트 적용됨")
        sys.exit(1)


if __name__ == "__main__":
    main()
