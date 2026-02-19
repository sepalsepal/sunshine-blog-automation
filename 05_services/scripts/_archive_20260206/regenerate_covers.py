#!/usr/bin/env python3
"""
표지 이미지 일괄 재생성 스크립트

CLAUDE.md 가이드라인 v8.1 기준:
- 상단 25~30% 여백 필수
- 제목은 상단 15~25%에 위치 (햇살이 얼굴 위)
- 햇살이: 프레임 중앙, 밝은 표정 (happy, tongue out, smiling)
- 음식: 하단 전경에 크게 (20~25%)

Author: 최기술 대리
"""

import os
import sys
import asyncio
import subprocess
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

# 프로젝트 루트
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))
load_dotenv(ROOT / ".env")

# fal.ai 클라이언트
try:
    import fal_client
    FAL_AVAILABLE = True
except ImportError:
    FAL_AVAILABLE = False

# 이미지 처리
from PIL import Image
import requests
from io import BytesIO


# ============================================
# 표지 생성 대상 (미게시 콘텐츠)
# ============================================

COVER_TARGETS = [
    {
        "folder": "011_strawberry",
        "name": "strawberry",
        "title": "STRAWBERRY",
        "food_desc": "fresh red strawberries in a white ceramic bowl",
        "food_kr": "딸기"
    },
    {
        "folder": "012_mango",
        "name": "mango",
        "title": "MANGO",
        "food_desc": "sliced fresh mango showing juicy orange flesh on a plate",
        "food_kr": "망고"
    },
    {
        "folder": "014_pear",
        "name": "pear",
        "title": "PEAR",
        "food_desc": "fresh green pear on a wooden cutting board",
        "food_kr": "배"
    },
    {
        "folder": "015_kiwi",
        "name": "kiwi",
        "title": "KIWI",
        "food_desc": "sliced kiwi fruit showing green flesh with seeds on a plate",
        "food_kr": "키위"
    },
    {
        "folder": "016_papaya",
        "name": "papaya",
        "title": "PAPAYA",
        "food_desc": "halved papaya showing orange flesh and black seeds on a plate",
        "food_kr": "파파야"
    },
    {
        "folder": "017_peach",
        "name": "peach",
        "title": "PEACH",
        "food_desc": "fresh ripe peaches with fuzzy skin on a plate",
        "food_kr": "복숭아"
    },
]


# ============================================
# 프롬프트 템플릿 (v8.1 가이드라인 준수)
# ============================================

def get_cover_prompt(food_desc: str) -> str:
    """표지용 프롬프트 생성 (승인된 레퍼런스 기반 v3)

    레퍼런스: Cover_ref 폴더의 승인된 이미지들
    핵심 레이아웃:
    - 개 머리 상단 = 프레임 상단에서 30%
    - 음식 그릇 하단 = 프레임 상단에서 70%
    """

    prompt = f"""High-quality photograph.
A senior 11-year-old Golden Retriever female named 'Haetsal',
with a significantly white muzzle and face, golden fur, black nose and eyes,
smiling brightly looking at {food_desc} in a pretty ceramic bowl on a dining table.

Background is a trendy 2026 Korean apartment living room with warm yellow indirect lighting.

(Layout Constraint Checklist:
Top of dog's head positioned at 30% from the top edge.
Bottom of the bowl with food positioned at 70% from the top edge.
Food is realistically sized and fits inside the bowl.)"""

    return prompt


def get_negative_prompt() -> str:
    """네거티브 프롬프트"""
    return """text, letters, words, watermark, logo,
sad expression, closed mouth, sleepy, tired, bored,
eating food, licking, biting, mouth on food, touching food,
puppy, young dog,
blurry, low quality, artifacts, distorted,
dark lighting, harsh shadows,
dog at top of frame, head touching top edge,
no empty space above head"""


# ============================================
# 이미지 생성 함수
# ============================================

async def generate_cover_image(target: dict, output_dir: Path) -> str:
    """fal.ai FLUX 2 Pro로 표지 이미지 생성"""

    if not FAL_AVAILABLE:
        print(f"  ⚠️ fal_client 미설치. pip install fal-client")
        return None

    fal_key = os.getenv("FAL_KEY")
    if not fal_key:
        print(f"  ⚠️ FAL_KEY 환경변수 없음")
        return None

    prompt = get_cover_prompt(target["food_desc"])
    negative = get_negative_prompt()

    print(f"  🎨 이미지 생성 중... ({target['name']})")

    try:
        # fal.ai API 호출 - FLUX 2.0 Pro 사용
        result = await fal_client.subscribe_async(
            "fal-ai/flux-2-pro",  # FLUX 2.0 Pro (올바른 모델 ID)
            arguments={
                "prompt": prompt,
                "negative_prompt": negative,
                "image_size": "square_hd",  # 1024x1024
                "num_images": 1,
                "safety_tolerance": "5",
            },
        )

        if result and "images" in result and len(result["images"]) > 0:
            image_url = result["images"][0]["url"]

            # 이미지 다운로드
            response = requests.get(image_url)
            img = Image.open(BytesIO(response.content))

            # 1080x1080으로 리사이즈
            img = img.resize((1080, 1080), Image.LANCZOS)

            # 저장 (텍스트 오버레이 전 원본)
            output_path = output_dir / f"{target['name']}_00_raw.png"
            img.save(str(output_path), "PNG")

            print(f"  ✅ 저장: {output_path.name}")
            return str(output_path)
        else:
            print(f"  ❌ 이미지 생성 실패: 응답 없음")
            return None

    except Exception as e:
        print(f"  ❌ 에러: {e}")
        return None


# ============================================
# 텍스트 오버레이 함수
# ============================================

