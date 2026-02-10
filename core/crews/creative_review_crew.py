"""
CreativeReviewCrew - 크리에이티브 검수 Crew
작성: Phase 2 Day 4
업데이트: Phase 7 - Gemini VLM 연동

VLM 기반 크리에이티브 검수 (Gemini Vision 사용)
- AestheticAgent: 미적 균형 검사
- EmotionAgent: 감성 품질 검사
- StoryAgent: 스토리텔링 검사
- DiversityAgent: 다양성 검사

비용: $0 (Gemini Free Tier)
"""

import os
import base64
import json
import asyncio
from pathlib import Path
from datetime import datetime
import sys

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# Phase 7: Gemini VisionLLM 임포트
try:
    from support.utils.vision_llm import VisionLLM
    VISION_LLM_AVAILABLE = True
except ImportError:
    VISION_LLM_AVAILABLE = False
    VisionLLM = None


# 크리에이티브 검수 항목 (100점 만점)
CREATIVE_CHECKLIST = {
    "aesthetic": {  # 25점
        "weight": 25,
        "items": {
            "visual_balance": "표지 제목 크기와 위치가 균형잡힘",
            "underline_ratio": "언더라인이 제목과 비례함",
            "color_tone": "따뜻하고 일관된 색감",
            "composition": "전체적 시각적 균형"
        }
    },
    "emotion": {  # 25점
        "weight": 25,
        "items": {
            "authenticity": "반려견 주인이 찍은 것 같은 자연스러움",
            "expression": "햇살이 표정이 자연스럽고 다양함",
            "warmth": "일상의 따뜻함이 느껴짐",
            "not_ai_like": "AI 또는 스톡 사진 느낌이 아님"
        }
    },
    "storytelling": {  # 25점
        "weight": 25,
        "items": {
            "narrative_flow": "슬라이드 간 서사 흐름이 자연스러움",
            "human_presence": "사람(보호자) 등장이 자연스러움",
            "situation_variety": "다양한 상황/장면 연출",
            "cta_connection": "CTA가 자연스럽게 연결됨"
        }
    },
    "diversity": {  # 25점
        "weight": 25,
        "items": {
            "poses": "포즈 4종 이상 (앉기/눕기/서기/올려다보기)",
            "angles": "앵글 4종 이상 (정면/측면/위/아래)",
            "backgrounds": "배경 2종 이상 (주방/거실)",
            "human_shots": "사람 등장 2장 이상",
            "food_forms": "음식 형태 3종 이상"
        }
    }
}


