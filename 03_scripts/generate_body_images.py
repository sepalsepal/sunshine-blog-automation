"""
본문 이미지 생성 스크립트 (규칙 v2)

규칙:
- 모델: fal-ai/flux-2-pro (필수!)
- 배경: 표지와 동일 (따뜻한 거실)
- 해상도: 1080x1080
"""

import os
import json
import asyncio
from pathlib import Path
from datetime import datetime

# fal_client 임포트
try:
    import fal_client
except ImportError:
    print("Error: fal_client not installed. Run: pip install fal-client")
    exit(1)

# 프로젝트 루트
ROOT = Path(__file__).parent.parent.parent

# 필수 모델 ID (변경 금지!)
MODEL_ID = "fal-ai/flux-2-pro"

# 표준 배경 프롬프트 (표지와 동일)
STANDARD_BACKGROUND = """
warm cozy living room with wooden ceiling fan,
indirect LED ceiling lights with warm glow,
night city view through large window with blinds,
monstera and palm plants in white pots,
floor lamp with white shade,
beige sofa in background,
wooden shelves and cabinets,
marble countertop in foreground,
warm ambient lighting
"""

# 햇살이 기본 특징
HAETSALI_BASE = """
senior golden retriever with white muzzle and gentle eyes,
natural fur texture,
"""


def get_slide_prompt(slide_num: int, food_name: str, food_description: str) -> str:
    """슬라이드별 프롬프트 생성"""

    if slide_num == 1:
        # 결론+효능 슬라이드: 측면 45도, 음식 응시
        pose = "looking at the food with curious expression, SIDE ANGLE VIEW (45 degrees)"
    elif slide_num == 2:
        # 주의+급여량 슬라이드: 블러 효과, 음식 포커스
        pose = "slightly blurred in background, SHALLOW DEPTH OF FIELD, food in sharp focus"
    else:
        pose = "happy expression, looking at camera"

    prompt = f"""
{HAETSALI_BASE}
{pose},
{food_description} in a red ceramic bowl on marble countertop,
{STANDARD_BACKGROUND}
8K, ultra detailed fur texture, Canon EOS R5,
soft natural lighting, professional pet photography,
bottom 30% slightly darker for text overlay space
"""
    return prompt.strip()


async def generate_image(prompt: str, output_path: Path, slide_num: int) -> dict:
    """이미지 생성 (flux-2-pro)"""

    print(f"\n🎨 슬라이드 {slide_num:02d} 생성 중...")
    print(f"   모델: {MODEL_ID}")

    try:
        result = fal_client.subscribe(
            MODEL_ID,
            arguments={
                "prompt": prompt,
                "image_size": {
                    "width": 1080,
                    "height": 1080
                },
                "num_inference_steps": 28,
                "guidance_scale": 3.5,
                "num_images": 1,
                "enable_safety_checker": True,
                "safety_tolerance": "2"
            },
            with_logs=False
        )

        # 이미지 URL 추출
        if result and "images" in result and len(result["images"]) > 0:
            image_url = result["images"][0]["url"]

            # 이미지 다운로드
            import urllib.request
            urllib.request.urlretrieve(image_url, output_path)

            # 메타데이터 저장
            meta = {
                "model": MODEL_ID,
                "prompt": prompt,
                "generated_at": datetime.now().isoformat(),
                "slide_num": slide_num
            }
            meta_path = output_path.with_suffix('.json')
            with open(meta_path, 'w', encoding='utf-8') as f:
                json.dump(meta, f, ensure_ascii=False, indent=2)

            print(f"   ✅ 저장: {output_path}")
            return {"success": True, "path": str(output_path)}
        else:
            print(f"   ❌ 이미지 생성 실패")
            return {"success": False, "error": "No image in result"}

    except Exception as e:
        print(f"   ❌ 오류: {e}")
        return {"success": False, "error": str(e)}


def generate_body_images(topic_en: str, topic_kr: str, folder_num: int, food_description: str):
    """본문 이미지 생성 (01, 02)"""

    content_dir = ROOT / f"content/images/{folder_num:03d}_{topic_en}_{topic_kr}"
    content_dir.mkdir(parents=True, exist_ok=True)

    results = []

    # 슬라이드 01, 02 생성
    for slide_num in [1, 2]:
        prompt = get_slide_prompt(slide_num, topic_en, food_description)
        output_path = content_dir / f"{topic_en}_{slide_num:02d}.png"

        result = asyncio.get_event_loop().run_until_complete(
            generate_image(prompt, output_path, slide_num)
        )
        results.append(result)

    return results


# CLI
if __name__ == "__main__":
    import sys

    if len(sys.argv) < 5:
        print("Usage: python generate_body_images.py <topic_en> <topic_kr> <folder_num> <food_description>")
        print('Example: python generate_body_images.py duck 오리고기 169 "raw duck meat chunks"')
        sys.exit(1)

    topic_en = sys.argv[1]
    topic_kr = sys.argv[2]
    folder_num = int(sys.argv[3])
    food_description = sys.argv[4]

    print(f"\n{'='*60}")
    print(f"🖼️ 본문 이미지 생성: {topic_kr} ({topic_en})")
    print(f"{'='*60}")
    print(f"모델: {MODEL_ID}")
    print(f"폴더: {folder_num:03d}_{topic_en}_{topic_kr}")
    print(f"음식: {food_description}")

    results = generate_body_images(topic_en, topic_kr, folder_num, food_description)

    success_count = sum(1 for r in results if r.get("success"))
    print(f"\n{'='*60}")
    print(f"완료: {success_count}/{len(results)} 이미지 생성")
    print(f"{'='*60}")
