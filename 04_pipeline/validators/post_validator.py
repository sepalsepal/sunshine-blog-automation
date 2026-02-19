#!/usr/bin/env python3
"""
pipeline/validators/post_validator.py - §22.12~13 생성 후 검증기
v3.1: 구조 ID 일치 검증, 금지 키워드 검출 강화

사용법:
    from pipeline.validators.post_validator import validate_after_generation

    result = validate_after_generation(
        food_id=127,
        safety=Safety.FORBIDDEN,
        caption="...",
        expected_structure_id="127_FORBIDDEN_v3.1_20260211"
    )
"""

import re
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime

import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.enums.safety import Safety, get_safety, SafetyError


# =============================================================================
# 설정
# =============================================================================

LOGS_DIR = PROJECT_ROOT / "logs" / "validation"
VERSION = "v3.1"
TEMPLATE_VERSION = "v3.1"


# =============================================================================
# A-1: 템플릿 버전 검증
# =============================================================================

class VersionMismatchError(Exception):
    """버전 불일치 예외"""
    pass


def validate_version(
    image_version: str,
    caption_version: str,
    validator_version: str,
) -> bool:
    """
    A-1: 템플릿 버전 3중 검증

    Args:
        image_version: 이미지 템플릿 버전
        caption_version: 캡션 템플릿 버전
        validator_version: 검증기 버전

    Returns:
        True if all match

    Raises:
        VersionMismatchError: 버전 불일치 시
    """
    if not (image_version == caption_version == validator_version == TEMPLATE_VERSION):
        raise VersionMismatchError(
            f"버전 불일치: image={image_version}, caption={caption_version}, "
            f"validator={validator_version}, expected={TEMPLATE_VERSION}"
        )
    return True


# =============================================================================
# A-3: 구조 ID 3중 검증
# =============================================================================

def validate_structure_ids(
    image_id: str,
    caption_id: str,
    validator_id: str,
) -> Dict:
    """
    A-3: 구조 ID 3중 검증

    Args:
        image_id: 이미지 구조 ID
        caption_id: 캡션 구조 ID
        validator_id: 검증기 구조 ID

    Returns:
        {"status": "PASS"|"FAIL", "violations": [...]}
    """
    if not (image_id == caption_id == validator_id):
        return {
            "status": "FAIL",
            "violations": [
                f"구조 ID 불일치: img={image_id}, cap={caption_id}, val={validator_id}"
            ]
        }
    return {"status": "PASS", "violations": []}


# =============================================================================
# §22.12 금지 키워드 정의 (강화)
# =============================================================================

# FORBIDDEN에서 절대 금지
FORBIDDEN_BLOCKED_KEYWORDS = [
    "급여 방법",
    "조리 방법",
    "권장량",
    "좋아요",
    "맛있어요",
    "맛있게",
    "체중별 급여량",
    "소형견 급여량",
    "중형견 급여량",
    "대형견 급여량",
    "영양 가득",
    "건강에 좋",
    "건강에좋",
    "드셔도 됩니다",
    "먹여도 됩니다",
    "먹여도 돼요",
    "줘도 돼요",
    "줘도 됩니다",
    "영양 정보",
    "영양정보",
    "영양소",
    "추천 급여량",
    "하루 권장량",
]

# FORBIDDEN에서 금지되는 헤더 패턴
FORBIDDEN_BLOCKED_HEADERS = [
    "[이미지 3번: 영양 정보]",
    "[이미지 3번: 영양정보]",
    "[이미지 4번: 급여 방법]",
    "[이미지 6번: 조리 방법]",
    "[이미지 7번: 조리 방법]",
]

# FORBIDDEN 필수 헤더
FORBIDDEN_REQUIRED_HEADERS = {
    3: "[이미지 3번: 위험 성분]",
    4: "[이미지 4번: 절대 급여 금지]",
    6: "[이미지 6번: 응급 대처법]",
    7: "[이미지 7번: 수의사 상담]",
}

# FORBIDDEN 필수 키워드 (하나 이상 포함 필요)
FORBIDDEN_REQUIRED_KEYWORDS = {
    "danger_warning": ["위험", "금지", "절대", "독성", "치명"],
    "emergency": ["응급", "병원", "대처", "증상"],
    "vet": ["수의사", "상담", "진료"],
    "zero_amount": ["0g", "절대 금지"],
}

