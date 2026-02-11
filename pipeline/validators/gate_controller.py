#!/usr/bin/env python3
"""
pipeline/validators/gate_controller.py - §22.11~13 게이트 컨트롤러
v3.1: PASS 시에만 저장 허용, FAIL 시 예외 + 로그

사용법:
    from pipeline.validators.gate_controller import (
        GateController,
        gate_check,
        can_save,
    )

    # 저장 전 게이트 체크
    gate = GateController(food_id=127, safety=Safety.FORBIDDEN)
    gate.pre_check(food_data)
    gate.post_check(caption)

    # 게이트 통과 시에만 저장
    if gate.can_proceed():
        save_content(...)
"""

import json
from typing import Dict, List, Optional, Union, Callable
from pathlib import Path
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.enums.safety import Safety, get_safety, SafetyError
from pipeline.validators.pre_validator import (
    validate_before_generation,
    PreValidationError,
    PreValidationResult,
)
from pipeline.validators.post_validator import (
    validate_after_generation,
    PostValidationError,
    PostValidationResult,
    generate_structure_id,
)


# =============================================================================
# 설정
# =============================================================================

LOGS_DIR = PROJECT_ROOT / "logs" / "gate"


# =============================================================================
# 게이트 상태
# =============================================================================

class GateStatus(Enum):
    """게이트 상태"""
    PENDING = "PENDING"      # 검증 대기
    PRE_PASS = "PRE_PASS"    # pre 검증 통과
    PRE_FAIL = "PRE_FAIL"    # pre 검증 실패
    POST_PASS = "POST_PASS"  # post 검증 통과
    POST_FAIL = "POST_FAIL"  # post 검증 실패
    GATE_PASS = "GATE_PASS"  # 최종 통과
    GATE_FAIL = "GATE_FAIL"  # 최종 실패


# =============================================================================
# GateError
# =============================================================================

class GateError(Exception):
    """게이트 통과 실패"""

    def __init__(self, message: str, status: GateStatus, errors: List[str]):
        super().__init__(message)
        self.status = status
        self.errors = errors


# =============================================================================
# GateController
# =============================================================================

