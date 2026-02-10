"""
Project Sunshine - 강제 검증 모듈 (v3.0 + v3.1)
=================================================

원칙: "위반하면 죽는다"

이 모듈의 모든 함수는:
- 검증 통과 → True 반환
- 검증 실패 → 즉시 Exception (실행 중단)

v3.0: 클린 이미지, CTA 실사진, 이모지 제거
v3.1: 디자인 파라미터 (폰트, 간격, 그라데이션, 안전도 색상)

사용법:
    from pipeline.validators_strict import (
        assert_cta_real_photo,
        assert_body_layout,
        assert_clean_image,
        validate_before_render,
        validate_v31_slide,
        DESIGN_PARAMS_V31,
    )

    # 렌더링 전 필수 호출 (v3.0 + v3.1 자동 체인)
    validate_before_render(slide_type='body', config=config, image_path=path)
"""

import os
import re
from typing import Dict, Any, Optional

# ============================================================
# 🔴 CRITICAL: v3.0 설정값 (pasta_01 기준, 변경 금지)
# ============================================================

class LOCKED_CONFIG:
    """
    ⚠️ 이 값들은 하드코딩됨
    ⚠️ 변경하려면 PD 승인 필요
    """

    # 본문 제목 (v3.1: 100→88)
    BODY_TITLE_SIZE = 88
    BODY_TITLE_ALIGN = 'center'

    # 본문 부제목 (v3.1: 56→44)
    BODY_SUBTITLE_SIZE = 44
    BODY_SUBTITLE_ALIGN = 'center'
    BODY_SUBTITLE_COLOR = '#FFFFFF'

    # CTA (v3.1: 64→48)
    CTA_TITLE_SIZE = 48
    CTA_TITLE_COLOR = '#FFD93D'
    CTA_SUBTITLE_COLOR = '#FFFFFF'

    # 표지
    COVER_TEXT_POSITION = 'top'
    COVER_TITLE_SIZE = 114


# ============================================================
# 🔴 CRITICAL: v3.1 디자인 파라미터 (변경 금지)
# ============================================================

DESIGN_PARAMS_V31 = {
    # 폰트
    "TITLE_FONT": "NotoSansCJK-Black.ttc",
    "SUB_FONT": "NotoSansCJK-Regular.ttc",
    "FONT_INDEX_KR": 1,

    # Cover
    "COVER_TITLE_SIZE": 114,
    "COVER_TITLE_COLOR": "#FFFFFF",
    "COVER_TITLE_Y": 100,
    "COVER_SHADOW_LAYERS": 2,

    # Body
    "BODY_TITLE_SIZE": 88,
    "BODY_SUB_SIZE": 44,
    "BODY_TITLE_ALIGN": "center",

    # CTA
    "CTA_TITLE_SIZE": 48,
    "CTA_SUB_SIZE": 44,
    "CTA_TITLE_COLOR": "#FFD93D",

    # 간격 (절대 고정)
    "GAP_TITLE_SUB": 48,
    "GAP_SUB_CTA": 56,
    "BOTTOM_MARGIN_MIN": 72,

    # 그라데이션
    "GRADIENT_RATIO": 0.38,
    "GRADIENT_ALPHA": 180,
    "COVER_TOP_GRADIENT_RATIO": 0.35,
    "COVER_TOP_GRADIENT_ALPHA": 140,

    # 그림자 (표준)
    "SHADOW_OFFSET": (4, 4),
    "SHADOW_BLUR": 5,
    "SHADOW_ALPHA": 120,

    # 그림자 (커버 2단)
    "COVER_SHADOW_L1_BLUR": 10,
    "COVER_SHADOW_L1_ALPHA": 160,
    "COVER_SHADOW_L2_BLUR": 4,
    "COVER_SHADOW_L2_ALPHA": 180,

    # 레터 스페이싱
    "LETTER_SPACING": -0.02,

    # 안전도 색상
    "SAFETY_COLORS": {
        "safe": "#4CAF50",
        "caution": "#FFD93D",
        "danger": "#FF6B6B",
        "forbidden": "#FF5252",
    },
}


# ============================================================
# 🔴 v3.1 디자인 검증 함수
# ============================================================

