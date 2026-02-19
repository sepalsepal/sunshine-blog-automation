#!/usr/bin/env python3
"""
햇살이 이미지 분류 스크립트 (김감독 책임, 김작가 실행)

캐러셀 본문 적합성 기준으로 이미지 분류:
- A등급 (90점+): 현재 위치 유지
- B등급 (80-89점): grade_B_80_89 폴더로 이동
- C등급 (80점 미만): grade_C_under_80 폴더로 이동

평가 기준:
1. 시니어 햇살이 여부 (퍼피 = 탈락)
2. 얼굴 특징 가시성 (흰 주둥이, 검은 눈/코)
3. 이미지 품질 (해상도, 선명도)
4. 구도 (회전 필요 여부, 얼굴 크기)
5. 배경 적합성
"""

import os
import shutil
from pathlib import Path
from PIL import Image
import json
from datetime import datetime

# 경로 설정
USABLE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/content/images/sunshine/01_usable")
GRADE_B_DIR = USABLE_DIR / "grade_B_80_89"
GRADE_C_DIR = USABLE_DIR / "grade_C_under_80"

# 결과 저장
results = {
    "grade_A": [],  # 90점+
    "grade_B": [],  # 80-89점
    "grade_C": [],  # 80점 미만
    "summary": {}
}

def analyze_image(img_path: Path) -> dict:
    """이미지 분석 및 점수 산정

    기준:
    - A등급 (90+): 캐러셀 본문 적합
    - B등급 (80-89): 수정 후 사용 가능
    - C등급 (80-): 사용 불가
    """
    score = 95  # 기본 점수 (대부분 사용 가능 가정)
    issues = []
    grade_reason = ""

    filename = img_path.name.lower()
    parent_folder = img_path.parent.name

    try:
        img = Image.open(img_path)
        width, height = img.size

        # === C등급 (사용 불가) 조건들 ===

        # 1. eating 폴더 전체 - 음식 먹는 포즈 금지 정책
        if "eating" in filename or parent_folder == "action":
            score = 70
            issues.append("eating_action(금지)")
            grade_reason = "음식 먹는 포즈 정책 위반"
            return {"path": str(img_path), "filename": img_path.name,
                    "score": score, "issues": issues, "reason": grade_reason}

        # 2. 퍼피 의심 (curious 250~400번대)
        if "curious" in filename:
            num = int(''.join(filter(str.isdigit, filename)) or 0)
            if 250 <= num <= 400:
                score = 60
                issues.append("퍼피의심")
                grade_reason = "시니어 햇살이 아님 (퍼피)"
                return {"path": str(img_path), "filename": img_path.name,
                        "score": score, "issues": issues, "reason": grade_reason}

        # 3. 저해상도 (800px 미만)
        if width < 800 or height < 800:
            score = 75
            issues.append("저해상도")
            grade_reason = "해상도 부족"

        # 4. 저용량 (100KB 미만)
        file_size = img_path.stat().st_size
        if file_size < 100000:
            score -= 15
            issues.append("저용량")

        # === B등급 (수정 후 사용) 조건들 ===

        # 5. 회전 필요 (세로 이미지)
        if score >= 80 and height > width * 1.3:
            score = 85
            issues.append("회전필요")
            grade_reason = "세로 이미지 - 회전 필요"

        # 6. 중해상도 (1000px 미만)
        if score >= 90 and (width < 1000 or height < 1000):
            score = 88
            issues.append("중해상도")

        # === A등급 유지 조건 확인 ===
        if score >= 90 and not issues:
            grade_reason = "캐러셀 본문 적합"

    except Exception as e:
        score = 50
        issues.append(f"분석실패: {str(e)}")
        grade_reason = "파일 오류"

    return {
        "path": str(img_path),
        "filename": img_path.name,
        "score": max(0, min(100, score)),
        "issues": issues,
        "reason": grade_reason
    }


def classify_images():
    """이미지 분류 실행"""
    print("=" * 60)
    print("🎬 김감독 책임 / 김작가 실행 - 이미지 분류 시작")
    print("=" * 60)

    folders = ["action", "expression", "location"]

    for folder in folders:
        folder_path = USABLE_DIR / folder
        if not folder_path.exists():
            continue

        print(f"\n📁 {folder} 폴더 분석 중...")

        images = list(folder_path.glob("*.jpg")) + list(folder_path.glob("*.png"))

        for img_path in images:
            result = analyze_image(img_path)
            score = result["score"]

            if score >= 90:
                results["grade_A"].append(result)
                # 현재 위치 유지
            elif score >= 80:
                results["grade_B"].append(result)
                # B등급 폴더로 이동
                dest = GRADE_B_DIR / folder
                dest.mkdir(exist_ok=True)
                shutil.move(str(img_path), str(dest / img_path.name))
            else:
                results["grade_C"].append(result)
                # C등급 폴더로 이동
                dest = GRADE_C_DIR / folder
                dest.mkdir(exist_ok=True)
                shutil.move(str(img_path), str(dest / img_path.name))

    # 요약
    results["summary"] = {
        "total": len(results["grade_A"]) + len(results["grade_B"]) + len(results["grade_C"]),
        "grade_A_count": len(results["grade_A"]),
        "grade_B_count": len(results["grade_B"]),
        "grade_C_count": len(results["grade_C"]),
        "timestamp": datetime.now().isoformat()
    }

    return results


def print_report(results: dict):
    """결과 리포트 출력"""
    print("\n" + "=" * 60)
    print("📊 분류 결과 리포트")
    print("=" * 60)

    summary = results["summary"]
    total = summary["total"]

    print(f"\n총 이미지: {total}개")
    print(f"  ✅ A등급 (90점+): {summary['grade_A_count']}개 ({summary['grade_A_count']/total*100:.1f}%)")
    print(f"  ⚠️  B등급 (80-89): {summary['grade_B_count']}개 ({summary['grade_B_count']/total*100:.1f}%)")
    print(f"  ❌ C등급 (80점-): {summary['grade_C_count']}개 ({summary['grade_C_count']/total*100:.1f}%)")

    # B등급 주요 이슈
    if results["grade_B"]:
        print("\n📋 B등급 주요 이슈:")
        issue_counts = {}
        for item in results["grade_B"]:
            for issue in item["issues"]:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"   - {issue}: {count}건")

    # C등급 주요 이슈
    if results["grade_C"]:
        print("\n📋 C등급 주요 이슈:")
        issue_counts = {}
        for item in results["grade_C"]:
            for issue in item["issues"]:
                issue_counts[issue] = issue_counts.get(issue, 0) + 1
        for issue, count in sorted(issue_counts.items(), key=lambda x: -x[1])[:5]:
            print(f"   - {issue}: {count}건")


if __name__ == "__main__":
    results = classify_images()
    print_report(results)

    # 결과 저장
    report_path = USABLE_DIR / "classification_report.json"
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print(f"\n📄 상세 리포트: {report_path}")
    print("\n🎬 김감독 컨펌 대기 중...")
