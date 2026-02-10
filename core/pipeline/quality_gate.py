"""
Quality Gate System - 단계별 품질 검증 및 합의 시스템
각 파이프라인 단계 완료 후 다음 단계 진행 전 품질 검증

Author: 김부장 (프로젝트 총괄)
Version: 2.0
Date: 2026-01-25

핵심 원칙:
1. 각 단계 완료 후 반드시 품질 게이트 통과 필요
2. 복수 검토자(서브 에이전트)의 합의 필요
3. 불합격 시 자동 수정 및 재검토 (최대 3회)
4. 비용 발생 단계(이미지 생성) 전 철저한 사전 검증
"""

from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Callable
from enum import Enum
import json


class GateStatus(Enum):
    """게이트 통과 상태"""
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"


class ReviewerRole(Enum):
    """검토자 역할"""
    BRAND_GUARDIAN = "brand_guardian"      # 브랜드 가이드라인 준수
    SAFETY_CHECKER = "safety_checker"      # 안전성 검증
    QUALITY_AUDITOR = "quality_auditor"    # 품질 검수
    COST_OPTIMIZER = "cost_optimizer"      # 비용 효율성
    CUSTOMER_ADVOCATE = "customer_advocate" # 고객 관점


@dataclass
class ReviewResult:
    """개별 검토 결과"""
    reviewer: ReviewerRole
    status: GateStatus
    score: int  # 0-100
    issues: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    blocking: bool = False  # True면 즉시 중단


@dataclass
class GateResult:
    """게이트 종합 결과"""
    gate_name: str
    status: GateStatus
    reviews: List[ReviewResult] = field(default_factory=list)
    consensus_score: float = 0.0
    blocking_issues: List[str] = field(default_factory=list)
    revision_count: int = 0
    max_revisions: int = 3

    @property
    def can_proceed(self) -> bool:
        """다음 단계 진행 가능 여부"""
        return self.status == GateStatus.APPROVED and len(self.blocking_issues) == 0

    @property
    def needs_revision(self) -> bool:
        """수정 필요 여부"""
        return self.status == GateStatus.NEEDS_REVISION and self.revision_count < self.max_revisions


# ============================================================
# 브랜드 가이드라인 (절대 위반 불가)
# ============================================================
BRAND_GUIDELINES = {
    "character": {
        "name": "햇살이",
        "breed": "10살 시니어 골든리트리버",
        "forbidden_terms": ["puppy", "young dog", "baby dog"],
        "required_features": ["white muzzle", "white fur around eyes", "black nose", "black eyes"],
    },
    "image_rules": {
        "forbidden_poses": [
            "dog eating food",
            "dog holding food",
            "dog biting food",
            "dog touching food with paws",
            "food in mouth",
            "tongue touching food",
            "paws near food bowl",
        ],
        "required_composition": {
            "cover": "subject in center-bottom 80%, top 20% clear for text",
            "content": "subject in upper 70%, bottom 30% clear for text",
        },
    },
    "text_rules": {
        "cover": {"font_size": 58, "position_y": 120, "underline_width": 180},
        "content": {"title_size": 52, "subtitle_size": 26},
    },
}


# ============================================================
# 검토자별 검증 함수
# ============================================================

def review_brand_guidelines(data: Dict, stage: str) -> ReviewResult:
    """
    브랜드 가이드라인 검토 (Brand Guardian)
    - 햇살이 캐릭터 규칙 준수
    - 금지 포즈/표현 확인
    - 레이아웃 규격 확인
    """
    issues = []
    suggestions = []
    blocking = False
    score = 100

    if stage == "prompt":
        prompts = data.get("prompts", [])
        for p in prompts:
            prompt_text = p.get("prompt", "").lower()

            # 금지 용어 체크
            for forbidden in BRAND_GUIDELINES["character"]["forbidden_terms"]:
                if forbidden in prompt_text:
                    issues.append(f"[CRITICAL] 금지 용어 '{forbidden}' 포함 (슬라이드 {p.get('index')})")
                    blocking = True
                    score -= 30

            # 금지 포즈 체크
            for forbidden_pose in BRAND_GUIDELINES["image_rules"]["forbidden_poses"]:
                if forbidden_pose.replace(" ", "") in prompt_text.replace(" ", ""):
                    issues.append(f"[CRITICAL] 금지 포즈 '{forbidden_pose}' 암시 (슬라이드 {p.get('index')})")
                    blocking = True
                    score -= 25

            # 필수 특징 체크 (캐릭터 프롬프트에)
            if p.get("type") in ["cover", "content", "cta"]:
                has_character_desc = any(
                    feat in prompt_text
                    for feat in ["senior", "golden retriever", "10-year", "10 year"]
                )
                if not has_character_desc:
                    issues.append(f"[WARNING] 햇살이 캐릭터 설명 부족 (슬라이드 {p.get('index')})")
                    score -= 10

    elif stage == "image":
        # 이미지 메타데이터 검증 (실제 이미지 분석은 별도)
        images = data.get("images", [])
        for img in images:
            if not img.get("exists"):
                issues.append(f"[ERROR] 이미지 생성 실패 (슬라이드 {img.get('index')})")
                score -= 15

    return ReviewResult(
        reviewer=ReviewerRole.BRAND_GUARDIAN,
        status=GateStatus.REJECTED if blocking else (
            GateStatus.NEEDS_REVISION if issues else GateStatus.APPROVED
        ),
        score=max(0, score),
        issues=issues,
        suggestions=suggestions,
        blocking=blocking
    )


