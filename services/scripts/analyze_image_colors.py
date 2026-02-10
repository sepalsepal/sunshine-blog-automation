"""
이미지 색상 분석 - 텍스트 영역의 실제 RGB 값 확인
"""

from PIL import Image
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).parent.parent.parent


def analyze_bottom_region(img_path: Path, region_percent: int = 25):
    """하단 영역의 색상 분석"""
    img = Image.open(img_path).convert("RGB")
    width, height = img.size

    # 하단 25% 영역
    y_start = int(height * (100 - region_percent) / 100)

    print(f"\n📊 {img_path.name} 분석")
    print(f"   이미지 크기: {width}x{height}")
    print(f"   분석 영역: Y {y_start}~{height} (하단 {region_percent}%)")

    # 색상 수집
    colors = []
    for y in range(y_start, height):
        for x in range(0, width, 3):  # 3픽셀 간격
            r, g, b = img.getpixel((x, y))
            brightness = (r + g + b) / 3
            if brightness > 150:  # 텍스트 영역 (밝은 픽셀)
                colors.append((r, g, b))

    if not colors:
        print("   ⚠️ 밝은 픽셀 없음")
        return

    # 색상 분류
    yellow_count = 0  # #FFD700 (R:245-255, G:205-225, B:0-10)
    white_count = 0   # 흰색 (R,G,B 모두 245-255)
    other_count = 0

    yellow_samples = []
    white_samples = []

    for r, g, b in colors:
        is_yellow = (245 <= r <= 255 and 205 <= g <= 225 and 0 <= b <= 10)
        is_white = (245 <= r <= 255 and 245 <= g <= 255 and 245 <= b <= 255)

        if is_yellow:
            yellow_count += 1
            if len(yellow_samples) < 5:
                yellow_samples.append((r, g, b))
        elif is_white:
            white_count += 1
            if len(white_samples) < 5:
                white_samples.append((r, g, b))
        else:
            other_count += 1

    total = len(colors)
    print(f"\n   총 밝은 픽셀: {total}")
    print(f"   노란색 (#FFD700): {yellow_count} ({yellow_count/total*100:.1f}%)")
    print(f"   흰색: {white_count} ({white_count/total*100:.1f}%)")
    print(f"   기타: {other_count} ({other_count/total*100:.1f}%)")

    if yellow_samples:
        print(f"   노란색 샘플: {yellow_samples}")
    if white_samples:
        print(f"   흰색 샘플: {white_samples}")

    # 가장 흔한 색상 (밝은 것만)
    color_counter = Counter(colors)
    top_colors = color_counter.most_common(10)
    print(f"\n   상위 10개 색상:")
    for color, count in top_colors:
        r, g, b = color
        # 색상 분류
        label = ""
        if 245 <= r <= 255 and 205 <= g <= 225 and 0 <= b <= 10:
            label = "[노란색]"
        elif 245 <= r <= 255 and 245 <= g <= 255 and 245 <= b <= 255:
            label = "[흰색]"
        elif r > 200 and g > 150 and b < 100:
            label = "[노란빛]"
        print(f"      RGB({r:3d}, {g:3d}, {b:3d}): {count}px {label}")

    return {
        "yellow": yellow_count,
        "white": white_count,
        "other": other_count,
        "dominant": "yellow" if yellow_count > white_count else "white" if white_count > 0 else "other"
    }


def analyze_top_region(img_path: Path, region_percent: int = 50):
    """상단 영역의 텍스트 위치 분석"""
    img = Image.open(img_path).convert("RGB")
    width, height = img.size

    # 상단 50% 영역
    y_end = int(height * region_percent / 100)

    print(f"\n📊 {img_path.name} 상단 분석")
    print(f"   이미지 크기: {width}x{height}")
    print(f"   분석 영역: Y 0~{y_end} (상단 {region_percent}%)")

    # 각 행의 흰색 픽셀 수 계산
    row_white_counts = []
    for y in range(0, y_end):
        white_count = 0
        for x in range(0, width, 5):
            r, g, b = img.getpixel((x, y))
            if r > 240 and g > 240 and b > 240:  # 흰색
                white_count += 1
        if white_count > 10:  # 텍스트가 있을 가능성
            row_white_counts.append((y, white_count))

    if row_white_counts:
        # 흰색 픽셀이 가장 많은 영역 찾기
        best_row = max(row_white_counts, key=lambda x: x[1])
        text_y = best_row[0]
        text_y_percent = (text_y / height) * 100
        print(f"\n   텍스트 추정 위치: Y={text_y}px ({text_y_percent:.1f}%)")
        print(f"   규칙 기준: 20~30% (216~324px)")

        if 20 <= text_y_percent <= 30:
            print(f"   ✅ PASS: 텍스트 위치 규칙 준수")
        else:
            print(f"   ❌ BLOCK: 텍스트 위치 규칙 위반 ({text_y_percent:.1f}% ≠ 20~30%)")
    else:
        print("   ⚠️ 상단에서 흰색 텍스트 감지 실패")


def main():
    duck_folder = ROOT / "content/images/169_duck_오리고기"

    print("=" * 60)
    print("🔍 Duck 콘텐츠 색상 분석")
    print("=" * 60)

    # 표지 분석
    analyze_top_region(duck_folder / "duck_00.png")

    # 본문 분석
    for i in [1, 2, 3]:
        analyze_bottom_region(duck_folder / f"duck_{i:02d}.png")


if __name__ == "__main__":
    main()
