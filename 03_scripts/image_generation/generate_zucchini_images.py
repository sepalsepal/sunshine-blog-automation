#!/usr/bin/env python3
"""
애호박 본문 이미지 생성 스크립트
- 01, 02번 슬라이드 AI 이미지 생성
- 모델: fal-ai/flux-2-pro
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from services.scripts.generate_images import generate_image

ZUCCHINI_DIR = ROOT / "content" / "images" / "027_zucchini_애호박"

# 햇살이 + 애호박 프롬프트
PROMPTS = {
    1: """A senior golden retriever with white muzzle and gentle eyes, sitting calmly behind a wooden cutting board with fresh sliced zucchini,
the dog has a curious expression looking at the vegetables,
SIDE ANGLE VIEW (45 degrees),
bright modern kitchen background with natural window lighting,
warm and cozy atmosphere,
8K, ultra detailed fur texture, Canon EOS R5,
soft natural lighting, shallow depth of field,
the zucchini pieces are prominent in the foreground""",

    2: """A senior golden retriever with white muzzle sitting in a kitchen,
looking at a small bowl of cooked zucchini pieces,
the dog has an attentive expression,
PROFILE VIEW (side view, 90 degrees),
clean modern kitchen with stainless steel appliances,
8K, ultra detailed fur texture, Canon EOS R5,
soft natural lighting, shallow depth of field,
MOUTH CLOSED, calm demeanor"""
}

async def main():
    print("═" * 50)
    print("🥒 애호박 본문 이미지 생성 (AI)")
    print("═" * 50)

    ZUCCHINI_DIR.mkdir(parents=True, exist_ok=True)

    for slide_num, prompt in PROMPTS.items():
        output_path = ZUCCHINI_DIR / f"zucchini_0{slide_num}_bg.png"
        print(f"\n📌 Slide {slide_num} 생성 중...")

        result = await generate_image(prompt, output_path)

        if result.get("success"):
            print(f"  ✅ {output_path.name} 생성 완료")
        else:
            print(f"  ❌ 생성 실패: {result.get('error')}")

    print("\n" + "═" * 50)
    print("✨ 이미지 생성 완료!")

if __name__ == "__main__":
    asyncio.run(main())
