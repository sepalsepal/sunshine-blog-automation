"""
StoryboardCrew - 스토리보드 자동 생성 Crew
작성: Phase 2 Day 1
지시: 김부장 마스터 지시서

체리(Gold Standard) 기반 스토리보드 생성
- ResearchAgent: 음식 정보 조사
- ReferenceAgent: 체리 레퍼런스 분석
- StoryboardAgent: 스토리보드 작성
"""

import asyncio
import json
import os
from pathlib import Path
from datetime import datetime
import sys

ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")


# 다양성 필수 요건 (체리 기준)
DIVERSITY_REQUIREMENTS = {
    "poses": ["sitting", "lying", "standing", "looking_up"],  # 최소 4종
    "angles": ["front", "side_45", "side_90", "top_down", "blur_effect"],  # 최소 4종
    "backgrounds": ["kitchen", "living_room"],  # 최소 2종
    "human_appearance": 2,  # 최소 2장
    "food_forms": ["whole", "sliced", "prepared"]  # 최소 3종
}


# 슬라이드 구조 템플릿 (Phase 6: 8장→7장으로 변경, 박리서치 추천)
SLIDE_STRUCTURE = [
    {"index": 0, "type": "cover", "purpose": "표지 - 호기심 유발"},
    {"index": 1, "type": "result", "purpose": "결과 - 먹어도 돼요/안돼요"},
    {"index": 2, "type": "benefit1", "purpose": "효능1 - 주요 영양소"},
    {"index": 3, "type": "benefit2", "purpose": "효능2 - 건강 효과"},
    {"index": 4, "type": "caution", "purpose": "주의사항 - 조심할 점"},
    {"index": 5, "type": "amount", "purpose": "적정량 - 급여량"},
    {"index": 6, "type": "cta", "purpose": "CTA - 저장하세요"},
]