@dataclass
class GateController:
    """
    §22.11~13 게이트 컨트롤러

    생성 파이프라인의 검증 게이트 역할:
    - pre_check: 생성 전 검증
    - post_check: 생성 후 검증
    - can_proceed: 저장 허용 여부

    FAIL 시:
    - 예외 발생 (strict 모드)
    - 로그 기록
    - 저장 차단
    """

    food_id: int
    safety: Safety
    structure_id: str = ""
    status: GateStatus = GateStatus.PENDING

    pre_result: Optional[PreValidationResult] = None
    post_result: Optional[PostValidationResult] = None

    all_errors: List[str] = field(default_factory=list)
    all_warnings: List[str] = field(default_factory=list)

    timestamp: str = ""
    log_path: Optional[Path] = None

    def __post_init__(self):
        """초기화"""
        if isinstance(self.safety, str):
            self.safety = get_safety(self.safety)

        self.structure_id = generate_structure_id(self.food_id, self.safety)
        self.timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    def pre_check(
        self,
        food_data: Dict,
        strict: bool = True,
    ) -> bool:
        """
        §22.11 생성 전 검증

        Args:
            food_data: 음식 데이터
            strict: True면 실패 시 예외

        Returns:
            통과 여부
        """
        try:
            self.pre_result = validate_before_generation(
                food_id=self.food_id,
                safety=self.safety,
                food_data=food_data,
                strict=False,  # 내부에서 예외 처리
            )

            if self.pre_result.valid:
                self.status = GateStatus.PRE_PASS
                return True
            else:
                self.status = GateStatus.PRE_FAIL
                self.all_errors.extend(self.pre_result.errors)
                self.all_warnings.extend(self.pre_result.warnings)

                if strict:
                    self._save_gate_log()
                    raise GateError(
                        f"§22.11 Pre-gate FAIL - #{self.food_id}",
                        self.status,
                        self.pre_result.errors,
                    )

                return False

        except PreValidationError as e:
            self.status = GateStatus.PRE_FAIL
            self.all_errors.append(str(e))

            if strict:
                self._save_gate_log()
                raise GateError(
                    f"§22.11 Pre-gate ERROR - #{self.food_id}",
                    self.status,
                    [str(e)],
                )

            return False

    def post_check(
        self,
        caption: str,
        strict: bool = True,
    ) -> bool:
        """
        §22.12~13 생성 후 검증

        Args:
            caption: 생성된 캡션
            strict: True면 실패 시 예외

        Returns:
            통과 여부
        """
        # pre_check 통과 필수
        if self.status not in (GateStatus.PRE_PASS, GateStatus.PENDING):
            if self.status == GateStatus.PRE_FAIL:
                raise GateError(
                    "Post-check 불가: Pre-check 실패 상태",
                    self.status,
                    self.all_errors,
                )

        try:
            self.post_result = validate_after_generation(
                food_id=self.food_id,
                safety=self.safety,
                caption=caption,
                expected_structure_id=self.structure_id,
                strict=False,
            )

            if self.post_result.valid:
                self.status = GateStatus.POST_PASS
                self.all_warnings.extend(self.post_result.warnings)
                return True
            else:
                self.status = GateStatus.POST_FAIL
                self.all_errors.extend(self.post_result.errors)
                self.all_warnings.extend(self.post_result.warnings)

                if strict:
                    self._save_gate_log()
                    raise GateError(
                        f"§22.12~13 Post-gate FAIL - #{self.food_id}",
                        self.status,
                        self.post_result.errors,
                    )

                return False

        except PostValidationError as e:
            self.status = GateStatus.POST_FAIL
            self.all_errors.append(str(e))

            if strict:
                self._save_gate_log()
                raise GateError(
                    f"§22.12~13 Post-gate ERROR - #{self.food_id}",
                    self.status,
                    [str(e)],
                )

            return False

    def can_proceed(self) -> bool:
        """
        저장 진행 가능 여부

        Returns:
            True if PASS, False otherwise
        """
        if self.status == GateStatus.POST_PASS:
            self.status = GateStatus.GATE_PASS
            self._save_gate_log()
            return True

        elif self.status == GateStatus.PRE_PASS:
            # post_check 아직 안 함
            return False

        else:
            self.status = GateStatus.GATE_FAIL
            self._save_gate_log()
            return False

    def force_fail(self, reason: str):
        """수동 실패 처리"""
        self.status = GateStatus.GATE_FAIL
        self.all_errors.append(f"수동 실패: {reason}")
        self._save_gate_log()

        raise GateError(
            f"Gate 수동 실패 - #{self.food_id}: {reason}",
            self.status,
            [reason],
        )

    def get_summary(self) -> Dict:
        """게이트 상태 요약"""
        return {
            "food_id": self.food_id,
            "safety": self.safety.value,
            "structure_id": self.structure_id,
            "status": self.status.value,
            "can_save": self.status == GateStatus.GATE_PASS,
            "error_count": len(self.all_errors),
            "warning_count": len(self.all_warnings),
            "errors": self.all_errors,
            "warnings": self.all_warnings,
            "timestamp": self.timestamp,
        }

    def _save_gate_log(self) -> Path:
        """게이트 로그 저장"""
        date_str = datetime.now().strftime("%Y%m%d")
        log_dir = LOGS_DIR / date_str
        log_dir.mkdir(parents=True, exist_ok=True)

        status_str = "PASS" if self.status == GateStatus.GATE_PASS else "FAIL"
        log_path = log_dir / f"{self.food_id:03d}_gate_{status_str}.log"

        with open(log_path, "w", encoding="utf-8") as f:
            f.write(f"{'='*60}\n")
            f.write(f"§22.11~13 Gate Controller Log\n")
            f.write(f"{'='*60}\n\n")

            f.write(f"Timestamp: {self.timestamp}\n")
            f.write(f"Food ID: {self.food_id}\n")
            f.write(f"Safety: {self.safety.value}\n")
            f.write(f"Structure ID: {self.structure_id}\n")
            f.write(f"Final Status: {self.status.value}\n\n")

            f.write(f"{'='*60}\n")
            f.write(f"RESULT: {status_str}\n")
            f.write(f"{'='*60}\n\n")

            if self.all_errors:
                f.write("[ERRORS]\n")
                for i, err in enumerate(self.all_errors, 1):
                    f.write(f"  {i}. {err}\n")
                f.write("\n")

            if self.all_warnings:
                f.write("[WARNINGS]\n")
                for i, warn in enumerate(self.all_warnings, 1):
                    f.write(f"  {i}. {warn}\n")
                f.write("\n")

            # Pre-validation 상세
            if self.pre_result:
                f.write("[Pre-Validation]\n")
                f.write(f"  Valid: {self.pre_result.valid}\n")
                f.write(f"  Errors: {len(self.pre_result.errors)}\n\n")

            # Post-validation 상세
            if self.post_result:
                f.write("[Post-Validation]\n")
                f.write(f"  Valid: {self.post_result.valid}\n")
                f.write(f"  Keyword Violations: {len(self.post_result.keyword_violations)}\n")
                f.write(f"  Header Violations: {len(self.post_result.header_violations)}\n\n")

            f.write(f"{'='*60}\n")
            f.write("End of Log\n")

        self.log_path = log_path
        return log_path


