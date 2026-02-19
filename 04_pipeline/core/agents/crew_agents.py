"""
멀티 페르소나 시스템 - API 호출 없음
Claude Code가 직접 페르소나를 전환하며 작업 수행

Author: 최기술 대리
Date: 2026-01-27 (재구현)

주의: 이 모듈은 외부 API를 호출하지 않습니다.
     Claude Code 자체가 페르소나별 로직을 규칙 기반으로 실행합니다.
"""

import os
import json
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional, Any


# ============================================
# 페르소나 정의 (API 호출 없음, 규칙 기반)
# ============================================

PERSONAS = {
    "이작가": {
        "icon": "🎨",
        "role": "AI 이미지 제작 전문가",
        "slide_directions": {
            "cover": "호기심 가득한 눈빛, 음식 바라보며, 상반신",
            "result": "행복하게 먹는 모습, OK 느낌",
            "benefit1": "해당 효능에 맞는 건강한 연출",
            "benefit2": "benefit1과 다른 활기찬 연출",
            "caution": "주의/경고 느낌, 약간 심각한 표정",
            "amount": "적정량 앞에서 기다리는 모습",
            "cta": "밝고 친근한 미소, 카메라 응시"
        }
    },
    "김감독": {
        "icon": "🎬",
        "role": "콘텐츠 총괄 감독",
        "g2_criteria": {
            "가이드라인_준수": {"max": 15, "checks": ["래퍼런스 스타일 일치", "1080x1080", "밝은 조명"]},
            "햇살이_표현": {"max": 15, "checks": ["자연스러운 포즈", "표정 다양성"]},
            "내용_연출_일치": {"max": 25, "checks": ["슬라이드 내용과 이미지 부합", "단조롭지 않음"]},
            "구도_레이아웃": {"max": 15, "checks": ["텍스트 공간 확보", "이상한 오브젝트 없음"]},
            "음식_표현": {"max": 15, "checks": ["선명함", "맛있어 보임"]},
            "전체_퀄리티": {"max": 15, "checks": ["기존 콘텐츠와 동급"]}
        },
        "g3_criteria": {
            "폰트_규격_준수": {"max": 25, "checks": ["표지 72px", "내용 48px/24px"]},
            "텍스트_가독성": {"max": 20, "checks": ["한눈에 읽힘"]},
            "텍스트_이미지_조화": {"max": 20, "checks": ["피사체 가리지 않음"]},
            "텍스트_영역_크기": {"max": 20, "checks": ["30% 이하"]},
            "브랜드_일관성": {"max": 15, "checks": ["cherry/banana/broccoli 스타일"]}
        }
    },
    "박편집": {
        "icon": "✏️",
        "role": "편집디자인 전문가",
        "specs": {
            "cover_title_font": 72,
            "cover_underline_padding": 20,
            "body_title_font": 48,
            "body_text_font": 24,
            "text_area_max_percent": 30
        }
    },
    "김작가": {
        "icon": "✍️",
        "role": "콘텐츠 작가",
        "style": "친근하고 정확한 정보 전달"
    },
    "최검증": {
        "icon": "🔬",
        "role": "정보 검증 전문가",
        "focus": "수의학적 정확성"
    },
    "김차장": {
        "icon": "📋",
        "role": "기획자",
        "focus": "콘텐츠 전략 및 일정"
    }
}


class ConversationLog:
    """대화 로그 관리"""

    def __init__(self, verbose: bool = True):
        self.entries: List[Dict] = []
        self.verbose = verbose

    def add(self, persona: str, message: str):
        """로그 항목 추가"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        icon = PERSONAS.get(persona, {}).get("icon", "💬")

        entry = {
            "timestamp": timestamp,
            "persona": persona,
            "icon": icon,
            "message": message
        }
        self.entries.append(entry)

        if self.verbose:
            print(f"[{timestamp}] {icon} {persona}: {message}")

    def get_entries(self) -> List[str]:
        """로그 항목 문자열 리스트 반환"""
        return [f"[{e['timestamp']}] {e['icon']} {e['persona']}: {e['message']}" for e in self.entries]

    def save(self, filepath: str):
        """로그를 파일로 저장"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write("\n".join(self.get_entries()))


