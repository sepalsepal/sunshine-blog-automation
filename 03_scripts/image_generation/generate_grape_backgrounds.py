#!/usr/bin/env python3
"""
포도 콘텐츠 배경 이미지 생성
fal-ai/flux-2-pro 사용 (CLAUDE.md 필수 규칙)

담당: 김영현 과장
"""

import os
import sys
import asyncio
from pathlib import Path

# 환경변수 로드
from dotenv import load_dotenv
load_dotenv()

import fal_client

ROOT = Path(__file__).parent.parent.parent
OUTPUT_DIR = ROOT / "content/images/025_grape_포도"

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
    # slide 1: danger - 측면 45도
    {
        "filename": "grape_01_bg.png",
        "prompt": f"""{BASE_PROMPT},
SIDE ANGLE VIEW (45 degrees), looking at purple grapes on a plate,
curious concerned expression, gentle gaze at the dangerous food,
fresh purple grapes prominently displayed in foreground,
warm cozy living room with soft evening lighting,
shallow depth of field, grapes in sharp focus"""
    },
    # slide 2: danger - 정면
    {
        "filename": "grape_02_bg.png",
        "prompt": f"""{BASE_PROMPT},
FRONT VIEW, looking directly at camera with concerned expression,
bowl of purple grapes visible on table in front,
bright modern kitchen background, natural window lighting,
warning educational content style"""
    },
    # slide 3: cta - 행복한 표정 (실제 햇살이 사진 사용 권장)
    {
        "filename": "grape_03_bg.png",
        "prompt": f"""{BASE_PROMPT},
happy expression, tongue out, cheerful smile, bright eyes,
looking at camera, outdoor park setting,
green grass background, sunny day,
friendly approachable pose"""
    }
]

async def generate_image(prompt: str, output_path: Path) -> bool:
    """fal-ai/flux-2-pro로 이미지 생성"""
    print(f"🎨 김영현 과장입니다. 이미지 생성 중...")
    print(f"   출력: {output_path.name}")

    try:
        result = fal_client.subscribe(
            "fal-ai/flux-2-pro",  # CLAUDE.md 필수 규칙
            arguments={
                "prompt": prompt,
                "image_size": "square",  # 1024x1024
                "num_images": 1,
                "safety_tolerance": "5",
            }
        )

        if result and "images" in result and len(result["images"]) > 0:
            image_url = result["images"][0]["url"]

            # 이미지 다운로드
            import urllib.request
            output_path.parent.mkdir(parents=True, exist_ok=True)
            urllib.request.urlretrieve(image_url, str(output_path))

            print(f"   ✅ 저장 완료: {output_path.name}")
            return True
        else:
            print(f"   ❌ 이미지 생성 실패")
            return False

    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return False

async def main():
    print("=" * 60)
    print("🍇 포도 콘텐츠 배경 이미지 생성")
    print("   모델: fal-ai/flux-2-pro (CLAUDE.md 필수)")
    print("=" * 60)

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    for i, config in enumerate(SLIDE_PROMPTS):
        if config is None:
            print(f"\n📌 Slide {i}: 스킵 (PD 제작)")
            continue

        print(f"\n📌 Slide {i}: {config['filename']}")
        output_path = OUTPUT_DIR / config["filename"]

        success = await generate_image(config["prompt"], output_path)

        if not success:
            print(f"   ⚠️ Slide {i} 생성 실패 - 수동 재시도 필요")

    print("\n" + "=" * 60)
    print("✨ 배경 이미지 생성 완료")
    print(f"   출력 폴더: {OUTPUT_DIR}")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())
