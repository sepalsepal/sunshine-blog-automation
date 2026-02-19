#!/usr/bin/env python3
"""
아보카도 & 콜라 본문 이미지 생성 스크립트
- 표지 배경과 동일한 따뜻한 거실 배경 사용
- fal-ai/flux-2-pro 모델 사용 (generate_images.py 사용)
"""

import asyncio
from pathlib import Path
import sys

# 프로젝트 루트 추가
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from services.scripts.generate_images import generate_batch

# 표준 배경 프롬프트 (가이드 준수)
BACKGROUND_PROMPT = """warm cozy living room with wooden ceiling fan,
night city view through large window,
monstera and palm plants,
floor lamp with white shade,
cute bear-shaped mood lamp (Mr. Maria Brown),
beige sofa in background,
wooden dining table,
warm ambient lighting with indirect LED ceiling lights"""

# 햇살이 특징 (CLAUDE.md 준수)
SUNSHINE_PROMPT = """senior golden retriever (10 years old) with white muzzle and white fur around eyes,
black eyes, black nose,
golden caramel fur color,
ears 30% smaller than typical golden retriever,
NOT EATING, NOT LICKING, NOT TOUCHING FOOD,
mouth closed"""

# ============================================
# 아보카도 프롬프트 (위험 음식)
# ============================================
AVOCADO_PROMPTS = [
    {
        "filename": "avocado_01.png",
        "prompt": f"""A {SUNSHINE_PROMPT},
SIDE ANGLE VIEW (45 degrees), looking curiously at a whole avocado on wooden table,
avocado prominently displayed in foreground,
warning expression, concerned look,
{BACKGROUND_PROMPT},
8K, ultra detailed fur texture, Canon EOS R5,
soft natural window lighting, shallow depth of field,
bottom 30% of image slightly darker for text overlay"""
    },
    {
        "filename": "avocado_02.png",
        "prompt": f"""A {SUNSHINE_PROMPT},
FRONT VIEW, looking directly at camera with serious expression,
a cut avocado showing the pit/seed on wooden table in foreground,
warning mood, concerned atmosphere,
{BACKGROUND_PROMPT},
8K, ultra detailed fur texture, Canon EOS R5,
soft natural window lighting, shallow depth of field,
bottom 30% of image slightly darker for text overlay"""
    },
    {
        "filename": "avocado_03.png",
        "prompt": f"""A {SUNSHINE_PROMPT},
FRONT VIEW, happy expression, looking at camera,
whole avocado visible in corner of frame,
bright cheerful mood for CTA,
{BACKGROUND_PROMPT},
8K, ultra detailed fur texture, Canon EOS R5,
soft natural window lighting, shallow depth of field,
bottom 30% of image slightly darker for text overlay"""
    }
]

# ============================================
# 콜라 프롬프트 (위험 음식)
# ============================================
COCA_COLA_PROMPTS = [
    {
        "filename": "coca_cola_01.png",
        "prompt": f"""A {SUNSHINE_PROMPT},
SIDE ANGLE VIEW (45 degrees), looking curiously at a red Coca-Cola can on wooden table,
cola can prominently displayed in foreground,
warning expression, concerned look,
{BACKGROUND_PROMPT},
8K, ultra detailed fur texture, Canon EOS R5,
soft natural window lighting, shallow depth of field,
bottom 30% of image slightly darker for text overlay"""
    },
    {
        "filename": "coca_cola_02.png",
        "prompt": f"""A {SUNSHINE_PROMPT},
FRONT VIEW, looking directly at camera with serious expression,
a glass of dark cola with ice and bubbles on wooden table in foreground,
red Coca-Cola can next to glass,
warning mood, concerned atmosphere,
{BACKGROUND_PROMPT},
8K, ultra detailed fur texture, Canon EOS R5,
soft natural window lighting, shallow depth of field,
bottom 30% of image slightly darker for text overlay"""
    },
    {
        "filename": "coca_cola_03.png",
        "prompt": f"""A {SUNSHINE_PROMPT},
FRONT VIEW, happy expression, looking at camera,
Coca-Cola can visible in corner of frame,
bright cheerful mood for CTA,
{BACKGROUND_PROMPT},
8K, ultra detailed fur texture, Canon EOS R5,
soft natural window lighting, shallow depth of field,
bottom 30% of image slightly darker for text overlay"""
    }
]

async def main():
    print("=" * 60)
    print("아보카도 & 콜라 본문 이미지 생성")
    print("=" * 60)

    # 아보카도 이미지 생성
    avocado_dir = ROOT / "content" / "images" / "022_아보카도"
    print(f"\n📁 아보카도 이미지 생성 → {avocado_dir}")
    await generate_batch(AVOCADO_PROMPTS, avocado_dir)

    # 콜라 이미지 생성
    cola_dir = ROOT / "content" / "images" / "023_코카콜라"
    print(f"\n📁 콜라 이미지 생성 → {cola_dir}")
    await generate_batch(COCA_COLA_PROMPTS, cola_dir)

    print("\n" + "=" * 60)
    print("✨ 전체 완료!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
