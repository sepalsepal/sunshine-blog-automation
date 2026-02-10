#!/usr/bin/env python3
"""
Pillow 기반 텍스트 오버레이 모듈 v3.1

v1.0 → v3.1 주요 변경:
- Cover: 114px/#FFFFFF/y=100, 2단 그림자(L1 blur=10, L2 blur=4), 상단 그라데이션
- Body: 88px Black + 44px Medium, gap=48, margin>=72
- CTA: 48px Bold #FFD93D + 44px Medium #FFFFFF
- 하단 그라데이션 (38%, alpha 180)
- 상단 그라데이션 (커버: 35%, alpha 140)
- 레터 스페이싱 -0.02em
- v3.0 + v3.1 강제 검증 연동

작성: 레드2 + 최부장
승인: 박세준 PD
일시: 2026-02-05

규칙 출처: DESIGN_PARAMS_V31 (validators_strict.py)
"""

import re
from pathlib import Path
from typing import Optional, Tuple, Dict, Any

from PIL import Image, ImageDraw, ImageFont, ImageFilter

# ============================================
# 프로젝트 설정
# ============================================

PROJECT_ROOT = Path(__file__).parent.parent
FONTS_DIR = PROJECT_ROOT / "config" / "fonts"

FONT_FILES = {
    "black": FONTS_DIR / "NotoSansCJKkr-Black.otf",    # 900 weight
    "bold": FONTS_DIR / "NotoSansCJKkr-Bold.otf",      # 700 weight
    "medium": FONTS_DIR / "NotoSansCJKkr-Medium.otf",   # 500 weight (Regular 대용)
}

# ============================================
# v3.1 디자인 상수 (DESIGN_PARAMS_V31 동기화)
# ============================================

SAFETY_COLORS = {
    "safe": "#4CAF50",
    "caution": "#FFD93D",
    "danger": "#FF6B6B",
    "forbidden": "#FF5252",
}

# Cover
COVER_TITLE_SIZE = 114
COVER_TITLE_COLOR = "#FFFFFF"
COVER_TITLE_Y = 100
COVER_SHADOW_L1_BLUR = 10
COVER_SHADOW_L1_ALPHA = 160
COVER_SHADOW_L2_BLUR = 4
COVER_SHADOW_L2_ALPHA = 180
COVER_TOP_GRADIENT_RATIO = 0.35
COVER_TOP_GRADIENT_ALPHA = 140

# Body
BODY_TITLE_SIZE = 88
BODY_SUB_SIZE = 44

# CTA
CTA_TITLE_SIZE = 48
CTA_SUB_SIZE = 44
CTA_TITLE_COLOR = "#FFD93D"

# Spacing
GAP_TITLE_SUB = 48
BOTTOM_MARGIN_MIN = 72

# Gradient (하단 기본)
GRADIENT_RATIO = 0.38
GRADIENT_ALPHA = 180

# Shadow (표준)
SHADOW_OFFSET = (4, 4)
SHADOW_BLUR = 5
SHADOW_ALPHA = 120

# Letter spacing
LETTER_SPACING = -0.02


# ============================================
# 유틸리티 함수
# ============================================

def get_font(weight: str = "black", size: int = 88) -> ImageFont.FreeTypeFont:
    """폰트 로드 (한글 지원 확정)"""
    font_path = FONT_FILES.get(weight, FONT_FILES["black"])
    if not font_path.exists():
        raise FileNotFoundError(f"폰트 파일 없음: {font_path}")
    return ImageFont.truetype(str(font_path), size)


def hex_to_rgba(hex_color: str, alpha: int = 255) -> Tuple[int, int, int, int]:
    """HEX 색상을 RGBA 튜플로 변환"""
    hex_color = hex_color.lstrip('#')
    r = int(hex_color[0:2], 16)
    g = int(hex_color[2:4], 16)
    b = int(hex_color[4:6], 16)
    return (r, g, b, alpha)


