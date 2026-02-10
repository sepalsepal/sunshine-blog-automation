#!/usr/bin/env python3
"""
배치 본문 이미지 생성기
- 커버만 있는 폴더에 본문(01, 02, 03) 이미지 생성
- fal.ai FLUX 2.0 Pro 사용
- v9.1 규칙 준수
"""

import os
import sys
import asyncio
import json
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 설정
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

from dotenv import load_dotenv
load_dotenv(ROOT / ".env")

# fal.ai 설정
FAL_KEY = os.getenv("FAL_KEY")
if FAL_KEY:
    os.environ["FAL_KEY"] = FAL_KEY

import fal_client

# ============================================
# 🔒 하드코딩 설정 - 절대 수정 금지
# ============================================
MODEL_ID = "fal-ai/flux-2-pro"
IMAGE_SIZE = {"width": 1080, "height": 1080}
# ============================================

CONTENT_DIR = ROOT / "content" / "images"
PUBLISHED_CSV = ROOT / "config" / "data" / "published_contents.csv"


def get_published_foods() -> set:
    """게시 완료된 음식 목록 가져오기"""
    published = set()
    if PUBLISHED_CSV.exists():
        import csv
        with open(PUBLISHED_CSV, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                if row.get('게시상태') == '게시완료':
                    published.add(row.get('영문명', '').lower())
    return published


# 음식별 안전도 분류
FOOD_SAFETY = {
    # SAFE
    'cucumber': ('오이', 'SAFE'),
    'beef': ('소고기', 'SAFE'),
    'kale': ('케일', 'SAFE'),
    'celery': ('셀러리', 'SAFE'),
    'blackberry': ('블랙베리', 'SAFE'),
    'cauliflower': ('콜리플라워', 'SAFE'),
    'oatmeal': ('오트밀', 'SAFE'),
    'poached_egg': ('수란', 'SAFE'),
    'almonds': ('아몬드', 'CAUTION'),  # 소량만 OK
    'nuts': ('견과류', 'CAUTION'),  # 종류에 따라 다름
}

# 슬라이드별 프롬프트 템플릿 (v6 4장 구조)
# 규칙: AI 2장 (01, 02) + 실사 1장 (03)
AI_SLIDES = {
    '01': {  # 결론 + 효능 (AI 생성)
        'desc': 'result_benefit',
        'prompt': """A senior golden retriever with white muzzle and warm eyes,
sitting beside a bowl of fresh {food_en},
looking curious at the food with happy expression,
SIDE ANGLE VIEW (45 degrees), looking at food,
bright modern kitchen with natural window lighting,
8K, ultra detailed fur texture, Canon EOS R5,
soft natural lighting, shallow depth of field,
the {food_en} takes up 20% of the frame in the lower portion"""
    },
    '02': {  # 주의사항 + 급여량 (AI 생성)
        'desc': 'caution_amount',
        'prompt': """A senior golden retriever with white muzzle,
in background BLURRED while {food_en} in foreground SHARP,
SHALLOW DEPTH OF FIELD, dog BLURRED in background,
food clearly visible and in focus,
bright kitchen setting,
8K, ultra detailed, Canon EOS R5,
{food_en} prominently displayed"""
    }
}

# 03번(CTA)은 실사 사진 사용 - AI 생성 안 함
REAL_PHOTO_SLIDE = '03'  # sunshine/ 폴더에서 실사 사진 복사


async def generate_single_image(prompt: str, output_path: Path) -> bool:
    """단일 이미지 생성"""
    try:
        print(f"  📸 생성 중: {output_path.name}")

        result = await asyncio.to_thread(
            fal_client.subscribe,
            MODEL_ID,
            arguments={
                "prompt": prompt,
                "image_size": IMAGE_SIZE,
                "num_images": 1,
                "enable_safety_checker": True,
            }
        )

        if result and result.get("images"):
            img_url = result["images"][0]["url"]

            import httpx
            async with httpx.AsyncClient() as client:
                response = await client.get(img_url)
                response.raise_for_status()

                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(response.content)

            print(f"  ✅ 저장됨: {output_path}")
            return True

        return False

    except Exception as e:
        print(f"  ❌ 오류: {e}")
        return False


def copy_real_photo_for_cta(folder_path: Path, food_en: str) -> bool:
    """03번(CTA)용 실사 사진 복사"""
    output_path = folder_path / f"{food_en}_03.png"

    if output_path.exists():
        print(f"  ⏭️ 이미 존재: {output_path.name}")
        return True

    # CTA용 사진 경로 (best_cta 폴더 우선)
    cta_dir = CONTENT_DIR / "sunshine" / "cta_source" / "best_cta"
    if not cta_dir.exists():
        cta_dir = CONTENT_DIR / "sunshine" / "01_usable"
    if not cta_dir.exists():
        print(f"  ⚠️ CTA 사진 폴더 없음 - 03번 스킵")
        return False

    import shutil
    import random
    from PIL import Image

    # happy 키워드 사진 우선 선택
    cta_photos = list(cta_dir.glob("*happy*.jpg")) + list(cta_dir.glob("*happy*.png"))
    if not cta_photos:
        cta_photos = list(cta_dir.glob("*.jpg")) + list(cta_dir.glob("*.png"))

    if not cta_photos:
        print(f"  ⚠️ 실사 사진 없음 - 03번 스킵")
        return False

    # 랜덤 선택
    selected = random.choice(cta_photos)

    # 1080x1080으로 리사이즈 후 저장
    img = Image.open(selected)
    if img.mode == 'RGBA':
        img = img.convert('RGB')
    img = img.resize((1080, 1080), Image.LANCZOS)
    img.save(output_path, 'PNG', quality=95)

    print(f"  📷 실사 복사: {selected.name} → {output_path.name}")
    return True


async def generate_body_for_folder(folder_path: Path, food_en: str, food_kr: str):
    """폴더에 본문 이미지 생성 (AI 2장 + 실사 1장)"""
    print(f"\n🔄 {food_kr} ({food_en}) 본문 생성 시작...")

    results = {'ai_success': 0, 'ai_failed': 0, 'real_success': 0}

    # 1. AI 이미지 생성 (01, 02번)
    for slide_num, template in AI_SLIDES.items():
        output_path = folder_path / f"{food_en}_{slide_num}.png"

        if output_path.exists():
            print(f"  ⏭️ 이미 존재: {output_path.name}")
            results['ai_success'] += 1
            continue

        prompt = template['prompt'].format(food_en=food_en)

        success = await generate_single_image(prompt, output_path)
        if success:
            results['ai_success'] += 1
        else:
            results['ai_failed'] += 1

    # 2. 실사 사진 복사 (03번 CTA)
    if copy_real_photo_for_cta(folder_path, food_en):
        results['real_success'] = 1

    return results


async def main(folders: list = None, limit: int = 10):
    """메인 실행"""
    print("=" * 50)
    print("🎨 김과장 - 배치 본문 이미지 생성기")
    print("=" * 50)
    print(f"모델: {MODEL_ID}")
    print(f"크기: {IMAGE_SIZE['width']}x{IMAGE_SIZE['height']}")
    print(f"제한: {limit}개 폴더")
    print(f"규칙: AI 2장 + 실사 1장")
    print("=" * 50)

    # 1️⃣ 게시 완료 목록 체크 (규칙 준수!)
    published_foods = get_published_foods()
    print(f"\n📋 게시 완료 음식: {len(published_foods)}개")

    # 본문이 없는 폴더 찾기
    need_body = []

    for folder in CONTENT_DIR.iterdir():
        if not folder.is_dir():
            continue
        if folder.name.startswith('000_') or folder.name in ['archive', 'reference', 'sunshine']:
            continue
        if 'published' in folder.name:
            continue

        # 폴더명에서 영문명 추출
        parts = folder.name.split('_')
        if len(parts) >= 2:
            food_en = parts[1]

            # ✅ 게시 완료 체크 (중복 방지!)
            if food_en.lower() in published_foods:
                continue

            # 01번 이미지 존재 여부 확인
            body_check = folder / f"{food_en}_01.png"
            if not body_check.exists():
                food_kr = parts[2] if len(parts) >= 3 else food_en
                need_body.append({
                    'path': folder,
                    'food_en': food_en,
                    'food_kr': food_kr
                })

    if folders:
        # 특정 폴더만 처리
        need_body = [f for f in need_body if f['food_en'] in folders]

    # 제한 적용
    need_body = need_body[:limit]

    print(f"\n📋 처리 대상: {len(need_body)}개 폴더 (게시완료 제외)")
    for i, item in enumerate(need_body, 1):
        print(f"  {i}. {item['food_kr']} ({item['food_en']})")

    # 비용 계산 (AI 2장만 비용 발생, 실사는 무료)
    ai_images = len(need_body) * 2  # AI 이미지는 01, 02 두 장
    cost = ai_images * 0.04
    print(f"\n💰 예상 비용: ${cost:.2f} (AI {ai_images}장 × $0.04)")
    print(f"   실사 {len(need_body)}장은 무료 (기존 사진 활용)")

    # 생성 시작
    total_ai_success = 0
    total_ai_failed = 0
    total_real_success = 0

    for i, item in enumerate(need_body, 1):
        print(f"\n[{i}/{len(need_body)}] {item['food_kr']}")

        results = await generate_body_for_folder(
            item['path'],
            item['food_en'],
            item['food_kr']
        )

        total_ai_success += results['ai_success']
        total_ai_failed += results['ai_failed']
        total_real_success += results['real_success']

        # 진행률 출력
        progress = (i / len(need_body)) * 100
        print(f"  📊 진행률: {progress:.0f}% ({i}/{len(need_body)})")

    # 최종 결과
    print("\n" + "=" * 50)
    print("📊 최종 결과")
    print("=" * 50)
    print(f"🤖 AI 이미지: {total_ai_success}장 성공 / {total_ai_failed}장 실패")
    print(f"📷 실사 이미지: {total_real_success}장 복사")
    print(f"💰 실제 비용: ~${total_ai_success * 0.04:.2f} (AI만 비용 발생)")
    print("=" * 50)

    return {
        'ai_success': total_ai_success,
        'ai_failed': total_ai_failed,
        'real_success': total_real_success
    }


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='배치 본문 이미지 생성')
    parser.add_argument('--limit', type=int, default=10, help='처리할 폴더 수')
    parser.add_argument('--folders', nargs='+', help='특정 폴더만 처리')

    args = parser.parse_args()

    asyncio.run(main(folders=args.folders, limit=args.limit))