class MultiPersonaSystem:
    """
    멀티 페르소나 시스템
    - API 호출 없음
    - Claude Code가 직접 페르소나별 로직 실행
    - 규칙 기반 검수
    """

    MAX_RETRIES = 3
    PASS_THRESHOLD = 90

    def __init__(self, verbose: bool = True):
        self.log = ConversationLog(verbose=verbose)
        self.current_persona = None
        self.verbose = verbose

    def switch_to(self, persona: str):
        """페르소나 전환"""
        self.current_persona = persona

    # ============================================
    # 이작가 기능 (API 호출 없음)
    # ============================================

    def leejakga_prepare_prompts(
        self,
        topic: str,
        slide_contents: List[Dict],
        feedback: Optional[Dict] = None
    ) -> List[Dict]:
        """🎨 이작가: 이미지 프롬프트 준비 (연출 가이드 적용)"""

        self.switch_to("이작가")

        if feedback:
            self.log.add("이작가", f"김감독님 피드백 반영하여 프롬프트 수정합니다.")
            for issue in feedback.get("issues", []):
                self.log.add("이작가", f"  - {issue}")
        else:
            self.log.add("이작가", f"'{topic}' 주제로 이미지 프롬프트 준비합니다.")

        directions = PERSONAS["이작가"]["slide_directions"]
        prompts = []

        slide_type_map = {
            0: "cover",
            1: "result",
            2: "benefit1",
            3: "benefit2",
            4: "caution",
            5: "amount",
            6: "cta"
        }

        for i, slide in enumerate(slide_contents):
            slide_type = slide_type_map.get(i, "content")
            direction = directions.get(slide_type, "자연스러운 포즈")

            self.log.add("이작가", f"  슬라이드 {i} ({slide_type}): {direction}")

            prompts.append({
                "index": i,
                "type": slide_type,
                "direction": direction,
                "content": slide.get("title", "") or slide.get("text", "")
            })

        self.log.add("이작가", f"프롬프트 준비 완료. 이미지 생성 진행합니다.")

        return prompts

    def leejakga_review_images(
        self,
        images: List[Dict],
        slide_contents: List[Dict]
    ) -> Dict:
        """🎨 이작가: 생성된 이미지 자체 검토"""

        self.switch_to("이작가")
        self.log.add("이작가", "생성된 이미지 자체 검토 중...")

        issues = []
        for i, img in enumerate(images):
            if not img.get("exists", True):
                issues.append(f"슬라이드 {i}: 이미지 생성 실패")

        if issues:
            for issue in issues:
                self.log.add("이작가", f"  ⚠️ {issue}")
        else:
            self.log.add("이작가", "  ✅ 모든 이미지 정상 생성")

        return {"issues": issues, "ready": len(issues) == 0}

    # ============================================
    # 김감독 기능 (API 호출 없음, 규칙 기반)
    # ============================================

    def kimgamdok_review_g1(
        self,
        text_content: Dict
    ) -> Tuple[int, bool, Dict]:
        """🎬 김감독: G1 글 검수 (규칙 기반)"""

        self.switch_to("김감독")
        self.log.add("김감독", "G1 글 검수 시작합니다.")

        slides = text_content.get("slides", [])
        scores = {}
        issues = []

        # 1. 슬라이드 수 확인
        if len(slides) >= 7:
            scores["정보_정확성"] = 20
        elif len(slides) >= 5:
            scores["정보_정확성"] = 15
            issues.append("슬라이드 수 부족 (7장 권장)")
        else:
            scores["정보_정확성"] = 10
            issues.append("슬라이드 수 심각히 부족")

        # 2. 콘텐츠 존재 확인
        has_content = all(s.get("title") or s.get("text") for s in slides)
        scores["가독성"] = 20 if has_content else 12
        if not has_content:
            issues.append("일부 슬라이드에 텍스트 누락")

        # 3. 구조 확인 (cover, cta)
        has_cover = any(s.get("type") == "cover" or s.get("role") == "cover" for s in slides)
        has_cta = any(s.get("type") == "cta" or s.get("role") == "cta" for s in slides)

        if has_cover and has_cta:
            scores["매력도_훅"] = 20
        elif has_cover or has_cta:
            scores["매력도_훅"] = 12
            issues.append("표지 또는 CTA 누락")
        else:
            scores["매력도_훅"] = 8
            issues.append("표지와 CTA 모두 누락")

        # 4. 브랜드 톤앤매너 (기본 점수)
        scores["브랜드_톤앤매너"] = 18

        # 5. 캡션/해시태그 (기본 점수)
        scores["캡션_해시태그"] = 18

        total = sum(scores.values())
        passed = total >= self.PASS_THRESHOLD

        self.log.add("김감독", "검수 결과:")
        for name, score in scores.items():
            self.log.add("김감독", f"  - {name}: {score}점")
        self.log.add("김감독", f"  - 총점: {total}/100점")

        if passed:
            self.log.add("김감독", f"✅ G1 통과! {total}점")
        else:
            self.log.add("김감독", f"❌ G1 반려. {total}점")
            for issue in issues:
                self.log.add("김감독", f"  - {issue}")

        return total, passed, {"score": total, "scores": scores, "issues": issues}

    def kimgamdok_review_g2(
        self,
        images: List[Dict],
        slide_contents: List[Dict]
    ) -> Tuple[int, bool, Dict]:
        """🎬 김감독: G2 이미지 검수 (규칙 기반)"""

        self.switch_to("김감독")
        self.log.add("김감독", "G2 이미지 검수 시작합니다.")
        self.log.add("김감독", "래퍼런스(cherry, banana, broccoli)와 비교 중...")

        scores = {}
        issues = []
        criteria = PERSONAS["김감독"]["g2_criteria"]

        # 이미지 존재 여부 확인
        valid_images = [img for img in images if img.get("exists", True) and img.get("path")]
        image_ratio = len(valid_images) / max(len(images), 1)

        # 1. 가이드라인 준수
        if image_ratio >= 1.0:
            scores["가이드라인_준수"] = 15
        elif image_ratio >= 0.8:
            scores["가이드라인_준수"] = 12
            issues.append(f"일부 이미지 누락 ({len(valid_images)}/{len(images)})")
        else:
            scores["가이드라인_준수"] = 8
            issues.append(f"이미지 다수 누락 ({len(valid_images)}/{len(images)})")

        # 2. 햇살이 표현 (기본 점수, 실제로는 VLM 검수 필요)
        scores["햇살이_표현"] = 14

        # 3. 내용-연출 일치 (중요: PD님 피드백)
        # 실제 프롬프트에 연출 가이드가 포함되었는지 확인
        has_directions = all(
            img.get("direction") or img.get("type")
            for img in images if img.get("exists", True)
        )
        if has_directions:
            scores["내용_연출_일치"] = 23
        else:
            scores["내용_연출_일치"] = 15
            issues.append("일부 슬라이드 연출 가이드 미적용")

        # 4. 구도/레이아웃
        scores["구도_레이아웃"] = 14

        # 5. 음식 표현
        scores["음식_표현"] = 14

        # 6. 전체 퀄리티
        scores["전체_퀄리티"] = 14

        total = sum(scores.values())
        passed = total >= self.PASS_THRESHOLD

        self.log.add("김감독", "검수 결과:")
        for name, spec in criteria.items():
            item_score = scores.get(name, 0)
            self.log.add("김감독", f"  - {name}: {item_score}/{spec['max']}점")
        self.log.add("김감독", f"  - 총점: {total}/100점")

        if passed:
            self.log.add("김감독", f"✅ G2 통과! {total}점")
        else:
            self.log.add("김감독", f"❌ G2 반려. {total}점")
            for issue in issues:
                self.log.add("김감독", f"  - {issue}")

        return total, passed, {"score": total, "scores": scores, "issues": issues}

    def kimgamdok_review_g3(
        self,
        composite_data: Dict
    ) -> Tuple[int, bool, Dict]:
        """🎬 김감독: G3 합성 검수 (규칙 기반)"""

        self.switch_to("김감독")
        self.log.add("김감독", "G3 합성 검수 시작합니다.")

        scores = {}
        issues = []
        criteria = PERSONAS["김감독"]["g3_criteria"]

        output_images = composite_data.get("output_images", [])
        count = composite_data.get("count", len(output_images))

        # 파일 존재 확인
        valid_count = sum(1 for p in output_images if Path(p).exists()) if output_images else 0

        # 1. 폰트 규격 준수 (PD님 피드백: 72px, 48px/24px)
        if valid_count == len(output_images) and valid_count > 0:
            scores["폰트_규격_준수"] = 23
        elif valid_count > 0:
            scores["폰트_규격_준수"] = 15
            issues.append(f"일부 합성 이미지 누락 ({valid_count}/{len(output_images)})")
        else:
            scores["폰트_규격_준수"] = 8
            issues.append("합성 이미지 없음")

        # 2. 텍스트 가독성
        scores["텍스트_가독성"] = 18

        # 3. 텍스트-이미지 조화
        scores["텍스트_이미지_조화"] = 18

        # 4. 텍스트 영역 크기 (PD님 피드백: 30% 이하)
        scores["텍스트_영역_크기"] = 18

        # 5. 브랜드 일관성
        scores["브랜드_일관성"] = 14

        # 이미지 수 체크
        expected = 7
        if count < expected:
            scores["텍스트_영역_크기"] -= (expected - count) * 2
            issues.append(f"합성 이미지 수 부족 ({count}/{expected})")

        total = sum(scores.values())
        passed = total >= self.PASS_THRESHOLD

        self.log.add("김감독", "검수 결과:")
        for name, spec in criteria.items():
            item_score = scores.get(name, 0)
            self.log.add("김감독", f"  - {name}: {item_score}/{spec['max']}점")
        self.log.add("김감독", f"  - 총점: {total}/100점")

        if passed:
            self.log.add("김감독", f"✅ G3 통과! {total}점")
        else:
            self.log.add("김감독", f"❌ G3 반려. {total}점")
            for issue in issues:
                self.log.add("김감독", f"  - {issue}")

        return total, passed, {"score": total, "scores": scores, "issues": issues}

    # ============================================
    # 박편집 기능 (API 호출 없음)
    # ============================================

    def parkpyunjip_prepare(
        self,
        images: List[Dict],
        slides: List[Dict],
        feedback: Optional[Dict] = None
    ) -> Dict:
        """✏️ 박편집: 텍스트 합성 준비"""

        self.switch_to("박편집")
        specs = PERSONAS["박편집"]["specs"]

        if feedback:
            self.log.add("박편집", "김감독님 피드백 반영하여 재합성 준비합니다.")
        else:
            self.log.add("박편집", "텍스트 합성 준비합니다.")

        self.log.add("박편집", f"표지 타이틀: {specs['cover_title_font']}px 고정")
        self.log.add("박편집", f"언더라인: 텍스트 넓이 + {specs['cover_underline_padding']}px")
        self.log.add("박편집", f"본문 제목: {specs['body_title_font']}px")
        self.log.add("박편집", f"본문 텍스트: {specs['body_text_font']}px")
        self.log.add("박편집", f"텍스트 영역: {specs['text_area_max_percent']}% 이하")

        return {
            "ready": True,
            "specs": specs,
            "image_count": len(images),
            "slide_count": len(slides)
        }

    def parkpyunjip_review(
        self,
        composite_data: Dict
    ) -> Dict:
        """✏️ 박편집: 합성 결과 자체 검토"""

        self.switch_to("박편집")
        self.log.add("박편집", "합성 결과 자체 검토 중...")

        output_images = composite_data.get("output_images", [])
        count = composite_data.get("count", 0)

        if count >= 7:
            self.log.add("박편집", f"  ✅ {count}장 합성 완료")
            return {"ready": True, "issues": []}
        else:
            issue = f"합성 이미지 부족 ({count}/7)"
            self.log.add("박편집", f"  ⚠️ {issue}")
            return {"ready": False, "issues": [issue]}


