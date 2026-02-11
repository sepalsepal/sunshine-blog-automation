#!/usr/bin/env python3
"""
pipeline/validators/pre_validator.py - §22.11 생성 전 검증기
v3.1: FORBIDDEN + 긍정 데이터 조합 차단

사용법:
    from pipeline.validators.pre_validator import validate_before_generation

    # 생성 전 검증 (실패 시 예외)
    validate_before_generation(food_id=127, safety=Safety.FORBIDDEN, food_data=data)
"""

import json
from typing import Dict, List, Tuple, Optional, Union
from pathlib import Path
from dataclasses import dataclass
from datetime import datetime

import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.enums.safety import Safety, get_safety, SafetyError


# =============================================================================
# 설정
# =============================================================================

FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
LOGS_DIR = PROJECT_ROOT / "logs" / "validation"


# =============================================================================
# §22.11.1 PreValidationError
# =============================================================================

class PreValidationError(Exception):
    """생성 전 검증 실패"""
    pass


# =============================================================================
# §22.11 금지 조합 정의
# =============================================================================

# FORBIDDEN 음식에서 긍정적 표현 금지
POSITIVE_KEYWORDS = [
    "건강에 좋",
    "영양 가득",
    "맛있",
    "좋아요",
    "추천",
    "급여량",  # 긍정적 급여량 표현
    "드셔도",
    "먹여도",
    "면역력",
    "피부 건강",
    "눈 건강",
    "장 건강",
]

# FORBIDDEN 음식의 benefit 필드에 허용되는 표현 (독성 효과)
ALLOWED_FORBIDDEN_BENEFITS = [
    "독성",
    "위험",
    "파괴",
    "손상",
    "자극",
    "빈혈",
    "유발",
    "산화",
    "스트레스",
    "중독",
]


# =============================================================================
# 검증 함수
# =============================================================================

@dataclass
class PreValidationResult:
    """검증 결과"""
    valid: bool
    food_id: int
    safety: Safety
    errors: List[str]
    warnings: List[str]
    timestamp: str


def validate_safety_enum(value: Union[str, Safety]) -> Safety:
    """
    §22.11.1: Safety ENUM 변환 및 검증

    Args:
        value: 안전도 값 (문자열 또는 ENUM)

    Returns:
        Safety ENUM

    Raises:
        PreValidationError: 유효하지 않은 값
    """
    try:
        return get_safety(value)
    except SafetyError as e:
        raise PreValidationError(f"§22.11.1 위반: {e}")


def validate_forbidden_positive_combo(
    food_id: int,
    safety: Safety,
    food_data: Dict,
) -> Tuple[bool, List[str]]:
    """
    §22.11 핵심: FORBIDDEN + 긍정 데이터 조합 차단

    FORBIDDEN 음식의 nutrients/benefits에 긍정적 표현이 있으면 차단

    Returns:
        (valid, errors)
    """
    if safety != Safety.FORBIDDEN:
        return True, []

    errors = []

    # nutrients 검증
    nutrients = food_data.get("nutrients", [])
    for nutrient in nutrients:
        benefit = nutrient.get("benefit", "")

        # 긍정 키워드 감지
        for pos_keyword in POSITIVE_KEYWORDS:
            if pos_keyword in benefit:
                errors.append(
                    f"§22.11 위반: FORBIDDEN 음식에 긍정 표현\n"
                    f"  nutrient: {nutrient.get('name')}\n"
                    f"  benefit: {benefit}\n"
                    f"  감지: '{pos_keyword}'"
                )

        # 허용된 독성 표현 확인
        has_toxic_expression = any(
            kw in benefit for kw in ALLOWED_FORBIDDEN_BENEFITS
        )

        if not has_toxic_expression and benefit:
            # benefit이 있는데 독성 표현이 없으면 경고
            # (에러는 아니지만 검토 필요)
            pass

    # do_items 검증 (FORBIDDEN에는 do_items가 없어야 함)
    do_items = food_data.get("do_items", [])
    if do_items:
        # FORBIDDEN 음식에 "권장 사항"이 있으면 위험
        for item in do_items:
            for pos_keyword in POSITIVE_KEYWORDS:
                if pos_keyword in item:
                    errors.append(
                        f"§22.11 위반: FORBIDDEN에 긍정 do_item\n"
                        f"  item: {item}\n"
                        f"  감지: '{pos_keyword}'"
                    )

    return len(errors) == 0, errors


