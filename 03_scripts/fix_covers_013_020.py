#!/usr/bin/env python3
"""
Cover Image Fixer for 013-020
Based on COVER_RULE.md v2.0

규칙:
- 1080x1080px
- 한글 Y=80px, 영어 Y=210px
- 폰트: BlackHanSans-Regular (한글 120px, 영어 72px)
- 드롭쉐도우: offset=2, alpha=100, blur=3 (레이어 방식)
- stroke 사용 금지
"""

from PIL import Image, ImageDraw, ImageFont, ImageFilter
import os

# Base paths
BASE_DIR = "/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine"
CONTENTS_DIR = os.path.join(BASE_DIR, "contents")

# Font paths
FONT_PATHS = [
    "/System/Library/Fonts/Supplemental/Arial Unicode.ttf",
    "/Library/Fonts/NanumGothicExtraBold.otf",
    "/Library/Fonts/NanumGothicBold.otf",
    "/Library/Fonts/NanumGothic.otf",
    "/System/Library/Fonts/AppleSDGothicNeo.ttc",
]

def get_font(size):
    """Get available Korean font"""
    for path in FONT_PATHS:
        if os.path.exists(path):
            try:
                return ImageFont.truetype(path, size)
            except:
                continue
    return ImageFont.load_default()

# Cover data: (folder_name, korean_name, english_name)
COVERS = [
    ("013_Orange", "오렌지", "ORANGE"),
    ("014_Pear", "배", "PEAR"),
    # 015_Kiwi is already correct - skip
    ("016_Papaya", "파파야", "PAPAYA"),
    ("017_Peach", "복숭아", "PEACH"),
    ("018_Rice", "흰쌀밥", "RICE"),
    ("019_Cucumber", "오이", "CUCUMBER"),
    ("020_Pringles", "프링글스", "PRINGLES"),
]

def draw_text_with_shadow(img, text, position, font, text_color="#FFFFFF",
                          shadow_color=(0, 0, 0, 100), offset=2, blur_radius=3):
    """Draw text with drop shadow using layer method (no stroke!)"""
    x, y = position

    # Create shadow layer
    shadow_layer = Image.new('RGBA', img.size, (0, 0, 0, 0))
    shadow_draw = ImageDraw.Draw(shadow_layer)

    # Draw shadow text
    shadow_draw.text((x + offset, y + offset), text, font=font, fill=shadow_color)

    # Apply gaussian blur to shadow
    shadow_layer = shadow_layer.filter(ImageFilter.GaussianBlur(radius=blur_radius))

    # Composite shadow onto image
    img = Image.alpha_composite(img.convert('RGBA'), shadow_layer)

    # Draw main text
    draw = ImageDraw.Draw(img)
    draw.text((x, y), text, font=font, fill=text_color)

    return img

def get_text_center_x(img_width, text, font):
    """Calculate X position for centered text"""
    # Create temp image to measure text
    temp_img = Image.new('RGBA', (1, 1))
    temp_draw = ImageDraw.Draw(temp_img)
    bbox = temp_draw.textbbox((0, 0), text, font=font)
    text_width = bbox[2] - bbox[0]
    return (img_width - text_width) // 2

def generate_cover(folder_name, korean_name, english_name):
    """Generate cover with correct text overlay"""
    folder_path = os.path.join(CONTENTS_DIR, folder_name)

    # Find clean image
    clean_path = os.path.join(folder_path, "00_Clean", f"{folder_name.split('_')[1]}_Cover_Clean.png")

    # Special case for Pear (no cover clean)
    if not os.path.exists(clean_path):
        # Use current cover as background
        current_cover = os.path.join(folder_path, f"{folder_name.split('_')[1]}_Common_01_Cover.png")
        if os.path.exists(current_cover):
            clean_path = current_cover
            print(f"  [!] No clean image, using current cover: {clean_path}")
        else:
            print(f"  [ERROR] No background image found for {folder_name}")
            return False

    print(f"  Loading: {clean_path}")

    # Load background
    try:
        img = Image.open(clean_path).convert('RGBA')
    except Exception as e:
        print(f"  [ERROR] Failed to load image: {e}")
        return False

    # Resize to 1080x1080 if needed
    if img.size != (1080, 1080):
        img = img.resize((1080, 1080), Image.LANCZOS)

    # Get fonts
    font_korean = get_font(120)
    font_english = get_font(72)

    # Calculate center positions
    korean_x = get_text_center_x(1080, korean_name, font_korean)
    english_x = get_text_center_x(1080, english_name, font_english)

    # Draw Korean text (Y=80)
    img = draw_text_with_shadow(img, korean_name, (korean_x, 80), font_korean)

    # Draw English text (Y=210)
    img = draw_text_with_shadow(img, english_name, (english_x, 210), font_english)

    # Save
    output_path = os.path.join(folder_path, f"{folder_name.split('_')[1]}_Common_01_Cover.png")
    img.save(output_path, "PNG")
    print(f"  Saved: {output_path}")

    return True

def main():
    print("=" * 60)
    print("Cover Image Fixer (013-020)")
    print("Based on COVER_RULE.md v2.0")
    print("=" * 60)

    success_count = 0
    fail_count = 0

    for folder_name, korean_name, english_name in COVERS:
        print(f"\n[{folder_name}] {korean_name} / {english_name}")

        if generate_cover(folder_name, korean_name, english_name):
            success_count += 1
            print(f"  [OK] Generated successfully")
        else:
            fail_count += 1
            print(f"  [FAIL] Generation failed")

    print("\n" + "=" * 60)
    print(f"Results: {success_count} success, {fail_count} failed")
    print("=" * 60)

if __name__ == "__main__":
    main()