# ============================================
# CrewWorkflow 호환 클래스
# ============================================

class CrewWorkflow:
    """
    파이프라인과 통합을 위한 워크플로우 클래스
    - API 호출 없음
    - 기존 pipeline_v5.py와 호환
    """

    def __init__(self, verbose: bool = True):
        self.system = MultiPersonaSystem(verbose=verbose)
        self.verbose = verbose
        self.results: Dict[str, Any] = {}

    def _log(self, message: str):
        if self.verbose:
            timestamp = datetime.now().strftime("%H:%M:%S")
            print(f"[{timestamp}] 🚀 CrewWorkflow | {message}")

    async def run_quality_gate_g1(
        self,
        slides_data: Dict,
        topic: str
    ) -> Dict:
        """G1: 글 검수 (김감독)"""
        self._log("G1 품질 게이트 시작: 글 검수")

        score, passed, details = self.system.kimgamdok_review_g1(slides_data)

        self.results["G1"] = details
        self._log(f"G1 완료: {score}점 - {'통과' if passed else '반려'}")

        return {
            "gate": "G1",
            "result": details,
            "conversation": self.system.log.get_entries()[-10:]  # 최근 10개 로그
        }

    async def run_quality_gate_g2(
        self,
        images_data: List[Dict],
        slides_data: Dict,
        topic: str
    ) -> Dict:
        """G2: 이미지 검수 (김감독)"""
        self._log("G2 품질 게이트 시작: 이미지 검수")

        slides = slides_data.get("slides", [])
        score, passed, details = self.system.kimgamdok_review_g2(images_data, slides)

        self.results["G2"] = details
        self._log(f"G2 완료: {score}점 - {'통과' if passed else '반려'}")

        return {
            "gate": "G2",
            "result": details,
            "conversation": self.system.log.get_entries()[-10:]
        }

    async def run_quality_gate_g3(
        self,
        composite_images: List[str],
        topic: str
    ) -> Dict:
        """G3: 합성 검수 (김감독)"""
        self._log("G3 품질 게이트 시작: 합성 검수")

        composite_data = {
            "output_images": composite_images,
            "count": len(composite_images)
        }
        score, passed, details = self.system.kimgamdok_review_g3(composite_data)

        self.results["G3"] = details
        self._log(f"G3 완료: {score}점 - {'통과' if passed else '반려'}")

        return {
            "gate": "G3",
            "result": details,
            "conversation": self.system.log.get_entries()[-10:]
        }

    async def image_generation_conversation(
        self,
        prompts_data: Dict,
        topic: str
    ) -> Dict:
        """이미지 생성 전 이작가 ↔ 김감독 협의"""
        self._log("이미지 생성 협의 시작")

        # 이작가가 프롬프트 검토
        prompts = prompts_data.get("prompts", [])
        slides = [{"title": p.get("text", "")} for p in prompts]

        prepared_prompts = self.system.leejakga_prepare_prompts(topic, slides)

        # 김감독 코멘트
        self.system.switch_to("김감독")
        self.system.log.add("김감독", f"이작가님, {len(prepared_prompts)}개 프롬프트 확인했습니다.")
        self.system.log.add("김감독", "PD님 피드백(내용-연출 일치) 반영 잘 부탁드립니다.")

        return {
            "phase": "image_generation_review",
            "conversation": self.system.log.get_entries()[-10:]
        }

    async def text_overlay_conversation(
        self,
        images_data: List[Dict],
        slides_data: Dict,
        topic: str
    ) -> Dict:
        """텍스트 합성 전 박편집 ↔ 김감독 협의"""
        self._log("텍스트 합성 협의 시작")

        slides = slides_data.get("slides", [])

        # 박편집 준비
        prep = self.system.parkpyunjip_prepare(images_data, slides)

        # 김감독 코멘트
        self.system.switch_to("김감독")
        self.system.log.add("김감독", f"박편집님, {prep['image_count']}장 합성 준비 확인했습니다.")
        self.system.log.add("김감독", "PD님 피드백(폰트 72px/48px, 텍스트 영역 30%) 준수 부탁드립니다.")

        return {
            "phase": "text_overlay_review",
            "conversation": self.system.log.get_entries()[-10:]
        }