# CTA 필수 문구
CTA_REQUIRED = [
    "같은 보호자",
    "댓글",
]

# AI 공개 필수
AI_DISCLOSURE = "AI로 생성"


# =============================================================================
# PostValidationError
# =============================================================================

class PostValidationError(Exception):
    """생성 후 검증 실패"""
    pass


# =============================================================================
# §22.13 구조 ID
# =============================================================================

def generate_structure_id(food_id: int, safety: Safety) -> str:
    """
    §22.13.1 구조 ID 생성

    형식: {food_id}_{safety}_{version}_{date}
    """
    date_str = datetime.now().strftime("%Y%m%d")
    return f"{food_id}_{safety.value}_{VERSION}_{date_str}"


def parse_structure_id(structure_id: str) -> Optional[Dict]:
    """
    구조 ID 파싱

    Returns:
        {"food_id": int, "safety": str, "version": str, "date": str}
    """
    pattern = r"^(\d+)_(SAFE|CAUTION|FORBIDDEN)_(v[\d.]+)_(\d{8})$"
    match = re.match(pattern, structure_id)

    if not match:
        return None

    return {
        "food_id": int(match.group(1)),
        "safety": match.group(2),
        "version": match.group(3),
        "date": match.group(4),
    }


# =============================================================================
# 검증 결과
# =============================================================================

@dataclass
class PostValidationResult:
    """검증 결과"""
    valid: bool
    food_id: int
    safety: Safety
    structure_id: str
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    keyword_violations: List[str] = field(default_factory=list)
    header_violations: List[str] = field(default_factory=list)
    missing_requirements: List[str] = field(default_factory=list)
    timestamp: str = ""


# =============================================================================
# §22.12 금지 키워드 검증
# =============================================================================

def check_forbidden_keywords(
    caption: str,
    safety: Safety,
) -> Tuple[bool, List[str]]:
    """
    §22.12: FORBIDDEN 캡션 금지 키워드 검출

    Returns:
        (valid, violations)
    """
    if safety != Safety.FORBIDDEN:
        return True, []

    violations = []

    # 금지 키워드 검사
    for keyword in FORBIDDEN_BLOCKED_KEYWORDS:
        if keyword in caption:
            violations.append(f"금지 키워드: '{keyword}'")

    # 금지 헤더 패턴 검사
    for header in FORBIDDEN_BLOCKED_HEADERS:
        if header in caption:
            violations.append(f"금지 헤더: '{header}'")

    return len(violations) == 0, violations


def check_required_headers(
    caption: str,
    safety: Safety,
) -> Tuple[bool, List[str]]:
    """
    §22.11.2: FORBIDDEN 필수 헤더 확인

    Returns:
        (valid, missing)
    """
    if safety != Safety.FORBIDDEN:
        return True, []

    missing = []

    for slide_num, header in FORBIDDEN_REQUIRED_HEADERS.items():
        if header not in caption:
            # 대안 확인 (슬라이드 번호 + 키워드)
            alt_patterns = {
                3: ["위험", "독성", "성분"],
                4: ["금지", "절대"],
                6: ["응급", "대처", "병원"],
                7: ["수의사", "상담"],
            }

            keywords = alt_patterns.get(slide_num, [])
            has_alt = any(kw in caption for kw in keywords)

            if not has_alt:
                missing.append(f"슬라이드 {slide_num}: {header} 또는 관련 키워드 필요")

    return len(missing) == 0, missing


def check_required_keywords(
    caption: str,
    safety: Safety,
) -> Tuple[bool, List[str]]:
    """
    FORBIDDEN 필수 키워드 확인

    Returns:
        (valid, missing_categories)
    """
    if safety != Safety.FORBIDDEN:
        return True, []

    missing = []

    for category, keywords in FORBIDDEN_REQUIRED_KEYWORDS.items():
        has_any = any(kw in caption for kw in keywords)
        if not has_any:
            missing.append(f"{category}: {keywords} 중 하나 필요")

    return len(missing) == 0, missing