def get_safety_color(safety: str) -> str:
    """안전도별 제목 색상 반환"""
    return SAFETY_COLORS.get(safety.lower(), "#FFFFFF")


# ============================================
# 레터 스페이싱 텍스트 렌더링
# ============================================

def _draw_text_spaced(
    draw: ImageDraw.Draw,
    x: float,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    fill,
    spacing_em: float = LETTER_SPACING,
):
    """레터 스페이싱(-0.02em) 적용 텍스트 그리기"""
    if not text:
        return
    if spacing_em == 0:
        draw.text((int(x), y), text, font=font, fill=fill)
        return

    spacing_px = font.size * spacing_em
    cx = float(x)
    for i, ch in enumerate(text):
        draw.text((int(round(cx)), y), ch, font=font, fill=fill)
        if i < len(text) - 1:
            cx += draw.textlength(ch, font=font) + spacing_px


def _measure_text(
    draw: ImageDraw.Draw,
    text: str,
    font: ImageFont.FreeTypeFont,
    spacing_em: float = LETTER_SPACING,
) -> Tuple[float, int]:
    """레터 스페이싱 적용 텍스트 크기 측정 -> (width, height)"""
    if not text:
        return 0.0, 0

    bbox = draw.textbbox((0, 0), text, font=font)
    height = bbox[3] - bbox[1]

    if spacing_em == 0:
        return float(bbox[2] - bbox[0]), height

    spacing_px = font.size * spacing_em
    total_w = 0.0
    for i, ch in enumerate(text):
        total_w += draw.textlength(ch, font=font)
        if i < len(text) - 1:
            total_w += spacing_px
    return total_w, height


# ============================================
# 그라데이션 오버레이
# ============================================

def _apply_gradient(
    img: Image.Image,
    ratio: float,
    alpha: int,
    position: str = "bottom",
) -> Image.Image:
    """반투명 검정 그라데이션 합성"""
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
    draw_ov = ImageDraw.Draw(overlay)
    h, w = img.height, img.width

    if position == "bottom":
        start = int(h * (1 - ratio))
        span = max(h - start, 1)
        for y in range(start, h):
            progress = (y - start) / span
            a = int(alpha * progress)
            draw_ov.line([(0, y), (w, y)], fill=(0, 0, 0, a))
    else:  # top
        end = int(h * ratio)
        for y in range(0, end):
            progress = 1.0 - y / max(end, 1)
            a = int(alpha * progress)
            draw_ov.line([(0, y), (w, y)], fill=(0, 0, 0, a))

    return Image.alpha_composite(img, overlay)


# ============================================
# 그림자 렌더링
# ============================================

def _shadow_standard(
    img: Image.Image,
    x: float,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
    blur: int = SHADOW_BLUR,
    alpha: int = SHADOW_ALPHA,
    offset: Tuple[int, int] = SHADOW_OFFSET,
) -> Image.Image:
    """표준 1단 그림자 (body/CTA 용)"""
    layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    ld = ImageDraw.Draw(layer)
    sx, sy = x + offset[0], y + offset[1]
    _draw_text_spaced(ld, sx, sy, text, font, (0, 0, 0, alpha))
    if blur > 0:
        layer = layer.filter(ImageFilter.GaussianBlur(radius=blur))
    return Image.alpha_composite(img, layer)