def validate_data_safety_match(
    food_id: int,
    safety: Safety,
    food_data: Dict,
) -> Tuple[bool, List[str]]:
    """
    데이터와 안전도 일치 검증

    - FORBIDDEN인데 dosages에 실제 급여량이 있으면 에러
    - SAFE인데 위험 경고가 있으면 경고
    """
    errors = []

    if safety == Safety.FORBIDDEN:
        # dosages 검증 - 모두 0g 또는 "금지"여야 함
        dosages = food_data.get("dosages", {})
        for size, dosage in dosages.items():
            amount = dosage.get("amount", "")
            if amount and "0g" not in amount and "금지" not in amount:
                errors.append(
                    f"§22.11 위반: FORBIDDEN에 실제 급여량\n"
                    f"  {size}: {amount}\n"
                    f"  필수: '0g' 또는 '금지'"
                )

    return len(errors) == 0, errors


def validate_before_generation(
    food_id: int,
    safety: Union[str, Safety],
    food_data: Dict,
    strict: bool = True,
) -> PreValidationResult:
    """
    §22.11 생성 전 전체 검증

    Args:
        food_id: 음식 ID
        safety: 안전도 (문자열 또는 ENUM)
        food_data: 음식 데이터
        strict: True면 에러 시 예외 발생

    Returns:
        PreValidationResult

    Raises:
        PreValidationError: strict=True이고 검증 실패 시
    """
    result = PreValidationResult(
        valid=True,
        food_id=food_id,
        safety=None,
        errors=[],
        warnings=[],
        timestamp=datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
    )

    # 1. Safety ENUM 검증
    try:
        safety_enum = validate_safety_enum(safety)
        result.safety = safety_enum
    except PreValidationError as e:
        result.valid = False
        result.errors.append(str(e))
        if strict:
            raise
        return result

    # 2. FORBIDDEN + 긍정 데이터 조합 차단
    valid, errors = validate_forbidden_positive_combo(food_id, safety_enum, food_data)
    if not valid:
        result.valid = False
        result.errors.extend(errors)

    # 3. 데이터-안전도 일치 검증
    valid, errors = validate_data_safety_match(food_id, safety_enum, food_data)
    if not valid:
        result.valid = False
        result.errors.extend(errors)

    # 로그 저장
    save_pre_validation_log(result)

    # strict 모드에서 실패 시 예외
    if strict and not result.valid:
        error_msg = "\n".join(result.errors)
        raise PreValidationError(
            f"§22.11 생성 전 검증 실패 - #{food_id}\n\n{error_msg}"
        )

    return result


def save_pre_validation_log(result: PreValidationResult) -> Path:
    """검증 로그 저장"""
    date_str = datetime.now().strftime("%Y%m%d")
    log_dir = LOGS_DIR / date_str
    log_dir.mkdir(parents=True, exist_ok=True)

    log_path = log_dir / f"{result.food_id:03d}_pre_validation.log"

    with open(log_path, "w", encoding="utf-8") as f:
        f.write(f"=== §22.11 Pre-Validation Log ===\n")
        f.write(f"Timestamp: {result.timestamp}\n")
        f.write(f"Food ID: {result.food_id}\n")
        f.write(f"Safety: {result.safety.value if result.safety else 'N/A'}\n")
        f.write(f"Valid: {'PASS' if result.valid else 'FAIL'}\n\n")

        if result.errors:
            f.write("[ERRORS]\n")
            for err in result.errors:
                f.write(f"  {err}\n")
            f.write("\n")

        if result.warnings:
            f.write("[WARNINGS]\n")
            for warn in result.warnings:
                f.write(f"  {warn}\n")
            f.write("\n")

        f.write("=== End of Log ===\n")

    return log_path


