"""
CTA 이미지 생성 스크립트 (규칙 v2)

규칙:
- 이미지: best_cta 폴더에서 실사 선택 (AI 생성 금지!)
- 텍스트: Noto Sans KR Bold
- 제목 색상: #FFD93D (노란색)
"""

import os
import random
import shutil
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from pathlib import Path
import sys

# 프로젝트 루트
ROOT = Path(__file__).parent.parent.parent

# CTA 소스 폴더
CTA_SOURCE_DIR = ROOT / "content/images/sunshine/cta_source/best_cta"


class CTAImageCreator:
    """CTA 이미지 생성기"""

    # 스펙
    TITLE_COLOR = (255, 217, 61)  # #FFD93D 노란색
    SUBTITLE_COLOR = (255, 255, 255)  # 흰색
    SHADOW_COLOR = (0, 0, 0, 200)
    FONT_SIZE_TITLE = 52
    FONT_SIZE_SUBTITLE = 26
    GRADIENT_HEIGHT_PERCENT = 50  # 하단 50% 그라데이션

    def __init__(self):
        self.title_font = self._load_font(self.FONT_SIZE_TITLE, bold=True)
        self.subtitle_font = self._load_font(self.FONT_SIZE_SUBTITLE)

    def _load_font(self, size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
        """폰트 로드"""
        # Noto Sans KR 또는 대체 폰트
        font_paths = [
            "/System/Library/Fonts/Supplemental/NotoSansKR-Bold.otf",
            "/Library/Fonts/NotoSansKR-Bold.otf",
            "/System/Library/Fonts/AppleSDGothicNeo.ttc",
            "/System/Library/Fonts/Supplemental/AppleGothic.ttf",
        ]

        for font_path in font_paths:
            try:
                return ImageFont.truetype(font_path, size)
            except (IOError, OSError):
                continue

        print("Warning: Korean font not found, using default")
        return ImageFont.load_default()

    def select_random_cta_source(self) -> Path:
        """best_cta에서 랜덤 이미지 선택"""
        if not CTA_SOURCE_DIR.exists():
            raise FileNotFoundError(f"CTA 소스 폴더 없음: {CTA_SOURCE_DIR}")

        jpg_files = list(CTA_SOURCE_DIR.glob("*.jpg"))
        if not jpg_files:
            raise FileNotFoundError("CTA 이미지 없음")

        selected = random.choice(jpg_files)
        print(f"📸 CTA 원본 선택: {selected.name}")
        return selected

    def add_gradient_overlay(self, img: Image.Image) -> Image.Image:
        """하단 그라데이션 오버레이 추가"""
        width, height = img.size
        gradient_height = int(height * self.GRADIENT_HEIGHT_PERCENT / 100)

        # RGBA로 변환
        if img.mode != "RGBA":
            img = img.convert("RGBA")

        # 그라데이션 레이어 생성
        gradient = Image.new("RGBA", (width, height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(gradient)

        # 하단부터 위로 그라데이션
        for y in range(height - gradient_height, height):
            alpha = int(180 * (y - (height - gradient_height)) / gradient_height)
            draw.rectangle([(0, y), (width, y + 1)], fill=(0, 0, 0, alpha))

        # 합성
        return Image.alpha_composite(img, gradient)

    def add_text_overlay(self, img: Image.Image, title: str, subtitle: str) -> Image.Image:
        """텍스트 오버레이 추가"""
        width, height = img.size
        draw = ImageDraw.Draw(img)

        # 텍스트 위치 계산 (하단 25%)
        title_y = int(height * 0.78)
        subtitle_y = int(height * 0.88)

        # 제목 (노란색)
        title_bbox = draw.textbbox((0, 0), title, font=self.title_font)
        title_width = title_bbox[2] - title_bbox[0]
        title_x = (width - title_width) // 2

        # 그림자
        draw.text((title_x + 2, title_y + 2), title, font=self.title_font, fill=self.SHADOW_COLOR)
        # 메인 텍스트
        draw.text((title_x, title_y), title, font=self.title_font, fill=self.TITLE_COLOR)

        # 부제목 (흰색)
        subtitle_bbox = draw.textbbox((0, 0), subtitle, font=self.subtitle_font)
        subtitle_width = subtitle_bbox[2] - subtitle_bbox[0]
        subtitle_x = (width - subtitle_width) // 2

        # 그림자
        draw.text((subtitle_x + 1, subtitle_y + 1), subtitle, font=self.subtitle_font, fill=self.SHADOW_COLOR)
        # 메인 텍스트
        draw.text((subtitle_x, subtitle_y), subtitle, font=self.subtitle_font, fill=self.SUBTITLE_COLOR)

        return img

    def create_cta(self, output_path: Path, title: str, subtitle: str) -> bool:
        """CTA 이미지 생성"""
        try:
            # 1. 랜덤 실사 선택
            source_path = self.select_random_cta_source()

            # 2. 이미지 로드 및 리사이즈
            img = Image.open(source_path)

            # 1080x1080 중앙 크롭
            img = self._center_crop_square(img, 1080)

            # 3. 그라데이션 추가
            img = self.add_gradient_overlay(img)

            # 4. 텍스트 추가
            img = self.add_text_overlay(img, title, subtitle)

            # 5. 저장
            img_rgb = img.convert("RGB")
            img_rgb.save(output_path, "PNG", quality=95)

            print(f"✅ CTA 생성 완료: {output_path}")
            return True

        except Exception as e:
            print(f"❌ CTA 생성 실패: {e}")
            return False

    def _center_crop_square(self, img: Image.Image, size: int) -> Image.Image:
        """중앙 정사각형 크롭"""
        width, height = img.size
        min_dim = min(width, height)

        left = (width - min_dim) // 2
        top = (height - min_dim) // 2
        right = left + min_dim
        bottom = top + min_dim

        img = img.crop((left, top, right, bottom))
        img = img.resize((size, size), Image.LANCZOS)
        return img


def create_cta_image(topic_en: str, topic_kr: str, folder_num: int, title: str, subtitle: str) -> bool:
    """CTA 이미지 생성"""
    content_dir = ROOT / f"content/images/{folder_num:03d}_{topic_en}_{topic_kr}"
    content_dir.mkdir(parents=True, exist_ok=True)

    output_path = content_dir / f"{topic_en}_03.png"

    creator = CTAImageCreator()
    return creator.create_cta(output_path, title, subtitle)


# CLI
if __name__ == "__main__":
    if len(sys.argv) < 6:
        print("Usage: python create_cta_image.py <topic_en> <topic_kr> <folder_num> <title> <subtitle>")
        print('Example: python create_cta_image.py duck 오리고기 169 "저장 필수! 📌" "우리 아이 최애 단백질은?"')
        sys.exit(1)

    topic_en = sys.argv[1]
    topic_kr = sys.argv[2]
    folder_num = int(sys.argv[3])
    title = sys.argv[4]
    subtitle = sys.argv[5]

    success = create_cta_image(topic_en, topic_kr, folder_num, title, subtitle)
    sys.exit(0 if success else 1)