def assert_v31_cover(config: Dict[str, Any]) -> bool:
    """커버 슬라이드 v3.1 검증"""
    P = DESIGN_PARAMS_V31
    errors = []

    title_size = config.get("title_size", 0)
    if title_size != P["COVER_TITLE_SIZE"]:
        errors.append(f"커버 제목 크기: {title_size} != {P['COVER_TITLE_SIZE']}")

    title_color = config.get("title_color", "").upper()
    if title_color != P["COVER_TITLE_COLOR"]:
        errors.append(f"커버 제목 색상: {title_color} != {P['COVER_TITLE_COLOR']}")

    title_y = config.get("title_y", -1)
    if title_y != P["COVER_TITLE_Y"]:
        errors.append(f"커버 Y위치: {title_y} != {P['COVER_TITLE_Y']}")

    title_font = config.get("title_font", "")
    if "Black" not in title_font:
        errors.append(f"커버 폰트: Black weight 필수 (현재: {title_font})")

    if errors:
        raise AssertionError(
            f"\n❌ v3.1 커버 검증 실패\n" +
            "\n".join(f"  - {e}" for e in errors)
        )

    return True


def assert_v31_body(config: Dict[str, Any]) -> bool:
    """본문 슬라이드 v3.1 검증"""
    P = DESIGN_PARAMS_V31
    errors = []

    title_size = config.get("title_size", 0)
    if title_size != P["BODY_TITLE_SIZE"]:
        errors.append(f"본문 제목 크기: {title_size} != {P['BODY_TITLE_SIZE']}")

    sub_size = config.get("sub_size", 0)
    if sub_size != P["BODY_SUB_SIZE"]:
        errors.append(f"본문 서브 크기: {sub_size} != {P['BODY_SUB_SIZE']}")

    title_align = config.get("title_align", "")
    if title_align != P["BODY_TITLE_ALIGN"]:
        errors.append(f"본문 정렬: {title_align} != {P['BODY_TITLE_ALIGN']}")

    title_font = config.get("title_font", "")
    if "Black" not in title_font:
        errors.append(f"본문 제목 폰트: Black weight 필수 (현재: {title_font})")

    sub_font = config.get("sub_font", "")
    if "Regular" not in sub_font and "Medium" not in sub_font:
        errors.append(f"본문 서브 폰트: Regular/Medium weight 필수 (현재: {sub_font})")

    if errors:
        raise AssertionError(
            f"\n❌ v3.1 본문 검증 실패\n" +
            "\n".join(f"  - {e}" for e in errors)
        )

    return True


def assert_v31_cta(config: Dict[str, Any]) -> bool:
    """CTA 슬라이드 v3.1 검증"""
    P = DESIGN_PARAMS_V31
    errors = []

    title_size = config.get("title_size", 0)
    if title_size != P["CTA_TITLE_SIZE"]:
        errors.append(f"CTA 제목 크기: {title_size} != {P['CTA_TITLE_SIZE']}")

    title_color = config.get("title_color", "").upper()
    if title_color != P["CTA_TITLE_COLOR"]:
        errors.append(f"CTA 제목 색상: {title_color} != {P['CTA_TITLE_COLOR']}")

    if errors:
        raise AssertionError(
            f"\n❌ v3.1 CTA 검증 실패\n" +
            "\n".join(f"  - {e}" for e in errors)
        )

    return True


def assert_v31_spacing(config: Dict[str, Any]) -> bool:
    """간격 v3.1 검증"""
    P = DESIGN_PARAMS_V31
    errors = []

    gap = config.get("gap_title_sub", 0)
    if gap < P["GAP_TITLE_SUB"]:
        errors.append(f"제목-서브 간격: {gap} < {P['GAP_TITLE_SUB']}")

    margin = config.get("bottom_margin", 0)
    if margin < P["BOTTOM_MARGIN_MIN"]:
        errors.append(f"하단 여백: {margin} < {P['BOTTOM_MARGIN_MIN']}")

    if errors:
        raise AssertionError(
            f"\n❌ v3.1 간격 검증 실패\n" +
            "\n".join(f"  - {e}" for e in errors)
        )

    return True