def review_safety(data: Dict, stage: str) -> ReviewResult:
    """
    안전성 검토 (Safety Checker)
    - 음식 안전 정보 정확성
    - 위험 요소 경고 포함 여부
    """
    issues = []
    suggestions = []
    score = 100

    if stage == "plan":
        plan = data
        safety = plan.get("safety", "unknown")
        slides = plan.get("slides", [])

        # 주의사항 슬라이드 존재 확인
        has_caution = any(s.get("type") == "caution" or "주의" in s.get("title", "") for s in slides)
        if not has_caution:
            issues.append("[WARNING] 주의사항 슬라이드 없음 - 안전 정보 부족")
            score -= 15
            suggestions.append("주의사항/금지사항 슬라이드 추가 권장")

        # 위험 음식인 경우 추가 경고 필요
        if safety == "dangerous":
            has_warning = any("위험" in s.get("title", "") or "금지" in s.get("title", "") for s in slides)
            if not has_warning:
                issues.append("[CRITICAL] 위험 음식이나 명확한 경고 슬라이드 없음")
                score -= 30

    return ReviewResult(
        reviewer=ReviewerRole.SAFETY_CHECKER,
        status=GateStatus.NEEDS_REVISION if issues else GateStatus.APPROVED,
        score=max(0, score),
        issues=issues,
        suggestions=suggestions,
        blocking=False
    )


def review_quality(data: Dict, stage: str) -> ReviewResult:
    """
    품질 검토 (Quality Auditor)
    - 전반적 품질 수준
    - 일관성 확인
    """
    issues = []
    suggestions = []
    score = 100

    if stage == "prompt":
        prompts = data.get("prompts", [])

        # 프롬프트 길이 체크
        for p in prompts:
            prompt_text = p.get("prompt", "")
            if len(prompt_text) < 100:
                issues.append(f"[WARNING] 프롬프트 너무 짧음 ({len(prompt_text)}자) - 슬라이드 {p.get('index')}")
                score -= 5

            # 품질 태그 포함 확인
            quality_keywords = ["Canon", "85mm", "Kodak", "film", "natural light"]
            has_quality_tags = any(kw.lower() in prompt_text.lower() for kw in quality_keywords)
            if not has_quality_tags:
                suggestions.append(f"슬라이드 {p.get('index')}: 품질 태그 추가 권장")

        # 일관성 체크 (모든 프롬프트가 유사한 스타일)
        if len(prompts) > 1:
            first_style = "Candid photograph" in prompts[0].get("prompt", "")
            inconsistent = [
                p.get("index") for p in prompts[1:]
                if ("Candid photograph" in p.get("prompt", "")) != first_style
            ]
            if inconsistent:
                issues.append(f"[WARNING] 스타일 불일치: 슬라이드 {inconsistent}")
                score -= 10

    return ReviewResult(
        reviewer=ReviewerRole.QUALITY_AUDITOR,
        status=GateStatus.NEEDS_REVISION if issues else GateStatus.APPROVED,
        score=max(0, score),
        issues=issues,
        suggestions=suggestions,
        blocking=False
    )