def run_async(coro):
    """비동기 코루틴을 안전하게 실행하는 헬퍼 함수."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # 이벤트 루프가 없으면 새로 생성
        return asyncio.run(coro)

    # 이미 이벤트 루프가 있으면 ThreadPoolExecutor 사용
    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor() as executor:
        future = executor.submit(asyncio.run, coro)
        return future.result()


class CreativeReviewCrew:
    """
    크리에이티브 검수 Crew

    Phase 7: Gemini VisionLLM을 사용하여
    미적/감성/스토리텔링/다양성 검수 수행

    비용: $0 (Gemini Free Tier)
    """

    def __init__(self):
        self.checklist = CREATIVE_CHECKLIST
        self.gold_standard_dir = ROOT / "images" / "reference" / "gold_standard" / "cherry"

        # Phase 7: Gemini VisionLLM 초기화
        if VISION_LLM_AVAILABLE:
            self.vlm = VisionLLM()
            self.vlm_available = self.vlm.is_available()
        else:
            self.vlm = None
            self.vlm_available = False

    def _default_evaluation(self, category: str, items: dict) -> dict:
        """VLM 없을 때 기본 평가"""
        # 기본 점수 (항목당 3점)
        scores = {item: 3 for item in items.keys()}
        total = len(items) * 3

        return {
            "category": category,
            "scores": scores,
            "total": total,
            "feedback": "VLM 미연결로 기본 평가 적용",
            "strengths": [],
            "improvements": ["VLM 연결 후 정밀 평가 필요"],
            "vlm_used": False
        }

    async def _check_aesthetic_async(self, images: list) -> dict:
        """AestheticAgent: 미적 균형 검사 (비동기)"""
        if not self.vlm_available:
            return self._default_evaluation("aesthetic", self.checklist["aesthetic"]["items"])

        result = await self.vlm.analyze_aesthetic(images)
        result["category"] = "aesthetic"
        return result

    async def _check_emotion_async(self, images: list) -> dict:
        """EmotionAgent: 감성 품질 검사 (비동기)"""
        if not self.vlm_available:
            return self._default_evaluation("emotion", self.checklist["emotion"]["items"])

        result = await self.vlm.analyze_emotion(images)
        result["category"] = "emotion"
        return result

    async def _check_storytelling_async(self, images: list) -> dict:
        """StoryAgent: 스토리텔링 검사 (비동기)"""
        if not self.vlm_available:
            return self._default_evaluation("storytelling", self.checklist["storytelling"]["items"])

        result = await self.vlm.analyze_storytelling(images)
        result["category"] = "storytelling"
        return result

    async def _check_diversity_async(self, images: list) -> dict:
        """DiversityAgent: 다양성 검사 (비동기)"""
        if not self.vlm_available:
            return self._default_evaluation("diversity", self.checklist["diversity"]["items"])

        result = await self.vlm.analyze_diversity(images)
        result["category"] = "diversity"
        return result

    async def _compare_with_gold_standard_async(self, images: list) -> dict:
        """체리(Gold Standard)와 비교 (비동기)"""
        if not self.vlm_available:
            return {
                "similarity_score": 70,
                "feedback": "VLM 미연결로 비교 불가",
                "vlm_used": False
            }

        gold_images = sorted([str(f) for f in self.gold_standard_dir.glob("*.png")])[:3]

        if not gold_images:
            return {
                "similarity_score": 75,
                "feedback": "Gold Standard 이미지 없음",
                "vlm_used": False
            }

        result = await self.vlm.compare_with_gold_standard(images, gold_images)
        return result

    def _check_aesthetic(self, images: list) -> dict:
        """AestheticAgent: 미적 균형 검사 (동기 래퍼)"""
        return run_async(self._check_aesthetic_async(images))

    def _check_emotion(self, images: list) -> dict:
        """EmotionAgent: 감성 품질 검사 (동기 래퍼)"""
        return run_async(self._check_emotion_async(images))

    def _check_storytelling(self, images: list) -> dict:
        """StoryAgent: 스토리텔링 검사 (동기 래퍼)"""
        return run_async(self._check_storytelling_async(images))

    def _check_diversity(self, images: list) -> dict:
        """DiversityAgent: 다양성 검사 (동기 래퍼)"""
        return run_async(self._check_diversity_async(images))

    def _compare_with_gold_standard(self, images: list) -> dict:
        """체리(Gold Standard)와 비교 (동기 래퍼)"""
        return run_async(self._compare_with_gold_standard_async(images))

    def run(
        self,
        content_dir: str,
        food_name: str
    ) -> dict:
        """
        크리에이티브 검수 실행

        Args:
            content_dir: 콘텐츠 폴더
            food_name: 음식명

        Returns:
            {
                "success": bool,
                "total_score": int,
                "grade": str,
                "pass": bool,
                "categories": {...},
                "gold_comparison": {...}
            }
        """
        print(f"{'━'*60}")
        print(f"  CreativeReviewCrew: 크리에이티브 검수")
        print(f"{'━'*60}")
        print(f"   폴더: {content_dir}")
        print(f"   VLM: {'Gemini 연결됨' if self.vlm_available else '미연결 (기본 평가)'}")
        print()

        content_path = Path(content_dir)
        images = sorted([str(f) for f in content_path.glob(f"{food_name}_*.png")])

        if not images:
            return {
                "success": False,
                "error": "이미지 없음",
                "total_score": 0,
                "pass": False
            }

        print(f"   이미지: {len(images)}장")
        print()

        categories = {}
        total_score = 0

        # 1. 미적 균형 검사
        print("[1/5] 미적 균형 검사...")
        aesthetic = self._check_aesthetic(images)
        categories["aesthetic"] = aesthetic
        # 점수 정규화 (총 25점 만점)
        aesthetic_score = min(aesthetic.get("total", 15), 25)
        total_score += aesthetic_score
        print(f"      {aesthetic_score}/25점 {'(Gemini)' if aesthetic.get('vlm_used') else '(기본)'}")

        # 2. 감성 품질 검사
        print("[2/5] 감성 품질 검사...")
        emotion = self._check_emotion(images)
        categories["emotion"] = emotion
        emotion_score = min(emotion.get("total", 15), 25)
        total_score += emotion_score
        print(f"      {emotion_score}/25점 {'(Gemini)' if emotion.get('vlm_used') else '(기본)'}")

        # 3. 스토리텔링 검사
        print("[3/5] 스토리텔링 검사...")
        storytelling = self._check_storytelling(images)
        categories["storytelling"] = storytelling
        storytelling_score = min(storytelling.get("total", 15), 25)
        total_score += storytelling_score
        print(f"      {storytelling_score}/25점 {'(Gemini)' if storytelling.get('vlm_used') else '(기본)'}")

        # 4. 다양성 검사
        print("[4/5] 다양성 검사...")
        diversity = self._check_diversity(images)
        categories["diversity"] = diversity
        diversity_score = min(diversity.get("total", 15), 25)
        total_score += diversity_score
        print(f"      {diversity_score}/25점 {'(Gemini)' if diversity.get('vlm_used') else '(기본)'}")

        # 5. Gold Standard 비교
        print("[5/5] Gold Standard(체리) 비교...")
        gold_comparison = self._compare_with_gold_standard(images)
        print(f"      유사도: {gold_comparison.get('similarity_score', 0)}%")

        # 등급 결정 (Phase 6/7: 기준 상향)
        if total_score >= 95:
            grade = "A+"
            grade_desc = "매우 우수"
        elif total_score >= 90:
            grade = "A"
            grade_desc = "우수"
        elif total_score >= 80:
            grade = "B"
            grade_desc = "양호"
        elif total_score >= 70:
            grade = "C"
            grade_desc = "보통"
        else:
            grade = "F"
            grade_desc = "불량"

        # 판정 (Phase 6/7: 90점 통과, 80점 조건부)
        if total_score >= 90:
            verdict = "PASS"
            verdict_desc = "게시 승인"
        elif total_score >= 80:
            verdict = "CONDITIONAL"
            verdict_desc = "조건부 승인 (경미한 수정 권장)"
        else:
            verdict = "FAIL"
            verdict_desc = "재작업 필요"

        # 결과 출력
        print()
        print(f"{'━'*60}")
        print(f"  크리에이티브 검수 결과")
        print(f"{'━'*60}")
        print(f"   미적 균형:    {aesthetic_score}/25점")
        print(f"   감성 품질:    {emotion_score}/25점")
        print(f"   스토리텔링:   {storytelling_score}/25점")
        print(f"   다양성:       {diversity_score}/25점")
        print(f"   {'─'*40}")
        print(f"   총점: {total_score}/100점")
        print(f"   등급: {grade} ({grade_desc})")
        print(f"   Gold Standard 유사도: {gold_comparison.get('similarity_score', 0)}%")
        print(f"\n   판정: {'PASS' if verdict == 'PASS' else 'CONDITIONAL' if verdict == 'CONDITIONAL' else 'FAIL'} - {verdict_desc}")
        print(f"{'━'*60}")

        return {
            "success": True,
            "total_score": round(total_score, 1),
            "max_score": 100,
            "grade": grade,
            "grade_desc": grade_desc,
            "verdict": verdict,
            "verdict_desc": verdict_desc,
            "pass": verdict in ["PASS", "CONDITIONAL"],
            "categories": categories,
            "gold_comparison": gold_comparison,
            "vlm_used": self.vlm_available,
            "vlm_provider": "gemini" if self.vlm_available else None,
            "timestamp": datetime.now().isoformat()
        }

    def kickoff(self, inputs: dict) -> dict:
        """
        CrewAI 스타일 실행

        Args:
            inputs: {
                "content_dir": "outputs/watermelon_final/",
                "food_name": "watermelon"
            }
        """
        return self.run(
            content_dir=inputs.get("content_dir", ""),
            food_name=inputs.get("food_name", "unknown")
        )


# CLI 실행
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="CreativeReviewCrew - 크리에이티브 검수 (Phase 7: Gemini VLM)")
    parser.add_argument("content_dir", help="콘텐츠 폴더")
    parser.add_argument("--food", default="unknown", help="음식명")
    args = parser.parse_args()

    crew = CreativeReviewCrew()
    result = crew.kickoff({
        "content_dir": args.content_dir,
        "food_name": args.food
    })

    print(f"\n{result['verdict']}: {result['total_score']}/100점 ({result['grade']})")