def assert_v31_gradient(config: Dict[str, Any]) -> bool:
    """그라데이션 v3.1 검증"""
    P = DESIGN_PARAMS_V31
    errors = []

    ratio = config.get("gradient_ratio", -1)
    if ratio != P["GRADIENT_RATIO"]:
        errors.append(f"그라데이션 비율: {ratio} != {P['GRADIENT_RATIO']}")

    alpha = config.get("gradient_alpha", -1)
    if alpha != P["GRADIENT_ALPHA"]:
        errors.append(f"그라데이션 alpha: {alpha} != {P['GRADIENT_ALPHA']}")

    if errors:
        raise AssertionError(
            f"\n❌ v3.1 그라데이션 검증 실패\n" +
            "\n".join(f"  - {e}" for e in errors)
        )

    return True


def assert_v31_safety_color(safety: str, color: str) -> bool:
    """안전도 색상 매칭 검증"""
    expected = DESIGN_PARAMS_V31["SAFETY_COLORS"]

    if safety not in expected:
        raise AssertionError(
            f"\n❌ v3.1 안전도 검증 실패\n"
            f"  - 알 수 없는 안전도: {safety} (허용: {list(expected.keys())})"
        )

    if color.upper() != expected[safety].upper():
        raise AssertionError(
            f"\n❌ v3.1 안전도 색상 불일치\n"
            f"  - {safety} → {color} != {expected[safety]}"
        )

    return True


def validate_v31_slide(
    slide_type: str,
    config: Dict[str, Any],
    image_path: Optional[str] = None,
) -> bool:
    """
    슬라이드 타입별 v3.1 전체 검증
    실패 시 → Exception → 렌더링 불가

    Args:
        slide_type: 'cover', 'body1', 'body2', 'body', 'cta'
        config: 슬라이드 렌더링 설정
        image_path: CTA일 경우 이미지 경로 (기존 v3.0 실사진 검증용)
    """
    # 공통 검증
    assert_v31_spacing(config)
    assert_v31_gradient(config)

    # 타입별 검증
    if slide_type == "cover":
        assert_v31_cover(config)

    elif slide_type in ("body", "body1", "body2"):
        assert_v31_body(config)
        if "safety" in config and "title_color" in config:
            assert_v31_safety_color(config["safety"], config["title_color"])

    elif slide_type == "cta":
        assert_v31_cta(config)
        if image_path:
            assert_cta_real_photo(image_path)

    else:
        raise ValueError(f"알 수 없는 슬라이드 타입: {slide_type}")

    print(f"✅ v3.1 STRICT PASS: {slide_type}")
    return True


# ============================================================
# 🔴 CTA 실사진 강제 검증 (가장 중요)
# ============================================================