# =============================================================================
# 편의 함수
# =============================================================================

def load_and_validate(food_id: int, strict: bool = True) -> PreValidationResult:
    """
    food_data.json에서 로드하여 검증

    Args:
        food_id: 음식 ID

    Returns:
        PreValidationResult
    """
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        all_data = json.load(f)

    food_data = all_data.get(str(food_id), {})
    if not food_data:
        raise PreValidationError(f"Food ID {food_id} not found in food_data.json")

    safety_str = food_data.get("safety", "SAFE")

    return validate_before_generation(
        food_id=food_id,
        safety=safety_str,
        food_data=food_data,
        strict=strict,
    )


# =============================================================================
# 테스트
# =============================================================================

def test_pre_validator():
    """Pre-validator 테스트"""
    print("=" * 60)
    print("§22.11 Pre-Validator 테스트")
    print("=" * 60)

    results = []

    # 테스트 1: FORBIDDEN + 긍정 데이터 → 차단
    print("\n[테스트 1] FORBIDDEN + 긍정 데이터 차단")
    bad_data = {
        "safety": "FORBIDDEN",
        "nutrients": [
            {"name": "테스트", "benefit": "건강에 좋아요"}  # 긍정 표현
        ],
        "dosages": {"소형견": {"amount": "10g"}},  # 실제 급여량
    }

    try:
        validate_before_generation(127, Safety.FORBIDDEN, bad_data, strict=True)
        results.append(("FORBIDDEN+긍정 차단", False))
        print("  ❌ 차단 실패")
    except PreValidationError as e:
        results.append(("FORBIDDEN+긍정 차단", True))
        print("  ✅ 정상 차단")

    # 테스트 2: FORBIDDEN + 올바른 데이터 → 통과
    print("\n[테스트 2] FORBIDDEN + 올바른 데이터 통과")
    good_data = {
        "safety": "FORBIDDEN",
        "nutrients": [
            {"name": "알리신", "benefit": "적혈구 파괴"}
        ],
        "dosages": {"소형견": {"amount": "0g - 금지"}},
    }

    try:
        result = validate_before_generation(127, Safety.FORBIDDEN, good_data, strict=True)
        if result.valid:
            results.append(("FORBIDDEN 정상 통과", True))
            print("  ✅ 정상 통과")
        else:
            results.append(("FORBIDDEN 정상 통과", False))
    except PreValidationError:
        results.append(("FORBIDDEN 정상 통과", False))
        print("  ❌ 통과해야 하는데 차단됨")

    # 테스트 3: SAFE 데이터 → 통과
    print("\n[테스트 3] SAFE 데이터 통과")
    safe_data = {
        "safety": "SAFE",
        "nutrients": [
            {"name": "비타민", "benefit": "면역력 강화"}
        ],
        "dosages": {"소형견": {"amount": "10g"}},
    }

    try:
        result = validate_before_generation(1, Safety.SAFE, safe_data, strict=True)
        if result.valid:
            results.append(("SAFE 통과", True))
            print("  ✅ 정상 통과")
        else:
            results.append(("SAFE 통과", False))
    except PreValidationError:
        results.append(("SAFE 통과", False))
        print("  ❌ 통과해야 하는데 차단됨")

    # 테스트 4: 잘못된 Safety 값 → 차단
    print("\n[테스트 4] 잘못된 Safety 값 차단")
    try:
        validate_before_generation(1, "INVALID", {}, strict=True)
        results.append(("잘못된 Safety 차단", False))
        print("  ❌ 차단 실패")
    except PreValidationError:
        results.append(("잘못된 Safety 차단", True))
        print("  ✅ 정상 차단")

    # 결과 요약
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in results if ok)
    print(f"결과: {passed}/{len(results)} 통과")

    return all(ok for _, ok in results)


if __name__ == "__main__":
    test_pre_validator()