def _shadow_cover_2layer(
    img: Image.Image,
    x: float,
    y: int,
    text: str,
    font: ImageFont.FreeTypeFont,
) -> Image.Image:
    """커버 2단 그림자 (L1 넓은 글로우 + L2 선명 윤곽)"""
    # Layer 1: 넓은 블러 - 부드러운 글로우
    l1 = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d1 = ImageDraw.Draw(l1)
    _draw_text_spaced(d1, x, y, text, font, (0, 0, 0, COVER_SHADOW_L1_ALPHA))
    l1 = l1.filter(ImageFilter.GaussianBlur(radius=COVER_SHADOW_L1_BLUR))
    img = Image.alpha_composite(img, l1)

    # Layer 2: 좁은 블러 - 선명한 윤곽
    l2 = Image.new('RGBA', img.size, (0, 0, 0, 0))
    d2 = ImageDraw.Draw(l2)
    _draw_text_spaced(
        d2, x + SHADOW_OFFSET[0], y + SHADOW_OFFSET[1],
        text, font, (0, 0, 0, COVER_SHADOW_L2_ALPHA),
    )
    l2 = l2.filter(ImageFilter.GaussianBlur(radius=COVER_SHADOW_L2_BLUR))
    img = Image.alpha_composite(img, l2)

    return img


# ============================================
# 검증 config 빌더
# ============================================

def build_validation_config(slide_type: str, safety: str = "safe") -> Dict[str, Any]:
    """
    validate_before_render()에 전달할 config 딕셔너리 생성

    v3.0 키 + v3.1 키 모두 포함하여 이중 검증 통과
    """
    cfg: Dict[str, Any] = {
        "gap_title_sub": GAP_TITLE_SUB,
        "bottom_margin": BOTTOM_MARGIN_MIN,
        "gradient_ratio": GRADIENT_RATIO,
        "gradient_alpha": GRADIENT_ALPHA,
    }

    if slide_type == "cover":
        cfg.update({
            "title_size": COVER_TITLE_SIZE,
            "title_color": COVER_TITLE_COLOR,
            "title_y": COVER_TITLE_Y,
            "title_font": "NotoSansCJKkr-Black.otf",
            # v3.0 호환
            "has_bottom_text": False,
            "text_position": "top",
        })

    elif slide_type == "body":
        safety_color = get_safety_color(safety)
        cfg.update({
            # v3.1 키
            "title_size": BODY_TITLE_SIZE,
            "sub_size": BODY_SUB_SIZE,
            "title_align": "center",
            "title_font": "NotoSansCJKkr-Black.otf",
            "sub_font": "NotoSansCJKkr-Medium.otf",
            "safety": safety,
            "title_color": safety_color,
            # v3.0 호환 키
            "subtitle_size": BODY_SUB_SIZE,
            "subtitle_align": "center",
            "subtitle_color": "#FFFFFF",
        })

    elif slide_type == "cta":
        cfg.update({
            "title_size": CTA_TITLE_SIZE,
            "title_color": CTA_TITLE_COLOR,
        })

    return cfg


# ============================================
# 렌더링 함수 (핵심)
# ============================================

