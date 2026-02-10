"""
validators_v32_cta_patch.py
CTA 텍스트 규칙 강제 검증 - v3.2 실험 패치

⚠️ 이 파일은 v3.2-experimental 분기용입니다.
   PD 승인 후 validators_strict.py에 병합하세요.

추가되는 검증 (3개):
- assert_no_emoji: 이모지/특수문자 사용 금지
- assert_cta_title_color: CTA 제목 색상 #FFD93D 강제
- assert_cta_text_content: CTA 텍스트 내용 화이트리스트 검증
"""

import re
from typing import Dict, Any, List, Tuple

# ============================================================
# CTA 텍스트 규칙 정의 (단일 진실원)
# ============================================================

CTA_RULES = {
    # 색상 규칙
    "title_color": "#FFD93D",      # 노란색 (CTA 제목)
    "subtitle_color": "#FFFFFF",   # 흰색 (서브텍스트)
    
    # 폰트 규칙
    "title_font_size": 48,
    "subtitle_font_size": 32,
    "font_family": "NotoSansCJK",
    
    # 금지 문자 패턴 (이모지, 특수문자)
    "forbidden_chars_pattern": r'[^\w\s가-힣a-zA-Z0-9.,!?&\-:;\'\"()%]',
    
    # 허용된 CTA 텍스트 (화이트리스트)
    "allowed_titles": [
        "저장 & 공유",
        "저장 필수!",
        "꼭 저장하세요!",
        "공유해주세요!",
        "팔로우 & 저장",
    ],
    
    "allowed_subtitles": [
        "주변 견주에게 알려주세요!",
        "우리 아이 최애 간식은? 댓글로 알려주세요!",
        "다른 견주분들께도 공유해주세요!",
        "저장해두면 나중에 유용해요!",
        "팔로우하고 새 정보 받아보세요!",
    ],
}

# ============================================================
# 검증 함수들
# ============================================================

def assert_no_emoji(text: str, context: str = "") -> Tuple[bool, str]:
    """
    이모지/특수문자 사용 금지 검증
    
    Args:
        text: 검사할 텍스트
        context: 오류 메시지용 컨텍스트 (예: "CTA 제목")
    
    Returns:
        (통과여부, 오류메시지)
    """
    # 이모지 패턴 (유니코드 범위)
    emoji_pattern = re.compile(
        "["
        "\U0001F600-\U0001F64F"  # 이모티콘
        "\U0001F300-\U0001F5FF"  # 기호 & 픽토그램
        "\U0001F680-\U0001F6FF"  # 교통 & 지도
        "\U0001F1E0-\U0001F1FF"  # 국기
        "\U00002702-\U000027B0"  # 딩뱃
        "\U000024C2-\U0001F251"  # 기타
        "\U0001F900-\U0001F9FF"  # 보충 기호
        "\U0001FA00-\U0001FA6F"  # 체스 기호
        "\U0001FA70-\U0001FAFF"  # 확장-A 기호
        "\U00002600-\U000026FF"  # 기타 기호
        "\U00002700-\U000027BF"  # 딩뱃
        "]+",
        flags=re.UNICODE
    )
    
    # 금지 특수문자 패턴
    forbidden_pattern = re.compile(CTA_RULES["forbidden_chars_pattern"])
    
    # 이모지 검사
    emoji_found = emoji_pattern.findall(text)
    if emoji_found:
        return False, f"[{context}] 이모지 사용 금지: {emoji_found}"
    
    # 특수문자 검사
    forbidden_found = forbidden_pattern.findall(text)
    if forbidden_found:
        # 일부 허용 문자 필터링 (&, !, ? 등은 허용)
        truly_forbidden = [c for c in forbidden_found if c not in ['&', '!', '?', '.', ',', ':', ';', '-', '(', ')', '%', "'", '"']]
        if truly_forbidden:
            return False, f"[{context}] 금지된 특수문자: {truly_forbidden}"
    
    return True, ""


def assert_cta_title_color(color_hex: str) -> Tuple[bool, str]:
    """
    CTA 제목 색상 검증 - #FFD93D 강제
    
    Args:
        color_hex: 사용된 색상 코드 (예: "#FFD93D")
    
    Returns:
        (통과여부, 오류메시지)
    """
    expected = CTA_RULES["title_color"].upper()
    actual = color_hex.upper().strip()
    
    if actual != expected:
        return False, f"CTA 제목 색상 위반: 사용={actual}, 규칙={expected}"
    
    return True, ""


def assert_cta_subtitle_color(color_hex: str) -> Tuple[bool, str]:
    """
    CTA 서브텍스트 색상 검증 - #FFFFFF 강제
    """
    expected = CTA_RULES["subtitle_color"].upper()
    actual = color_hex.upper().strip()
    
    if actual != expected:
        return False, f"CTA 서브텍스트 색상 위반: 사용={actual}, 규칙={expected}"
    
    return True, ""


