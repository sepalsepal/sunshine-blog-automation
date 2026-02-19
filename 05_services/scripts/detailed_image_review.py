#!/usr/bin/env python3
"""
A등급 이미지 상세 검토 스크립트 (김감독 책임, 김작가 실행)

목적: 831개 A등급 이미지를 개별 검토하여 세부 카테고리 분류
네이밍 규칙: haetsali_{표정}_{포즈}_{앵글}_{번호}.jpg

분류 기준:
- 표정: happy, curious, calm, sleepy
- 포즈: sit, stand, lay, walk, run
- 앵글: front, side45, side90, back, top
- 배경: indoor, outdoor, kitchen, park, bed
- 특수: with_human, with_clothes, with_toy
"""

import os
from pathlib import Path
from PIL import Image
from PIL.ExifTags import TAGS
import json
from datetime import datetime

# 경로 설정
BASE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/content/images/sunshine/01_usable")
EXPRESSION_DIR = BASE_DIR / "expression"
LOCATION_DIR = BASE_DIR / "location"

# 결과 저장
review_results = {
    "metadata": {
        "reviewer": "김감독",
        "executor": "김작가",
        "timestamp": datetime.now().isoformat(),
        "total_reviewed": 0
    },
    "categories": {
        "A_plus": [],      # 캐러셀 본문 최적합
        "A_standard": [],  # 캐러셀 본문 적합
        "A_special": [],   # 특수 용도 (잠자는 포즈, 뒷모습 등)
        "reclassify_B": [],  # B등급으로 재분류 (회전 필요)
        "reclassify_C": [],  # C등급으로 재분류 (품질 문제)
    },
    "statistics": {},
    "issues": []
}


def check_rotation_needed(img_path: Path) -> dict:
    """이미지 회전 필요 여부 확인"""
    try:
        img = Image.open(img_path)
        width, height = img.size

        # EXIF 회전 정보 확인
        exif_rotation = None
        try:
            exif = img._getexif()
            if exif:
                for tag_id, value in exif.items():
                    tag = TAGS.get(tag_id, tag_id)
                    if tag == 'Orientation':
                        exif_rotation = value
                        break
        except:
            pass

        # 세로 이미지 감지 (가로보다 세로가 1.3배 이상 길면)
        is_portrait = height > width * 1.2

        return {
            "width": width,
            "height": height,
            "is_portrait": is_portrait,
            "exif_rotation": exif_rotation,
            "needs_rotation": is_portrait or (exif_rotation and exif_rotation != 1)
        }
    except Exception as e:
        return {"error": str(e), "needs_rotation": False}


def analyze_image_quality(img_path: Path) -> dict:
    """이미지 품질 분석"""
    try:
        img = Image.open(img_path)
        width, height = img.size
        file_size = img_path.stat().st_size

        # 해상도 점수 (1080px 기준)
        min_dim = min(width, height)
        if min_dim >= 1080:
            resolution_score = 100
        elif min_dim >= 800:
            resolution_score = 85
        elif min_dim >= 600:
            resolution_score = 70
        else:
            resolution_score = 50

        # 파일 크기 점수 (500KB 기준)
        if file_size >= 1000000:  # 1MB+
            size_score = 100
        elif file_size >= 500000:  # 500KB+
            size_score = 90
        elif file_size >= 200000:  # 200KB+
            size_score = 75
        else:
            size_score = 60

        return {
            "width": width,
            "height": height,
            "file_size_kb": round(file_size / 1024, 1),
            "resolution_score": resolution_score,
            "size_score": size_score,
            "quality_score": (resolution_score + size_score) // 2
        }
    except Exception as e:
        return {"error": str(e), "quality_score": 0}


def categorize_by_filename(filename: str) -> dict:
    """파일명에서 카테고리 추출"""
    name_lower = filename.lower()

    # 기존 표정 카테고리
    if "curious" in name_lower:
        expression = "curious"
    elif "happy" in name_lower:
        expression = "happy"
    elif "profile" in name_lower:
        expression = "profile"
    elif "outdoor" in name_lower:
        expression = "outdoor"
    else:
        expression = "unknown"

    # 번호 추출
    import re
    num_match = re.search(r'(\d+)', filename)
    number = int(num_match.group(1)) if num_match else 0

    return {
        "original_category": expression,
        "number": number
    }


