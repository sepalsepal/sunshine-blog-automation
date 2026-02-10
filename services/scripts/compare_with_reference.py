"""
기존 콘텐츠 대비 신규 콘텐츠 비교 분석
visual_guard 검수 규칙 추가용
"""

from PIL import Image
from pathlib import Path
from typing import Dict, List, Tuple
import json

ROOT = Path(__file__).parent.parent.parent

# 기준 콘텐츠 (최근 게시 3종)
REFERENCE_CONTENT = [
    ("032_boiled_egg_삶은달걀", "boiled_egg"),
    ("074_yangnyeom_chicken_양념치킨", "yangnyeom_chicken"),
    ("010_watermelon", "watermelon"),
]


def analyze_content_style(folder_path: Path, prefix: str) -> Dict:
    """콘텐츠 스타일 분석"""
    result = {
        "folder": folder_path.name,
        "images": [],
        "text_colors": {"yellow": 0, "white": 0, "other": 0},
        "avg_yellow_ratio": 0,
        "avg_white_ratio": 0,
        "image_sizes": [],
    }

    # 본문 이미지 분석 (01, 02, 03)
    for i in range(1, 4):
        img_path = folder_path / f"{prefix}_{i:02d}.png"
        if not img_path.exists():
            img_path = folder_path / f"{prefix}_0{i}.png"
        if not img_path.exists():
            continue

        img = Image.open(img_path).convert("RGB")
        width, height = img.size
        result["image_sizes"].append((width, height))

        # 하단 25% 색상 분석
        y_start = int(height * 0.75)
        yellow_count = 0
        white_count = 0
        total_bright = 0

        for y in range(y_start, height):
            for x in range(0, width, 5):
                r, g, b = img.getpixel((x, y))
                brightness = (r + g + b) / 3

                if brightness > 150:
                    total_bright += 1
                    # 노란색 (#FFD700)
                    if 245 <= r <= 255 and 205 <= g <= 225 and 0 <= b <= 10:
                        yellow_count += 1
                    # 흰색
                    elif 245 <= r <= 255 and 245 <= g <= 255 and 245 <= b <= 255:
                        white_count += 1

        if total_bright > 0:
            yellow_ratio = yellow_count / total_bright
            white_ratio = white_count / total_bright
        else:
            yellow_ratio = 0
            white_ratio = 0

        result["images"].append({
            "file": img_path.name,
            "size": (width, height),
            "yellow_pixels": yellow_count,
            "white_pixels": white_count,
            "yellow_ratio": yellow_ratio,
            "white_ratio": white_ratio,
            "dominant": "yellow" if yellow_ratio > 0.03 else "white" if white_ratio > 0.01 else "other"
        })

        result["text_colors"][result["images"][-1]["dominant"]] += 1

    # 평균 계산
    if result["images"]:
        result["avg_yellow_ratio"] = sum(img["yellow_ratio"] for img in result["images"]) / len(result["images"])
        result["avg_white_ratio"] = sum(img["white_ratio"] for img in result["images"]) / len(result["images"])

    return result


def print_analysis(analysis: Dict, label: str):
    """분석 결과 출력"""
    print(f"\n{'='*60}")
    print(f"📊 {label}: {analysis['folder']}")
    print(f"{'='*60}")

    print(f"\n이미지 분석:")
    for img in analysis["images"]:
        dominant_icon = "🟡" if img["dominant"] == "yellow" else "⚪" if img["dominant"] == "white" else "⚫"
        print(f"  {dominant_icon} {img['file']}: 노란색 {img['yellow_pixels']}px ({img['yellow_ratio']*100:.1f}%), 흰색 {img['white_pixels']}px ({img['white_ratio']*100:.1f}%)")

    print(f"\n요약:")
    print(f"  텍스트 색상 분포: 노란색 {analysis['text_colors']['yellow']}개, 흰색 {analysis['text_colors']['white']}개, 기타 {analysis['text_colors']['other']}개")
    print(f"  평균 노란색 비율: {analysis['avg_yellow_ratio']*100:.2f}%")
    print(f"  평균 흰색 비율: {analysis['avg_white_ratio']*100:.2f}%")


def compare_with_references(target_folder: Path, target_prefix: str) -> Dict:
    """기준 콘텐츠와 비교"""
    print("\n" + "="*70)
    print("🔍 기존 콘텐츠 vs 신규 콘텐츠 비교 분석")
    print("="*70)

    # 기준 콘텐츠 분석
    references = []
    print("\n📋 기준 콘텐츠 분석 (최근 게시 3종)")
    for folder_name, prefix in REFERENCE_CONTENT:
        folder_path = ROOT / "content/images" / folder_name
        if folder_path.exists():
            analysis = analyze_content_style(folder_path, prefix)
            references.append(analysis)
            print_analysis(analysis, "기준")

    # 타겟 콘텐츠 분석
    print("\n📋 신규 콘텐츠 분석")
    target_analysis = analyze_content_style(target_folder, target_prefix)
    print_analysis(target_analysis, "신규")

    # 비교 결과
    print("\n" + "="*70)
    print("📊 비교 결과")
    print("="*70)

    if references:
        # 기준 평균 계산
        ref_avg_yellow = sum(r["avg_yellow_ratio"] for r in references) / len(references)
        ref_avg_white = sum(r["avg_white_ratio"] for r in references) / len(references)

        print(f"\n기준 콘텐츠 평균:")
        print(f"  노란색 비율: {ref_avg_yellow*100:.2f}%")
        print(f"  흰색 비율: {ref_avg_white*100:.2f}%")

        print(f"\n신규 콘텐츠:")
        print(f"  노란색 비율: {target_analysis['avg_yellow_ratio']*100:.2f}%")
        print(f"  흰색 비율: {target_analysis['avg_white_ratio']*100:.2f}%")

        # 판정
        print("\n" + "-"*60)

        # 기준: 노란색 텍스트가 있어야 함 (최소 1%)
        if target_analysis["avg_yellow_ratio"] < 0.01:
            print("❌ BLOCK: 노란색 텍스트 비율이 기준(1%) 미달")
            print(f"   기준 평균: {ref_avg_yellow*100:.2f}%, 신규: {target_analysis['avg_yellow_ratio']*100:.2f}%")
            return {"result": "BLOCK", "reason": "노란색 텍스트 부족"}

        # 기준과 비교하여 큰 차이 없는지 확인
        yellow_diff = abs(target_analysis["avg_yellow_ratio"] - ref_avg_yellow)
        if yellow_diff > 0.1:  # 10% 이상 차이
            print(f"⚠️ CAUTION: 기준 대비 노란색 비율 차이가 큼 ({yellow_diff*100:.1f}%)")
        else:
            print("✅ PASS: 기준 콘텐츠와 유사한 텍스트 스타일")

        return {"result": "PASS", "reason": "기준 콘텐츠와 유사"}

    return {"result": "CAUTION", "reason": "기준 콘텐츠 없음"}


def main():
    # Duck 콘텐츠 비교
    duck_folder = ROOT / "content/images/169_duck_오리고기"
    compare_with_references(duck_folder, "duck")


if __name__ == "__main__":
    main()