# =============================================================================
# 편의 함수
# =============================================================================

def gate_check(
    food_id: int,
    safety: Union[str, Safety],
    food_data: Dict,
    caption: str,
    strict: bool = True,
) -> GateController:
    """
    원스텝 게이트 체크

    Args:
        food_id: 음식 ID
        safety: 안전도
        food_data: 음식 데이터
        caption: 캡션
        strict: True면 실패 시 예외

    Returns:
        GateController (상태 확인용)
    """
    if isinstance(safety, str):
        safety = get_safety(safety)

    gate = GateController(food_id=food_id, safety=safety)
    gate.pre_check(food_data, strict=strict)
    gate.post_check(caption, strict=strict)

    return gate


def can_save(gate: GateController) -> bool:
    """저장 가능 여부 확인"""
    return gate.can_proceed()


# =============================================================================
# 테스트
# =============================================================================

def test_gate_controller():
    """Gate Controller 테스트"""
    print("=" * 60)
    print("§22.11~13 Gate Controller 테스트")
    print("=" * 60)

    results = []

    # 테스트 1: 정상 데이터 → GATE_PASS
    print("\n[테스트 1] 정상 데이터 → GATE_PASS")

    good_data = {
        "safety": "FORBIDDEN",
        "nutrients": [{"name": "알리신", "benefit": "적혈구 파괴"}],
        "dosages": {"소형견": {"amount": "0g - 금지"}},
    }

    good_caption = """
    [이미지 1번: 표지]
    [이미지 3번: 위험 성분]
    독성 성분 알리신이 있어요.
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
        gate = gate_check(127, Safety.FORBIDDEN, good_data, good_caption, strict=True)
        if gate.can_proceed():
            results.append(("정상 GATE_PASS", True))
            print(f"  ✅ PASS - Status: {gate.status.value}")
        else:
            results.append(("정상 GATE_PASS", False))
    except GateError as e:
        results.append(("정상 GATE_PASS", False))
        print(f"  ❌ 실패: {e}")

    # 테스트 2: 잘못된 데이터 → PRE_FAIL
    print("\n[테스트 2] 잘못된 데이터 → PRE_FAIL")

    bad_data = {
        "safety": "FORBIDDEN",
        "nutrients": [{"name": "비타민", "benefit": "건강에 좋아요"}],  # 긍정 표현
        "dosages": {"소형견": {"amount": "10g"}},  # 실제 급여량
    }

    try:
        gate = gate_check(127, Safety.FORBIDDEN, bad_data, good_caption, strict=True)
        results.append(("PRE_FAIL 차단", False))
        print("  ❌ 차단 실패")
    except GateError as e:
        if e.status == GateStatus.PRE_FAIL:
            results.append(("PRE_FAIL 차단", True))
            print(f"  ✅ 정상 차단 - Status: {e.status.value}")
        else:
            results.append(("PRE_FAIL 차단", False))

    # 테스트 3: 잘못된 캡션 → POST_FAIL
    print("\n[테스트 3] 잘못된 캡션 → POST_FAIL")

    bad_caption = """
    [이미지 3번: 영양 정보]
    건강에 좋은 음식이에요.
    """

    try:
        gate = gate_check(127, Safety.FORBIDDEN, good_data, bad_caption, strict=True)
        results.append(("POST_FAIL 차단", False))
        print("  ❌ 차단 실패")
    except GateError as e:
        if e.status == GateStatus.POST_FAIL:
            results.append(("POST_FAIL 차단", True))
            print(f"  ✅ 정상 차단 - Status: {e.status.value}")
        else:
            results.append(("POST_FAIL 차단", False))

    # 테스트 4: non-strict 모드
    print("\n[테스트 4] non-strict 모드")

    try:
        gate = gate_check(127, Safety.FORBIDDEN, bad_data, bad_caption, strict=False)
        if not gate.can_proceed():
            results.append(("non-strict 모드", True))
            print(f"  ✅ 예외 없이 FAIL 반환 - Status: {gate.status.value}")
        else:
            results.append(("non-strict 모드", False))
    except GateError:
        results.append(("non-strict 모드", False))
        print("  ❌ strict=False인데 예외 발생")

    # 결과 요약
    print("\n" + "=" * 60)
    passed = sum(1 for _, ok in results if ok)
    print(f"결과: {passed}/{len(results)} 통과")

    return all(ok for _, ok in results)


if __name__ == "__main__":
    test_gate_controller()
