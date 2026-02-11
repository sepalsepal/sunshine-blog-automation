#!/usr/bin/env python3
"""
pipeline/caption_generator.py - §22.11.2 캡션 템플릿 분기
v3.1: ENUM 기반 분기 (문자열 조건문 금지)

사용법:
    from pipeline.caption_generator import get_caption_template, generate_caption

    template = get_caption_template(Safety.FORBIDDEN)
    caption = generate_caption(food_id=127, safety=Safety.FORBIDDEN)
"""

from typing import Dict, List, Optional, Callable
from dataclasses import dataclass
from enum import Enum

# Safety ENUM import
import sys
from pathlib import Path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.enums.safety import Safety, get_safety, SafetyError


# =============================================================================
# §22.11.2 CAPTION_TEMPLATE_MAP - ENUM 기반 분기
# =============================================================================

@dataclass
class SlideTemplate:
    """슬라이드 템플릿 정의"""
    slide_num: int
    header: str
    content_type: str  # 'text', 'list', 'table', 'warning'
    required_keywords: List[str]


@dataclass
class CaptionTemplate:
    """캡션 템플릿 정의"""
    safety: Safety
    slides: List[SlideTemplate]
    emoji_prefix: str
    tone: str
    forbidden_keywords: List[str]


# SAFE/CAUTION 공통 템플릿
SAFE_CAUTION_SLIDES = [
    SlideTemplate(1, "[이미지 1번: 표지]", "text", []),
    SlideTemplate(2, "[이미지 2번: 음식 사진]", "text", ["강아지"]),
    SlideTemplate(3, "[이미지 3번: 영양 정보]", "list", ["영양", "비타민"]),
    SlideTemplate(4, "[이미지 4번: 급여 방법]", "text", ["급여", "방법"]),
    SlideTemplate(5, "[이미지 5번: 급여량 표]", "table", ["소형견", "중형견", "대형견"]),
    SlideTemplate(6, "[이미지 6번: 주의사항]", "list", ["주의", "확인"]),
    SlideTemplate(7, "[이미지 7번: 조리 방법]", "text", ["조리", "익혀"]),
    SlideTemplate(8, "[이미지 8번: 햇살이 실사]", "text", ["댓글", "팔로우"]),
]

# FORBIDDEN 전용 템플릿
FORBIDDEN_SLIDES = [
    SlideTemplate(1, "[이미지 1번: 표지]", "text", []),
    SlideTemplate(2, "[이미지 2번: 음식 사진]", "warning", ["위험", "금지"]),
    SlideTemplate(3, "[이미지 3번: 위험 성분]", "list", ["독성", "성분", "위험"]),
    SlideTemplate(4, "[이미지 4번: 절대 급여 금지]", "warning", ["절대", "금지", "0g"]),
    SlideTemplate(5, "[이미지 5번: 급여량 표]", "table", ["0g", "금지"]),
    SlideTemplate(6, "[이미지 6번: 응급 대처법]", "list", ["응급", "병원", "대처"]),
    SlideTemplate(7, "[이미지 7번: 수의사 상담]", "text", ["수의사", "상담"]),
    SlideTemplate(8, "[이미지 8번: 햇살이 실사]", "text", ["댓글", "같은 보호자"]),
]

# 금지 키워드 (FORBIDDEN에서 사용 불가)
FORBIDDEN_BLOCKED_KEYWORDS = [
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
    "영양 정보",
    "영양정보",
]


# =============================================================================
# §22.11.2 CAPTION_TEMPLATE_MAP 딕셔너리
# =============================================================================

CAPTION_TEMPLATE_MAP: Dict[Safety, CaptionTemplate] = {
    Safety.SAFE: CaptionTemplate(
        safety=Safety.SAFE,
        slides=SAFE_CAUTION_SLIDES,
        emoji_prefix="",  # 일반
        tone="friendly",
        forbidden_keywords=[],
    ),
    Safety.CAUTION: CaptionTemplate(
        safety=Safety.CAUTION,
        slides=SAFE_CAUTION_SLIDES,
        emoji_prefix="",  # 주의
        tone="careful",
        forbidden_keywords=[],
    ),
    Safety.FORBIDDEN: CaptionTemplate(
        safety=Safety.FORBIDDEN,
        slides=FORBIDDEN_SLIDES,
        emoji_prefix="",  # 위험 (🔴 대신 텍스트로)
        tone="warning",
        forbidden_keywords=FORBIDDEN_BLOCKED_KEYWORDS,
    ),
}


# =============================================================================
# 템플릿 조회 함수 (ENUM만 허용)
# =============================================================================

def get_caption_template(safety: Safety) -> CaptionTemplate:
    """
    §22.11.2: ENUM 기반 템플릿 조회

    Args:
        safety: Safety ENUM (문자열 금지)

    Returns:
        CaptionTemplate

    Raises:
        TypeError: Safety ENUM이 아닌 경우
    """
    # ENUM 타입 강제 (문자열 조건문 금지)
    if not isinstance(safety, Safety):
        raise TypeError(
            f"§22.11.2 위반: Safety ENUM만 허용\n"
            f"  받은 타입: {type(safety)}\n"
            f"  받은 값: {safety}\n"
            f"  올바른 사용: get_caption_template(Safety.FORBIDDEN)"
        )

    return CAPTION_TEMPLATE_MAP[safety]