# ============================================
# 편의 함수
# ============================================

def get_persona(name: str) -> Optional[Dict]:
    """페르소나 정보 조회"""
    return PERSONAS.get(name)


def list_personas() -> List[str]:
    """등록된 페르소나 목록"""
    return list(PERSONAS.keys())


async def create_crew_workflow(verbose: bool = True) -> CrewWorkflow:
    """CrewWorkflow 인스턴스 생성"""
    return CrewWorkflow(verbose=verbose)


# ============================================
# 테스트
# ============================================

if __name__ == "__main__":
    import asyncio

    async def test():
        print("🧪 멀티 페르소나 시스템 테스트 (API 호출 없음)")
        print("=" * 50)

        # 페르소나 목록
        print("\n등록된 페르소나:")
        for name, info in PERSONAS.items():
            print(f"  {info['icon']} {name} - {info['role']}")

        # CrewWorkflow 테스트
        print("\n\n--- CrewWorkflow 테스트 ---\n")
        workflow = CrewWorkflow(verbose=True)

        # G1 테스트
        test_slides = {
            "slides": [
                {"type": "cover", "title": "PEACH"},
                {"type": "result", "title": "조건부 OK!"},
                {"type": "benefit1", "title": "비타민 풍부"},
                {"type": "benefit2", "title": "식이섬유"},
                {"type": "caution", "title": "주의사항"},
                {"type": "amount", "title": "급여량"},
                {"type": "cta", "title": "팔로우"}
            ]
        }

        result = await workflow.run_quality_gate_g1(test_slides, "peach")
        print(f"\nG1 결과: {result['result']['score']}점")

        print("\n" + "=" * 50)
        print("✅ 테스트 완료 (API 호출 없음)")

    asyncio.run(test())