def assert_cta_real_photo(image_path: str) -> bool:
    """
    CTA 이미지가 햇살이 실사진인지 강제 검증

    규칙:
    1. AI 생성 키워드 포함 → 죽음
    2. 음식 키워드 포함 → 죽음
    3. 'haetsali' 또는 'photo' 또는 'real' 없음 → 경고

    Args:
        image_path: CTA 이미지 경로

    Returns:
        True (검증 통과 시)

    Raises:
        ValueError: 검증 실패 시 (즉시 죽음)
    """
    path_lower = image_path.lower()
    filename = os.path.basename(image_path).lower()

    # ❌ AI 생성 이미지 키워드 (있으면 죽음)
    ai_keywords = [
        'ai', 'generated', 'flux', 'higgsfield', 'midjourney',
        'dalle', 'stable', 'diffusion', 'synthetic'
    ]

    for keyword in ai_keywords:
        if keyword in path_lower:
            raise ValueError(
                f"\n"
                f"╔══════════════════════════════════════════════════════════╗\n"
                f"║  ❌ CTA 검증 실패: AI 이미지 감지                         ║\n"
                f"╠══════════════════════════════════════════════════════════╣\n"
                f"║  파일: {filename:<46} ║\n"
                f"║  감지된 키워드: {keyword:<40} ║\n"
                f"║                                                          ║\n"
                f"║  🚫 CTA는 햇살이 실사진만 허용                            ║\n"
                f"║  📁 실사진 폴더에서 가져오세요                            ║\n"
                f"╚══════════════════════════════════════════════════════════╝\n"
            )

    # ❌ 음식 관련 키워드 (파일명에 있고 _bg가 아닌 경우 → 죽음)
    food_keywords = [
        'food', 'meal', 'dish', 'onion', 'garlic', 'apple',
        'banana', 'carrot', 'meat', 'chicken', 'beef'
    ]

    # 파일명에 음식 이름이 있으면서 cta_bg가 아닌 경우 (body 이미지 재사용 감지)
    for keyword in food_keywords:
        if keyword in filename and 'cta_bg' not in filename and '_03_bg' not in filename and '_03_clean' not in filename:
            raise ValueError(
                f"\n"
                f"╔══════════════════════════════════════════════════════════╗\n"
                f"║  ❌ CTA 검증 실패: 음식 이미지 감지                       ║\n"
                f"╠══════════════════════════════════════════════════════════╣\n"
                f"║  파일: {filename:<46} ║\n"
                f"║  감지된 키워드: {keyword:<40} ║\n"
                f"║                                                          ║\n"
                f"║  🚫 CTA는 햇살이 단독 사진만 허용                         ║\n"
                f"║  🚫 음식이 포함된 이미지 사용 금지                        ║\n"
                f"╚══════════════════════════════════════════════════════════╝\n"
            )

    # ✅ 실사진 키워드 확인 (없으면 경고, 있으면 통과)
    real_photo_keywords = ['haetsali', 'photo', 'real', 'cta_bg', '실사', '_03_bg', '_03_clean']

    has_real_keyword = any(k in path_lower for k in real_photo_keywords)

    if not has_real_keyword:
        # 경고만 (죽이지는 않음, 하지만 로그 남김)
        print(
            f"\n"
            f"⚠️ 경고: CTA 이미지 경로에 실사진 키워드 없음\n"
            f"   파일: {image_path}\n"
            f"   권장: 'haetsali', 'photo', 'real' 폴더 사용\n"
        )

    print(f"✅ [PASS] CTA 실사진 검증 통과: {filename}")
    return True


# ============================================================
# 🔴 본문 레이아웃 강제 검증
# ============================================================

def assert_body_layout(config: Dict[str, Any]) -> bool:
    """
    본문 레이아웃 설정이 규칙과 일치하는지 강제 검증

    규칙 (pasta_01 기준):
    - 제목: 100px, 중앙 정렬
    - 부제목: 56px, 중앙 정렬, 흰색

    Args:
        config: 본문 설정 딕셔너리

    Returns:
        True (검증 통과 시)

    Raises:
        AssertionError: 검증 실패 시 (즉시 죽음)
    """
    errors = []

    # 제목 크기 검증
    title_size = config.get('title_size', 0)
    if title_size != LOCKED_CONFIG.BODY_TITLE_SIZE:
        errors.append(
            f"제목 크기: {title_size}px (필수: {LOCKED_CONFIG.BODY_TITLE_SIZE}px)"
        )

    # 제목 정렬 검증
    title_align = config.get('title_align', 'left')
    if title_align != LOCKED_CONFIG.BODY_TITLE_ALIGN:
        errors.append(
            f"제목 정렬: {title_align} (필수: {LOCKED_CONFIG.BODY_TITLE_ALIGN})"
        )

    # 부제목 크기 검증
    subtitle_size = config.get('subtitle_size', 0)
    if subtitle_size != LOCKED_CONFIG.BODY_SUBTITLE_SIZE:
        errors.append(
            f"부제목 크기: {subtitle_size}px (필수: {LOCKED_CONFIG.BODY_SUBTITLE_SIZE}px)"
        )

    # 부제목 정렬 검증
    subtitle_align = config.get('subtitle_align', 'left')
    if subtitle_align != LOCKED_CONFIG.BODY_SUBTITLE_ALIGN:
        errors.append(
            f"부제목 정렬: {subtitle_align} (필수: {LOCKED_CONFIG.BODY_SUBTITLE_ALIGN})"
        )

    # 부제목 색상 검증
    subtitle_color = config.get('subtitle_color', '').upper()
    if subtitle_color and subtitle_color != LOCKED_CONFIG.BODY_SUBTITLE_COLOR:
        errors.append(
            f"부제목 색상: {subtitle_color} (필수: {LOCKED_CONFIG.BODY_SUBTITLE_COLOR})"
        )

    # 에러가 있으면 죽음
    if errors:
        error_msg = "\n".join(f"  - {e}" for e in errors)
        raise AssertionError(
            f"\n"
            f"╔══════════════════════════════════════════════════════════╗\n"
            f"║  ❌ 본문 레이아웃 검증 실패                               ║\n"
            f"╠══════════════════════════════════════════════════════════╣\n"
            f"║  위반 항목:                                              ║\n"
            f"{error_msg}\n"
            f"║                                                          ║\n"
            f"║  📏 pasta_01 기준 레이아웃을 사용하세요                   ║\n"
            f"╚══════════════════════════════════════════════════════════╝\n"
        )

    print("✅ [PASS] 본문 레이아웃 검증 통과")
    return True