def review_cost_efficiency(data: Dict, stage: str) -> ReviewResult:
    """
    비용 효율성 검토 (Cost Optimizer)
    - 불필요한 API 호출 방지
    - 리소스 최적화
    """
    issues = []
    suggestions = []
    score = 100

    if stage == "prompt":
        prompts = data.get("prompts", [])

        # 중복 프롬프트 체크
        prompt_texts = [p.get("prompt", "")[:200] for p in prompts]
        if len(prompt_texts) != len(set(prompt_texts)):
            issues.append("[WARNING] 유사/중복 프롬프트 발견 - 비용 낭비 가능")
            score -= 20
            suggestions.append("프롬프트 차별화 필요")

        # 이미지 수 적정성
        if len(prompts) > 10:
            issues.append(f"[WARNING] 이미지 수 과다 ({len(prompts)}장) - 비용 검토 필요")
            score -= 10

    return ReviewResult(
        reviewer=ReviewerRole.COST_OPTIMIZER,
        status=GateStatus.NEEDS_REVISION if issues else GateStatus.APPROVED,
        score=max(0, score),
        issues=issues,
        suggestions=suggestions,
        blocking=False
    )


def review_customer_perspective(data: Dict, stage: str) -> ReviewResult:
    """
    고객 관점 검토 (Customer Advocate)
    - 고객이 이해하기 쉬운지
    - 오해 소지가 없는지
    - 매력적인지
    """
    issues = []
    suggestions = []
    score = 100

    if stage == "plan":
        slides = data.get("slides", [])

        # 첫 슬라이드가 긍정적인지
        if slides and slides[0].get("type") == "cover":
            pass  # OK

        # 정보 흐름 체크
        types_order = [s.get("type") for s in slides]
        expected_flow = ["cover", "content", "content", "content", "content", "content", "cta"]

        if len(types_order) < 5:
            issues.append("[WARNING] 콘텐츠 부족 - 고객에게 충분한 정보 미제공")
            score -= 15

    elif stage == "prompt":
        prompts = data.get("prompts", [])

        for p in prompts:
            prompt_text = p.get("prompt", "").lower()

            # 부정적 표현 체크
            negative_terms = ["sad", "angry", "aggressive", "scary", "dangerous looking"]
            for term in negative_terms:
                if term in prompt_text:
                    issues.append(f"[WARNING] 부정적 표현 '{term}' - 고객 인상 저해 (슬라이드 {p.get('index')})")
                    score -= 10

    return ReviewResult(
        reviewer=ReviewerRole.CUSTOMER_ADVOCATE,
        status=GateStatus.NEEDS_REVISION if issues else GateStatus.APPROVED,
        score=max(0, score),
        issues=issues,
        suggestions=suggestions,
        blocking=False
    )


# ============================================================
# Quality Gate 메인 클래스
# ============================================================