class StoryboardCrew:
    """
    스토리보드 자동 생성 Crew

    체리(Gold Standard) 패턴을 분석하고
    다양성 요건을 충족하는 스토리보드 생성
    """

    def __init__(self):
        self.reference_dir = ROOT / "images" / "reference" / "gold_standard" / "cherry"
        self.storyboard_dir = ROOT / "storyboards"
        self.storyboard_dir.mkdir(exist_ok=True)

        # 음식별 기본 정보 DB
        self.food_db = self._load_food_database()

    def _load_food_database(self) -> dict:
        """음식 정보 DB 로드"""
        db_path = ROOT / "config" / "food_database.json"
        if db_path.exists():
            with open(db_path, 'r', encoding='utf-8') as f:
                return json.load(f)
        return {}

    def _research_food(self, food_name: str, food_name_kr: str) -> dict:
        """
        ResearchAgent 역할: 음식 정보 조사
        (실제 구현에서는 웹 검색 또는 LLM 활용)
        """
        # 기본 정보 DB에서 조회
        if food_name in self.food_db:
            return self.food_db[food_name]

        # 기본 템플릿 반환
        return {
            "name": food_name,
            "name_kr": food_name_kr,
            "safe": True,
            "benefits": [
                {"title": "영양소 풍부", "description": "비타민, 미네랄 등"},
                {"title": "수분 보충", "description": "수분 함량이 높음"},
                {"title": "저칼로리", "description": "다이어트에 도움"}
            ],
            "cautions": [
                "씨, 껍질 제거 필요",
                "적정량만 급여"
            ],
            "amount": "체중 1kg당 10~20g",
            "preparation": ["깨끗이 세척", "적당한 크기로 자르기"]
        }

    def _analyze_reference(self) -> dict:
        """
        ReferenceAgent 역할: 체리(Gold Standard) 분석
        """
        reference_readme = self.reference_dir.parent.parent / "README.md"

        # 체리 레퍼런스 패턴
        cherry_pattern = {
            "story_flow": "씻기 → 씨빼기 → 급여 → 휴식",
            "poses": {
                "slide_00": {"pose": "sitting", "angle": "front", "desc": "정면 앉기, 눈맞춤"},
                "slide_01": {"pose": "looking_up", "angle": "front", "desc": "올려다보기, 기대감"},
                "slide_02": {"pose": "sitting", "angle": "side_45", "desc": "측면 앉기, 음식 응시"},
                "slide_03": {"pose": "standing", "angle": "side_90", "desc": "서서 기다리기"},
                "slide_04": {"pose": "lying", "angle": "top_down", "desc": "부감, 음식 포커스"},
                "slide_05": {"pose": "sitting", "angle": "blur_effect", "desc": "블러 효과, 음식 강조"},
                "slide_06": {"pose": "looking_up", "angle": "front", "desc": "올려다보기, 급여 장면"},
                "slide_07": {"pose": "lying", "angle": "side_45", "desc": "소파 눕기, 편안함"},
            },
            "human_slides": [3, 5, 6],  # 사람 등장 슬라이드
            "backgrounds": {
                "kitchen": [0, 1, 2, 3, 5, 6],
                "living_room": [4, 7]
            },
            "emotions": ["호기심", "기대감", "행복", "편안함"],
            "key_elements": [
                "보호자-반려견 관계 표현",
                "일상의 따뜻함",
                "자연스러운 포즈",
                "AI 느낌 탈피"
            ]
        }

        return cherry_pattern

    def _generate_storyboard(
        self,
        food_name: str,
        food_name_kr: str,
        food_info: dict,
        reference_pattern: dict
    ) -> dict:
        """
        StoryboardAgent 역할: 스토리보드 작성
        """
        slides = []

        # 체리 패턴을 기반으로 각 슬라이드 설계 (7장)
        for slide_template in SLIDE_STRUCTURE:
            idx = slide_template["index"]
            slide_type = slide_template["type"]
            purpose = slide_template["purpose"]

            # 체리 패턴에서 포즈/앵글 가져오기 (7장 구조에 맞게 매핑)
            # 0:cover, 1:result, 2:benefit1, 3:benefit2, 4:caution, 5:amount, 6:cta
            pose_mapping = {0: 0, 1: 1, 2: 2, 3: 3, 4: 5, 5: 6, 6: 7}  # 7장→8장 매핑
            ref_idx = pose_mapping.get(idx, idx)
            ref_slide = reference_pattern["poses"].get(f"slide_{ref_idx:02d}", {})

            slide = {
                "index": idx,
                "type": slide_type,
                "purpose": purpose,
                "pose": ref_slide.get("pose", "sitting"),
                "angle": ref_slide.get("angle", "front"),
                "background": "kitchen" if idx in reference_pattern["backgrounds"]["kitchen"] else "living_room",
                "human_appearance": idx in reference_pattern["human_slides"],
                "food_form": self._get_food_form(slide_type),
                "text": self._generate_slide_text(slide_type, food_name_kr, food_info),
                "emotion": self._get_slide_emotion(slide_type),
                "prompt_hint": ref_slide.get("desc", "")
            }
            slides.append(slide)

        # 다양성 검증
        diversity_check = self._verify_diversity(slides)

        return {
            "food_name": food_name,
            "food_name_kr": food_name_kr,
            "created_at": datetime.now().isoformat(),
            "reference": "cherry (Gold Standard)",
            "slides": slides,
            "diversity_check": diversity_check,
            "food_info": food_info
        }

    def _get_food_form(self, slide_type: str) -> str:
        """슬라이드 타입에 따른 음식 형태 (7장 구조)"""
        food_forms = {
            "cover": "whole",
            "result": "whole",      # 기존 intro → result
            "benefit1": "sliced",
            "benefit2": "prepared",
            "caution": "prepared",
            "amount": "sliced",
            "cta": "sliced"  # Phase 6: 음식 일관성 유지 (김부장 지시)
        }
        return food_forms.get(slide_type, "whole")

    def _generate_slide_text(self, slide_type: str, food_name_kr: str, food_info: dict) -> dict:
        """슬라이드 텍스트 생성"""
        benefits = food_info.get("benefits", [])
        cautions = food_info.get("cautions", [])
        amount = food_info.get("amount", "적정량 급여")

        # 7장 구조 텍스트 템플릿
        text_templates = {
            "cover": {
                "title": food_name_kr.upper() if len(food_name_kr) <= 10 else food_name_kr,
                "subtitle": None
            },
            "result": {
                "title": f"{food_name_kr}, 먹어도 돼요!",
                "subtitle": "안전하게 급여 가능해요"
            },
            "benefit1": {
                "title": benefits[0]["title"] if benefits else "영양 풍부",
                "subtitle": benefits[0]["description"] if benefits else ""
            },
            "benefit2": {
                "title": benefits[1]["title"] if len(benefits) > 1 else "건강 효과",
                "subtitle": benefits[1]["description"] if len(benefits) > 1 else ""
            },
            "caution": {
                "title": "주의하세요!",
                "subtitle": cautions[0] if cautions else "적정량만 급여해주세요"
            },
            "amount": {
                "title": "적정량",
                "subtitle": amount
            },
            "cta": {
                "title": "저장해두세요!",
                "subtitle": "우리 아이 건강 간식 정보"
            }
        }

        return text_templates.get(slide_type, {"title": "", "subtitle": ""})

    def _get_slide_emotion(self, slide_type: str) -> str:
        """슬라이드 감성 키워드 (7장 구조)"""
        emotions = {
            "cover": "호기심",
            "result": "안심",     # 기존 intro → result
            "benefit1": "기대감",
            "benefit2": "기대감",
            "caution": "조심",
            "amount": "신뢰",
            "cta": "행동유도"
        }
        return emotions.get(slide_type, "중립")

    def _verify_diversity(self, slides: list) -> dict:
        """다양성 요건 검증"""
        poses = set()
        angles = set()
        backgrounds = set()
        human_count = 0
        food_forms = set()

        for slide in slides:
            if slide.get("pose"):
                poses.add(slide["pose"])
            if slide.get("angle"):
                angles.add(slide["angle"])
            if slide.get("background"):
                backgrounds.add(slide["background"])
            if slide.get("human_appearance"):
                human_count += 1
            if slide.get("food_form"):
                food_forms.add(slide["food_form"])

        return {
            "poses": {
                "count": len(poses),
                "items": list(poses),
                "required": 4,
                "pass": len(poses) >= 4
            },
            "angles": {
                "count": len(angles),
                "items": list(angles),
                "required": 4,
                "pass": len(angles) >= 4
            },
            "backgrounds": {
                "count": len(backgrounds),
                "items": list(backgrounds),
                "required": 2,
                "pass": len(backgrounds) >= 2
            },
            "human_appearance": {
                "count": human_count,
                "required": 2,
                "pass": human_count >= 2
            },
            "food_forms": {
                "count": len(food_forms),
                "items": list(food_forms),
                "required": 3,
                "pass": len(food_forms) >= 3
            },
            "overall_pass": (
                len(poses) >= 4 and
                len(angles) >= 4 and
                len(backgrounds) >= 2 and
                human_count >= 2 and
                len(food_forms) >= 3
            )
        }

    def _generate_prompts(self, storyboard: dict) -> list:
        """슬라이드별 이미지 프롬프트 생성"""
        food_name = storyboard["food_name"]
        food_name_kr = storyboard["food_name_kr"]
        prompts = []

        for slide in storyboard["slides"]:
            idx = slide["index"]
            pose = slide["pose"]
            angle = slide["angle"]
            background = slide["background"]
            human = slide["human_appearance"]
            food_form = slide["food_form"]
            hint = slide["prompt_hint"]

            # 기본 프롬프트 구성
            base = f"A golden retriever dog named Sunshine"

            # 포즈
            pose_map = {
                "sitting": "sitting calmly",
                "lying": "lying down relaxed",
                "standing": "standing attentively",
                "looking_up": "looking up expectantly at camera"
            }
            pose_text = pose_map.get(pose, "sitting")

            # 앵글
            angle_map = {
                "front": "front view, eye contact with camera",
                "side_45": "45 degree side angle view",
                "side_90": "profile view, 90 degree side angle",
                "top_down": "top-down bird's eye view",
                "blur_effect": "shallow depth of field, dog slightly blurred, food in sharp focus"
            }
            angle_text = angle_map.get(angle, "front view")

            # 배경
            bg_map = {
                "kitchen": "in a bright modern kitchen, natural lighting from window",
                "living_room": "in a cozy living room with warm lighting"
            }
            bg_text = bg_map.get(background, "in a home setting")

            # 음식
            if food_form:
                food_map = {
                    "whole": f"fresh whole {food_name} nearby",
                    "sliced": f"sliced {food_name} pieces on a plate",
                    "prepared": f"prepared {food_name} in a dog-safe bowl"
                }
                food_text = food_map.get(food_form, f"with {food_name}")
            else:
                food_text = ""

            # 사람 등장
            human_text = "human hand visible giving food to dog" if human else ""

            # 표지 특별 처리
            if idx == 0:
                prompt = (
                    f"{base}, {pose_text}, {angle_text}, {bg_text}, "
                    f"{food_text}, HEAD POSITIONED IN CENTER OF FRAME, "
                    f"TOP 30% OF IMAGE IS EMPTY NEGATIVE SPACE for text overlay, "
                    f"warm natural lighting, professional pet photography, "
                    f"8k resolution, photorealistic, NOT AI-looking"
                )
            else:
                prompt = (
                    f"{base}, {pose_text}, {angle_text}, {bg_text}, "
                    f"{food_text}, {human_text}, "
                    f"warm natural lighting, authentic pet photography style, "
                    f"8k resolution, photorealistic, cozy atmosphere, NOT stock photo"
                )

            prompts.append({
                "index": idx,
                "type": slide["type"],
                "prompt": prompt.strip().replace("  ", " ").replace(", ,", ",")
            })

        return prompts

    def _save_storyboard(self, storyboard: dict, prompts: list) -> str:
        """스토리보드 파일 저장"""
        food_name = storyboard["food_name"]
        output_path = self.storyboard_dir / f"{food_name}_storyboard.md"

        content = f"""# {storyboard['food_name_kr']} 콘텐츠 스토리보드

**작성일:** {storyboard['created_at'][:10]}
**레퍼런스:** {storyboard['reference']}
**자동 생성:** StoryboardCrew

---

## 1. 컨셉

### 핵심 메시지
> "{storyboard['food_name_kr']}는 안전하게 급여 가능하지만 적정량을 지켜주세요"

### 감성 키워드
- 따뜻함
- 일상
- 건강
- 사랑

---

## 2. 슬라이드 설계

| # | 타입 | 포즈 | 앵글 | 배경 | 사람 | 음식형태 |
|---|------|------|------|------|------|----------|
"""
        for slide in storyboard["slides"]:
            human_mark = "O" if slide["human_appearance"] else "-"
            content += f"| {slide['index']:02d} | {slide['type']} | {slide['pose']} | {slide['angle']} | {slide['background']} | {human_mark} | {slide['food_form'] or '-'} |\n"

        content += f"""

---

## 3. 다양성 체크

| 항목 | 현재 | 요건 | 결과 |
|------|------|------|------|
| 포즈 | {storyboard['diversity_check']['poses']['count']}종 | 4종+ | {'✅' if storyboard['diversity_check']['poses']['pass'] else '❌'} |
| 앵글 | {storyboard['diversity_check']['angles']['count']}종 | 4종+ | {'✅' if storyboard['diversity_check']['angles']['pass'] else '❌'} |
| 배경 | {storyboard['diversity_check']['backgrounds']['count']}종 | 2종+ | {'✅' if storyboard['diversity_check']['backgrounds']['pass'] else '❌'} |
| 사람등장 | {storyboard['diversity_check']['human_appearance']['count']}장 | 2장+ | {'✅' if storyboard['diversity_check']['human_appearance']['pass'] else '❌'} |
| 음식형태 | {storyboard['diversity_check']['food_forms']['count']}종 | 3종+ | {'✅' if storyboard['diversity_check']['food_forms']['pass'] else '❌'} |

**전체 판정:** {'✅ PASS' if storyboard['diversity_check']['overall_pass'] else '❌ FAIL (수정 필요)'}

---

## 4. 이미지 프롬프트

"""
        for p in prompts:
            content += f"""### Slide {p['index']:02d} - {p['type']}
```
{p['prompt']}
```

"""

        content += f"""---

## 5. 텍스트 내용

| # | 제목 | 부제 |
|---|------|------|
"""
        for slide in storyboard["slides"]:
            text = slide["text"]
            content += f"| {slide['index']:02d} | {text['title']} | {text['subtitle'] or '-'} |\n"

        content += f"""

---

## 6. 승인

- [ ] 김부장 크리에이티브 검토
- [ ] PD님 최종 승인

**승인일:** _______________

"""

        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # JSON 버전도 저장
        json_path = self.storyboard_dir / f"{food_name}_storyboard.json"
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump({**storyboard, "prompts": prompts}, f, ensure_ascii=False, indent=2)

        return str(output_path)

    def run(
        self,
        food_name: str,
        food_name_kr: str,
        reference: str = "cherry",
        slide_count: int = 7  # Phase 6: 8장→7장 변경
    ) -> dict:
        """
        스토리보드 생성 실행

        Args:
            food_name: 영문 음식명 (예: "watermelon")
            food_name_kr: 한글 음식명 (예: "수박")
            reference: 레퍼런스 콘텐츠 (기본: cherry)
            slide_count: 슬라이드 수 (기본: 8)

        Returns:
            {
                "success": bool,
                "storyboard_path": str,
                "diversity_pass": bool,
                "slides": list
            }
        """
        print(f"━{'━'*58}")
        print(f"📝 StoryboardCrew: {food_name_kr} 스토리보드 생성")
        print(f"━{'━'*58}")

        # Step 1: 음식 정보 조사 (ResearchAgent)
        print("\n[1/4] 음식 정보 조사 중...")
        food_info = self._research_food(food_name, food_name_kr)
        print(f"   ✓ 효능 {len(food_info.get('benefits', []))}개, 주의사항 {len(food_info.get('cautions', []))}개")

        # Step 2: 레퍼런스 분석 (ReferenceAgent)
        print("\n[2/4] 체리(Gold Standard) 분석 중...")
        reference_pattern = self._analyze_reference()
        print(f"   ✓ 포즈 패턴 {len(reference_pattern['poses'])}개 추출")

        # Step 3: 스토리보드 작성 (StoryboardAgent)
        print("\n[3/4] 스토리보드 작성 중...")
        storyboard = self._generate_storyboard(
            food_name, food_name_kr, food_info, reference_pattern
        )
        prompts = self._generate_prompts(storyboard)
        print(f"   ✓ 슬라이드 {len(storyboard['slides'])}개 설계")

        # Step 4: 저장
        print("\n[4/4] 스토리보드 저장 중...")
        output_path = self._save_storyboard(storyboard, prompts)
        print(f"   ✓ {output_path}")

        # 결과 출력
        diversity = storyboard["diversity_check"]
        print(f"\n━{'━'*58}")
        print("📊 다양성 검증 결과")
        print(f"━{'━'*58}")
        print(f"   포즈: {diversity['poses']['count']}/4 {'✅' if diversity['poses']['pass'] else '❌'}")
        print(f"   앵글: {diversity['angles']['count']}/4 {'✅' if diversity['angles']['pass'] else '❌'}")
        print(f"   배경: {diversity['backgrounds']['count']}/2 {'✅' if diversity['backgrounds']['pass'] else '❌'}")
        print(f"   사람: {diversity['human_appearance']['count']}/2 {'✅' if diversity['human_appearance']['pass'] else '❌'}")
        print(f"   음식형태: {diversity['food_forms']['count']}/3 {'✅' if diversity['food_forms']['pass'] else '❌'}")
        print(f"\n   전체: {'✅ PASS' if diversity['overall_pass'] else '❌ FAIL'}")
        print(f"━{'━'*58}")

        return {
            "success": True,
            "storyboard_path": output_path,
            "json_path": str(self.storyboard_dir / f"{food_name}_storyboard.json"),
            "diversity_pass": diversity["overall_pass"],
            "slides": storyboard["slides"],
            "prompts": prompts
        }

    def kickoff(self, inputs: dict) -> dict:
        """
        CrewAI 스타일 실행

        Args:
            inputs: {
                "food_name": "watermelon",
                "food_name_kr": "수박",
                "reference": "cherry",
                "slide_count": 8
            }
        """
        return self.run(
            food_name=inputs.get("food_name", "unknown"),
            food_name_kr=inputs.get("food_name_kr", "알 수 없음"),
            reference=inputs.get("reference", "cherry"),
            slide_count=inputs.get("slide_count", 8)
        )


# CLI 실행
if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="StoryboardCrew - 스토리보드 생성")
    parser.add_argument("food_name", help="영문 음식명 (예: watermelon)")
    parser.add_argument("food_name_kr", help="한글 음식명 (예: 수박)")
    args = parser.parse_args()

    crew = StoryboardCrew()
    result = crew.kickoff({
        "food_name": args.food_name,
        "food_name_kr": args.food_name_kr
    })

    print(f"\n✅ 스토리보드 생성 완료: {result['storyboard_path']}")
