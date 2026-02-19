#!/usr/bin/env python3
"""
Cover Generator - COVER_RULE.md v2.0 준수
커버 이미지 생성 스크립트

규칙:
- 해상도: 1080x1080px
- 텍스트: 한글(Y=80px, 120px) + 영어(Y=210px, 72px, 대문자)
- 폰트: BlackHanSans-Regular
- 드롭쉐도우: GaussianBlur (stroke 금지)
- 그라데이션: 없음 (금지)
- 안전도 배지: 없음 (금지)
"""

import os
import sys
import json
from PIL import Image, ImageDraw, ImageFont, ImageFilter

# 경로 설정
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
FONT_PATH = os.path.expanduser("~/Library/Fonts/BlackHanSans-Regular.ttf")
CONTENTS_PATH = os.path.join(PROJECT_ROOT, "contents")


def draw_text_with_shadow(img, text, font, y_position, shadow_offset=2, shadow_alpha=100, blur_radius=3):
    """드롭쉐도우가 있는 텍스트 그리기 (stroke 사용 금지, GaussianBlur 사용)"""
    width, height = img.size

    # 텍스트 바운딩 박스 계산
    temp_draw = ImageDraw.Draw(img)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]

    # 중앙 X 좌표
    x_position = (width - text_width) // 2

    # 그림자 레이어 생성
    shadow_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    # 그림자 텍스트
    shadow_draw.text(
        (x_position + shadow_offset, y_position + shadow_offset),
        text,
        font=font,
        fill=(0, 0, 0, shadow_alpha)
    )

    # 블러 적용
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # 그림자 합성
    img = Image.alpha_composite(img, shadow_layer)

    # 메인 텍스트 레이어
    text_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    text_draw = ImageDraw.Draw(text_layer)
    text_draw.text(
        (x_position, y_position),
        text,
        font=font,
        fill=(255, 255, 255, 255)
    )

    # 텍스트 합성
    img = Image.alpha_composite(img, text_layer)

    return img


def generate_cover(clean_image_path, name_ko, name_en, output_path):
    """커버 이미지 생성 (v2.0 - 그라데이션/배지 없음)"""

    # 폰트 로드
    try:
        font_ko = ImageFont.truetype(FONT_PATH, 120)
        font_en = ImageFont.truetype(FONT_PATH, 72)
    except Exception as e:
        print(f"[ERROR] 폰트 로드 실패: {e}")
        return False

    # 클린 이미지 로드
    try:
        img = Image.open(clean_image_path).convert('RGBA')
    except Exception as e:
        print(f"[ERROR] 이미지 로드 실패: {e}")
        return False

    # 1080x1080 리사이즈 (필요 시)
    if img.size != (1080, 1080):
        img = img.resize((1080, 1080), Image.LANCZOS)

    # v2.0: 그라데이션 없음

    # 한글 텍스트 (Y=80px)
    img = draw_text_with_shadow(img, name_ko, font_ko, 80)

    # 영어 텍스트 (Y=210px, 대문자, 언더스코어 제거)
    name_en_upper = name_en.upper().replace("_", " ")
    img = draw_text_with_shadow(img, name_en_upper, font_en, 210)

    # v2.0: 안전도 배지 없음

    # RGB로 변환하여 저장
    img_rgb = img.convert('RGB')
    img_rgb.save(output_path, 'PNG', quality=95)

    print(f"[OK] 생성 완료: {output_path}")
    return True


def get_food_data(food_number):
    """food_data.json에서 음식 정보 조회"""
    food_data_path = os.path.join(PROJECT_ROOT, "config", "food_data.json")

    try:
        with open(food_data_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except Exception as e:
        print(f"[ERROR] food_data.json 로드 실패: {e}")
        return None

    # 번호로 검색 (키가 "1", "2", ... 형태)
    food_number_int = str(int(food_number))  # "001" -> "1"

    if food_number_int in data:
        food = data[food_number_int]
        # 필드명 통일
        return {
            "name_ko": food.get("name", ""),
            "name_en": food.get("english_name", ""),
            "safety": food.get("safety", "SAFE")
        }

    return None


def find_clean_image(folder_path):
    """00_Clean 폴더에서 Cover Clean 이미지 찾기"""
    clean_folder = os.path.join(folder_path, "00_Clean")

    if not os.path.exists(clean_folder):
        return None

    for file in os.listdir(clean_folder):
        if "Cover" in file and "Clean" in file and file.endswith(".png"):
            return os.path.join(clean_folder, file)

    return None


def main():
    if len(sys.argv) < 2:
        print("사용법: python cover_generator.py <폴더번호>")
        print("예시: python cover_generator.py 001")
        sys.exit(1)

    folder_number = sys.argv[1].zfill(3)

    # 콘텐츠 폴더 찾기
    content_folder = None

    # 먼저 contents 루트 검색
    for folder in os.listdir(CONTENTS_PATH):
        folder_path = os.path.join(CONTENTS_PATH, folder)
        if os.path.isdir(folder_path) and folder.startswith(folder_number + "_"):
            content_folder = folder_path
            break

    # 없으면 stage 폴더 검색
    if not content_folder:
        for stage in ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]:
            stage_path = os.path.join(CONTENTS_PATH, stage)
            if os.path.exists(stage_path):
                for folder in os.listdir(stage_path):
                    if folder.startswith(folder_number + "_"):
                        content_folder = os.path.join(stage_path, folder)
                        break
            if content_folder:
                break

    if not content_folder:
        print(f"[ERROR] 폴더 번호 {folder_number}에 해당하는 콘텐츠 없음")
        sys.exit(1)

    print(f"[INFO] 콘텐츠 폴더: {content_folder}")

    # 클린 이미지 찾기
    clean_image = find_clean_image(content_folder)
    if not clean_image:
        print(f"[ERROR] 클린 이미지 없음: {content_folder}/00_Clean/")
        sys.exit(1)

    print(f"[INFO] 클린 이미지: {clean_image}")

    # 음식 데이터 조회
    food_data = get_food_data(folder_number)
    if not food_data:
        print(f"[ERROR] food_data.json에서 번호 {folder_number} 찾기 실패")
        sys.exit(1)

    name_ko = food_data.get("name_ko", "")
    name_en = food_data.get("name_en", "")

    print(f"[INFO] 음식: {name_ko} / {name_en.upper()}")

    # 출력 경로
    folder_name = os.path.basename(content_folder)
    food_name = folder_name.split("_", 1)[1] if "_" in folder_name else folder_name
    output_filename = f"{food_name}_Common_01_Cover.png"
    output_path = os.path.join(content_folder, output_filename)

    # 커버 생성
    success = generate_cover(clean_image, name_ko, name_en, output_path)

    if success:
        print(f"\n[결과] COVER_RULE v2.0 기준")
        print(f"- 한글: {name_ko}")
        print(f"- 영어: {name_en.upper()} (대문자)")
        print(f"- 그라데이션: 없음")
        print(f"- 배지: 없음")
        print(f"- 출력: {output_path}")
    else:
        sys.exit(1)


if __name__ == "__main__":
    main()
