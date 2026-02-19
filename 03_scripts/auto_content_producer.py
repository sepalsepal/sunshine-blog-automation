#!/usr/bin/env python3
"""
자동 콘텐츠 제작 스크립트 (v1.0)
- 규칙 위반 원천 차단
- 모든 스펙 하드코딩으로 실수 방지
- CTA는 반드시 실제 햇살이 사진 사용

작성: 2026-01-30
"""

import asyncio
import json
import os
import random
import shutil
import sys
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from datetime import datetime

# 프로젝트 루트
ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(ROOT))

# ============================================================
# 🔒 하드코딩된 규칙 (절대 변경 금지)
# ============================================================

# 이미지 생성 API (필수)
FLUX_MODEL_ID = "fal-ai/flux-2-pro"  # 이것만 사용!

# 표지 텍스트 스펙
COVER_FONT = "Arial"
COVER_FONT_SIZE = 114
COVER_TEXT_Y_PERCENT = 0.25  # 상단 25%
COVER_TEXT_COLOR = (255, 255, 255)  # 흰색

# 본문 텍스트 스펙
CONTENT_TITLE_SIZE = 52
CONTENT_SUBTITLE_SIZE = 26
CONTENT_GRADIENT_START = 0.50  # 하단 50%부터 그라데이션

# CTA 스펙
CTA_TITLE_COLOR = (255, 217, 61)  # #FFD93D 노란색

# 이미지 크기
IMAGE_SIZE = (1080, 1080)

# 경로
COVER_READY_DIR = ROOT / "content/images/000_cover/02_ready"
CTA_SOURCE_DIR = ROOT / "content/images/sunshine/cta_source/best_cta"
CONTENT_DIR = ROOT / "content/images"

# ============================================================
# 📋 슬라이드 타입별 처리 규칙
# ============================================================

SLIDE_RULES = {
    "cover": {
        "image_source": "cover_ready",  # 표지는 02_ready에서 복사
        "ai_generate": False,
        "text_overlay": True,
        "font": COVER_FONT,
        "font_size": COVER_FONT_SIZE,
        "text_y": COVER_TEXT_Y_PERCENT,
        "text_color": COVER_TEXT_COLOR,
        "gradient": False,
    },
    "content_bottom": {
        "image_source": "ai",  # AI 생성
        "ai_generate": True,
        "text_overlay": True,
        "font": "Pretendard",
        "font_size": CONTENT_TITLE_SIZE,
        "text_y": 0.85,
        "text_color": (255, 255, 255),
        "gradient": True,
        "gradient_start": CONTENT_GRADIENT_START,
    },
    "cta": {
        "image_source": "real_photo",  # 실제 햇살이 사진!
        "ai_generate": False,
        "text_overlay": True,
        "font": "Pretendard",
        "font_size": CONTENT_TITLE_SIZE,
        "text_y": 0.85,
        "text_color": CTA_TITLE_COLOR,  # 노란색!
        "gradient": True,
        "gradient_start": CONTENT_GRADIENT_START,
    },
}


