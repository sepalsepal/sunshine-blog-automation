"""
PromptGeneratorAgent - 이미지 프롬프트 생성 에이전트
기획안을 받아 각 슬라이드별 이미지 프롬프트 생성

프롬프트 규칙 (v7 표지 표준화):
- 햇살이: 10살 시니어 골든리트리버 (puppy 절대 금지)
- 흰 주둥이 + 눈 주변 흰 털 + 검은 눈/코 필수
- 슬라이드별 역할 기반 상황 연출 (메시지 정합성 기반 포즈)
- 여백: 표지=상단 20% (피사체 중앙~하단), 본문=하단 30% (텍스트용)
- 필름 감성: Kodak Portra 400, 85mm f/2.8, film grain
- 강아지가 음식을 먹거나 만지는 포즈 금지

표지 규칙:
- 텍스트 위치: 상단 15-20% (약 120px)
- 폰트 크기: 58px
- AI 이미지: 강아지/음식을 중앙~하단에 배치, 상단 20%는 깨끗한 배경만

Author: 최기술 대리
"""

from typing import Any, Dict, List
from .base import BaseAgent, AgentResult


# ============================================================
# 햇살이 캐릭터 정의 (김차장 Gem 기준)
# - 10살 시니어 골든리트리버
# - puppy/young 표현 절대 금지
# ============================================================
SUNSHINE_CHARACTER = (
    "a 10-year-old senior golden retriever with distinctive white muzzle, "
    "white fur mixed around the eyes, black eyes, black nose, "
    "golden caramel coat color, fluffy healthy body, "
    "wavy long fur around smaller ears (not oversized)"
)

# ============================================================
# 구도 가이드 (v8 - 솔리드 박스 방지)
# 핵심: "text overlay" 문구 절대 금지 → Flux가 박스를 그림
# 대신: "no text, no overlays, pure photograph" 필수 포함
# ============================================================
TEXT_SPACE_BOTTOM = (
    "full frame photograph with subject naturally positioned, "
    "soft bokeh background throughout, "
    "no text, no overlays, no solid color blocks, no gradients, "
    "pure photographic image only"
)
# 표지용: 피사체는 중앙~하단, 상단은 자연스러운 배경
TEXT_SPACE_TOP_COVER = (
    "subject and food positioned in center-lower area of frame, "
    "soft blurred background in upper area, "
    "no text, no overlays, no solid color blocks, no gradients, "
    "pure photographic image only"
)

# v5 실사 품질 태그 (필름 감성)
QUALITY_TAGS = (
    "shot on Canon EOS R5 with 85mm f/2.8 lens, "
    "Kodak Portra 400 film emulation, subtle film grain, "
    "slight lens vignetting, natural window side lighting with gentle shadows, "
    "shallow depth of field, warm golden tones, "
    "authentic candid pet photography, not posed, relaxed natural moment"
)


# ============================================================
# 슬라이드 타입별 프롬프트 (v7 표지 상단 20% 확보)
# 표지(00): 상단 20% 여백 → 상단 텍스트 (중앙~하단에 피사체)
# 본문(01~06): 하단 30% 여백 → 하단 텍스트 (통일)
# ============================================================
PROMPT_TEMPLATES = {
    # 표지(00): 햇살이 정면 호기심, 음식 앞 배치, 상단 20% 텍스트 공간 확보
    "cover": (
        f"Candid photograph of {SUNSHINE_CHARACTER} sitting behind a rustic wooden table "
        "with fresh {topic} placed in front, looking directly at camera with curious excited expression, "
        f"ears slightly forward, warm cozy kitchen, {TEXT_SPACE_TOP_COVER}, {QUALITY_TAGS}"
    ),
    # CTA(06): 햇살이 웃는 표정, 정면 응시, 빈 그릇 앞 행복, 하단 텍스트
    "cta": (
        f"Candid photograph of {SUNSHINE_CHARACTER} sitting in front of a small treat bowl "
        "with a few pieces of {topic} in it, looking at camera with a happy satisfied smile, "
        f"tail slightly wagging, warm golden hour lighting, cozy home, {TEXT_SPACE_BOTTOM}, {QUALITY_TAGS}"
    ),
}