def check_cta_and_disclosure(caption: str) -> Tuple[bool, List[str]]:
    """
    CTA 및 AI 공개 확인

    Returns:
        (valid, missing)
    """
    missing = []

    # CTA 필수 문구
    for req in CTA_REQUIRED:
        if req not in caption:
            missing.append(f"CTA 필수: '{req}'")

    # AI 공개
    if AI_DISCLOSURE not in caption:
        missing.append(f"AI 공개 필수: '{AI_DISCLOSURE}'")

    return len(missing) == 0, missing


# =============================================================================
# §22.13 구조 ID 일치 검증
# =============================================================================

def validate_structure_id_match(
    expected_id: str,
    actual_safety: Safety,
    actual_food_id: int,
) -> Tuple[bool, List[str]]:
    """
    §22.13: 구조 ID 일치 검증

    Returns:
        (valid, errors)
    """
    parsed = parse_structure_id(expected_id)

    if not parsed:
        return False, [f"구조 ID 형식 오류: '{expected_id}'"]

    errors = []

    if parsed["food_id"] != actual_food_id:
        errors.append(f"Food ID 불일치: {parsed['food_id']} != {actual_food_id}")

    if parsed["safety"] != actual_safety.value:
        errors.append(f"Safety 불일치: {parsed['safety']} != {actual_safety.value}")

    return len(errors) == 0, errors


# =============================================================================
# 통합 검증 함수
# =============================================================================

def validate_after_generation(
    food_id: int,
    safety: Union[str, Safety],
    caption: str,
    expected_structure_id: Optional[str] = None,
    strict: bool = True,
) -> PostValidationResult:
    """
    §22.12~13 생성 후 전체 검증

    Args:
        food_id: 음식 ID
        safety: 안전도
        caption: 생성된 캡션
        expected_structure_id: 예상 구조 ID (없으면 자동 생성)
        strict: True면 에러 시 예외 발생

    Returns:
        PostValidationResult

    Raises:
        PostValidationError: strict=True이고 검증 실패 시
    """
    # Safety ENUM 변환
    if isinstance(safety, str):
        safety = get_safety(safety)

    # 구조 ID 생성/검증
    if expected_structure_id is None:
        structure_id = generate_structure_id(food_id, safety)
    else:
        structure_id = expected_structure_id

    result = PostValidationResult(
        valid=True,
        food_id=food_id,
        safety=safety,
        structure_id=structure_id,
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    # 1. §22.12 금지 키워드 검증
    valid, violations = check_forbidden_keywords(caption, safety)
    if not valid:
        result.valid = False
        result.keyword_violations = violations
        for v in violations:
            result.errors.append(f"§22.12 위반: {v}")

    # 2. §22.11.2 필수 헤더 검증
    valid, missing = check_required_headers(caption, safety)
    if not valid:
        result.header_violations = missing
        for m in missing:
            result.warnings.append(f"§22.11.2: {m}")

    # 3. FORBIDDEN 필수 키워드 검증
    valid, missing = check_required_keywords(caption, safety)
    if not valid:
        for m in missing:
            result.warnings.append(f"필수 키워드 부족: {m}")

    # 4. CTA/AI 공개 검증
    valid, missing = check_cta_and_disclosure(caption)
    if not valid:
        result.missing_requirements = missing
        for m in missing:
            result.warnings.append(m)

    # 5. §22.13 구조 ID 일치 검증
    if expected_structure_id:
        valid, errors = validate_structure_id_match(
            expected_structure_id, safety, food_id
        )
        if not valid:
            result.valid = False
            for e in errors:
                result.errors.append(f"§22.13 위반: {e}")

    # 로그 저장
    save_post_validation_log(result)

    # strict 모드에서 에러 시 예외
    if strict and not result.valid:
        error_msg = "\n".join(result.errors)
        raise PostValidationError(
            f"§22.12~13 생성 후 검증 실패 - #{food_id}\n\n{error_msg}"
        )

    return result


def save_post_validation_log(result: PostValidationResult) -> Path:
    """검증 로그 저장"""
    date_str = datetime.now().strftime("%Y%m%d")
    log_dir = LOGS_DIR / date_str
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / f"{result.food_id:03d}_post_validation.log"

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"=== §22.12~13 Post-Validation Log ===\n")
        f.write(f"Timestamp: {result.timestamp}\n")
        f.write(f"Food ID: {result.food_id}\n")
        f.write(f"Safety: {result.safety.value}\n")
        f.write(f"Structure ID: {result.structure_id}\n")
        f.write(f"Valid: {'PASS' if result.valid else 'FAIL'}\n\n")

        if result.errors:
            f.write("[ERRORS]\n")
            for err in result.errors:
                f.write(f"  {err}\n")
            f.write("\n")

        if result.keyword_violations:
            f.write("[KEYWORD VIOLATIONS]\n")
            for v in result.keyword_violations:
                f.write(f"  {v}\n")
            f.write("\n")

        if result.warnings:
            f.write("[WARNINGS]\n")
            for w in result.warnings:
                f.write(f"  {w}\n")
            f.write("\n")

        f.write("=== End of Log ===\n")

    return log_path