def get_slide_headers(safety: Safety) -> Dict[int, str]:
    """
    안전도별 슬라이드 헤더 반환

    Returns:
        {slide_num: header_text}
    """
    template = get_caption_template(safety)
    return {slide.slide_num: slide.header for slide in template.slides}


def get_forbidden_keywords(safety: Safety) -> List[str]:
    """
    해당 안전도에서 금지된 키워드 반환
    """
    template = get_caption_template(safety)
    return template.forbidden_keywords


# =============================================================================
# 캡션 생성 함수
# =============================================================================

def generate_caption_structure(
    food_id: int,
    safety: Safety,
    food_name: str,
    content_data: Dict,
) -> str:
    """
    §22.11.2: 안전도별 캡션 구조 생성

    Args:
        food_id: 음식 ID
        safety: Safety ENUM
        food_name: 음식 이름
        content_data: 콘텐츠 데이터 (nutrients, dosages 등)

    Returns:
        캡션 텍스트
    """
    template = get_caption_template(safety)
    lines = []

    for slide in template.slides:
        lines.append(slide.header)

        if slide.slide_num == 1:
            # 표지
            lines.append(f"안녕하세요, 11살 골든리트리버 햇살이 엄마예요.")
            if safety == Safety.FORBIDDEN:
                lines.append(f"오늘은 좀 무거운 이야기를 해야 할 것 같아요.")
            else:
                lines.append(f"오늘은 {food_name}에 대해 알아볼게요.")

        elif slide.slide_num == 2:
            # 음식 사진/경고
            if safety == Safety.FORBIDDEN:
                lines.append(f"## 🔴 {food_name}, 강아지에게 줘도 될까요?")
                lines.append("❌ 절대 급여 금지!")
            else:
                lines.append(f"## {food_name}, 강아지에게 줘도 될까요?")

        # 나머지 슬라이드는 content_data에서 채움
        lines.append("")  # 빈 줄

    # CTA 및 해시태그
    lines.append("같은 보호자로서 우리 아이들 건강 지키는 게 제일 중요하잖아요.")
    lines.append("궁금한 점 있으시면 댓글로 남겨주세요!")
    lines.append("")
    lines.append(f"ℹ️ 일부 이미지는 AI로 생성되었습니다.")
    lines.append(f"#강아지{food_name} #반려견 #펫스타그램")

    return "\n".join(lines)


# =============================================================================
# 테스트
# =============================================================================

def test_template_map():
    """템플릿 맵 테스트"""
    print("=" * 60)
    print("§22.11.2 CAPTION_TEMPLATE_MAP 테스트")
    print("=" * 60)

    results = []

    # 테스트 1: ENUM으로 조회
    print("\n[테스트 1] ENUM으로 템플릿 조회")
    for safety in Safety:
        template = get_caption_template(safety)
        print(f"  {safety.value}: {len(template.slides)}개 슬라이드")
        results.append((f"ENUM {safety.value}", True))

    # 테스트 2: 문자열로 조회 시도 → 에러
    print("\n[테스트 2] 문자열 조회 차단")
    try:
        get_caption_template("FORBIDDEN")  # 문자열 금지
        results.append(("문자열 차단", False))
        print("  ❌ 차단 실패")
    except TypeError:
        results.append(("문자열 차단", True))
        print("  ✅ 정상 차단")

    # 테스트 3: FORBIDDEN 템플릿 검증
    print("\n[테스트 3] FORBIDDEN 템플릿 구조")
    template = get_caption_template(Safety.FORBIDDEN)
    expected_headers = ["위험 성분", "절대 급여 금지", "응급 대처법", "수의사 상담"]

    found = 0
    for slide in template.slides:
        for expected in expected_headers:
            if expected in slide.header:
                print(f"  ✅ 슬라이드 {slide.slide_num}: {slide.header}")
                found += 1

    if found == len(expected_headers):
        results.append(("FORBIDDEN 구조", True))
    else:
        results.append(("FORBIDDEN 구조", False))

    # 테스트 4: 금지 키워드 확인
    print("\n[테스트 4] FORBIDDEN 금지 키워드")
    keywords = get_forbidden_keywords(Safety.FORBIDDEN)
    print(f"  금지 키워드 {len(keywords)}개: {keywords[:3]}...")

    if "급여 방법" in keywords and "조리 방법" in keywords:
        results.append(("금지 키워드", True))
        print("  ✅ 핵심 금지 키워드 포함")
    else:
        results.append(("금지 키워드", False))

    # 결과 요약
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in results if ok)
    print(f"결과: {passed}/{len(results)} 통과")

    return all(ok for _, ok in results)


if __name__ == "__main__":
    test_template_map()
