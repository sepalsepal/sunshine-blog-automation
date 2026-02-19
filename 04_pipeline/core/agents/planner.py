"""
PlannerAgent - 콘텐츠 기획 에이전트 (v5)
주제를 받아 슬라이드 콘텐츠 기획안 생성

v5 워크플로우:
- 1단계: TopicExplorerAgent - 주제 탐색 (김작가)
- 2단계: TopicValidatorAgent - 주제 검증 (최검증)
- 4단계: PlannerAgent - 슬라이드 기획 (김작가)

슬라이드 수 설정 (config.yaml → agents.planner.slides):
- default: 7 (일반)
- by_safety: dangerous=5, safe=7, caution=7
- by_topic: 주제별 오버라이드
- deep_dive: 10 (특집)

Author: 김작가 (v5 업데이트)
"""

import json
import os
from pathlib import Path
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple
from .base import BaseAgent, AgentResult


# topics_expanded.json 로드
_TOPICS_DB: Optional[Dict] = None


def _load_topics_db() -> Dict:
    """topics_expanded.json에서 주제 데이터 로드 (캐싱)"""
    global _TOPICS_DB
    if _TOPICS_DB is not None:
        return _TOPICS_DB

    db_path = Path(__file__).parent.parent / "config" / "topics_expanded.json"
    if db_path.exists():
        with open(db_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        topics_map = {}
        for category_key, category in data.get("categories", {}).items():
            for topic in category.get("topics", []):
                topics_map[topic["id"]] = {
                    "id": topic["id"],
                    "ko": topic["ko"],
                    "safety": topic["safety"],
                    "note": topic.get("note", ""),
                    "category": category_key,
                    "category_label": category.get("label", ""),
                }
        _TOPICS_DB = topics_map
    else:
        _TOPICS_DB = {}

    return _TOPICS_DB


def _get_existing_contents() -> List[str]:
    """images/ 폴더에서 기제작 콘텐츠 목록 추출"""
    images_path = Path(__file__).parent.parent / "images"
    existing = []

    if images_path.exists():
        for folder in images_path.iterdir():
            if folder.is_dir() and not folder.name.startswith('.'):
                # 폴더명에서 영문명 추출 (예: 001_pumpkin → pumpkin)
                parts = folder.name.split('_', 1)
                if len(parts) == 2:
                    existing.append(parts[1])
                else:
                    existing.append(folder.name)

    return existing


# v5 주제 검증 기준 (config.yaml에서 오버라이드 가능)
_TOPIC_VALIDATION_CRITERIA = {
    "duplicate_check": {"weight": 20, "description": "기제작 목록에 없어야 함"},
    "trend_score": {"weight": 20, "description": "검색량/관심도 있어야 함"},
    "safety_score": {"weight": 20, "description": "강아지에게 위험하지 않아야 함"},
    "content_fit": {"weight": 20, "description": "7장 구성 가능해야 함"},
    "visual_potential": {"weight": 20, "description": "이미지로 표현하기 좋아야 함"},
}


class TopicExplorerAgent(BaseAgent):
    """
    1단계: 주제 탐색 에이전트 (김작가)

    PD 디렉션이 없을 때 실행:
    - 기제작 목록 확인
    - 트렌드 웹서치 (향후 구현)
    - 추천 5개안 생성
    """

    @property
    def name(self) -> str:
        return "TopicExplorer"

    async def execute(self, input_data: Any) -> AgentResult:
        """
        주제 탐색 실행

        Args:
            input_data: None 또는 {"web_search": True}
        """
        self.log("주제 탐색 시작...")

        # 1. 기제작 콘텐츠 목록 확인
        existing = _get_existing_contents()
        self.log(f"기제작 콘텐츠: {len(existing)}개 ({', '.join(existing[:5])}...)")

        # 2. topics_expanded.json에서 미제작 주제 추출
        db = _load_topics_db()
        candidates = []
        for topic_id, topic_info in db.items():
            if topic_id not in existing:
                candidates.append({
                    "food": topic_info["ko"],
                    "food_en": topic_id,
                    "safety": topic_info["safety"],
                    "category": topic_info.get("category", ""),
                    "note": topic_info.get("note", ""),
                })

        # 3. 추천 5개안 생성 (안전한 것 우선)
        # 정렬: safe > caution > dangerous
        safety_order = {"safe": 0, "caution": 1, "dangerous": 2, "unknown": 3}
        candidates.sort(key=lambda x: safety_order.get(x["safety"], 3))

        recommendations = []
        for i, candidate in enumerate(candidates[:5]):
            recommendations.append({
                "rank": i + 1,
                "food": candidate["food"],
                "food_en": candidate["food_en"],
                "safety": candidate["safety"],
                "trend_reason": f"강아지 간식 트렌드 (카테고리: {candidate['category']})",
                "interest_score": 90 - (i * 5),  # 임시 점수
            })

        result = {
            "recommendations": recommendations,
            "excluded": existing,
            "total_candidates": len(candidates),
            "metadata": {
                "searched_at": datetime.now().isoformat(),
                "agent": "kimjakga",
                "step": 1,
            }
        }

        self.log(f"추천 5개안 생성 완료: {[r['food'] for r in recommendations]}")

        return AgentResult(
            success=True,
            data=result,
            metadata={"step": 1, "recommendations_count": len(recommendations)}
        )


class TopicValidatorAgent(BaseAgent):
    """
    2단계: 주제 검증 에이전트 (최검증)

    김작가 추천 5개안 검토 → 승인/반려
    """

    @property
    def name(self) -> str:
        return "TopicValidator"

    def _validate_topic(self, recommendation: Dict, existing: List[str]) -> Tuple[bool, int, Dict]:
        """
        개별 주제 검증

        Returns:
            (passed, total_score, scores_detail)
        """
        scores = {}
        topic_db = _load_topics_db()
        topic_info = topic_db.get(recommendation["food_en"], {})

        # 1. 중복 체크 (20점)
        if recommendation["food_en"] in existing:
            scores["duplicate_check"] = 0
        else:
            scores["duplicate_check"] = 20

        # 2. 트렌드성 (20점) - 관심도 기반
        interest = recommendation.get("interest_score", 50)
        scores["trend_score"] = min(20, int(interest / 5))

        # 3. 안전성 (20점)
        safety = recommendation.get("safety", topic_info.get("safety", "unknown"))
        if safety == "safe":
            scores["safety_score"] = 20
        elif safety == "caution":
            scores["safety_score"] = 15
        elif safety == "dangerous":
            scores["safety_score"] = 5  # 위험 식품도 경고 콘텐츠로 가능
        else:
            scores["safety_score"] = 10

        # 4. 콘텐츠 적합성 (20점)
        # 효능/주의사항 등 정보가 충분한지 확인
        if topic_info.get("note"):
            scores["content_fit"] = 20
        else:
            scores["content_fit"] = 15

        # 5. 비주얼 잠재력 (20점)
        # 음식 카테고리 기반 평가
        visual_categories = {"fruits": 20, "vegetables": 18, "protein": 16, "grains": 14}
        category = topic_info.get("category", "")
        scores["visual_potential"] = visual_categories.get(category, 15)

        total_score = sum(scores.values())
        passed = total_score >= 90

        return passed, total_score, scores

    async def execute(self, input_data: Any) -> AgentResult:
        """
        주제 검증 실행

        Args:
            input_data: TopicExplorerAgent 출력 결과
        """
        self.log("주제 검증 시작...")

        recommendations = input_data.get("recommendations", [])
        excluded = input_data.get("excluded", [])

        if not recommendations:
            return AgentResult(
                success=False,
                data={"error": "추천 목록이 비어있습니다"},
                metadata={"step": 2}
            )

        # 각 추천안 검증
        validation_results = []
        selected = None

        for rec in recommendations:
            passed, score, scores = self._validate_topic(rec, excluded)
            result = {
                "food": rec["food"],
                "food_en": rec["food_en"],
                "rank": rec["rank"],
                "passed": passed,
                "total_score": score,
                "scores": scores,
            }
            validation_results.append(result)

            # 첫 번째 통과한 주제 선정
            if passed and selected is None:
                selected = result

        # 결과 생성
        if selected:
            output = {
                "validation_type": "topic_selection",
                "selected_topic": {
                    "food": selected["food"],
                    "food_en": selected["food_en"],
                    "rank": selected["rank"],
                },
                "validation_result": {
                    "passed": True,
                    "total_score": selected["total_score"],
                    "scores": selected["scores"],
                },
                "all_results": validation_results,
                "feedback": f"'{selected['food']}' 선정 완료. 콘텐츠 제작 진행.",
                "next_step": 3,
                "metadata": {
                    "validated_at": datetime.now().isoformat(),
                    "agent": "choigeomjeung",
                    "step": 2,
                }
            }
            self.log(f"✅ 주제 승인: {selected['food']} ({selected['total_score']}점)")
        else:
            # 모든 주제 반려
            output = {
                "validation_type": "topic_selection",
                "selected_topic": None,
                "validation_result": {
                    "passed": False,
                    "failed_items": [r for r in validation_results if not r["passed"]],
                },
                "all_results": validation_results,
                "feedback": "모든 추천안이 90점 미만. 주제 탐색 재작업 필요.",
                "next_step": 1,
                "action_required": "김작가에게 재작업 요청",
                "metadata": {
                    "validated_at": datetime.now().isoformat(),
                    "agent": "choigeomjeung",
                    "step": 2,
                }
            }
            self.log("❌ 모든 주제 반려. 1단계 재작업 필요.")

        return AgentResult(
            success=selected is not None,
            data=output,
            metadata={"step": 2, "passed": selected is not None}
        )


# v4 워크플로우: 7장 슬라이드 구성 (01~07)
# 01: cover, 02: result, 03: benefit1, 04: benefit2, 05: caution, 06: amount, 07: cta
_SLIDE_STRUCTURE_7 = {
    "safe": [
        {"type": "cover", "title": ""},  # 01 표지 (동적 생성)
        {"type": "result", "title": "급여 가능!"},  # 02 결론
        {"type": "benefit1", "title": "효능 1"},  # 03 효능1
        {"type": "benefit2", "title": "효능 2"},  # 04 효능2
        {"type": "caution", "title": "주의사항"},  # 05 주의사항
        {"type": "amount", "title": "급여량 가이드"},  # 06 급여량
        {"type": "cta", "title": ""},  # 07 CTA (동적 생성)
    ],
    "caution": [
        {"type": "cover", "title": ""},
        {"type": "result", "title": "조건부 급여 가능"},
        {"type": "benefit1", "title": "효능"},
        {"type": "benefit2", "title": "안전한 급여 방법"},
        {"type": "caution", "title": "절대 금지 부위"},
        {"type": "amount", "title": "급여량 가이드"},
        {"type": "cta", "title": ""},
    ],
    "dangerous": [
        {"type": "cover", "title": ""},
        {"type": "result", "title": "급여 금지!"},
        {"type": "benefit1", "title": "왜 위험한가요?"},
        {"type": "benefit2", "title": "독성 성분"},
        {"type": "caution", "title": "중독 증상"},
        {"type": "amount", "title": "실수로 먹었다면?"},
        {"type": "cta", "title": ""},
    ],
}

# 레거시 호환: 안전도별 콘텐츠 슬라이드 풀 (10장 구성용)
_CONTENT_POOL = {
    "safe": [
        "급여 가능!",
        "효능 1",
        "효능 2",
        "효능 3",
        "주의사항",
        "급여량 가이드",
        "준비 방법",
        "햇살이의 한마디",
    ],
    "caution": [
        "조건부 급여 가능",
        "효능",
        "위험 요소",
        "안전한 급여 방법",
        "절대 금지 부위",
        "급여량 가이드",
        "이상 증상 시 대처",
        "햇살이의 한마디",
    ],
    "dangerous": [
        "급여 금지!",
        "왜 위험한가요?",
        "독성 성분",
        "중독 증상",
        "실수로 먹었다면?",
        "응급 대처법",
        "대체 간식 추천",
        "수의사 연락처",
    ],
}


class PlannerAgent(BaseAgent):
    """콘텐츠 기획 에이전트 (슬라이드 수 config 연동)"""

    @property
    def name(self) -> str:
        return "Planner"

    def _lookup_topic(self, topic: str) -> Dict:
        """topics_expanded.json에서 주제 조회"""
        db = _load_topics_db()
        if topic in db:
            return db[topic]
        return {"id": topic, "ko": topic, "safety": "unknown", "note": "", "category": "unknown"}

    def _get_slide_count(self, topic: str, safety: str) -> int:
        """
        슬라이드 수 결정 (우선순위: by_topic > by_safety > default)

        config.yaml → agents.planner.slides
        """
        slides_config = self.config.get("slides", {})
        default = slides_config.get("default", 7)

        # 1순위: 주제별 오버라이드
        by_topic = slides_config.get("by_topic", {})
        if topic in by_topic:
            return by_topic[topic]

        # 2순위: 안전도별 설정
        by_safety = slides_config.get("by_safety", {})
        if safety in by_safety:
            return by_safety[safety]

        # 3순위: 기본값
        return default

    async def execute(self, input_data: Any) -> AgentResult:
        """
        콘텐츠 기획 실행

        Args:
            input_data: {"topic": "cherry"} 또는 "cherry"
                        {"topic": "cherry", "deep_dive": True} → 특집 10장
        """
        if isinstance(input_data, str):
            topic = input_data
            deep_dive = False
        else:
            topic = input_data.get("topic")
            deep_dive = input_data.get("deep_dive", False)

        topic_info = self._lookup_topic(topic)
        topic_kr = topic_info["ko"]
        safety = topic_info["safety"]

        # 슬라이드 수 결정
        if deep_dive:
            slide_count = self.config.get("slides", {}).get("deep_dive", 10)
        else:
            slide_count = self._get_slide_count(topic, safety)

        self.log(f"주제 '{topic}' ({topic_kr}) 기획 시작 [안전도: {safety}, 슬라이드: {slide_count}장]")

        # 슬라이드 생성
        slides = self._build_slides(topic_kr, safety, slide_count)

        plan = {
            "topic": topic,
            "topic_kr": topic_kr,
            "safety": safety,
            "note": topic_info["note"],
            "category": topic_info["category"],
            "slide_count": slide_count,
            "slides": slides,
            "caption": "",
            "hashtags": []
        }

        return AgentResult(
            success=True,
            data=plan,
            metadata={"slides_count": len(slides), "safety": safety}
        )

    def _build_slides(self, topic_kr: str, safety: str, count: int) -> List[Dict]:
        """
        슬라이드 동적 생성

        v4 워크플로우 (7장):
        01: cover, 02: result, 03: benefit1, 04: benefit2,
        05: caution, 06: amount, 07: cta

        레거시 (10장): [cover] + [content × 8] + [cta]
        """
        # cover/cta 타이틀 결정
        if safety == "dangerous":
            cover_title = f"강아지 {topic_kr} 절대 금지!"
            cta_title = "공유해서 알려주세요!"
        elif safety == "caution":
            cover_title = f"강아지 {topic_kr} 먹어도 되나요?"
            cta_title = "저장 & 팔로우!"
        else:
            cover_title = f"강아지 {topic_kr} 먹어도 되나요?"
            cta_title = "저장 & 팔로우!"

        # v4 워크플로우: 7장 구조 사용
        if count == 7:
            structure = _SLIDE_STRUCTURE_7.get(safety, _SLIDE_STRUCTURE_7["safe"])
            slides = []
            for i, slide_info in enumerate(structure):
                slide = {
                    "index": i,
                    "type": slide_info["type"],
                    "title": slide_info["title"]
                }
                # cover/cta 타이틀 동적 설정
                if slide_info["type"] == "cover":
                    slide["title"] = cover_title
                elif slide_info["type"] == "cta":
                    slide["title"] = cta_title
                slides.append(slide)
            return slides

        # 레거시: 가변 장수 구성 (기존 10장 콘텐츠 대응)
        content_count = max(count - 2, 1)
        pool = _CONTENT_POOL.get(safety, _CONTENT_POOL["safe"])
        content_titles = pool[:content_count]

        slides = [{"index": 0, "type": "cover", "title": cover_title}]
        for i, title in enumerate(content_titles):
            slides.append({"index": i + 1, "type": "content", "title": title})
        slides.append({"index": len(slides), "type": "cta", "title": cta_title})

        return slides