# ============================================================
# 🔴 클린 이미지 강제 검증
# ============================================================

def assert_clean_image(image_path: str) -> bool:
    """
    클린 이미지(_bg.png 또는 _clean.png) 여부 강제 검증

    규칙:
    - 파일명에 '_bg' 또는 '_clean' 포함 필수
    - 파일 존재 필수

    Args:
        image_path: 베이스 이미지 경로

    Returns:
        True (검증 통과 시)

    Raises:
        ValueError: 검증 실패 시 (즉시 죽음)
    """
    filename = os.path.basename(image_path)

    # _bg 또는 _clean 검증
    if '_bg' not in filename.lower() and '_clean' not in filename.lower():
        raise ValueError(
            f"\n"
            f"╔══════════════════════════════════════════════════════════╗\n"
            f"║  ❌ 클린 이미지 검증 실패                                 ║\n"
            f"╠══════════════════════════════════════════════════════════╣\n"
            f"║  파일: {filename:<46} ║\n"
            f"║                                                          ║\n"
            f"║  🚫 _bg.png 또는 _clean.png 파일만 사용 가능             ║\n"
            f"║  🚫 텍스트 포함된 이미지 위에 덮어쓰기 금지               ║\n"
            f"╚══════════════════════════════════════════════════════════╝\n"
        )

    # 파일 존재 검증
    if not os.path.exists(image_path):
        raise FileNotFoundError(
            f"\n"
            f"╔══════════════════════════════════════════════════════════╗\n"
            f"║  ❌ 파일 없음                                             ║\n"
            f"╠══════════════════════════════════════════════════════════╣\n"
            f"║  경로: {image_path:<46} ║\n"
            f"╚══════════════════════════════════════════════════════════╝\n"
        )

    print(f"✅ [PASS] 클린 이미지 검증 통과: {filename}")
    return True


# ============================================================
# 🔴 표지 규칙 강제 검증
# ============================================================

def assert_cover_rules(config: Dict[str, Any]) -> bool:
    """
    표지 규칙 강제 검증

    규칙:
    - 텍스트 위치: 상단만
    - 하단 텍스트: 금지

    Args:
        config: 표지 설정

    Returns:
        True (검증 통과 시)

    Raises:
        ValueError: 검증 실패 시 (즉시 죽음)
    """
    # 하단 텍스트 검증
    if config.get('has_bottom_text', False):
        raise ValueError(
            f"\n"
            f"╔══════════════════════════════════════════════════════════╗\n"
            f"║  ❌ 표지 규칙 위반: 하단 텍스트 감지                      ║\n"
            f"╠══════════════════════════════════════════════════════════╣\n"
            f"║  🚫 표지는 상단에만 텍스트 허용                           ║\n"
            f"║  🚫 하단 텍스트 절대 금지                                 ║\n"
            f"╚══════════════════════════════════════════════════════════╝\n"
        )

    # 텍스트 위치 검증
    text_position = config.get('text_position', 'top')
    if text_position != 'top':
        raise ValueError(
            f"\n"
            f"╔══════════════════════════════════════════════════════════╗\n"
            f"║  ❌ 표지 규칙 위반: 텍스트 위치 오류                      ║\n"
            f"╠══════════════════════════════════════════════════════════╣\n"
            f"║  현재: {text_position:<48} ║\n"
            f"║  필수: top (상단)                                        ║\n"
            f"╚══════════════════════════════════════════════════════════╝\n"
        )

    print("✅ [PASS] 표지 규칙 검증 통과")
    return True