def render_cover(img: Image.Image, title: str) -> Image.Image:
    """
    표지 렌더링 v3.1

    - 114px Black, #FFFFFF, y=100
    - 상단 그라데이션 (35%, alpha 140)
    - 하단 그라데이션 (38%, alpha 180)
    - 2단 그림자 (L1 blur=10 + L2 blur=4)
    - 레터 스페이싱 -0.02em
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # 그라데이션: 상단(타이틀 가독성) + 하단(일관성)
    img = _apply_gradient(img, COVER_TOP_GRADIENT_RATIO, COVER_TOP_GRADIENT_ALPHA, "top")
    img = _apply_gradient(img, GRADIENT_RATIO, GRADIENT_ALPHA, "bottom")

    font = get_font("black", COVER_TITLE_SIZE)

    # 텍스트 크기 측정
    temp_draw = ImageDraw.Draw(img)
    tw, th = _measure_text(temp_draw, title, font)

    # 중앙 정렬, y=100
    x = (img.width - tw) / 2
    y = COVER_TITLE_Y

    # 2단 그림자
    img = _shadow_cover_2layer(img, x, y, title, font)

    # 메인 텍스트 (흰색)
    draw = ImageDraw.Draw(img)
    _draw_text_spaced(draw, x, y, title, font, COVER_TITLE_COLOR)

    print(f"  [COVER v3.1] {COVER_TITLE_SIZE}px {COVER_TITLE_COLOR} y={COVER_TITLE_Y} 2-layer shadow")
    return img


def render_body(
    img: Image.Image,
    title: str,
    subtitle: str,
    safety: str,
) -> Image.Image:
    """
    본문 렌더링 v3.1

    - 제목: 88px Black, 안전도 색상
    - 부제목: 44px Medium, #FFFFFF
    - 하단 그라데이션 (38%, alpha 180)
    - 간격: gap=48, margin>=72
    - 레터 스페이싱 -0.02em
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # 하단 그라데이션
    img = _apply_gradient(img, GRADIENT_RATIO, GRADIENT_ALPHA, "bottom")

    title_font = get_font("black", BODY_TITLE_SIZE)
    sub_font = get_font("medium", BODY_SUB_SIZE)
    title_color = get_safety_color(safety)

    # 텍스트 크기 측정
    temp_draw = ImageDraw.Draw(img)
    tw, th = _measure_text(temp_draw, title, title_font)
    sw, sh = _measure_text(temp_draw, subtitle, sub_font) if subtitle else (0, 0)

    # 블록 높이 및 Y 위치 (하단 여백 기준)
    block_h = th + (GAP_TITLE_SUB + sh if subtitle else 0)
    block_y = img.height - BOTTOM_MARGIN_MIN - block_h

    # 제목 (안전도 색상)
    tx = (img.width - tw) / 2
    ty = block_y
    img = _shadow_standard(img, tx, ty, title, title_font)
    draw = ImageDraw.Draw(img)
    _draw_text_spaced(draw, tx, ty, title, title_font, title_color)

    # 부제목 (흰색)
    if subtitle:
        sx = (img.width - sw) / 2
        sy = ty + th + GAP_TITLE_SUB
        img = _shadow_standard(img, sx, sy, subtitle, sub_font, blur=3, alpha=100, offset=(2, 2))
        draw = ImageDraw.Draw(img)
        _draw_text_spaced(draw, sx, sy, subtitle, sub_font, "#FFFFFF")

    print(f"  [BODY v3.1] 제목({title_color}, {BODY_TITLE_SIZE}px) + 부제목(#FFF, {BODY_SUB_SIZE}px) gap={GAP_TITLE_SUB}")
    return img


def render_cta(
    img: Image.Image,
    title: str,
    subtitle: str,
    bg_path: str = "",
) -> Image.Image:
    """
    CTA 렌더링 v3.1

    - 제목: 48px Bold, #FFD93D (노랑)
    - 부제목: 44px Medium, #FFFFFF
    - 하단 그라데이션 (38%, alpha 180)
    - 간격: gap=48, margin>=72
    """
    if img.mode != 'RGBA':
        img = img.convert('RGBA')

    # 하단 그라데이션
    img = _apply_gradient(img, GRADIENT_RATIO, GRADIENT_ALPHA, "bottom")

    title_font = get_font("bold", CTA_TITLE_SIZE)
    sub_font = get_font("medium", CTA_SUB_SIZE)

    # 텍스트 크기 측정
    temp_draw = ImageDraw.Draw(img)
    tw, th = _measure_text(temp_draw, title, title_font)
    sw, sh = _measure_text(temp_draw, subtitle, sub_font) if subtitle else (0, 0)

    # 블록 높이 및 Y 위치
    block_h = th + (GAP_TITLE_SUB + sh if subtitle else 0)
    block_y = img.height - BOTTOM_MARGIN_MIN - block_h

    # 제목 (노랑)
    tx = (img.width - tw) / 2
    ty = block_y
    img = _shadow_standard(img, tx, ty, title, title_font)
    draw = ImageDraw.Draw(img)
    _draw_text_spaced(draw, tx, ty, title, title_font, CTA_TITLE_COLOR)

    # 부제목 (흰색)
    if subtitle:
        sx = (img.width - sw) / 2
        sy = ty + th + GAP_TITLE_SUB
        img = _shadow_standard(img, sx, sy, subtitle, sub_font, blur=3, alpha=100, offset=(2, 2))
        draw = ImageDraw.Draw(img)
        _draw_text_spaced(draw, sx, sy, subtitle, sub_font, "#FFFFFF")

    print(f"  [CTA v3.1] 제목({CTA_TITLE_COLOR}, {CTA_TITLE_SIZE}px) + 부제목(#FFF, {CTA_SUB_SIZE}px)")
    return img


