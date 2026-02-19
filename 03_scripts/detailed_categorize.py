#!/usr/bin/env python3
"""
A등급 이미지 세부 카테고리 분류 (김감독 책임, 김작가 실행)

네이밍 규칙: haetsali_{표정}_{포즈}_{배경}_{번호}.jpg

표정 코드:
- happy: 밝은 표정, 미소, 혀 내밈
- curious: 호기심, 뭔가 응시
- calm: 차분, 평온
- sleepy: 졸린, 눈 감음

포즈 코드:
- sit: 앉아있음
- stand: 서있음
- lay: 누워있음
- walk: 걷기/뛰기

배경 코드:
- indoor: 실내 (거실, 방)
- kitchen: 주방
- outdoor: 야외 (공원, 잔디)
- bed: 침대/소파
"""

import json
from pathlib import Path
from PIL import Image
from collections import defaultdict

# 경로 설정
BASE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/content/images/sunshine/01_usable")
EXPRESSION_DIR = BASE_DIR / "expression"
LOCATION_DIR = BASE_DIR / "location"

# 분류 결과
categories = {
    "by_expression": defaultdict(list),
    "by_pose": defaultdict(list),
    "by_background": defaultdict(list),
    "summary": {}
}

def infer_expression(filename: str) -> str:
    """파일명에서 표정 추론"""
    lower = filename.lower()
    if "happy" in lower:
        return "happy"
    elif "curious" in lower:
        return "curious"
    elif "profile" in lower:
        return "calm"  # profile은 주로 차분한 포즈
    elif "outdoor" in lower:
        return "happy"  # 야외는 주로 활발
    return "calm"

def infer_pose(filename: str, width: int, height: int) -> str:
    """포즈 추론 (파일명 + 이미지 비율)"""
    lower = filename.lower()

    # outdoor는 주로 걷기/서기
    if "outdoor" in lower:
        return "walk"

    # profile은 주로 누워있음
    if "profile" in lower:
        return "lay"

    # happy/curious - 비율로 추정 (세로가 길면 앉아있을 확률)
    if height > width * 0.9:
        return "sit"
    else:
        return "lay"

def infer_background(filename: str) -> str:
    """배경 추론"""
    lower = filename.lower()
    if "outdoor" in lower:
        return "outdoor"
    elif "profile" in lower:
        return "bed"
    else:
        return "indoor"

def categorize_image(img_path: Path) -> dict:
    """이미지 분류"""
    try:
        img = Image.open(img_path)
        width, height = img.size
    except:
        width, height = 1000, 1000

    filename = img_path.name

    expression = infer_expression(filename)
    pose = infer_pose(filename, width, height)
    background = infer_background(filename)

    return {
        "filename": filename,
        "path": str(img_path),
        "expression": expression,
        "pose": pose,
        "background": background,
        "width": width,
        "height": height
    }

def generate_new_filename(info: dict, idx: int) -> str:
    """새 파일명 생성"""
    return f"haetsali_{info['expression']}_{info['pose']}_{info['background']}_{idx:04d}.jpg"

def categorize_all():
    """전체 이미지 분류"""
    print("=" * 60)
    print("🎬 A등급 이미지 세부 카테고리 분류")
    print("=" * 60)

    all_images = []

    # expression 폴더
    if EXPRESSION_DIR.exists():
        for img in sorted(EXPRESSION_DIR.glob("*.jpg")):
            all_images.append(img)

    # location 폴더
    if LOCATION_DIR.exists():
        for img in sorted(LOCATION_DIR.glob("*.jpg")):
            all_images.append(img)

    print(f"\n분류 대상: {len(all_images)}개 이미지")

    results = []
    for img_path in all_images:
        info = categorize_image(img_path)
        results.append(info)

        categories["by_expression"][info["expression"]].append(info)
        categories["by_pose"][info["pose"]].append(info)
        categories["by_background"][info["background"]].append(info)

    # 통계
    categories["summary"] = {
        "total": len(results),
        "by_expression": {k: len(v) for k, v in categories["by_expression"].items()},
        "by_pose": {k: len(v) for k, v in categories["by_pose"].items()},
        "by_background": {k: len(v) for k, v in categories["by_background"].items()}
    }

    return results

def print_report():
    """분류 결과 리포트"""
    summary = categories["summary"]

    print("\n" + "=" * 60)
    print("📊 세부 카테고리 분류 결과")
    print("=" * 60)

    print(f"\n총 이미지: {summary['total']}개")

    print("\n📌 표정별 분포:")
    for exp, count in sorted(summary["by_expression"].items(), key=lambda x: -x[1]):
        pct = count * 100 / summary["total"]
        bar = "█" * int(pct / 5)
        print(f"   {exp:10s} {count:4d}개 ({pct:5.1f}%) {bar}")

    print("\n📌 포즈별 분포:")
    for pose, count in sorted(summary["by_pose"].items(), key=lambda x: -x[1]):
        pct = count * 100 / summary["total"]
        bar = "█" * int(pct / 5)
        print(f"   {pose:10s} {count:4d}개 ({pct:5.1f}%) {bar}")

    print("\n📌 배경별 분포:")
    for bg, count in sorted(summary["by_background"].items(), key=lambda x: -x[1]):
        pct = count * 100 / summary["total"]
        bar = "█" * int(pct / 5)
        print(f"   {bg:10s} {count:4d}개 ({pct:5.1f}%) {bar}")

def save_results(results: list):
    """결과 저장"""
    output = {
        "images": results,
        "categories": {
            "by_expression": {k: [i["filename"] for i in v] for k, v in categories["by_expression"].items()},
            "by_pose": {k: [i["filename"] for i in v] for k, v in categories["by_pose"].items()},
            "by_background": {k: [i["filename"] for i in v] for k, v in categories["by_background"].items()},
        },
        "summary": categories["summary"]
    }

    output_path = BASE_DIR / "a_grade_categories.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)
    print(f"\n📄 분류 결과 저장: {output_path}")

    # 네이밍 맵 생성 (기존 → 새이름)
    naming_map = {}
    counters = defaultdict(int)

    for info in results:
        key = f"{info['expression']}_{info['pose']}_{info['background']}"
        counters[key] += 1
        new_name = generate_new_filename(info, counters[key])
        naming_map[info["filename"]] = new_name

    naming_path = BASE_DIR / "naming_map.json"
    with open(naming_path, "w", encoding="utf-8") as f:
        json.dump(naming_map, f, ensure_ascii=False, indent=2)
    print(f"📄 네이밍 맵 저장: {naming_path}")


if __name__ == "__main__":
    results = categorize_all()
    print_report()
    save_results(results)

    print("\n" + "=" * 60)
    print("✅ 세부 분류 완료")
    print("=" * 60)
    print("\n💡 다음 단계: 네이밍 맵 검토 후 실제 파일명 변경")