# ============================================================
# 🔴 이모지 제거 (렌더링 오류 방지)
# ============================================================

def strip_emoji(text: str) -> str:
    """
    이모지 강제 제거 (Pillow □ 방지)

    Args:
        text: 원본 텍스트

    Returns:
        이모지 제거된 텍스트
    """
    if not text:
        return text

    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"
        "\U0001F300-\U0001F5FF"
        "\U0001F680-\U0001F6FF"
        "\U0001F1E0-\U0001F1FF"
        "\U00002702-\U000027B0"
        "\U0001F900-\U0001F9FF"
        "\U00002600-\U000026FF"
        "\U00002700-\U000027BF"
        "]+",
        flags=re.UNICODE
    )
    cleaned = emoji_pattern.sub('', text).strip()

    if cleaned != text:
        print(f"⚠️ 이모지 제거됨: '{text}' → '{cleaned}'")

    return cleaned


# ============================================================
# 🔴 통합 검증 함수 (렌더링 전 필수 호출)
# ============================================================

def validate_before_render(
    slide_type: str,
    image_path: str,
    config: Dict[str, Any]
) -> bool:
    """
    렌더링 전 모든 규칙 강제 검증

    ⚠️ 이 함수는 모든 render 함수 시작 부분에서 호출해야 함
    ⚠️ 검증 실패 시 즉시 Exception 발생

    Args:
        slide_type: 'cover', 'body', 'cta'
        image_path: 베이스 이미지 경로
        config: 슬라이드 설정

    Returns:
        True (모든 검증 통과 시)

    Raises:
        Exception: 검증 실패 시 (즉시 죽음)
    """
    print(f"\n{'='*60}")
    print(f"🔒 강제 검증 시작: {slide_type.upper()}")
    print(f"   파일: {image_path}")
    print(f"{'='*60}")

    # 1. 클린 이미지 검증 (공통)
    assert_clean_image(image_path)

    # 2. 슬라이드별 v3.0 검증
    if slide_type == 'cover':
        assert_cover_rules(config)

    elif slide_type == 'body':
        assert_body_layout(config)

    elif slide_type == 'cta':
        assert_cta_real_photo(image_path)

    else:
        raise ValueError(f"알 수 없는 슬라이드 타입: {slide_type}")

    print("✅ v3.0 검증 통과")

    # 3. v3.1 디자인 파라미터 검증 (추가 레이어)
    v31_type = slide_type
    if slide_type == 'body':
        v31_type = 'body1'
    validate_v31_slide(v31_type, config, image_path)

    print(f"\n✅✅✅ v3.0 + v3.1 모든 검증 통과 - 렌더링 허용 ✅✅✅\n")
    return True


# ============================================================
# 테스트 함수
# ============================================================