class QualityGate:
    """
    품질 게이트 - 각 단계별 합의 기반 승인 시스템

    사용법:
        gate = QualityGate("prompt_review")
        result = gate.review(prompt_data, stage="prompt")

        if result.can_proceed:
            # 다음 단계로
        elif result.needs_revision:
            # 수정 후 재검토
        else:
            # 중단
    """

    # 단계별 필수 검토자
    STAGE_REVIEWERS = {
        "plan": [
            ReviewerRole.SAFETY_CHECKER,
            ReviewerRole.CUSTOMER_ADVOCATE,
        ],
        "prompt": [
            ReviewerRole.BRAND_GUARDIAN,  # 필수
            ReviewerRole.QUALITY_AUDITOR,
            ReviewerRole.COST_OPTIMIZER,
            ReviewerRole.CUSTOMER_ADVOCATE,
        ],
        "image": [
            ReviewerRole.BRAND_GUARDIAN,  # 필수
            ReviewerRole.QUALITY_AUDITOR,
        ],
        "overlay": [
            ReviewerRole.QUALITY_AUDITOR,
        ],
        "final": [
            ReviewerRole.BRAND_GUARDIAN,
            ReviewerRole.SAFETY_CHECKER,
            ReviewerRole.QUALITY_AUDITOR,
            ReviewerRole.CUSTOMER_ADVOCATE,
        ],
    }

    # 검토자별 검증 함수 매핑
    REVIEWER_FUNCTIONS = {
        ReviewerRole.BRAND_GUARDIAN: review_brand_guidelines,
        ReviewerRole.SAFETY_CHECKER: review_safety,
        ReviewerRole.QUALITY_AUDITOR: review_quality,
        ReviewerRole.COST_OPTIMIZER: review_cost_efficiency,
        ReviewerRole.CUSTOMER_ADVOCATE: review_customer_perspective,
    }

    # 합의 기준
    CONSENSUS_THRESHOLD = 0.75  # 75% 이상 승인 필요
    MIN_SCORE_THRESHOLD = 70    # 최소 평균 점수

    def __init__(self, gate_name: str, max_revisions: int = 3):
        self.gate_name = gate_name
        self.max_revisions = max_revisions
        self.revision_count = 0

    def review(self, data: Dict, stage: str) -> GateResult:
        """
        데이터 검토 및 합의 도출

        Args:
            data: 검토 대상 데이터
            stage: 현재 단계 (plan, prompt, image, overlay, final)

        Returns:
            GateResult: 검토 결과
        """
        reviewers = self.STAGE_REVIEWERS.get(stage, [])
        reviews = []
        blocking_issues = []

        for reviewer_role in reviewers:
            review_func = self.REVIEWER_FUNCTIONS.get(reviewer_role)
            if review_func:
                result = review_func(data, stage)
                reviews.append(result)

                if result.blocking:
                    blocking_issues.extend(result.issues)

        # 합의 계산
        if reviews:
            approved_count = sum(1 for r in reviews if r.status == GateStatus.APPROVED)
            consensus_ratio = approved_count / len(reviews)
            avg_score = sum(r.score for r in reviews) / len(reviews)
        else:
            consensus_ratio = 1.0
            avg_score = 100

        # 최종 상태 결정
        if blocking_issues:
            status = GateStatus.REJECTED
        elif consensus_ratio >= self.CONSENSUS_THRESHOLD and avg_score >= self.MIN_SCORE_THRESHOLD:
            status = GateStatus.APPROVED
        else:
            status = GateStatus.NEEDS_REVISION

        return GateResult(
            gate_name=self.gate_name,
            status=status,
            reviews=reviews,
            consensus_score=consensus_ratio * 100,
            blocking_issues=blocking_issues,
            revision_count=self.revision_count,
            max_revisions=self.max_revisions
        )

    def increment_revision(self):
        """수정 횟수 증가"""
        self.revision_count += 1

    def format_report(self, result: GateResult) -> str:
        """검토 결과 리포트 포맷"""
        lines = [
            f"\n{'='*60}",
            f"🚦 Quality Gate: {result.gate_name}",
            f"{'='*60}",
            f"상태: {result.status.value.upper()}",
            f"합의율: {result.consensus_score:.1f}%",
            f"수정 횟수: {result.revision_count}/{result.max_revisions}",
            "",
        ]

        if result.blocking_issues:
            lines.append("🚨 [BLOCKING ISSUES]")
            for issue in result.blocking_issues:
                lines.append(f"   {issue}")
            lines.append("")

        for review in result.reviews:
            emoji = "✅" if review.status == GateStatus.APPROVED else "❌"
            lines.append(f"{emoji} {review.reviewer.value}: {review.score}점")
            for issue in review.issues:
                lines.append(f"   - {issue}")
            for suggestion in review.suggestions:
                lines.append(f"   💡 {suggestion}")

        lines.append(f"{'='*60}\n")

        return "\n".join(lines)


# ============================================================
# 프롬프트 자동 수정 함수
# ============================================================

def auto_fix_prompt(prompt_data: Dict, issues: List[str]) -> Dict:
    """
    이슈 기반 프롬프트 자동 수정

    Args:
        prompt_data: 원본 프롬프트 데이터
        issues: 발견된 이슈 목록

    Returns:
        수정된 프롬프트 데이터
    """
    fixed_prompts = []

    for p in prompt_data.get("prompts", []):
        prompt_text = p.get("prompt", "")
        negative_prompt = p.get("negative_prompt", "")

        # 금지 포즈 관련 이슈 수정
        forbidden_pose_keywords = [
            "eating", "licking", "biting", "holding food",
            "touching food", "paws near", "tongue"
        ]

        for keyword in forbidden_pose_keywords:
            if keyword in prompt_text.lower():
                # 대체 표현으로 변경
                replacements = {
                    "eating": "looking at",
                    "licking": "sniffing curiously",
                    "biting": "sitting beside",
                    "holding food": "sitting near",
                    "touching food": "keeping distance from",
                }
                for old, new in replacements.items():
                    prompt_text = prompt_text.replace(old, new)

        # negative prompt 강화
        additional_negatives = [
            "dog eating", "dog licking", "tongue out towards food",
            "paws touching food", "mouth open near food"
        ]
        current_negatives = set(negative_prompt.split(", "))
        current_negatives.update(additional_negatives)
        negative_prompt = ", ".join(current_negatives)

        fixed_prompts.append({
            **p,
            "prompt": prompt_text,
            "negative_prompt": negative_prompt,
            "_fixed": True
        })

    return {**prompt_data, "prompts": fixed_prompts}
