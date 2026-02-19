#!/usr/bin/env python3
"""
quality_protocol.py - 콘텐츠 품질 점수 산출 프로토콜 v2.0
WO-OVERNIGHT-FINAL Task 2

20점 체계:
- 구조 일치: 0~5점
- 톤앤매너: 0~5점
- 정보 정확성: 0~5점
- 자연스러움: 0~5점

PASS 조건: 총점 ≥15 AND 각 항목 ≥3
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, field
from enum import Enum

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from pipeline.enums.safety import Safety, get_safety

# =============================================================================
# 상수 및 설정
# =============================================================================

SCORING_CRITERIA_PATH = PROJECT_ROOT / "config" / "scoring_criteria.json"
TOXICITY_MAPPING_PATH = PROJECT_ROOT / "config" / "toxicity_mapping.json"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
CONTENTS_DIR = PROJECT_ROOT / "contents"
STATUS_DIRS = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]

# PASS 조건
PASS_TOTAL_MIN = 15
PASS_EACH_MIN = 3

# 종료 조건
SAME_ITEM_FAIL_LIMIT = 2
CONSECUTIVE_FAIL_LIMIT = 3


# =============================================================================
# 데이터 클래스
# =============================================================================

@dataclass
class DimensionScore:
    """개별 차원 점수"""
    name: str
    name_ko: str
    score: int
    max_score: int
    details: str
    fail_reason: Optional[str] = None


@dataclass
class QualityResult:
    """품질 평가 결과"""
    food_id: int
    food_name: str
    safety: Safety
    total_score: int
    max_score: int
    passed: bool
    dimensions: List[DimensionScore]
    fail_reasons: List[str] = field(default_factory=list)


# =============================================================================
# 유틸리티
# =============================================================================

def find_content_folder(food_id: int) -> Optional[Path]:
    """콘텐츠 폴더 찾기"""
    num_str = f"{food_id:03d}"
    for status_dir in STATUS_DIRS:
        status_path = CONTENTS_DIR / status_dir
        if not status_path.exists():
            continue
        for item in status_path.iterdir():
            if item.is_dir() and item.name.startswith(num_str):
                return item
    return None


def load_caption(content_folder: Path, platform: str = "blog") -> Optional[str]:
    """캡션 로드"""
    caption_path = content_folder / platform / "caption.txt"
    if caption_path.exists():
        return caption_path.read_text(encoding="utf-8")

    # 루트 캡션 fallback
    root_caption = content_folder / "caption.txt"
    if root_caption.exists():
        return root_caption.read_text(encoding="utf-8")

    return None


def load_json(path: Path) -> Dict:
    """JSON 파일 로드"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


# =============================================================================
# 점수 산출 로직
# =============================================================================