def run_strict_tests():
    """강제 검증 테스트"""

    print("\n" + "="*60)
    print("🧪 강제 검증 테스트 시작")
    print("="*60)

    results = []

    # 테스트 1: CTA AI 이미지 → 죽어야 함
    print("\n[테스트 1] CTA AI 이미지 차단")
    try:
        assert_cta_real_photo('/content/higgsfield/onion_cta.png')
        results.append(('CTA AI 차단', False, '죽어야 하는데 통과됨'))
    except ValueError as e:
        results.append(('CTA AI 차단', True, '정상적으로 차단됨'))
        print("  → ✅ 정상 차단")

    # 테스트 2: CTA 음식 이미지 → 죽어야 함
    print("\n[테스트 2] CTA 음식 이미지 차단")
    try:
        assert_cta_real_photo('/content/onion/onion_01.png')
        results.append(('CTA 음식 차단', False, '죽어야 하는데 통과됨'))
    except ValueError as e:
        results.append(('CTA 음식 차단', True, '정상적으로 차단됨'))
        print("  → ✅ 정상 차단")

    # 테스트 3: 본문 레이아웃 틀림 → 죽어야 함
    print("\n[테스트 3] 본문 레이아웃 오류 차단")
    try:
        assert_body_layout({
            'title_size': 72,  # 틀림! 100이어야 함
            'title_align': 'left',  # 틀림! center여야 함
            'subtitle_size': 36,  # 틀림! 56이어야 함
            'subtitle_align': 'left'  # 틀림! center여야 함
        })
        results.append(('본문 레이아웃 차단', False, '죽어야 하는데 통과됨'))
    except AssertionError as e:
        results.append(('본문 레이아웃 차단', True, '정상적으로 차단됨'))
        print("  → ✅ 정상 차단")

    # 테스트 4: 클린 이미지 아님 → 죽어야 함
    print("\n[테스트 4] 비클린 이미지 차단")
    try:
        assert_clean_image('/content/onion/onion_01.png')  # _bg 없음
        results.append(('클린 이미지 차단', False, '죽어야 하는데 통과됨'))
    except ValueError as e:
        results.append(('클린 이미지 차단', True, '정상적으로 차단됨'))
        print("  → ✅ 정상 차단")

    # 테스트 5: 표지 하단 텍스트 → 죽어야 함
    print("\n[테스트 5] 표지 하단 텍스트 차단")
    try:
        assert_cover_rules({'has_bottom_text': True})
        results.append(('표지 하단 차단', False, '죽어야 하는데 통과됨'))
    except ValueError as e:
        results.append(('표지 하단 차단', True, '정상적으로 차단됨'))
        print("  → ✅ 정상 차단")

    # 테스트 6: 이모지 제거
    print("\n[테스트 6] 이모지 제거")
    original = "티오황산염 독성 🚫"
    cleaned = strip_emoji(original)
    if cleaned == "티오황산염 독성":
        results.append(('이모지 제거', True, '정상 제거'))
        print("  → ✅ 정상 제거")
    else:
        results.append(('이모지 제거', False, f'제거 실패: {cleaned}'))

    # ============================
    # v3.1 테스트
    # ============================

    # 테스트 7: v3.1 커버 - 잘못된 사이즈 → 죽어야 함
    print("\n[테스트 7] v3.1 커버 사이즈 위반 차단")
    try:
        assert_v31_cover({
            "title_size": 100,   # 틀림! 114여야 함
            "title_color": "#FFFFFF",
            "title_y": 100,
            "title_font": "NotoSansCJK-Black.ttc",
        })
        results.append(('v3.1 커버 차단', False, '죽어야 하는데 통과됨'))
    except AssertionError:
        results.append(('v3.1 커버 차단', True, '정상적으로 차단됨'))
        print("  → ✅ 정상 차단")

    # 테스트 8: v3.1 커버 - 올바른 값 → 통과
    print("\n[테스트 8] v3.1 커버 정상 통과")
    try:
        assert_v31_cover({
            "title_size": 114,
            "title_color": "#FFFFFF",
            "title_y": 100,
            "title_font": "NotoSansCJK-Black.ttc",
        })
        results.append(('v3.1 커버 통과', True, '정상 통과'))
        print("  → ✅ 정상 통과")
    except AssertionError as e:
        results.append(('v3.1 커버 통과', False, f'통과해야 하는데 실패: {e}'))

    # 테스트 9: v3.1 본문 - 잘못된 폰트 → 죽어야 함
    print("\n[테스트 9] v3.1 본문 폰트 위반 차단")
    try:
        assert_v31_body({
            "title_size": 88,
            "sub_size": 44,
            "title_align": "center",
            "title_font": "NotoSansCJK-Regular.ttc",  # 틀림! Black이어야 함
            "sub_font": "NotoSansCJK-Regular.ttc",
        })
        results.append(('v3.1 본문 폰트 차단', False, '죽어야 하는데 통과됨'))
    except AssertionError:
        results.append(('v3.1 본문 폰트 차단', True, '정상적으로 차단됨'))
        print("  → ✅ 정상 차단")

    # 테스트 10: v3.1 CTA - 잘못된 색상 → 죽어야 함
    print("\n[테스트 10] v3.1 CTA 색상 위반 차단")
    try:
        assert_v31_cta({
            "title_size": 48,
            "title_color": "#FFFFFF",  # 틀림! #FFD93D여야 함
        })
        results.append(('v3.1 CTA 색상 차단', False, '죽어야 하는데 통과됨'))
    except AssertionError:
        results.append(('v3.1 CTA 색상 차단', True, '정상적으로 차단됨'))
        print("  → ✅ 정상 차단")

    # 테스트 11: v3.1 간격 부족 → 죽어야 함
    print("\n[테스트 11] v3.1 간격 위반 차단")
    try:
        assert_v31_spacing({
            "gap_title_sub": 30,    # 틀림! >= 48
            "bottom_margin": 50,    # 틀림! >= 72
        })
        results.append(('v3.1 간격 차단', False, '죽어야 하는데 통과됨'))
    except AssertionError:
        results.append(('v3.1 간격 차단', True, '정상적으로 차단됨'))
        print("  → ✅ 정상 차단")

    # 테스트 12: v3.1 그라데이션 불일치 → 죽어야 함
    print("\n[테스트 12] v3.1 그라데이션 위반 차단")
    try:
        assert_v31_gradient({
            "gradient_ratio": 0.50,  # 틀림! 0.38
            "gradient_alpha": 200,   # 틀림! 180
        })
        results.append(('v3.1 그라데이션 차단', False, '죽어야 하는데 통과됨'))
    except AssertionError:
        results.append(('v3.1 그라데이션 차단', True, '정상적으로 차단됨'))
        print("  → ✅ 정상 차단")

    # 테스트 13: v3.1 안전도 색상 불일치 → 죽어야 함
    print("\n[테스트 13] v3.1 안전도 색상 불일치 차단")
    try:
        assert_v31_safety_color("safe", "#FF0000")  # 틀림! #4CAF50이어야 함
        results.append(('v3.1 안전도 차단', False, '죽어야 하는데 통과됨'))
    except AssertionError:
        results.append(('v3.1 안전도 차단', True, '정상적으로 차단됨'))
        print("  → ✅ 정상 차단")

    # 테스트 14: v3.1 안전도 색상 - 4가지 모두 정상 통과
    print("\n[테스트 14] v3.1 안전도 4등급 정상 통과")
    try:
        assert_v31_safety_color("safe", "#4CAF50")
        assert_v31_safety_color("caution", "#FFD93D")
        assert_v31_safety_color("danger", "#FF6B6B")
        assert_v31_safety_color("forbidden", "#FF5252")
        results.append(('v3.1 안전도 4등급', True, '4/4 통과'))
        print("  → ✅ 4등급 모두 통과")
    except AssertionError as e:
        results.append(('v3.1 안전도 4등급', False, str(e)))

    # 테스트 15: validate_v31_slide 통합 - 정상 cover
    print("\n[테스트 15] v3.1 통합 검증 - 커버 정상")
    try:
        validate_v31_slide("cover", {
            "title_size": 114,
            "title_color": "#FFFFFF",
            "title_y": 100,
            "title_font": "NotoSansCJK-Black.ttc",
            "gap_title_sub": 48,
            "bottom_margin": 72,
            "gradient_ratio": 0.38,
            "gradient_alpha": 180,
        })
        results.append(('v3.1 통합 커버', True, '정상 통과'))
        print("  → ✅ 정상 통과")
    except (AssertionError, ValueError) as e:
        results.append(('v3.1 통합 커버', False, str(e)))

    # 결과 요약
    print("\n" + "="*60)
    print("📊 테스트 결과")
    print("="*60)

    passed = sum(1 for _, result, _ in results if result)

    for name, result, note in results:
        status = "✅" if result else "❌"
        print(f"  {status} {name}: {note}")

    print(f"\n총 {len(results)}개 중 {passed}개 통과")

    if passed == len(results):
        print("\n🎉 모든 차단 테스트 통과!")
        return True
    else:
        print("\n⚠️ 일부 테스트 실패 - 코드 확인 필요")
        return False


if __name__ == '__main__':
    run_strict_tests()
