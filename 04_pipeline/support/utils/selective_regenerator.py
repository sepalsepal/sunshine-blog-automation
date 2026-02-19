"""
선택적 재생성 도구
Phase 4: 문제 슬라이드만 재생성

- 문제 슬라이드 식별
- 선택적 재생성
- 기존 슬라이드와 일관성 유지
"""

import shutil
from pathlib import Path
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass

from .feedback_improver import FeedbackImprover, FeedbackAnalysis


@dataclass
class RegenerationPlan:
    """재생성 계획"""
    slides_to_regenerate: List[int]
    slides_to_keep: List[int]
    improvements_per_slide: Dict[int, List[str]]
    strategy: str  # full, selective, patch


class SelectiveRegenerator:
    """
    선택적 슬라이드 재생성 도구

    전체 재생성 대신 문제가 있는 슬라이드만
    선택적으로 재생성하여 효율성 향상
    """

    def __init__(self):
        self.feedback_improver = FeedbackImprover()

    def analyze_and_plan(
        self,
        tech_result: Optional[Dict] = None,
        creative_result: Optional[Dict] = None,
        total_slides: int = 8
    ) -> RegenerationPlan:
        """
        피드백 분석 및 재생성 계획 수립

        Args:
            tech_result: 기술 검수 결과
            creative_result: 크리에이티브 검수 결과
            total_slides: 전체 슬라이드 수

        Returns:
            RegenerationPlan 객체
        """
        # 피드백 분석
        analysis = self.feedback_improver.analyze_feedback(
            tech_feedback=tech_result.get("feedback") if tech_result else None,
            creative_feedback=creative_result.get("feedback") if creative_result else None,
            tech_details=tech_result.get("details") if tech_result else None,
            creative_details=creative_result.get("details") if creative_result else None
        )

        # 재생성 대상 결정
        slides_to_regenerate = self._determine_slides_to_regenerate(
            analysis=analysis,
            total_slides=total_slides
        )

        slides_to_keep = [
            i for i in range(total_slides)
            if i not in slides_to_regenerate
        ]

        # 슬라이드별 개선 사항
        improvements_per_slide = {}
        for slide_idx in slides_to_regenerate:
            improvements = self.feedback_improver.get_slide_specific_improvements(
                analysis=analysis,
                slide_index=slide_idx
            )
            improvements_per_slide[slide_idx] = improvements

        # 전략 결정
        strategy = self._determine_strategy(
            analysis=analysis,
            num_to_regenerate=len(slides_to_regenerate),
            total_slides=total_slides
        )

        return RegenerationPlan(
            slides_to_regenerate=slides_to_regenerate,
            slides_to_keep=slides_to_keep,
            improvements_per_slide=improvements_per_slide,
            strategy=strategy
        )

    def _determine_slides_to_regenerate(
        self,
        analysis: FeedbackAnalysis,
        total_slides: int
    ) -> List[int]:
        """재생성할 슬라이드 결정"""
        # 명시적으로 문제가 있는 슬라이드
        problem_slides = set(analysis.problem_slides)

        # 전체 재생성 필요 조건
        if analysis.regeneration_scope == "full":
            return list(range(total_slides))

        # 선택적 재생성
        if problem_slides:
            return sorted(list(problem_slides))

        # 문제 슬라이드 불명확 시 추정
        # 일반적으로 Cover(0)와 CTA(마지막)는 문제 있을 확률 높음
        from .feedback_improver import ProblemCategory

        estimated = set()

        # 다양성 문제 → 중간 슬라이드들
        diversity_issues = {
            ProblemCategory.POSE_DIVERSITY,
            ProblemCategory.ANGLE_DIVERSITY,
            ProblemCategory.BACKGROUND,
            ProblemCategory.HUMAN_PRESENCE
        }

        if set(analysis.categories) & diversity_issues:
            # 슬라이드 2-6 (다양성 표현 구간)
            estimated.update([1, 2, 3, 4, 5])

        # 표지 문제
        if ProblemCategory.TEXT_POSITION in analysis.categories:
            estimated.add(0)

        # CTA 문제
        if ProblemCategory.STORYTELLING in analysis.categories:
            estimated.add(total_slides - 1)

        if estimated:
            return sorted(list(estimated))

        # 기본: 문제 추정 불가 시 전체
        return list(range(total_slides))

    def _determine_strategy(
        self,
        analysis: FeedbackAnalysis,
        num_to_regenerate: int,
        total_slides: int
    ) -> str:
        """재생성 전략 결정"""
        ratio = num_to_regenerate / total_slides

        if ratio >= 0.7:
            return "full"
        elif ratio >= 0.3:
            return "selective"
        else:
            return "patch"

    def prepare_selective_generation(
        self,
        plan: RegenerationPlan,
        existing_images_dir: str,
        output_dir: str,
        prompts: List[Dict]
    ) -> Dict[str, Any]:
        """
        선택적 재생성 준비

        기존 이미지 복사 및 재생성 프롬프트 준비

        Args:
            plan: RegenerationPlan
            existing_images_dir: 기존 이미지 디렉토리
            output_dir: 출력 디렉토리
            prompts: 원본 프롬프트 리스트

        Returns:
            {
                "prompts_to_generate": List[Dict],
                "copied_files": List[str],
                "generation_indices": List[int]
            }
        """
        existing_dir = Path(existing_images_dir)
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        copied_files = []
        prompts_to_generate = []

        for idx in range(len(prompts)):
            if idx in plan.slides_to_keep:
                # 기존 파일 복사
                existing_file = self._find_slide_file(existing_dir, idx)
                if existing_file:
                    dest_file = output_path / existing_file.name
                    shutil.copy2(existing_file, dest_file)
                    copied_files.append(str(dest_file))
            else:
                # 재생성 대상
                enhanced_prompt = prompts[idx].copy()

                # 개선 사항 추가
                improvements = plan.improvements_per_slide.get(idx, [])
                if improvements:
                    improvement_text = "\n\nIMPROVEMENTS REQUIRED:\n" + "\n".join(
                        f"- {imp}" for imp in improvements
                    )
                    enhanced_prompt["prompt"] = enhanced_prompt.get("prompt", "") + improvement_text

                # 일관성 지침 추가
                enhanced_prompt["prompt"] += "\n\nCONSISTENCY: Match the visual style of existing slides."

                prompts_to_generate.append({
                    "index": idx,
                    **enhanced_prompt
                })

        return {
            "prompts_to_generate": prompts_to_generate,
            "copied_files": copied_files,
            "generation_indices": plan.slides_to_regenerate
        }

    def _find_slide_file(self, directory: Path, slide_index: int) -> Optional[Path]:
        """슬라이드 파일 찾기"""
        # 파일 패턴들
        patterns = [
            f"slide_{slide_index:02d}*.png",
            f"slide_{slide_index}*.png",
            f"*_{slide_index:02d}*.png",
            f"*_{slide_index}*.png",
        ]

        for pattern in patterns:
            matches = list(directory.glob(pattern))
            if matches:
                return matches[0]

        # 인덱스 기반 정렬 시도
        all_files = sorted(directory.glob("*.png"))
        if slide_index < len(all_files):
            return all_files[slide_index]

        return None

    def merge_regenerated(
        self,
        plan: RegenerationPlan,
        kept_files: List[str],
        regenerated_files: List[str],
        output_dir: str
    ) -> List[str]:
        """
        재생성된 파일과 기존 파일 병합

        Args:
            plan: RegenerationPlan
            kept_files: 유지된 파일 리스트
            regenerated_files: 재생성된 파일 리스트
            output_dir: 최종 출력 디렉토리

        Returns:
            최종 파일 리스트 (순서대로)
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 인덱스별 파일 매핑
        file_map: Dict[int, str] = {}

        # 유지된 파일
        for file_path in kept_files:
            idx = self._extract_index_from_filename(file_path)
            if idx is not None:
                file_map[idx] = file_path

        # 재생성된 파일
        for file_path in regenerated_files:
            idx = self._extract_index_from_filename(file_path)
            if idx is not None:
                file_map[idx] = file_path

        # 순서대로 정렬 및 복사
        final_files = []
        total_slides = len(plan.slides_to_keep) + len(plan.slides_to_regenerate)

        for idx in range(total_slides):
            if idx in file_map:
                src = Path(file_map[idx])
                # 일관된 파일명으로 복사
                dest = output_path / f"slide_{idx:02d}_{src.stem.split('_')[-1]}.png"
                shutil.copy2(src, dest)
                final_files.append(str(dest))

        return final_files

    def _extract_index_from_filename(self, file_path: str) -> Optional[int]:
        """파일명에서 인덱스 추출"""
        import re

        filename = Path(file_path).stem

        # slide_XX 패턴
        match = re.search(r'slide_(\d+)', filename)
        if match:
            return int(match.group(1))

        # _XX_ 또는 _XX 패턴
        match = re.search(r'_(\d+)(?:_|$)', filename)
        if match:
            return int(match.group(1))

        return None

    def get_regeneration_report(self, plan: RegenerationPlan) -> str:
        """재생성 계획 리포트"""
        lines = [
            "=" * 50,
            "📋 선택적 재생성 계획",
            "=" * 50,
            f"전략: {plan.strategy}",
            f"재생성 슬라이드: {plan.slides_to_regenerate}",
            f"유지 슬라이드: {plan.slides_to_keep}",
            "",
            "슬라이드별 개선 사항:"
        ]

        for idx, improvements in plan.improvements_per_slide.items():
            lines.append(f"\n  슬라이드 #{idx}:")
            for imp in improvements[:3]:  # 상위 3개만
                lines.append(f"    - {imp[:50]}...")

        lines.append("=" * 50)

        return "\n".join(lines)


# 테스트
if __name__ == "__main__":
    regenerator = SelectiveRegenerator()

    # 테스트: 검수 결과 기반 계획 수립
    tech_result = {
        "score": 75,
        "feedback": "언더라인 비율 문제, 슬라이드 0 텍스트 위치 조정 필요",
        "details": {
            "text_position": {"pass": False},
            "underline": {"pass": False}
        }
    }

    creative_result = {
        "score": 65,
        "feedback": "포즈 다양성 부족, 사람 등장 없음",
        "details": {
            "diversity": {
                "total": 12,
                "scores": {
                    "pose_variety": 2,
                    "human_appearance": 1
                }
            }
        }
    }

    plan = regenerator.analyze_and_plan(
        tech_result=tech_result,
        creative_result=creative_result,
        total_slides=8
    )

    print(regenerator.get_regeneration_report(plan))

    # 선택적 재생성 준비 테스트
    prompts = [{"prompt": f"Slide {i} prompt"} for i in range(8)]

    # 실제 디렉토리가 있다면:
    # prep_result = regenerator.prepare_selective_generation(
    #     plan=plan,
    #     existing_images_dir="outputs/broccoli_v1",
    #     output_dir="outputs/broccoli_v2",
    #     prompts=prompts
    # )
    # print(f"재생성 대상: {prep_result['generation_indices']}")