def detailed_review_image(img_path: Path) -> dict:
    """이미지 상세 검토"""
    filename = img_path.name

    # 기본 정보
    category_info = categorize_by_filename(filename)
    rotation_info = check_rotation_needed(img_path)
    quality_info = analyze_image_quality(img_path)

    # 종합 판정
    issues = []
    recommended_grade = "A_standard"

    # 회전 필요 시 B등급
    if rotation_info.get("needs_rotation"):
        issues.append("회전필요")
        recommended_grade = "reclassify_B"

    # 저품질 시 C등급
    if quality_info.get("quality_score", 100) < 70:
        issues.append("저품질")
        recommended_grade = "reclassify_C"

    # 파일 크기가 매우 작으면 (100KB 미만)
    if quality_info.get("file_size_kb", 1000) < 100:
        issues.append("저용량")
        if recommended_grade == "A_standard":
            recommended_grade = "reclassify_B"

    # 특수 카테고리 (profile은 잠자는 포즈가 많음)
    if category_info["original_category"] == "profile":
        if not issues:
            recommended_grade = "A_special"

    # 품질 우수 + 문제 없으면 A+
    if not issues and quality_info.get("quality_score", 0) >= 90:
        recommended_grade = "A_plus"

    return {
        "filename": filename,
        "path": str(img_path),
        "category": category_info,
        "rotation": rotation_info,
        "quality": quality_info,
        "issues": issues,
        "recommended_grade": recommended_grade
    }


def review_all_images():
    """전체 이미지 검토"""
    print("=" * 60)
    print("🎬 김감독 책임 / 김작가 실행 - A등급 이미지 상세 검토")
    print("=" * 60)

    all_images = []

    # expression 폴더
    if EXPRESSION_DIR.exists():
        for img in EXPRESSION_DIR.glob("*.jpg"):
            all_images.append(img)

    # location 폴더
    if LOCATION_DIR.exists():
        for img in LOCATION_DIR.glob("*.jpg"):
            all_images.append(img)

    print(f"\n📊 검토 대상: {len(all_images)}개 이미지")
    print("-" * 60)

    # 진행률 표시용
    total = len(all_images)

    for i, img_path in enumerate(all_images, 1):
        if i % 100 == 0:
            print(f"   검토 중... {i}/{total} ({i*100//total}%)")

        result = detailed_review_image(img_path)
        grade = result["recommended_grade"]

        review_results["categories"][grade].append(result)

    # 통계 계산
    review_results["metadata"]["total_reviewed"] = total
    review_results["statistics"] = {
        "A_plus": len(review_results["categories"]["A_plus"]),
        "A_standard": len(review_results["categories"]["A_standard"]),
        "A_special": len(review_results["categories"]["A_special"]),
        "reclassify_B": len(review_results["categories"]["reclassify_B"]),
        "reclassify_C": len(review_results["categories"]["reclassify_C"]),
    }

    return review_results


def print_report(results: dict):
    """결과 리포트 출력"""
    stats = results["statistics"]
    total = results["metadata"]["total_reviewed"]

    print("\n" + "=" * 60)
    print("📊 상세 검토 결과 리포트")
    print("=" * 60)

    print(f"\n총 검토: {total}개 이미지")
    print(f"\n등급 분포:")
    print(f"  ⭐ A+ (최적합):    {stats['A_plus']:4d}개 ({stats['A_plus']*100/total:.1f}%)")
    print(f"  ✅ A  (적합):      {stats['A_standard']:4d}개 ({stats['A_standard']*100/total:.1f}%)")
    print(f"  🌟 A특수 (용도별): {stats['A_special']:4d}개 ({stats['A_special']*100/total:.1f}%)")
    print(f"  ⚠️  B재분류 (회전): {stats['reclassify_B']:4d}개 ({stats['reclassify_B']*100/total:.1f}%)")
    print(f"  ❌ C재분류 (품질): {stats['reclassify_C']:4d}개 ({stats['reclassify_C']*100/total:.1f}%)")

    # A등급 유지 비율
    a_total = stats['A_plus'] + stats['A_standard'] + stats['A_special']
    print(f"\n📈 A등급 유지: {a_total}개 ({a_total*100/total:.1f}%)")

    # 주요 이슈
    all_issues = []
    for grade in ["reclassify_B", "reclassify_C"]:
        for item in results["categories"][grade]:
            all_issues.extend(item["issues"])

    if all_issues:
        print("\n📋 주요 이슈:")
        issue_counts = {}
        for issue in all_issues:
            issue_counts[issue] = issue_counts.get(issue, 0) + 1
        for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1]):
            print(f"   - {issue}: {count}건")


def save_results(results: dict):
    """결과 저장"""
    output_path = BASE_DIR / "detailed_review_results.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print(f"\n📄 상세 결과 저장: {output_path}")

    # A+ 목록 별도 저장
    a_plus_path = BASE_DIR / "a_plus_images.txt"
    with open(a_plus_path, "w") as f:
        for item in results["categories"]["A_plus"]:
            f.write(item["filename"] + "\n")
    print(f"📄 A+ 목록 저장: {a_plus_path}")


if __name__ == "__main__":
    results = review_all_images()
    print_report(results)
    save_results(results)

    print("\n" + "=" * 60)
    print("🎬 김감독 컨펌 대기 중...")
    print("=" * 60)
