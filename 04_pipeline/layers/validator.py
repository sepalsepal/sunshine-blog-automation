#!/usr/bin/env python3
"""
validator.py - Layer 2: 품질 검증 계층
WO-LIGHTWEIGHT-SEPARATION

책임:
- URL 검증
- 품질 점수 산정
- FAIL 코드 발행
- 금지 코드 자동 차단

제한:
- Generator 로직 수정 불가
- Executor 직접 호출 불가
- 금지 코드 우회 불가
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional, Tuple

import sys
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.interfaces.layer_contract import (
    GeneratedContent,
    ValidationResult,
    ValidationStatus,
    LayerAccessControl,
    PermissionDeniedError,
    AutoBlockedError,
)


class Validator:
    """
    Layer 2: 품질 검증 전담

    Generator, Executor 직접 접근 불가
    금지 코드 자동 차단
    """

    LAYER_NAME = "validator"

    # 금지 코드: override 불가, 자동 차단
    BLOCKED_CODES = frozenset(["ACCURACY_ERROR", "SAFETY_MISMATCH"])

    # PASS 조건 (§22.15.1)
    PASS_TOTAL_MIN = 15
    PASS_EACH_MIN = 3
    MAX_SCORE = 20

    # FORBIDDEN 금지 키워드 (§22.12)
    FORBIDDEN_POSITIVE_KEYWORDS = [
        "건강에 좋", "영양 가득", "맛있어요", "좋아요",
        "급여 방법", "조리 방법", "권장량", "드셔도 됩니다", "먹여도 됩니다",
        "체중별 급여량", "소형견 급여량", "중형견 급여량", "대형견 급여량",
        "영양 정보", "영양정보", "영양소"
    ]

    # FORBIDDEN 필수 경고 마커
    FORBIDDEN_WARNING_MARKERS = ["절대", "위험", "금지", "독성", "응급", "치명"]

    def __init__(self):
        pass

    def validate(self, content: GeneratedContent) -> ValidationResult:
        """
        콘텐츠 품질 검증

        Args:
            content: Generator에서 전달받은 콘텐츠

        Returns:
            ValidationResult 객체
        """
        # 권한 확인
        LayerAccessControl.check_permission(self.LAYER_NAME, "validate")

        # 점수 계산
        scores, fail_codes = self._calculate_scores(content)
        total = sum(scores.values())

        # 금지 코드 확인 → 자동 차단
        blocked_codes = [c for c in fail_codes if c in self.BLOCKED_CODES]
        if blocked_codes:
            return ValidationResult(
                layer=self.LAYER_NAME,
                food_id=content.food_id,
                food_name=content.food_name,
                score=scores,
                total=total,
                status=ValidationStatus.BLOCKED,
                fail_codes=fail_codes,
                allow_override=False,  # 금지 코드는 override 불가
                requires_approval=None,
                reason=f"금지 코드 감지: {blocked_codes}",
                validated_at=datetime.now().isoformat()
            )

        # 점수 미달 확인
        each_fail = any(s < self.PASS_EACH_MIN for s in scores.values())
        total_fail = total < self.PASS_TOTAL_MIN

        if each_fail or total_fail or fail_codes:
            return ValidationResult(
                layer=self.LAYER_NAME,
                food_id=content.food_id,
                food_name=content.food_name,
                score=scores,
                total=total,
                status=ValidationStatus.FAIL,
                fail_codes=fail_codes,
                allow_override=True,  # 일반 FAIL은 override 가능
                requires_approval="김부장",
                reason=self._build_fail_reason(scores, fail_codes),
                validated_at=datetime.now().isoformat()
            )

        # PASS
        return ValidationResult(
            layer=self.LAYER_NAME,
            food_id=content.food_id,
            food_name=content.food_name,
            score=scores,
            total=total,
            status=ValidationStatus.PASS,
            fail_codes=[],
            allow_override=False,
            requires_approval=None,
            reason="",
            validated_at=datetime.now().isoformat()
        )

    def _calculate_scores(
        self,
        content: GeneratedContent
    ) -> Tuple[Dict[str, int], List[str]]:
        """
        4차원 점수 계산 (각 5점 만점, 총 20점)

        Returns:
            (scores dict, fail_codes list)
        """
        scores = {}
        fail_codes = []
        caption = content.content
        safety = content.safety

        # 1. 구조 일치 (5점)
        structure_score = self._score_structure(caption)
        scores["structure"] = structure_score
        if structure_score < self.PASS_EACH_MIN:
            fail_codes.append("STRUCTURE_MISMATCH")

        # 2. 톤앤매너 (5점)
        tone_score = self._score_tone(caption, safety)
        scores["tone"] = tone_score
        if tone_score < self.PASS_EACH_MIN:
            fail_codes.append("TONE_MISMATCH")

        # 3. 정보 정확성 (5점)
        accuracy_score, accuracy_issues = self._score_accuracy(caption, safety)
        scores["accuracy"] = accuracy_score
        if accuracy_score < self.PASS_EACH_MIN:
            fail_codes.append("ACCURACY_ERROR")
        if "SAFETY_MISMATCH" in accuracy_issues:
            fail_codes.append("SAFETY_MISMATCH")

        # 4. 자연스러움 (5점)
        naturalness_score = self._score_naturalness(caption)
        scores["naturalness"] = naturalness_score
        if naturalness_score < self.PASS_EACH_MIN:
            fail_codes.append("UNNATURAL")

        # 총점 미달 확인
        total = sum(scores.values())
        if total < self.PASS_TOTAL_MIN and "LOW_TOTAL" not in fail_codes:
            fail_codes.append("LOW_TOTAL")

        return scores, fail_codes

    def _score_structure(self, caption: str) -> int:
        """구조 일치 점수 (5점)"""
        # 슬라이드 헤더 카운트
        slide_pattern = r"\[이미지 \d+번:"
        slides = re.findall(slide_pattern, caption)
        slide_count = len(slides)

        if slide_count >= 8:
            return 5
        elif slide_count >= 7:
            return 4
        elif slide_count >= 6:
            return 3
        elif slide_count >= 5:
            return 2
        elif slide_count >= 3:
            return 1
        else:
            return 0

    def _score_tone(self, caption: str, safety: str) -> int:
        """톤앤매너 점수 (5점)"""
        # 햇살이 엄마 말투 마커 (실제 어미 패턴)
        friendly_patterns = ["요.", "요!", "요?", "요\n", "해요", "세요", "이에요", "인데요", "드릴게요", "거예요"]
        friendly_count = sum(1 for m in friendly_patterns if m in caption)

        # FORBIDDEN: 경고 톤 필수
        if safety == "FORBIDDEN":
            warning_count = sum(
                1 for m in self.FORBIDDEN_WARNING_MARKERS
                if m in caption
            )
            positive_count = sum(
                1 for kw in self.FORBIDDEN_POSITIVE_KEYWORDS
                if kw in caption
            )

            # 긍정 표현 있으면 감점
            if positive_count > 0:
                return max(0, 3 - positive_count)

            # 경고 마커 부족
            if warning_count < 2:
                return 3  # 부분 감점

            if warning_count >= 3 and friendly_count >= 2:
                return 5
            elif warning_count >= 2:
                return 4
            else:
                return 3

        # SAFE/CAUTION
        if friendly_count >= 4:
            return 5
        elif friendly_count >= 3:
            return 4
        elif friendly_count >= 2:
            return 3
        elif friendly_count >= 1:
            return 2
        else:
            return 1

    def _score_accuracy(
        self,
        caption: str,
        safety: str
    ) -> Tuple[int, List[str]]:
        """정보 정확성 점수 (5점)"""
        issues = []

        # FORBIDDEN에서 긍정 표현 금지 (§22.12)
        if safety == "FORBIDDEN":
            for kw in self.FORBIDDEN_POSITIVE_KEYWORDS:
                if kw in caption:
                    issues.append(f"FORBIDDEN_POSITIVE: {kw}")

            # 금지 헤더 패턴
            forbidden_headers = [
                "[이미지 3번: 영양 정보]",
                "[이미지 4번: 급여 방법]",
                "[이미지 6번: 조리 방법]",
            ]
            for header in forbidden_headers:
                if header in caption:
                    issues.append(f"FORBIDDEN_HEADER: {header}")

            if issues:
                issues.append("SAFETY_MISMATCH")

        if len(issues) == 0:
            return 5, []
        elif len(issues) == 1:
            return 4, issues
        elif len(issues) <= 3:
            return 3, issues
        elif len(issues) <= 5:
            return 2, issues
        else:
            return 1, issues

    def _score_naturalness(self, caption: str) -> int:
        """자연스러움 점수 (5점)"""
        issues = 0

        # 너무 긴 문장
        lines = caption.split("\n")
        long_lines = sum(1 for line in lines if len(line) > 100)
        if long_lines > 3:
            issues += 1

        # 연속 빈 줄
        if "\n\n\n\n" in caption:
            issues += 1

        # 어색한 조사
        awkward_patterns = ["을를", "이가", "은는", "의의"]
        for p in awkward_patterns:
            if p in caption:
                issues += 1
                break

        if issues == 0:
            return 5
        elif issues == 1:
            return 4
        elif issues == 2:
            return 3
        elif issues <= 4:
            return 2
        else:
            return 1

    def _build_fail_reason(
        self,
        scores: Dict[str, int],
        fail_codes: List[str]
    ) -> str:
        """FAIL 사유 문자열 생성"""
        reasons = []

        for dim, score in scores.items():
            if score < self.PASS_EACH_MIN:
                reasons.append(f"{dim}={score}/5 (미달)")

        total = sum(scores.values())
        if total < self.PASS_TOTAL_MIN:
            reasons.append(f"총점={total}/20 (미달)")

        if fail_codes:
            reasons.append(f"코드: {', '.join(fail_codes)}")

        return "; ".join(reasons)

    # =========================================================================
    # 금지 메서드 (계층 침범 방지)
    # =========================================================================

    def _blocked_generator_modify(self):
        """Generator 수정 시도 시 차단"""
        raise PermissionDeniedError(
            "Validator는 Generator 수정 불가 (계층 분리 원칙)"
        )

    def _blocked_executor_call(self):
        """Executor 직접 호출 시도 시 차단"""
        raise PermissionDeniedError(
            "Validator는 Executor 직접 호출 불가 (계층 분리 원칙)"
        )

    def _blocked_bypass_block(self):
        """금지 코드 우회 시도 시 차단"""
        raise PermissionDeniedError(
            "Validator는 금지 코드 우회 불가 (§22.15.2)"
        )

    # 금지 작업 래퍼 (테스트용)
    def generate(self, *args, **kwargs):
        """금지: generate"""
        LayerAccessControl.check_permission(self.LAYER_NAME, "generate")

    def execute(self, *args, **kwargs):
        """금지: execute"""
        LayerAccessControl.check_permission(self.LAYER_NAME, "execute")

    def modify_generator(self, *args, **kwargs):
        """금지: modify_generator"""
        LayerAccessControl.check_permission(self.LAYER_NAME, "modify_generator")

    def bypass_block(self, *args, **kwargs):
        """금지: bypass_block"""
        LayerAccessControl.check_permission(self.LAYER_NAME, "bypass_block")
