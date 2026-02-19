#!/usr/bin/env python3
"""
흰쌀밥 본문 이미지 재생성 스크립트
- 커버 이미지 배경과 동일한 공간
- flux-2-pro 사용
- 이작가 담당
"""

import os
import asyncio
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

PROJECT_ROOT = Path(__file__).parent.parent.parent
CONTENT_DIR = PROJECT_ROOT / "content" / "images" / "018_흰쌀밥"

# 커버 이미지 배경 설명 (레퍼런스)
BACKGROUND_REFERENCE = """warm cozy living room with wooden ceiling fan,
night city view through large window, monstera and palm plants,
floor lamp with white shade, cute bear-shaped mood lamp,
beige sofa in background, wooden dining table,
warm ambient lighting with indirect LED ceiling lights"""

# 본문 슬라이드 프롬프트 (커버 배경 매칭)
SLIDES = [
    {
        "slide": 1,
        "type": "result_benefit",
        "prompt": f"""A senior golden retriever with white muzzle and gentle eyes,
SIDE ANGLE VIEW 45 degrees looking curiously at food,
sitting beside a ceramic bowl of steamed white rice on wooden table,
rice bowl in foreground close to camera showing fluffy texture,
{BACKGROUND_REFERENCE},
bottom 30% slightly darker for text overlay,
8K ultra detailed fur texture, Canon EOS R5,
soft warm lighting, shallow depth of field""",
    },
    {
        "slide": 2,
        "type": "caution_amount",
        "prompt": f"""A senior golden retriever with white muzzle SOFTLY BLURRED in background,
SHALLOW DEPTH OF FIELD with bokeh effect,
sharp focus on ceramic bowl of warm rice porridge in foreground,
steam rising from the soft rice porridge,
wooden table surface,
{BACKGROUND_REFERENCE},
8K ultra detailed, Canon EOS R5, warm cinematic lighting""",
    },
    {
        "slide": 3,
        "type": "cta",
        "prompt": f"""A senior golden retriever with white muzzle,
front view looking at camera with happy smiling expression and bright eyes,
tongue slightly out, cheerful mood,
sitting at wooden table with small bowl of white rice nearby,
{BACKGROUND_REFERENCE},
golden hour warm lighting,
8K ultra detailed fur texture, Canon EOS R5, soft natural lighting""",
    }
]

NEGATIVE_PROMPT = "puppy, young dog, eating, licking, biting, mouth open with food, touching food, text, watermark, logo, harsh lighting, cold colors"


async def generate_images():
    """fal.ai flux-2-pro로 이미지 생성"""
    import fal_client
    import httpx
    from PIL import Image
    import io

    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print("❌ FAL_KEY가 .env에 설정되지 않았습니다.")
        return

    os.environ["FAL_KEY"] = fal_key

    print("🎨 흰쌀밥 본문 이미지 재생성 시작")
    print("📌 커버 배경과 동일한 공간으로 생성")
    print("📌 모델: flux-2-pro")
    print("=" * 50)

    for slide_info in SLIDES:
        slide_num = slide_info["slide"]
        slide_type = slide_info["type"]
        prompt = slide_info["prompt"]

        print(f"\n[{slide_num}/3] {slide_type} 생성 중...")

        try:
            result = await asyncio.to_thread(
                fal_client.subscribe,
                "fal-ai/flux-2-pro",  # FLUX.2 Pro (정확한 모델 ID)
                arguments={
                    "prompt": prompt,
                    "image_size": {"width": 1080, "height": 1080},
                    "num_images": 1,
                    "output_format": "png",
                    "safety_tolerance": "5",
                    "num_inference_steps": 28,
                    "guidance_scale": 3.5,
                }
            )

            image_url = result["images"][0]["url"]

            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(image_url)
                response.raise_for_status()

                img = Image.open(io.BytesIO(response.content))
                if img.size != (1080, 1080):
                    img = img.resize((1080, 1080), Image.Resampling.LANCZOS)

                # 기존 파일 백업
                output_path = CONTENT_DIR / f"rice_{slide_num:02d}.png"
                if output_path.exists():
                    archive_dir = CONTENT_DIR / "archive"
                    archive_dir.mkdir(exist_ok=True)
                    backup_path = archive_dir / f"rice_{slide_num:02d}_v1.png"
                    output_path.rename(backup_path)
                    print(f"   📦 기존 파일 백업: {backup_path.name}")

                img.save(output_path, "PNG", optimize=True)
                print(f"   ✅ 완료: {output_path.name}")

        except Exception as e:
            print(f"   ❌ 실패: {e}")

    print("\n" + "=" * 50)
    print("🎨 본문 이미지 재생성 완료!")
    print("📁 위치: content/images/018_흰쌀밥/")


if __name__ == "__main__":
    asyncio.run(generate_images())
