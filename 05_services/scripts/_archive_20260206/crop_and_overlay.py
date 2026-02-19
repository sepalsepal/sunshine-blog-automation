#!/usr/bin/env python3
"""
세로 이미지를 1:1로 크롭하고 텍스트 오버레이 적용
"""
import os
import sys
import subprocess
from pathlib import Path
from PIL import Image

ROOT = Path(__file__).parent.parent.parent

def crop_vertical_to_square(input_path: str, output_path: str, y_offset: int = 0):
    """3:4 세로 이미지를 1:1로 크롭

    y_offset: 양수면 아래로 이동 (위쪽 더 잘림), 음수면 위로 이동
    """
    img = Image.open(input_path)
    width, height = img.size

    # 1080x1080 크롭
    target_size = 1080

    # 크롭 영역 계산
    left = 0
    top = max(0, y_offset)
    right = target_size
    bottom = top + target_size

    # 범위 체크
    if bottom > height:
        bottom = height
        top = height - target_size

    cropped = img.crop((left, top, right, bottom))
    cropped.save(output_path, "PNG")
    print(f"  ✅ 크롭 완료: {Path(output_path).name} (offset={y_offset})")
    return output_path


def apply_text_overlay(input_path: str, title: str, output_path: str):
    """Puppeteer로 텍스트 오버레이"""
    script_path = ROOT / "services" / "scripts" / "apply_single_cover_overlay.js"

    result = subprocess.run(
        ["node", str(script_path), input_path, title, output_path],
        capture_output=True,
        text=True,
        cwd=str(ROOT / "services" / "scripts")
    )

    if result.returncode == 0:
        print(f"  ✅ 텍스트 오버레이 완료: {Path(output_path).name}")
        return True
    else:
        print(f"  ❌ 오버레이 실패: {result.stderr}")
        return False


def process_cover(topic: str, title: str, y_offset: int = 0):
    """표지 처리: 크롭 → 텍스트 오버레이"""

    # 폴더 매핑
    folder_map = {
        "strawberry": "011_strawberry",
        "mango": "012_mango",
        "pear": "014_pear",
        "kiwi": "015_kiwi",
        "papaya": "016_papaya",
        "peach": "017_peach",
    }

    folder = folder_map.get(topic)
    if not folder:
        print(f"❌ 알 수 없는 토픽: {topic}")
        return None

    images_dir = ROOT / "content" / "images" / folder
    vertical_path = images_dir / f"{topic}_00_vertical.png"
    cropped_path = images_dir / f"{topic}_00_cropped.png"
    final_path = images_dir / f"{topic}_00.png"

    if not vertical_path.exists():
        print(f"❌ 세로 이미지 없음: {vertical_path}")
        return None

    print(f"\n📁 {title} 표지 처리")
    print("-" * 40)

    # 1. 크롭
    crop_vertical_to_square(str(vertical_path), str(cropped_path), y_offset)

    # 2. 텍스트 오버레이
    success = apply_text_overlay(str(cropped_path), title, str(final_path))

    if success:
        return str(final_path)
    return None


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python crop_and_overlay.py <topic> <TITLE> [y_offset]")
        print("Example: python crop_and_overlay.py peach PEACH 0")
        sys.exit(1)

    topic = sys.argv[1]
    title = sys.argv[2]
    y_offset = int(sys.argv[3]) if len(sys.argv) > 3 else 0

    result = process_cover(topic, title, y_offset)
    if result:
        print(f"\n✅ 완료: {result}")
    else:
        print("\n❌ 처리 실패")
