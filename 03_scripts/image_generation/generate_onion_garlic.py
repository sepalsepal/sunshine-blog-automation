#!/usr/bin/env python3
"""
Day 8: onion/garlic 본문 슬라이드 생성
안전 분류: FORBIDDEN
"""

import asyncio
import sys
from pathlib import Path

# 프로젝트 루트 추가
ROOT = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(ROOT))

from services.scripts.image_generation.generate_images import generate_image, MODEL_ID

# 출력 폴더
ONION_DIR = ROOT / "content/images/056_onion_양파"
GARLIC_DIR = ROOT / "content/images/058_garlic_마늘"

# 프롬프트 템플릿 (FORBIDDEN 음식용)
PROMPTS = {
    "onion": {
        "01_bg": """A senior golden retriever with white muzzle, gentle curious expression,
sitting in a modern bright kitchen, looking at a bowl of sliced raw onions on the counter,
the dog is NOT touching or eating the food, keeping safe distance,
warm natural lighting from window, shallow depth of field,
8K, ultra detailed fur texture, Canon EOS R5,
bottom 30% slightly blurred for text overlay area""",

        "02_bg": """Close-up of raw onions (whole and sliced) on a white plate in foreground,
a senior golden retriever with white muzzle BLURRED in background looking concerned,
bright modern kitchen setting, natural window lighting,
SHALLOW DEPTH OF FIELD with onions in sharp focus,
8K, professional food photography style,
bottom 30% area clear for text""",

        "03_bg": """A happy senior golden retriever with white muzzle, tongue out, cheerful smile,
sitting in a cozy living room, warm lighting, looking directly at camera,
no food visible, friendly inviting atmosphere,
8K, ultra detailed fur texture, Canon EOS R5,
soft natural lighting, bottom 30% for text overlay"""
    },
    "garlic": {
        "01_bg": """A senior golden retriever with white muzzle, gentle curious expression,
sitting in a modern bright kitchen, looking at a bowl of garlic cloves on the counter,
the dog is NOT touching or eating the food, keeping safe distance,
warm natural lighting from window, shallow depth of field,
8K, ultra detailed fur texture, Canon EOS R5,
bottom 30% slightly blurred for text overlay area""",

        "02_bg": """Close-up of fresh garlic bulbs and cloves on a white plate in foreground,
a senior golden retriever with white muzzle BLURRED in background looking concerned,
bright modern kitchen setting, natural window lighting,
SHALLOW DEPTH OF FIELD with garlic in sharp focus,
8K, professional food photography style,
bottom 30% area clear for text""",

        "03_bg": """A happy senior golden retriever with white muzzle, tongue out, cheerful smile,
sitting in a cozy living room, warm lighting, looking directly at camera,
no food visible, friendly inviting atmosphere,
8K, ultra detailed fur texture, Canon EOS R5,
soft natural lighting, bottom 30% for text overlay"""
    }
}


async def generate_backgrounds():
    """배경 이미지 생성"""
    print("=" * 60)
    print("🚫 Day 8: onion/garlic 본문 이미지 생성")
    print(f"🤖 모델: {MODEL_ID}")
    print("=" * 60)

    results = []

    # onion 생성
    print("\n📁 onion 배경 생성...")
    for slide, prompt in PROMPTS["onion"].items():
        output_path = ONION_DIR / f"onion_{slide}.png"
        if output_path.exists():
            print(f"  ⏭️ 스킵: {output_path.name} (이미 존재)")
            continue
        result = await generate_image(prompt, output_path)
        results.append({"food": "onion", "slide": slide, **result})
        await asyncio.sleep(2)

    # garlic 생성
    print("\n📁 garlic 배경 생성...")
    for slide, prompt in PROMPTS["garlic"].items():
        output_path = GARLIC_DIR / f"garlic_{slide}.png"
        if output_path.exists():
            print(f"  ⏭️ 스킵: {output_path.name} (이미 존재)")
            continue
        result = await generate_image(prompt, output_path)
        results.append({"food": "garlic", "slide": slide, **result})
        await asyncio.sleep(2)

    # 결과 요약
    success = sum(1 for r in results if r.get("success"))
    print("\n" + "=" * 60)
    print(f"✨ 완료: {success}/{len(results)}개 성공")
    print("=" * 60)

    return results


if __name__ == "__main__":
    asyncio.run(generate_backgrounds())