# ============================================================
# content 슬라이드 역할별 상황 연출 (전 주제 공통)
#
# [0] 안전여부: 냄새 맡기 포즈 (호기심, 코 가까이)
# [1] 장점1/에너지: 활기찬 모습 or 산책 후 (활력)
# [2] 장점2/영양: 건강한 모습, 음식과 함께 (영양 강조)
# [3] 주의사항: 음식 클로즈업, 햇살이 배경 (경고 톤)
# [4] 급여량: 저울/계량, 분량 시각화 (정보 전달)
# ============================================================
CONTENT_VARIATIONS = [
    # [0] 안전여부 - 햇살이가 음식 냄새 맡는 포즈
    (
        f"Candid photograph of {SUNSHINE_CHARACTER} leaning forward with nose close to "
        "a plate of peeled {topic} on a wooden table, sniffing curiously with gentle expression, "
        f"natural daylight, warm kitchen background, {TEXT_SPACE_BOTTOM}, {QUALITY_TAGS}"
    ),
    # [1] 에너지/활력 - 햇살이 활기찬 모습, 배경에 음식
    (
        f"Candid photograph of {SUNSHINE_CHARACTER} looking energetic and alert, "
        "sitting upright with bright eyes and slightly open mouth as if panting happily, "
        "a small bowl of {topic} visible on the table beside, "
        f"bright natural morning light, lived-in kitchen, {TEXT_SPACE_BOTTOM}, {QUALITY_TAGS}"
    ),
    # [2] 영양/건강 - 햇살이 건강한 모습, 음식 슬라이스와 함께
    (
        f"Candid photograph of {SUNSHINE_CHARACTER} looking healthy and content, "
        "sitting calmly next to a cutting board with neatly sliced {topic}, "
        "the dog's shiny golden caramel coat and white muzzle clearly visible, "
        f"soft window light, clean kitchen, {TEXT_SPACE_BOTTOM}, {QUALITY_TAGS}"
    ),
    # [3] 주의사항 - 음식 클로즈업 전면, 햇살이 배경에서 관찰 (경고 톤)
    (
        f"Candid photograph with {{topic}} in sharp focus in the foreground on a plate, "
        f"{SUNSHINE_CHARACTER} sitting in the blurred background watching cautiously, "
        "slightly serious expression, keeping respectful distance from the food, "
        f"moody natural light, muted tones, {TEXT_SPACE_BOTTOM}, {QUALITY_TAGS}"
    ),
    # [4] 급여량 - 저울/계량 장면, 분량 시각화
    (
        f"Candid photograph of a small kitchen scale with a measured portion of {{topic}} on it, "
        f"{SUNSHINE_CHARACTER} sitting patiently beside the scale looking at camera, "
        "the portion size clearly visible for reference, "
        f"bright clean kitchen, informational composition, {TEXT_SPACE_BOTTOM}, {QUALITY_TAGS}"
    ),
]

# 절대 포함하면 안 되는 요소 (v8 - 솔리드 박스 방지 강화)
NEGATIVE_PROMPT = (
    "puppy, young dog, dog eating food, dog holding food, dog biting food, "
    "dog touching food with paws, food in mouth, text, watermark, "
    "text overlay, caption area, solid color block, gradient overlay, "
    "colored bar, banner, frame, border, "
    "digital art, illustration, 3d render, overly sharp, overly saturated, "
    "studio lighting, flash photography, HDR, "
    "low quality, blurry, sad expression, artifacts, deformed, ugly, bad anatomy"
)


class PromptGeneratorAgent(BaseAgent):
    """이미지 프롬프트 생성 에이전트 (v7 표지 표준화)"""

    @property
    def name(self) -> str:
        return "PromptGenerator"

    async def execute(self, input_data: Any) -> AgentResult:
        """
        이미지 프롬프트 생성

        Args:
            input_data: PlannerAgent의 출력 (plan dict)

        Returns:
            AgentResult with prompts list
        """
        plan = input_data
        topic = plan.get("topic", "food")
        topic_kr = plan.get("topic_kr", topic)

        self.log(f"'{topic}' 이미지 프롬프트 생성 중 (v7 표지 상단 20% 확보)")

        prompts = []
        content_index = 0

        for slide in plan.get("slides", []):
            slide_type = slide.get("type", "content")

            if slide_type in PROMPT_TEMPLATES:
                template = PROMPT_TEMPLATES[slide_type]
            else:
                variation_idx = content_index % len(CONTENT_VARIATIONS)
                template = CONTENT_VARIATIONS[variation_idx]
                content_index += 1

            prompt_text = template.format(topic=topic)

            prompt = {
                "index": slide["index"],
                "type": slide_type,
                "prompt": prompt_text,
                "negative_prompt": NEGATIVE_PROMPT,
            }
            prompts.append(prompt)

        self.log(f"{len(prompts)}개 프롬프트 생성 완료 (cover: 1, content: {content_index}, cta: 1)")

        return AgentResult(
            success=True,
            data={"prompts": prompts, "plan": plan},
            metadata={"prompt_count": len(prompts), "template_version": "v7"}
        )