# ============================================
# 클린 이미지 검증 (v1.0 호환)
# ============================================

def validate_base_image(base_path: str, strict: bool = True) -> bool:
    """클린 베이스 이미지(_bg.png 또는 _clean) 검증"""
    path_str = str(base_path)

    if path_str.endswith('_bg.png') or '_clean' in path_str:
        return True

    if re.search(r'_\d{2}\.png$', path_str):
        msg = (
            f"클린 이미지(_bg.png)만 overlay 가능\n"
            f"   입력 파일: {Path(base_path).name}\n"
            f"   -> *_bg.png 파일을 사용하세요"
        )
        if strict:
            raise ValueError(msg)
        print(f"[WARN] {msg}")
        return False

    print(f"[WARN] 비표준 파일명: {Path(base_path).name}")
    return True


def validate_slide_type(slide_num: int, config: dict) -> bool:
    """슬라이드 타입별 규칙 검증 (v1.0 호환)"""
    if slide_num == 0:
        if config.get('bottom_text') or config.get('subtitle'):
            raise ValueError("표지(00)에 하단 텍스트/부제목 금지")
    elif slide_num in [1, 2]:
        tc = config.get('title_color', '#FF5252')
        sc = config.get('subtitle_color', '#FFFFFF')
        if tc.upper() == sc.upper():
            raise ValueError(f"본문 제목/부제목 색상 동일 금지: {tc}")
    elif slide_num == 3:
        if config.get('image_source', 'photo_only') != 'photo_only':
            raise ValueError("CTA(03)는 실사진만 허용")
    return True


def get_text_color(safety: str, slide_type: str = "body") -> str:
    """안전도별 텍스트 색상 (v1.0 호환)"""
    if slide_type == "cover":
        return "#FFFFFF"
    if slide_type == "cta":
        return CTA_TITLE_COLOR
    return SAFETY_COLORS.get(safety.lower(), "#FFFFFF")


# ============================================
# 호환 래퍼 함수 (v1.0 API 유지)
# ============================================

def overlay_from_config(
    image_path: Path,
    slide_index: int,
    text_config: Dict[str, Any],
    safety: str = "safe",
    skip_validation: bool = False,
) -> bool:
    """설정 기반 오버레이 (reoverlay.py 호환)"""
    try:
        if not skip_validation:
            validate_base_image(str(image_path), strict=True)

        img = Image.open(image_path)

        slides = text_config.get("slides", [])
        if slide_index < len(slides):
            title = slides[slide_index].get("title", "")
            subtitle = slides[slide_index].get("subtitle", "")
        else:
            return True

        if not title:
            return True

        if slide_index == 0:
            result = render_cover(img, title)
        elif slide_index == 3 or "저장" in title or "공유" in title:
            result = render_cta(img, title, subtitle, str(image_path))
        else:
            result = render_body(img, title, subtitle, safety=safety)

        if image_path.suffix.lower() == '.png':
            result.save(image_path, 'PNG')
        else:
            result.convert('RGB').save(image_path, 'JPEG', quality=95)

        return True
    except Exception as e:
        print(f"[ERROR] overlay_from_config: {e}")
        return False


def apply_cover_overlay(image: Image.Image, title: str, food_name_ko=None) -> Image.Image:
    """v1.0 호환 래퍼"""
    return render_cover(image, title)