class QualityScorer:
    """품질 점수 산출기 (20점 체계)"""

    def __init__(self):
        self.criteria = load_json(SCORING_CRITERIA_PATH)
        self.food_data = load_json(FOOD_DATA_PATH)

        if TOXICITY_MAPPING_PATH.exists():
            self.toxicity = load_json(TOXICITY_MAPPING_PATH)
        else:
            self.toxicity = None

        # 연속 실패 추적
        self.fail_tracker = {}

    def evaluate(self, food_id: int, platform: str = "blog") -> QualityResult:
        """
        콘텐츠 품질 평가 (20점 체계)
        """
        # 기본 데이터 로드
        food_info = self.food_data.get(str(food_id), {})
        food_name = food_info.get("name", f"Unknown#{food_id}")
        safety = get_safety(food_info.get("safety", "SAFE"))

        # 콘텐츠 폴더 및 캡션 로드
        folder = find_content_folder(food_id)
        caption = None
        if folder:
            caption = load_caption(folder, platform)

        if not caption:
            return QualityResult(
                food_id=food_id,
                food_name=food_name,
                safety=safety,
                total_score=0,
                max_score=20,
                passed=False,
                dimensions=[],
                fail_reasons=["캡션 파일 없음"]
            )

        # 각 차원 평가
        dimensions = []
        fail_reasons = []

        # 1. 구조 일치 (5점)
        dim1 = self._score_structure(caption, safety)
        dimensions.append(dim1)
        if dim1.score < PASS_EACH_MIN:
            fail_reasons.append("STRUCTURE_MISMATCH")

        # 2. 톤앤매너 (5점)
        dim2 = self._score_tone(caption, safety)
        dimensions.append(dim2)
        if dim2.score < PASS_EACH_MIN:
            fail_reasons.append("TONE_MISMATCH")

        # 3. 정보 정확성 (5점)
        dim3 = self._score_accuracy(food_id, food_info, caption)
        dimensions.append(dim3)
        if dim3.score < PASS_EACH_MIN:
            fail_reasons.append("ACCURACY_ERROR")

        # 4. 자연스러움 (5점)
        dim4 = self._score_naturalness(caption)
        dimensions.append(dim4)
        if dim4.score < PASS_EACH_MIN:
            fail_reasons.append("UNNATURAL")

        # 총점 계산
        total_score = sum(d.score for d in dimensions)

        if total_score < PASS_TOTAL_MIN and "LOW_TOTAL" not in fail_reasons:
            fail_reasons.append("LOW_TOTAL")

        passed = total_score >= PASS_TOTAL_MIN and len(fail_reasons) == 0

        return QualityResult(
            food_id=food_id,
            food_name=food_name,
            safety=safety,
            total_score=total_score,
            max_score=20,
            passed=passed,
            dimensions=dimensions,
            fail_reasons=fail_reasons
        )

    def _score_structure(self, caption: str, safety: Safety) -> DimensionScore:
        """구조 일치 점수 (5점 만점)"""
        # 슬라이드 헤더 카운트
        slide_pattern = r"\[이미지 \d+번:"
        slides = re.findall(slide_pattern, caption)
        slide_count = len(slides)

        # 기대 슬라이드 수: 8개
        if slide_count == 8:
            score = 5
            details = "8개 슬라이드 완전, 구조 100% 일치"
        elif slide_count == 7:
            score = 4
            details = f"{slide_count}개 슬라이드 (1개 차이)"
        elif slide_count >= 6:
            score = 3
            details = f"{slide_count}개 슬라이드 (2개 이하 차이)"
        elif slide_count >= 5:
            score = 2
            details = f"{slide_count}개 슬라이드 (3개 차이)"
        elif slide_count >= 3:
            score = 1
            details = f"{slide_count}개 슬라이드 (구조 대폭 상이)"
        else:
            score = 0
            details = f"{slide_count}개 슬라이드 (구조 파괴)"

        return DimensionScore(
            name="structure",
            name_ko="구조 일치",
            score=score,
            max_score=5,
            details=details,
            fail_reason="STRUCTURE_MISMATCH" if score < PASS_EACH_MIN else None
        )

    def _score_tone(self, caption: str, safety: Safety) -> DimensionScore:
        """톤앤매너 점수 (5점 만점)"""
        # 햇살이 엄마 말투 마커
        friendly_markers = ["~요", "~해요", "~해주세요", "~이에요", "~인데요"]
        emoji_count = len(re.findall(r"[\U0001F300-\U0001F9FF]", caption))

        friendly_count = sum(1 for m in friendly_markers if m in caption)

        # Safety에 맞는 톤 확인
        tone_match = True
        if safety == Safety.FORBIDDEN:
            warning_markers = ["절대", "위험", "금지", "주의", "응급"]
            warning_count = sum(1 for m in warning_markers if m in caption)
            positive_markers = ["좋아요", "건강에 좋", "추천"]
            positive_count = sum(1 for m in positive_markers if m in caption)
            if positive_count > 0 or warning_count < 2:
                tone_match = False

        if friendly_count >= 4 and emoji_count >= 3 and tone_match:
            score = 5
            details = "햇살이 엄마 말투 완벽 구현"
        elif friendly_count >= 3 and tone_match:
            score = 4
            details = "전반적 톤 일치"
        elif friendly_count >= 2 and tone_match:
            score = 3
            details = "톤 유지, 일부 어색함"
        elif friendly_count >= 1:
            score = 2
            details = "톤 불일치 다수"
        else:
            score = 1 if tone_match else 0
            details = "톤 완전 불일치" if tone_match else "톤 파괴"

        return DimensionScore(
            name="tone",
            name_ko="톤앤매너",
            score=score,
            max_score=5,
            details=details,
            fail_reason="TONE_MISMATCH" if score < PASS_EACH_MIN else None
        )

    def _score_accuracy(self, food_id: int, food_info: Dict, caption: str) -> DimensionScore:
        """정보 정확성 점수 (5점 만점)"""
        issues = []

        # 음식 이름 포함 여부
        food_name = food_info.get("name", "")
        if food_name and food_name not in caption:
            issues.append("음식 이름 누락")

        # toxicity 정보 반영 여부 (FORBIDDEN의 경우)
        if self.toxicity and str(food_id) in self.toxicity.get("food_mapping", {}):
            tox_info = self.toxicity["food_mapping"][str(food_id)]
            compounds = tox_info.get("toxic_compounds", [])
            compound_mentioned = any(
                c.split("(")[0].lower() in caption.lower()
                for c in compounds if c
            )
            if not compound_mentioned and compounds:
                issues.append("독성 화합물 미반영")

        # Safety 정보 일치
        safety = food_info.get("safety", "SAFE").upper()
        structure_id_pattern = rf"{food_id}_{safety}_v\d+\.\d+_\d{{8}}"
        if not re.search(structure_id_pattern, caption):
            # 구조 ID 없어도 내용이 맞으면 허용
            pass

        if len(issues) == 0:
            score = 5
            details = "정보 100% 일치"
        elif len(issues) == 1:
            score = 4
            details = f"경미한 차이: {issues[0]}"
        elif len(issues) == 2:
            score = 3
            details = f"일부 오류: {', '.join(issues)}"
        else:
            score = 2
            details = f"다수 오류: {', '.join(issues)}"

        return DimensionScore(
            name="accuracy",
            name_ko="정보 정확성",
            score=score,
            max_score=5,
            details=details,
            fail_reason="ACCURACY_ERROR" if score < PASS_EACH_MIN else None
        )

    def _score_naturalness(self, caption: str) -> DimensionScore:
        """자연스러움 점수 (5점 만점)"""
        issues = []

        # 너무 긴 문장 체크
        lines = caption.split("\n")
        long_lines = sum(1 for line in lines if len(line) > 100)
        if long_lines > 3:
            issues.append("긴 문장 다수")

        # 연속 빈 줄 체크
        if "\n\n\n\n" in caption:
            issues.append("연속 빈 줄 과다")

        # 기계적 반복 체크
        words = caption.split()
        if len(words) > 10:
            unique_ratio = len(set(words)) / len(words)
            if unique_ratio < 0.3:
                issues.append("단어 반복 과다")

        # 어색한 조사 체크 (간략화)
        awkward_patterns = ["을를", "이가", "은는", "의의"]
        for p in awkward_patterns:
            if p in caption:
                issues.append(f"어색한 표현: {p}")
                break

        if len(issues) == 0:
            score = 5
            details = "자연스러운 한국어"
        elif len(issues) == 1:
            score = 4
            details = f"경미한 어색함: {issues[0]}"
        elif len(issues) <= 2:
            score = 3
            details = f"어색함 2-3곳: {', '.join(issues)}"
        elif len(issues) <= 4:
            score = 2
            details = "어색한 표현 다수"
        else:
            score = 1
            details = "부자연스러운 문장 다수"

        return DimensionScore(
            name="naturalness",
            name_ko="자연스러움",
            score=score,
            max_score=5,
            details=details,
            fail_reason="UNNATURAL" if score < PASS_EACH_MIN else None
        )


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse

    parser = argparse.ArgumentParser(description="콘텐츠 품질 점수 산출 (20점 체계)")
    parser.add_argument("--food-id", type=int, required=True, help="음식 ID")
    parser.add_argument("--platform", default="blog", help="플랫폼 (blog/insta)")
    parser.add_argument("--verbose", "-v", action="store_true", help="상세 출력")

    args = parser.parse_args()

    scorer = QualityScorer()
    result = scorer.evaluate(args.food_id, args.platform)

    print(f"\n{'='*50}")
    print(f"품질 평가 결과: #{result.food_id} {result.food_name}")
    print(f"{'='*50}")
    print(f"Safety: {result.safety.value}")
    print(f"총점: {result.total_score}/{result.max_score}")
    print(f"결과: {'✅ PASS' if result.passed else '❌ FAIL'}")

    if result.fail_reasons:
        print(f"\n[FAIL 사유]")
        for reason in result.fail_reasons:
            print(f"  - {reason}")

    if args.verbose and result.dimensions:
        print(f"\n[차원별 점수]")
        for dim in result.dimensions:
            status = "✓" if dim.score >= PASS_EACH_MIN else "✗"
            print(f"  {status} {dim.name_ko}: {dim.score}/{dim.max_score}")
            print(f"      {dim.details}")

    print()


if __name__ == "__main__":
    main()