def assert_cta_text_content(title: str, subtitle: str, strict: bool = False) -> Tuple[bool, str]:
    """
    CTA 텍스트 내용 검증 (화이트리스트)
    
    Args:
        title: CTA 제목 텍스트
        subtitle: CTA 서브텍스트
        strict: True면 화이트리스트에 없는 텍스트 거부
    
    Returns:
        (통과여부, 오류메시지)
    """
    errors = []
    
    # 제목 검증
    if strict and title not in CTA_RULES["allowed_titles"]:
        errors.append(f"CTA 제목 '{title}'이 허용 목록에 없음")
    
    # 서브텍스트 검증
    if strict and subtitle not in CTA_RULES["allowed_subtitles"]:
        errors.append(f"CTA 서브텍스트가 허용 목록에 없음")
    
    # 이모지 검증 (항상)
    title_ok, title_err = assert_no_emoji(title, "CTA 제목")
    if not title_ok:
        errors.append(title_err)
    
    subtitle_ok, subtitle_err = assert_no_emoji(subtitle, "CTA 서브텍스트")
    if not subtitle_ok:
        errors.append(subtitle_err)
    
    if errors:
        return False, "; ".join(errors)
    
    return True, ""


# ============================================================
# 통합 검증 함수
# ============================================================

def validate_cta_slide(metadata: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    CTA 슬라이드 전체 검증
    
    Args:
        metadata: CTA 슬라이드 메타데이터
            {
                "title": "저장 & 공유",
                "title_color": "#FFD93D",
                "subtitle": "주변 견주에게 알려주세요!",
                "subtitle_color": "#FFFFFF",
            }
    
    Returns:
        (전체통과여부, 오류목록)
    """
    errors = []
    
    # 1. 제목 색상 검증
    if "title_color" in metadata:
        ok, err = assert_cta_title_color(metadata["title_color"])
        if not ok:
            errors.append(err)
    
    # 2. 서브텍스트 색상 검증
    if "subtitle_color" in metadata:
        ok, err = assert_cta_subtitle_color(metadata["subtitle_color"])
        if not ok:
            errors.append(err)
    
    # 3. 텍스트 내용 검증 (이모지 포함)
    title = metadata.get("title", "")
    subtitle = metadata.get("subtitle", "")
    ok, err = assert_cta_text_content(title, subtitle, strict=False)
    if not ok:
        errors.append(err)
    
    return len(errors) == 0, errors


# ============================================================
# 렌더링 전 강제 검증 (Exception 발생)
# ============================================================

def enforce_cta_rules(metadata: Dict[str, Any]) -> None:
    """
    CTA 규칙 강제 - 위반 시 Exception 발생으로 렌더링 중단
    
    사용법:
        try:
            enforce_cta_rules(cta_metadata)
            render_cta_slide(...)  # 검증 통과 시에만 실행
        except ValueError as e:
            print(f"CTA 규칙 위반: {e}")
    """
    passed, errors = validate_cta_slide(metadata)
    
    if not passed:
        error_msg = "\n".join([f"  ❌ {e}" for e in errors])
        raise ValueError(
            f"🚫 CTA 규칙 위반으로 렌더링 중단\n"
            f"{error_msg}\n"
            f"\n"
            f"규칙 확인: CTA_RULES in validators_v32_cta_patch.py"
        )


# ============================================================
# 테스트
# ============================================================

if __name__ == "__main__":
    print("=" * 60)
    print("CTA 텍스트 규칙 검증 테스트")
    print("=" * 60)
    
    # 테스트 케이스 1: 정상
    test1 = {
        "title": "저장 & 공유",
        "title_color": "#FFD93D",
        "subtitle": "주변 견주에게 알려주세요!",
        "subtitle_color": "#FFFFFF",
    }
    print("\n[테스트 1] 정상 케이스")
    passed, errors = validate_cta_slide(test1)
    print(f"  결과: {'✅ PASS' if passed else '❌ FAIL'}")
    
    # 테스트 케이스 2: 이모지 포함 (실패해야 함)
    test2 = {
        "title": "저장 필수! 📌",
        "title_color": "#FFD93D",
        "subtitle": "우리 아이 최애 간식은? 댓글로 알려주세요!",
        "subtitle_color": "#FFFFFF",
    }
    print("\n[테스트 2] 이모지 포함")
    passed, errors = validate_cta_slide(test2)
    print(f"  결과: {'✅ PASS' if passed else '❌ FAIL'}")
    if errors:
        for e in errors:
            print(f"  → {e}")
    
    # 테스트 케이스 3: 잘못된 색상 (실패해야 함)
    test3 = {
        "title": "저장 필수!",
        "title_color": "#FFFFFF",  # 흰색 = 위반
        "subtitle": "우리 아이 최애 간식은? 댓글로 알려주세요!",
        "subtitle_color": "#FFFFFF",
    }
    print("\n[테스트 3] 제목 색상 위반")
    passed, errors = validate_cta_slide(test3)
    print(f"  결과: {'✅ PASS' if passed else '❌ FAIL'}")
    if errors:
        for e in errors:
            print(f"  → {e}")
    
    # 테스트 케이스 4: enforce 테스트
    print("\n[테스트 4] enforce_cta_rules 예외 발생 테스트")
    try:
        enforce_cta_rules(test3)
        print("  ⚠️ 예외가 발생하지 않음 (문제)")
    except ValueError as e:
        print(f"  ✅ 예외 정상 발생:")
        print(f"  {e}")