def apply_body_overlay(image: Image.Image, title: str, subtitle: str = "",
                       safety: str = "safe", config=None) -> Image.Image:
    """v1.0 호환 래퍼"""
    return render_body(image, title, subtitle, safety)


def apply_cta_overlay(image: Image.Image, title: str = "저장 & 공유",
                      subtitle: str = "주변 견주에게 알려주세요!") -> Image.Image:
    """v1.0 호환 래퍼"""
    return render_cta(image, title, subtitle)


def create_cover(base_path: str, title: str, output_path: str) -> bool:
    """표지 생성 (v1.0 API 호환)"""
    validate_base_image(base_path, strict=True)
    try:
        img = Image.open(base_path)
        result = render_cover(img, title)
        fmt = 'PNG' if output_path.endswith('.png') else 'JPEG'
        if fmt == 'JPEG':
            result = result.convert('RGB')
        result.save(output_path, fmt, quality=95)
        print(f"[OK] create_cover: {Path(output_path).name}")
        return True
    except Exception as e:
        print(f"[ERROR] create_cover: {e}")
        return False


def create_body(base_path: str, title: str, subtitle: str,
                output_path: str, safety: str = "safe") -> bool:
    """본문 생성 (v1.0 API 호환)"""
    validate_base_image(base_path, strict=True)
    try:
        img = Image.open(base_path)
        result = render_body(img, title, subtitle, safety)
        fmt = 'PNG' if output_path.endswith('.png') else 'JPEG'
        if fmt == 'JPEG':
            result = result.convert('RGB')
        result.save(output_path, fmt, quality=95)
        print(f"[OK] create_body: {Path(output_path).name}")
        return True
    except Exception as e:
        print(f"[ERROR] create_body: {e}")
        return False


def create_cta(base_path: str, output_path: str,
               title: str = "저장 & 공유",
               subtitle: str = "주변 견주에게 알려주세요!") -> bool:
    """CTA 생성 (v1.0 API 호환)"""
    validate_base_image(base_path, strict=True)
    try:
        img = Image.open(base_path)
        result = render_cta(img, title, subtitle, base_path)
        fmt = 'PNG' if output_path.endswith('.png') else 'JPEG'
        if fmt == 'JPEG':
            result = result.convert('RGB')
        result.save(output_path, fmt, quality=95)
        print(f"[OK] create_cta: {Path(output_path).name}")
        return True
    except Exception as e:
        print(f"[ERROR] create_cta: {e}")
        return False


# ============================================
# CLI 테스트
# ============================================

if __name__ == "__main__":
    print("=" * 50)
    print("Pillow Overlay v3.1 테스트")
    print("=" * 50)

    # 폰트 로드 테스트
    try:
        for w in ("black", "bold", "medium"):
            f = get_font(w, 48)
            print(f"  [OK] {w}: {FONT_FILES[w].name}")
    except Exception as e:
        print(f"  [FAIL] 폰트: {e}")

    # v3.1 상수 출력
    print(f"\n[v3.1 상수]")
    print(f"  Cover: {COVER_TITLE_SIZE}px, {COVER_TITLE_COLOR}, y={COVER_TITLE_Y}")
    print(f"  Body:  {BODY_TITLE_SIZE}px + {BODY_SUB_SIZE}px")
    print(f"  CTA:   {CTA_TITLE_SIZE}px, {CTA_TITLE_COLOR}")
    print(f"  Gap:   {GAP_TITLE_SUB}px, Margin: {BOTTOM_MARGIN_MIN}px")
    print(f"  Gradient: {GRADIENT_RATIO}/{GRADIENT_ALPHA}")
    print(f"  Letter spacing: {LETTER_SPACING}em")

    # 색상 테스트
    print(f"\n[안전도 색상]")
    for s, c in SAFETY_COLORS.items():
        print(f"  {s}: {c}")

    print("\n[OK] v3.1 모듈 로드 성공")