class ContentProducer:
    """자동 콘텐츠 제작기 (규칙 강제 적용)"""

    def __init__(self):
        self.errors = []
        self.warnings = []

    def validate_rules(self) -> bool:
        """제작 전 규칙 검증"""
        print("🔍 규칙 검증 중...")

        # 1. CTA 소스 폴더 확인
        if not CTA_SOURCE_DIR.exists():
            self.errors.append(f"CTA 소스 폴더 없음: {CTA_SOURCE_DIR}")
        else:
            cta_photos = list(CTA_SOURCE_DIR.glob("*.jpg"))
            if len(cta_photos) < 10:
                self.warnings.append(f"CTA 소스 부족: {len(cta_photos)}장")

        # 2. 표지 폴더 확인
        if not COVER_READY_DIR.exists():
            self.errors.append(f"표지 폴더 없음: {COVER_READY_DIR}")

        # 3. 모델 ID 검증
        if "flux-2-pro" not in FLUX_MODEL_ID:
            self.errors.append(f"잘못된 모델 ID: {FLUX_MODEL_ID}")

        if self.errors:
            print("❌ 규칙 검증 실패:")
            for e in self.errors:
                print(f"   - {e}")
            return False

        print("✅ 규칙 검증 통과")
        return True

    def find_cover_image(self, topic_en: str, topic_kr: str) -> Path | None:
        """표지 이미지 찾기"""
        patterns = [
            f"*{topic_kr}*{topic_en}*.png",
            f"*{topic_en}*.png",
            f"*{topic_kr}*.png",
        ]

        for pattern in patterns:
            matches = list(COVER_READY_DIR.glob(pattern))
            if matches:
                return matches[0]

        return None

    def get_random_cta_photo(self) -> Path | None:
        """랜덤 CTA 사진 선택 (실제 햇살이 사진만!)"""
        photos = list(CTA_SOURCE_DIR.glob("*.jpg"))
        if not photos:
            return None
        return random.choice(photos)

    def apply_gradient_overlay(self, img: Image.Image, start_percent: float = 0.5) -> Image.Image:
        """하단 그라데이션 오버레이 적용"""
        width, height = img.size
        overlay = Image.new('RGBA', img.size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(overlay)

        start_y = int(height * start_percent)
        for y in range(start_y, height):
            alpha = int(180 * (y - start_y) / (height - start_y))
            draw.line([(0, y), (width, y)], fill=(0, 0, 0, alpha))

        if img.mode != 'RGBA':
            img = img.convert('RGBA')

        return Image.alpha_composite(img, overlay)

    def add_text_overlay(
        self,
        img: Image.Image,
        title: str,
        subtitle: str = "",
        slide_type: str = "content_bottom"
    ) -> Image.Image:
        """텍스트 오버레이 추가 (규칙에 따라)"""
        rules = SLIDE_RULES[slide_type]

        # 그라데이션 적용
        if rules.get("gradient"):
            img = self.apply_gradient_overlay(img, rules.get("gradient_start", 0.5))

        # 텍스트 추가
        draw = ImageDraw.Draw(img)
        width, height = img.size

        # 폰트 로드
        try:
            if rules["font"] == "Arial":
                font_path = "/System/Library/Fonts/Supplemental/Arial Bold.ttf"
            else:
                font_path = str(ROOT / "assets/fonts/Pretendard-Bold.ttf")

            title_font = ImageFont.truetype(font_path, rules["font_size"])

            if subtitle:
                subtitle_font = ImageFont.truetype(font_path, CONTENT_SUBTITLE_SIZE)
        except:
            title_font = ImageFont.load_default()
            subtitle_font = title_font

        # 텍스트 위치 계산
        text_y = int(height * rules["text_y"])

        # 제목 그리기
        title_bbox = draw.textbbox((0, 0), title, font=title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2

        # 그림자 효과
        shadow_offset = 3
        draw.text(
            (title_x + shadow_offset, text_y + shadow_offset),
            title,
            font=title_font,
            fill=(0, 0, 0, 180)
        )

        # 실제 텍스트
        draw.text(
            (title_x, text_y),
            title,
            font=title_font,
            fill=rules["text_color"]
        )

        # 부제목 그리기
        if subtitle:
            subtitle_y = text_y + rules["font_size"] + 10
            subtitle_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
            subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
            subtitle_x = (width - subtitle_width) // 2

            draw.text(
                (subtitle_x, subtitle_y),
                subtitle,
                font=subtitle_font,
                fill=(255, 255, 255)
            )

        return img.convert('RGB')

    async def generate_ai_image(self, prompt: str, output_path: Path) -> bool:
        """AI 이미지 생성 (flux-2-pro 강제)"""
        try:
            import fal_client

            # 🔒 모델 ID 하드코딩 - 절대 변경 금지!
            result = fal_client.subscribe(
                "fal-ai/flux-2-pro",  # 이것만!
                arguments={
                    "prompt": prompt,
                    "image_size": "square_hd",
                    "num_images": 1,
                    "enable_safety_checker": True,
                }
            )

            if result and result.get("images"):
                image_url = result["images"][0]["url"]

                import requests
                response = requests.get(image_url)

                output_path.parent.mkdir(parents=True, exist_ok=True)
                with open(output_path, 'wb') as f:
                    f.write(response.content)

                return True

        except Exception as e:
            print(f"❌ 이미지 생성 실패: {e}")

        return False

    async def produce_content(
        self,
        topic_en: str,
        topic_kr: str,
        folder_number: int,
        text_config: list[dict],
        safety: str = "safe"
    ) -> dict:
        """콘텐츠 제작 (전체 파이프라인)"""

        print(f"\n{'='*60}")
        print(f"📦 콘텐츠 제작: {topic_kr} ({topic_en})")
        print(f"{'='*60}")

        # 1. 규칙 검증
        if not self.validate_rules():
            return {"success": False, "error": "규칙 검증 실패"}

        # 2. 폴더 생성
        folder_name = f"{folder_number:03d}_{topic_kr}"
        content_folder = CONTENT_DIR / folder_name
        final_folder = content_folder / "_final"
        archive_folder = content_folder / "archive"

        final_folder.mkdir(parents=True, exist_ok=True)
        archive_folder.mkdir(parents=True, exist_ok=True)

        print(f"📁 폴더 생성: {folder_name}")

        # 3. 표지 처리 (slide 0)
        cover_config = text_config[0]
        cover_src = self.find_cover_image(topic_en, topic_kr)

        if not cover_src:
            return {"success": False, "error": f"표지 이미지 없음: {topic_en}"}

        print(f"📷 표지 복사: {cover_src.name}")

        # 표지 이미지 로드 및 텍스트 오버레이
        cover_img = Image.open(cover_src).convert('RGB')
        cover_img = cover_img.resize(IMAGE_SIZE, Image.LANCZOS)

        cover_output = self.add_text_overlay(
            cover_img,
            title=cover_config["title"],
            subtitle=cover_config.get("subtitle", ""),
            slide_type="cover"
        )
        cover_output.save(final_folder / f"{topic_en}_00.png", quality=95)
        print(f"   ✅ {topic_en}_00.png 저장")

        # 4. 본문 이미지 생성 (slide 1, 2)
        for i, config in enumerate(text_config[1:3], start=1):
            print(f"\n🎨 슬라이드 {i:02d} 생성 중...")

            # 프롬프트 생성 (배경 일관성 유지)
            prompt = self._build_prompt(topic_en, topic_kr, safety, i)

            # AI 이미지 생성
            temp_path = archive_folder / f"{topic_en}_{i:02d}_raw.png"
            success = await self.generate_ai_image(prompt, temp_path)

            if not success:
                return {"success": False, "error": f"슬라이드 {i} 생성 실패"}

            # 텍스트 오버레이
            img = Image.open(temp_path).convert('RGB')
            img = img.resize(IMAGE_SIZE, Image.LANCZOS)

            final_img = self.add_text_overlay(
                img,
                title=config["title"],
                subtitle=config.get("subtitle", ""),
                slide_type="content_bottom"
            )

            final_img.save(final_folder / f"{topic_en}_{i:02d}.png", quality=95)
            print(f"   ✅ {topic_en}_{i:02d}.png 저장")

        # 5. CTA 이미지 (slide 3) - 실제 햇살이 사진!
        print(f"\n🐕 CTA 슬라이드 (실제 햇살이 사진)")

        cta_config = text_config[3]
        cta_photo = self.get_random_cta_photo()

        if not cta_photo:
            return {"success": False, "error": "CTA 사진 없음"}

        print(f"   📷 사진: {cta_photo.name}")

        # CTA 이미지 처리
        cta_img = Image.open(cta_photo).convert('RGB')
        cta_img = cta_img.resize(IMAGE_SIZE, Image.LANCZOS)

        cta_final = self.add_text_overlay(
            cta_img,
            title=cta_config["title"],
            subtitle=cta_config.get("subtitle", ""),
            slide_type="cta"  # 노란색 제목!
        )

        cta_final.save(final_folder / f"{topic_en}_03.png", quality=95)
        print(f"   ✅ {topic_en}_03.png 저장")

        # 6. 캡션 생성
        caption = self._generate_caption(topic_en, topic_kr, safety)
        caption_path = content_folder / "caption.txt"
        caption_path.write_text(caption, encoding='utf-8')
        print(f"\n📝 캡션 저장: caption.txt")

        # 7. 결과 요약
        result = {
            "success": True,
            "folder": str(content_folder),
            "files": [
                f"{topic_en}_00.png",
                f"{topic_en}_01.png",
                f"{topic_en}_02.png",
                f"{topic_en}_03.png",
            ],
            "caption": str(caption_path),
        }

        print(f"\n✅ 콘텐츠 제작 완료!")
        print(f"   📁 {content_folder}")

        return result

    def _build_prompt(self, topic_en: str, topic_kr: str, safety: str, slide_num: int) -> str:
        """AI 이미지 프롬프트 생성 (배경 일관성 필수)"""

        # 공통 배경 요소 (표지와 동일!)
        background = """
warm cozy living room with wooden ceiling fan,
night city view through large window,
monstera and palm plants in corners,
floor lamp with white shade,
cute bear-shaped mood lamp (Mr. Maria Brown),
beige sofa in background,
wooden dining table,
warm ambient lighting with indirect LED ceiling lights,
""".strip()

        # 음식 형태
        food_forms = {
            "spinach": "fresh green spinach leaves in a white bowl",
            "zucchini": "sliced green zucchini on a cutting board",
            "chicken": "cooked chicken breast pieces on a plate",
            "beef": "cooked beef cubes on a white plate",
            "salmon": "grilled salmon fillet on a plate",
            "tuna": "canned tuna in a small bowl",
            "yogurt": "white yogurt in a glass bowl",
            "tofu": "cubed white tofu on a plate",
            "boiled_egg": "halved boiled eggs showing yellow yolk",
            "mackerel": "grilled mackerel on a plate",
            "potato": "baked potato cut in half on a plate",
            "chocolate": "dark chocolate bar broken into pieces (DANGER)",
            "blackberry": "fresh blackberries in a small bowl",
        }

        food_desc = food_forms.get(topic_en, f"fresh {topic_en} on a plate")

        # 앵글 다양성
        angles = [
            "45 degree side angle view, looking at food",
            "front view, looking at camera with curious expression",
        ]
        angle = angles[slide_num - 1] if slide_num <= len(angles) else angles[0]

        # 금지 포즈 네거티브
        negative = "eating, licking, biting, chewing, mouth open with food"

        # 햇살이 특징
        dog_features = """
senior golden retriever with white muzzle and white fur around eyes,
black eyes, black nose, warm caramel golden fur,
10 years old senior gentle look,
smaller ears than typical golden retriever,
""".strip()

        prompt = f"""
{dog_features}
{angle},
{food_desc} placed in foreground,
{background}
8K ultra detailed fur texture, Canon EOS R5,
soft natural lighting, shallow depth of field,
--no {negative}
""".strip()

        return prompt

    def _generate_caption(self, topic_en: str, topic_kr: str, safety: str) -> str:
        """캡션 생성"""

        if safety == "dangerous":
            caption = f"""🚫 {topic_kr}, 강아지에게 절대 주지 마세요!

⚠️ {topic_kr}은(는) 강아지에게 매우 위험합니다!

🆘 섭취 시 즉시 동물병원으로!

📌 기억하세요
"{topic_kr} 조금이라도 위험할 수 있습니다"

💾 저장해두고 주변에 공유하세요!
모르는 분들이 생각보다 많아요 😢

ℹ️ 일부 이미지는 AI로 생성되었습니다.
ℹ️ Some images were generated by AI.

#강아지{topic_kr} #강아지위험음식 #반려견음식 #강아지건강
#강아지금지음식 #펫푸드 #강아지케어 #골든리트리버
#시니어독 #강아지정보 #반려견가이드 #강아지음식가이드
#dogfood #doghealth #petcare #goldensofinstagram
"""
        else:
            caption = f"""🐕 {topic_kr}, 강아지가 먹어도 될까요?

✅ 정답: 먹어도 됩니다!

👍 {topic_kr}의 좋은 점
• 영양가 풍부
• 적당량 급여 시 건강에 도움

⚠️ 주의사항
• 처음엔 소량만 급여
• 알레르기 반응 관찰
• 과다 급여 금지

📏 적정량
소형견: 소량 | 중형견: 적당량 | 대형견: 조금 더

💾 저장해두고 주변에 공유하세요!

ℹ️ 일부 이미지는 AI로 생성되었습니다.
ℹ️ Some images were generated by AI.

#강아지{topic_kr} #강아지음식 #반려견음식 #강아지건강
#펫푸드 #강아지케어 #골든리트리버 #시니어독
#강아지정보 #반려견가이드 #강아지음식가이드
#dogfood #doghealth #petcare #goldensofinstagram
"""

        return caption.strip()


# ============================================================
# CLI
# ============================================================

async def main():
    """CLI 진입점"""
    import argparse

    parser = argparse.ArgumentParser(description="자동 콘텐츠 제작 (규칙 강제)")
    parser.add_argument("topic_en", help="영문 토픽명 (예: spinach)")
    parser.add_argument("topic_kr", help="한글 토픽명 (예: 시금치)")
    parser.add_argument("--folder-num", type=int, default=26, help="폴더 번호")
    parser.add_argument("--safety", choices=["safe", "caution", "dangerous"], default="safe")
    parser.add_argument("--dry-run", action="store_true", help="테스트 모드")

    args = parser.parse_args()

    # 텍스트 설정 로드
    text_config_path = ROOT / f"config/settings/{args.topic_en}_text.json"

    if text_config_path.exists():
        with open(text_config_path, 'r', encoding='utf-8') as f:
            text_config = json.load(f)
    else:
        # 기본 설정 생성
        text_config = [
            {"slide": 0, "type": "cover", "title": args.topic_en.upper(), "subtitle": ""},
            {"slide": 1, "type": "content_bottom", "title": "먹어도 돼요!", "subtitle": "영양가 풍부한 음식이에요 ✅"},
            {"slide": 2, "type": "content_bottom", "title": "주의사항", "subtitle": "적정량만 급여하세요 ⚠️"},
            {"slide": 3, "type": "cta", "title": "저장 & 공유", "subtitle": "주변 견주에게 알려주세요! 🐶"},
        ]

    producer = ContentProducer()
    result = await producer.produce_content(
        topic_en=args.topic_en,
        topic_kr=args.topic_kr,
        folder_number=args.folder_num,
        text_config=text_config,
        safety=args.safety
    )

    print(json.dumps(result, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    asyncio.run(main())
