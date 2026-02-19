#!/usr/bin/env python3
"""
파스타 본문 이미지 생성 스크립트
- 01, 02번 슬라이드 AI 이미지 생성
- 모델: fal-ai/flux-2-pro
"""

import asyncio
import sys
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from services.scripts.generate_images import generate_image

PASTA_DIR = ROOT / "content" / "images" / "028_pasta_파스타"

# 햇살이 + 파스타 프롬프트
PROMPTS = {
    1: """A senior golden retriever with white muzzle and gentle eyes, sitting calmly behind a white plate with plain cooked pasta,
the dog has a curious expression looking at the food,
SIDE ANGLE VIEW (45 degrees),
bright modern kitchen background with natural window lighting,
warm and cozy atmosphere,
8K, ultra detailed fur texture, Canon EOS R5,
soft natural lighting, shallow depth of field,
the pasta is prominent in the foreground,
MOUTH CLOSED, no eating""",

    2: """A senior golden retriever with white muzzle sitting in a kitchen,
looking at a small portion of plain cooked pasta on a plate,
the dog has an attentive expression,
PROFILE VIEW (side view, 90 degrees),
clean modern kitchen with stainless steel appliances,
8K, ultra detailed fur texture, Canon EOS R5,
soft natural lighting, shallow depth of field,
MOUTH CLOSED, calm demeanor"""
}

async def main():
    print("=" * 50)
    print("🍝 파스타 본문 이미지 생성 (AI)")
    print("=" * 50)

    PASTA_DIR.mkdir(parents=True, exist_ok=True)

    for slide_num, prompt in PROMPTS.items():
        output_path = PASTA_DIR / f"pasta_0{slide_num}_bg.png"
        print(f"\n📌 Slide {slide_num} 생성 중...")

        result = await generate_image(prompt, output_path)

        if result.get("success"):
            print(f"  ✅ {output_path.name} 생성 완료")
        else:
            print(f"  ❌ 생성 실패: {result.get('error')}")

    print("\n" + "=" * 50)
    print("✨ 이미지 생성 완료!")

if __name__ == "__main__":
    asyncio.run(main())