# =============================================================================
# 테스트
# =============================================================================

def test_post_validator():
    """Post-validator 테스트"""
    print("=" * 60)
    print("§22.12~13 Post-Validator 테스트")
    print("=" * 60)

    results = []

    # 테스트 1: FORBIDDEN + 금지 키워드 → 차단
    print("\n[테스트 1] FORBIDDEN + 금지 키워드 차단")
    bad_caption = """
    [이미지 3번: 영양 정보]
    건강에 좋은 음식이에요.
    급여 방법을 알려드릴게요.
    """

    try:
        validate_after_generation(127, Safety.FORBIDDEN, bad_caption, strict=True)
        results.append(("금지 키워드 차단", False))
        print("  ❌ 차단 실패")
    except PostValidationError:
        results.append(("금지 키워드 차단", True))
        print("  ✅ 정상 차단")

    # 테스트 2: FORBIDDEN + 올바른 캡션 → 통과
    print("\n[테스트 2] FORBIDDEN + 올바른 캡션 통과")
    good_caption = """
    [이미지 1번: 표지]
    [이미지 3번: 위험 성분]
    독성 성분이 있어요.
    [이미지 4번: 절대 급여 금지]
    0g - 절대 금지
    [이미지 6번: 응급 대처법]
    병원에 가세요.
    [이미지 7번: 수의사 상담]
    수의사와 상담하세요.
    같은 보호자로서
    댓글로 남겨주세요
    AI로 생성되었습니다.
    """

    try:
        result = validate_after_generation(127, Safety.FORBIDDEN, good_caption, strict=True)
        if result.valid:
            results.append(("올바른 FORBIDDEN 통과", True))
            print("  ✅ 정상 통과")
        else:
            results.append(("올바른 FORBIDDEN 통과", False))
    except PostValidationError as e:
        results.append(("올바른 FORBIDDEN 통과", False))
        print(f"  ❌ 통과해야 하는데 차단됨: {e}")

    # 테스트 3: 구조 ID 생성
    print("\n[테스트 3] 구조 ID 생성")
    struct_id = generate_structure_id(127, Safety.FORBIDDEN)
    print(f"  생성된 ID: {struct_id}")

    parsed = parse_structure_id(struct_id)
    if parsed and parsed["food_id"] == 127 and parsed["safety"] == "FORBIDDEN":
        results.append(("구조 ID 생성/파싱", True))
        print("  ✅ 정상 생성/파싱")
    else:
        results.append(("구조 ID 생성/파싱", False))

    # 테스트 4: 구조 ID 불일치 → 차단
    print("\n[테스트 4] 구조 ID 불일치 차단")
    wrong_id = "999_SAFE_v3.1_20260211"  # 다른 food_id, 다른 safety

    try:
        validate_after_generation(
            127, Safety.FORBIDDEN, good_caption,
            expected_structure_id=wrong_id, strict=True
        )
        results.append(("구조 ID 불일치 차단", False))
        print("  ❌ 차단 실패")
    except PostValidationError:
        results.append(("구조 ID 불일치 차단", True))
        print("  ✅ 정상 차단")

    # 결과 요약
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in results if ok)
    print(f"결과: {passed}/{len(results)} 통과")

    return all(ok for _, ok in results)


if __name__ == "__main__":
    test_post_validator()
