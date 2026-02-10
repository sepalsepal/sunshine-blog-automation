"""
피드백 개선 도구
Phase 4: 검수 피드백 분석 및 개선 프롬프트 생성

- 기술/크리에이티브 피드백 분석
- 문제 유형 분류
- 개선 프롬프트 자동 생성
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum


class ProblemCategory(Enum):
    """문제 카테고리"""
    RESOLUTION = "resolution"           # 해상도 문제
    TEXT_POSITION = "text_position"     # 텍스트 위치
    UNDERLINE = "underline"             # 언더라인 비율
    POSE_DIVERSITY = "pose_diversity"   # 포즈 다양성
    ANGLE_DIVERSITY = "angle_diversity" # 앵글 다양성
    BACKGROUND = "background"           # 배경 다양성
    HUMAN_PRESENCE = "human_presence"   # 사람 등장
    FOOD_FORM = "food_form"             # 음식 형태
    EMOTION = "emotion"                 # 감성 품질
    COMPOSITION = "composition"         # 구도/균형
    COLOR = "color"                     # 색감
    STORYTELLING = "storytelling"       # 스토리텔링
    AUTHENTICITY = "authenticity"       # 자연스러움 (AI 느낌)


@dataclass
class FeedbackAnalysis:
    """피드백 분석 결과"""
    categories: List[ProblemCategory]
    problem_slides: List[int]
    improvement_suggestions: List[str]
    priority: str  # high, medium, low
    regeneration_scope: str  # full, selective, minor


class FeedbackImprover:
    """
    피드백 분석 및 개선 도구

    검수 피드백을 분석하여:
    1. 문제 유형 분류
    2. 영향받는 슬라이드 식별
    3. 개선 프롬프트 생성
    """

    # 키워드 → 카테고리 매핑
    KEYWORD_MAPPING = {
        # 기술 검수 관련
        "해상도": ProblemCategory.RESOLUTION,
        "resolution": ProblemCategory.RESOLUTION,
        "1080": ProblemCategory.RESOLUTION,
        "px": ProblemCategory.RESOLUTION,

        "제목 위치": ProblemCategory.TEXT_POSITION,
        "18%": ProblemCategory.TEXT_POSITION,
        "텍스트 위치": ProblemCategory.TEXT_POSITION,
        "title position": ProblemCategory.TEXT_POSITION,

        "언더라인": ProblemCategory.UNDERLINE,
        "underline": ProblemCategory.UNDERLINE,

        # 다양성 관련
        "포즈": ProblemCategory.POSE_DIVERSITY,
        "pose": ProblemCategory.POSE_DIVERSITY,
        "앉": ProblemCategory.POSE_DIVERSITY,
        "눕": ProblemCategory.POSE_DIVERSITY,

        "앵글": ProblemCategory.ANGLE_DIVERSITY,
        "angle": ProblemCategory.ANGLE_DIVERSITY,
        "정면": ProblemCategory.ANGLE_DIVERSITY,
        "측면": ProblemCategory.ANGLE_DIVERSITY,

        "배경": ProblemCategory.BACKGROUND,
        "background": ProblemCategory.BACKGROUND,
        "주방": ProblemCategory.BACKGROUND,
        "거실": ProblemCategory.BACKGROUND,

        "사람": ProblemCategory.HUMAN_PRESENCE,
        "human": ProblemCategory.HUMAN_PRESENCE,
        "손": ProblemCategory.HUMAN_PRESENCE,
        "조리": ProblemCategory.HUMAN_PRESENCE,

        "음식 형태": ProblemCategory.FOOD_FORM,
        "food form": ProblemCategory.FOOD_FORM,
        "통째": ProblemCategory.FOOD_FORM,
        "썬": ProblemCategory.FOOD_FORM,

        # 감성 관련
        "자연스러움": ProblemCategory.AUTHENTICITY,
        "AI 느낌": ProblemCategory.AUTHENTICITY,
        "스톡": ProblemCategory.AUTHENTICITY,
        "authenticity": ProblemCategory.AUTHENTICITY,

        "감성": ProblemCategory.EMOTION,
        "emotion": ProblemCategory.EMOTION,
        "따뜻": ProblemCategory.EMOTION,
        "표정": ProblemCategory.EMOTION,

        "구도": ProblemCategory.COMPOSITION,
        "균형": ProblemCategory.COMPOSITION,
        "composition": ProblemCategory.COMPOSITION,

        "색감": ProblemCategory.COLOR,
        "톤": ProblemCategory.COLOR,
        "color": ProblemCategory.COLOR,

        "스토리": ProblemCategory.STORYTELLING,
        "흐름": ProblemCategory.STORYTELLING,
        "narrative": ProblemCategory.STORYTELLING,
    }

    # 카테고리별 개선 프롬프트 템플릿
    IMPROVEMENT_TEMPLATES = {
        ProblemCategory.RESOLUTION:
            "IMPORTANT: Generate at exactly 1080x1080 pixels",

        ProblemCategory.TEXT_POSITION:
            "LAYOUT: Title must be positioned at 18% from top of image",

        ProblemCategory.UNDERLINE:
            "UNDERLINE: Underline width must be exactly 100% of title text width + 20px",

        ProblemCategory.POSE_DIVERSITY:
            "DOG POSES: Include variety - sitting, lying down, standing, looking up at camera",

        ProblemCategory.ANGLE_DIVERSITY:
            "CAMERA ANGLES: Mix of front view, 45-degree side, 90-degree side, top-down, and soft blur backgrounds",

        ProblemCategory.BACKGROUND:
            "BACKGROUNDS: Use both kitchen and living room settings",

        ProblemCategory.HUMAN_PRESENCE:
            "HUMAN ELEMENT: Include human hands or cooking scenes in at least 2 slides",

        ProblemCategory.FOOD_FORM:
            "FOOD FORMS: Show food in multiple forms - whole, sliced, in bowl/plate",

        ProblemCategory.AUTHENTICITY:
            "AUTHENTICITY: Avoid AI-generated or stock photo appearance. Make it feel like a real pet parent's photo. Include slight imperfections, natural lighting, genuine expressions",

        ProblemCategory.EMOTION:
            "EMOTION: Capture warmth and everyday life feeling. Show genuine dog-owner relationship moments",

        ProblemCategory.COMPOSITION:
            "COMPOSITION: Ensure visual balance with clear focal points and harmonious element placement",

        ProblemCategory.COLOR:
            "COLOR: Maintain consistent warm tones throughout. Natural, cozy color palette",

        ProblemCategory.STORYTELLING:
            "NARRATIVE: Create clear visual flow between slides. Each slide should connect to the next",
    }

    def __init__(self):
        pass

    def analyze_feedback(
        self,
        tech_feedback: Optional[str] = None,
        creative_feedback: Optional[str] = None,
        tech_details: Optional[Dict] = None,
        creative_details: Optional[Dict] = None
    ) -> FeedbackAnalysis:
        """
        피드백 분석

        Args:
            tech_feedback: 기술 검수 피드백 문자열
            creative_feedback: 크리에이티브 검수 피드백 문자열
            tech_details: 기술 검수 상세 결과
            creative_details: 크리에이티브 검수 상세 결과

        Returns:
            FeedbackAnalysis 객체
        """
        categories = set()
        problem_slides = set()

        # 텍스트 피드백 분석
        all_feedback = ""
        if tech_feedback:
            all_feedback += tech_feedback + " "
        if creative_feedback:
            all_feedback += creative_feedback + " "

        all_feedback_lower = all_feedback.lower()

        for keyword, category in self.KEYWORD_MAPPING.items():
            if keyword.lower() in all_feedback_lower:
                categories.add(category)

        # 상세 결과에서 추가 분석
        if tech_details:
            self._analyze_tech_details(tech_details, categories, problem_slides)

        if creative_details:
            self._analyze_creative_details(creative_details, categories, problem_slides)

        # 개선 제안 생성
        suggestions = self._generate_suggestions(list(categories))

        # 우선순위 및 범위 결정
        priority = self._determine_priority(categories)
        scope = self._determine_scope(categories, list(problem_slides))

        return FeedbackAnalysis(
            categories=list(categories),
            problem_slides=sorted(list(problem_slides)),
            improvement_suggestions=suggestions,
            priority=priority,
            regeneration_scope=scope
        )

    def _analyze_tech_details(
        self,
        details: Dict,
        categories: set,
        problem_slides: set
    ):
        """기술 검수 상세 분석"""
        # 해상도 체크
        resolution = details.get("resolution", {})
        if not resolution.get("pass", True):
            categories.add(ProblemCategory.RESOLUTION)
            for slide_info in resolution.get("failed_slides", []):
                if isinstance(slide_info, dict):
                    problem_slides.add(slide_info.get("index", 0))
                elif isinstance(slide_info, int):
                    problem_slides.add(slide_info)

        # 텍스트 위치 체크
        text_pos = details.get("text_position", {})
        if not text_pos.get("pass", True):
            categories.add(ProblemCategory.TEXT_POSITION)

        # 언더라인 체크
        underline = details.get("underline", {})
        if not underline.get("pass", True):
            categories.add(ProblemCategory.UNDERLINE)

    def _analyze_creative_details(
        self,
        details: Dict,
        categories: set,
        problem_slides: set
    ):
        """크리에이티브 검수 상세 분석"""
        # 카테고리별 점수 분석
        for cat_name, cat_data in details.items():
            if not isinstance(cat_data, dict):
                continue

            total = cat_data.get("total", 25)  # 각 25점 만점

            # 60% 미만이면 문제로 분류
            if total < 15:  # 25점의 60%
                if "aesthetic" in cat_name.lower():
                    categories.add(ProblemCategory.COMPOSITION)
                    categories.add(ProblemCategory.COLOR)
                elif "emotion" in cat_name.lower():
                    categories.add(ProblemCategory.EMOTION)
                    categories.add(ProblemCategory.AUTHENTICITY)
                elif "storytelling" in cat_name.lower():
                    categories.add(ProblemCategory.STORYTELLING)
                elif "diversity" in cat_name.lower():
                    # 다양성 세부 분석
                    detected = cat_data.get("detected", {})
                    scores = cat_data.get("scores", {})

                    if scores.get("pose_variety", 5) < 3:
                        categories.add(ProblemCategory.POSE_DIVERSITY)
                    if scores.get("angle_variety", 5) < 3:
                        categories.add(ProblemCategory.ANGLE_DIVERSITY)
                    if scores.get("background_variety", 5) < 3:
                        categories.add(ProblemCategory.BACKGROUND)
                    if scores.get("human_appearance", 5) < 3:
                        categories.add(ProblemCategory.HUMAN_PRESENCE)
                    if scores.get("food_form_variety", 5) < 3:
                        categories.add(ProblemCategory.FOOD_FORM)

    def _generate_suggestions(self, categories: List[ProblemCategory]) -> List[str]:
        """개선 제안 생성"""
        suggestions = []

        for category in categories:
            if category in self.IMPROVEMENT_TEMPLATES:
                suggestions.append(self.IMPROVEMENT_TEMPLATES[category])

        return suggestions

    def _determine_priority(self, categories: set) -> str:
        """우선순위 결정"""
        # 기술적 문제는 높은 우선순위
        tech_categories = {
            ProblemCategory.RESOLUTION,
            ProblemCategory.TEXT_POSITION,
            ProblemCategory.UNDERLINE
        }

        if categories & tech_categories:
            return "high"

        # 다양성/감성 문제
        if len(categories) >= 3:
            return "high"
        elif len(categories) >= 1:
            return "medium"

        return "low"

    def _determine_scope(
        self,
        categories: set,
        problem_slides: List[int]
    ) -> str:
        """재생성 범위 결정"""
        # 전체 구조 문제
        structural_issues = {
            ProblemCategory.STORYTELLING,
            ProblemCategory.COMPOSITION
        }

        if categories & structural_issues:
            return "full"

        # 특정 슬라이드만 문제
        if problem_slides and len(problem_slides) <= 3:
            return "selective"

        # 다양성 문제 (전체 재생성 필요할 수 있음)
        diversity_issues = {
            ProblemCategory.POSE_DIVERSITY,
            ProblemCategory.ANGLE_DIVERSITY,
            ProblemCategory.BACKGROUND
        }

        if categories & diversity_issues:
            return "full"

        return "minor"

    def generate_improvement_prompt(
        self,
        analysis: FeedbackAnalysis,
        original_prompts: Optional[List[Dict]] = None
    ) -> str:
        """
        개선 프롬프트 생성

        Args:
            analysis: FeedbackAnalysis 결과
            original_prompts: 원본 프롬프트 (옵션)

        Returns:
            개선된 프롬프트 문자열
        """
        prompt_parts = []

        # 헤더
        prompt_parts.append("=== IMPROVEMENT REQUIREMENTS ===")
        prompt_parts.append(f"Priority: {analysis.priority.upper()}")
        prompt_parts.append(f"Scope: {analysis.regeneration_scope}")
        prompt_parts.append("")

        # 개선 사항
        if analysis.improvement_suggestions:
            prompt_parts.append("REQUIRED IMPROVEMENTS:")
            for i, suggestion in enumerate(analysis.improvement_suggestions, 1):
                prompt_parts.append(f"{i}. {suggestion}")
            prompt_parts.append("")

        # 문제 슬라이드 (선택적 재생성 시)
        if analysis.problem_slides and analysis.regeneration_scope == "selective":
            prompt_parts.append(f"FOCUS SLIDES: {analysis.problem_slides}")
            prompt_parts.append("Only regenerate these specific slides while maintaining consistency with others.")
            prompt_parts.append("")

        # 추가 지침
        prompt_parts.append("CRITICAL REMINDERS:")
        prompt_parts.append("- Match Cherry (Gold Standard) quality level")
        prompt_parts.append("- Maintain consistent visual style across all slides")
        prompt_parts.append("- Ensure natural, authentic feeling (not AI-generated)")

        return "\n".join(prompt_parts)

    def get_slide_specific_improvements(
        self,
        analysis: FeedbackAnalysis,
        slide_index: int
    ) -> List[str]:
        """
        특정 슬라이드에 대한 개선 사항

        Args:
            analysis: FeedbackAnalysis 결과
            slide_index: 슬라이드 인덱스

        Returns:
            개선 사항 리스트
        """
        improvements = []

        if slide_index in analysis.problem_slides:
            improvements.append(f"This slide (#{slide_index}) needs regeneration")

        # 해당 슬라이드 유형에 맞는 개선 사항
        for suggestion in analysis.improvement_suggestions:
            improvements.append(suggestion)

        return improvements


# 테스트
if __name__ == "__main__":
    improver = FeedbackImprover()

    # 테스트 피드백
    analysis = improver.analyze_feedback(
        tech_feedback="언더라인 비율 문제, 제목 위치 조정 필요",
        creative_feedback="포즈 다양성 부족, AI 느낌이 남, 사람 등장 없음",
        creative_details={
            "diversity": {
                "total": 12,
                "scores": {
                    "pose_variety": 2,
                    "angle_variety": 3,
                    "background_variety": 4,
                    "human_appearance": 1,
                    "food_form_variety": 2
                }
            }
        }
    )

    print("=== 피드백 분석 결과 ===")
    print(f"문제 카테고리: {[c.value for c in analysis.categories]}")
    print(f"문제 슬라이드: {analysis.problem_slides}")
    print(f"우선순위: {analysis.priority}")
    print(f"재생성 범위: {analysis.regeneration_scope}")
    print()

    print("=== 개선 프롬프트 ===")
    improvement_prompt = improver.generate_improvement_prompt(analysis)
    print(improvement_prompt)
