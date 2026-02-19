"""
현재 버전 vs wrong_v1 버전 비교
"""

from PIL import Image
from pathlib import Path

ROOT = Path(__file__).parent.parent.parent


def analyze_text_color(img_path: Path, label: str):
    """텍스트 색상 분석"""
    img = Image.open(img_path).convert("RGB")
    width, height = img.size

    # 하단 25% 영역
    y_start = int(height * 0.75)

    yellow_count = 0
    white_count = 0

    for y in range(y_start, height):
        for x in range(0, width, 3):
            r, g, b = img.getpixel((x, y))

            # 노란색 (#FFD700)
            if 245 <= r <= 255 and 205 <= g <= 225 and 0 <= b <= 10:
                yellow_count += 1
            # 흰색
            elif 245 <= r <= 255 and 245 <= g <= 255 and 245 <= b <= 255:
                white_count += 1

    dominant = "노란색" if yellow_count > white_count else "흰색" if white_count > yellow_count * 0.5 else "기타"

    print(f"  {label:15} | 노란색: {yellow_count:5} | 흰색: {white_count:5} | 주요: {dominant}")

    return {"yellow": yellow_count, "white": white_count, "dominant": dominant}


def main():
    duck_folder = ROOT / "content/images/169_duck_오리고기"
    wrong_folder = duck_folder / "archive/wrong_v1"

    print("=" * 70)
    print("🔍 현재 버전 vs 이전 버전 (wrong_v1) 비교")
    print("=" * 70)

    for i in [1, 2, 3]:
        current_path = duck_folder / f"duck_{i:02d}.png"
        wrong_path = wrong_folder / f"duck_{i:02d}.png"

        print(f"\n📊 duck_{i:02d}.png:")

        if current_path.exists():
            analyze_text_color(current_path, "현재 버전")
        else:
            print(f"  현재 버전: 파일 없음")

        if wrong_path.exists():
            analyze_text_color(wrong_path, "wrong_v1")
        else:
            print(f"  wrong_v1: 파일 없음")


if __name__ == "__main__":
    main()
