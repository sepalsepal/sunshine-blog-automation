#!/usr/bin/env python3
"""
시금치 콘텐츠 배경 이미지 생성
fal-ai/flux-2-pro 사용 (CLAUDE.md 필수 규칙)

담당: 김영현 과장
"""

import asyncio
from pathlib import Path
import sys

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from services.scripts.generate_images import generate_image

OUTPUT_DIR = ROOT / "content/images/026_spinach_시금치"

# 햇살이 기본 프롬프트 (CLAUDE.md 규칙)
BASE_PROMPT = """A senior golden retriever with white muzzle, white fur around eyes,
black eyes, black nose, golden caramel fur color,
10 years old senior dog appearance, ears 30% smaller than typical golden retriever,
NOT a puppy, mature adult dog,
8K, ultra detailed fur texture, Canon EOS R5, soft natural lighting"""

# 슬라이드별 프롬프트
SLIDE_PROMPTS = [
    # slide 0: cover - PD 제작이므로 스킵
    None,
    # slide 1: 먹어도 돼요! - 측면 45도, 시금치 응시
    {
        "filename": "spinach_01_bg.png",
        "prompt": f"""{BASE_PROMPT},
SIDE ANGLE VIEW (45 degrees), looking at fresh spinach leaves on a plate,
curious happy expression, gentle gaze at the healthy food,
fresh green spinach leaves prominently displayed in foreground,
bright modern kitchen with natural window lighting,
shallow depth of field, spinach in sharp focus"""
    },
    # slide 2: 주의사항 - 정면
    {
        "filename": "spinach_02_bg.png",
        "prompt": f"""{BASE_PROMPT},
FRONT VIEW, looking directly at camera with attentive expression,
bowl of fresh spinach visible on table in front,
bright modern kitchen background, natural window lighting,
educational content style, informative mood"""
    },
    # slide 3: CTA - 행복한 표정
    {
        "filename": "spinach_03_bg.png",
        "prompt": f"""{BASE_PROMPT},
happy expression, tongue out, cheerful smile, bright eyes,
looking at camera, cozy kitchen setting,
warm lighting, friendly approachable pose,
feel-good content style"""
    }
]

async def main():
    print("=" * 60)
    print("🥬 시금치 콘텐츠 배경 이미지 생성")
    print("   모델: fal-ai/flux-2-pro (CLAUDE.md 필수)")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for i, config in enumerate(SLIDE_PROMPTS):
        if config is None:
            print(f"\n📌 Slide {i}: 스킵 (PD 제작)")
            continue

        print(f"\n📌 Slide {i}: {config['filename']}")
        output_path = OUTPUT_DIR / config["filename"]

        result = await generate_image(config["prompt"], output_path)

        if result.get("success"):
            print(f"   ✅ 저장 완료: {config['filename']}")
        else:
            print(f"   ❌ 생성 실패: {result.get('error')}")

    print("\n" + "=" * 60)
    print("✨ 배경 이미지 생성 완료")
    print(f"   출력 폴더: {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