def apply_text_overlay(raw_image_path: str, title: str, output_path: str) -> bool:
    """Puppeteer로 텍스트 오버레이 적용"""

    # Node.js 스크립트 실행
    script_path = ROOT / "services" / "scripts" / "apply_single_cover_overlay.js"

    if not script_path.exists():
        # 스크립트가 없으면 간단한 Python 대체 사용
        return apply_text_overlay_python(raw_image_path, title, output_path)

    try:
        result = subprocess.run(
            ["node", str(script_path), raw_image_path, title, output_path],
            capture_output=True,
            text=True,
            cwd=str(ROOT / "services" / "scripts")
        )

        if result.returncode == 0:
            print(f"  ✅ 텍스트 오버레이 완료: {Path(output_path).name}")
            return True
        else:
            print(f"  ⚠️ Node.js 에러, Python 대체 사용")
            return apply_text_overlay_python(raw_image_path, title, output_path)

    except Exception as e:
        print(f"  ⚠️ Node.js 실행 실패: {e}, Python 대체 사용")
        return apply_text_overlay_python(raw_image_path, title, output_path)


def apply_text_overlay_python(raw_image_path: str, title: str, output_path: str) -> bool:
    """PIL로 텍스트 오버레이 (대체 방법)"""
    from PIL import ImageDraw, ImageFont

    try:
        img = Image.open(raw_image_path)
        draw = ImageDraw.Draw(img)

        # 폰트 설정 (시스템 폰트 사용)
        font_size = calculate_font_size(title)
        try:
            # macOS 기본 폰트
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
        except:
            font = ImageFont.load_default()

        # 텍스트 위치 계산 (상단 18%)
        text_bbox = draw.textbbox((0, 0), title, font=font)
        text_width = text_bbox[2] - text_bbox[0]
        text_height = text_bbox[3] - text_bbox[1]

        x = (1080 - text_width) // 2
        y = int(1080 * 0.18)  # 상단 18%

        # 그림자 효과
        shadow_offset = 4
        draw.text((x + shadow_offset, y + shadow_offset), title, font=font, fill=(0, 0, 0, 128))

        # 메인 텍스트
        draw.text((x, y), title, font=font, fill=(255, 255, 255))

        # 언더라인
        underline_width = int(text_width * 1.0)  # 100%
        underline_x = (1080 - underline_width) // 2
        underline_y = y + text_height + 10
        draw.rectangle(
            [underline_x, underline_y, underline_x + underline_width, underline_y + 4],
            fill=(255, 255, 255)
        )

        img.save(output_path, "PNG")
        print(f"  ✅ 텍스트 오버레이 완료 (PIL): {Path(output_path).name}")
        return True

    except Exception as e:
        print(f"  ❌ PIL 오버레이 실패: {e}")
        return False


def calculate_font_size(title: str) -> int:
    """글자 수에 따른 폰트 크기"""
    size_map = {
        4: 160,
        5: 150,  # APPLE, PEACH
        6: 140,  # BANANA
        7: 130,  # PUMPKIN
        8: 120,  # BROCCOLI
        9: 110,  # BLUEBERRY
        10: 100, # STRAWBERRY
    }
    char_count = len(title)
    if char_count <= 4:
        return size_map[4]
    if char_count >= 10:
        return size_map[10]
    return size_map.get(char_count, 140)


# ============================================
# 메인 실행
# ============================================

def backup_existing_images(output_dir: Path, name: str):
    """기존 이미지를 temp 폴더로 백업"""
    temp_dir = output_dir / "temp"
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_dir = temp_dir / f"backup_{timestamp}"

    # 기존 표지 이미지 찾기
    existing_files = list(output_dir.glob(f"{name}_00*.png"))

    if existing_files:
        backup_dir.mkdir(parents=True, exist_ok=True)
        for f in existing_files:
            dest = backup_dir / f.name
            f.rename(dest)
            print(f"  📦 백업: {f.name} → temp/backup_{timestamp}/")
        return str(backup_dir)
    return None


async def main():
    print("=" * 60)
    print("🎨 표지 이미지 일괄 재생성 (FLUX 2.0 Pro)")
    print("=" * 60)
    print(f"대상: {len(COVER_TARGETS)}개 콘텐츠")
    print()

    results = []

    for target in COVER_TARGETS:
        print(f"\n📁 {target['title']} ({target['folder']})")
        print("-" * 40)

        # 출력 디렉토리
        output_dir = ROOT / "content" / "images" / target["folder"]
        output_dir.mkdir(parents=True, exist_ok=True)

        # 기존 이미지 백업
        backup_existing_images(output_dir, target["name"])

        # 1. 이미지 생성
        raw_path = await generate_cover_image(target, output_dir)

        if not raw_path:
            results.append({"name": target["name"], "status": "failed", "reason": "이미지 생성 실패"})
            continue

        # 2. 텍스트 오버레이
        final_path = str(output_dir / f"{target['name']}_00.png")
        success = apply_text_overlay(raw_path, target["title"], final_path)

        if success:
            results.append({"name": target["name"], "status": "success", "path": final_path})
        else:
            results.append({"name": target["name"], "status": "partial", "reason": "오버레이 실패"})

    # 결과 요약
    print("\n" + "=" * 60)
    print("📊 결과 요약")
    print("=" * 60)

    success = sum(1 for r in results if r["status"] == "success")
    failed = sum(1 for r in results if r["status"] == "failed")
    partial = sum(1 for r in results if r["status"] == "partial")

    print(f"✅ 성공: {success}개")
    print(f"⚠️ 부분 성공: {partial}개")
    print(f"❌ 실패: {failed}개")

    for r in results:
        status_icon = "✅" if r["status"] == "success" else "⚠️" if r["status"] == "partial" else "❌"
        print(f"  {status_icon} {r['name']}: {r.get('reason', r.get('path', ''))}")

    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
