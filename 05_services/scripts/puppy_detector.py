#!/usr/bin/env python3
"""
퍼피 이미지 탐지 스크립트 (김부장 총괄)

시니어 햇살이 특징:
- 흰 주둥이 (white muzzle)
- 검은 눈/코
- 성견 체형 (길고 날씬한 다리)
- 10살 시니어 느낌

퍼피 특징:
- 둥글둥글한 얼굴
- 짧고 푹신한 털
- 통통한 체형, 짧은 다리
- 큰 발
"""

import os
from pathlib import Path
import json
from datetime import datetime

# 경로 설정
BASE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine/content/images/sunshine/01_usable")
EXPRESSION_DIR = BASE_DIR / "expression"
LOCATION_DIR = BASE_DIR / "location"

# 퍼피 의심 폴더
PUPPY_SUSPECT_DIR = BASE_DIR / "puppy_suspect"
PUPPY_SUSPECT_DIR.mkdir(exist_ok=True)

def get_all_images():
    """모든 이미지 목록"""
    images = []

    if EXPRESSION_DIR.exists():
        images.extend(list(EXPRESSION_DIR.glob("*.jpg")))
    if LOCATION_DIR.exists():
        images.extend(list(LOCATION_DIR.glob("*.jpg")))

    return sorted(images)

def create_review_batches(images, batch_size=20):
    """리뷰용 배치 생성"""
    batches = []
    for i in range(0, len(images), batch_size):
        batch = images[i:i+batch_size]
        batches.append({
            "batch_id": i // batch_size + 1,
            "start_idx": i,
            "end_idx": min(i + batch_size, len(images)),
            "images": [str(img) for img in batch]
        })
    return batches

def save_batches_for_review():
    """배치 정보 저장"""
    images = get_all_images()
    batches = create_review_batches(images, batch_size=20)

    output = {
        "total_images": len(images),
        "total_batches": len(batches),
        "batch_size": 20,
        "batches": batches,
        "timestamp": datetime.now().isoformat()
    }

    output_path = BASE_DIR / "review_batches.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    print(f"총 이미지: {len(images)}개")
    print(f"총 배치: {len(batches)}개 (배치당 20개)")
    print(f"배치 정보 저장: {output_path}")

    return batches

if __name__ == "__main__":
    print("=" * 60)
    print("👔 김부장 총괄 - 퍼피 이미지 전수 조사 준비")
    print("=" * 60)

    batches = save_batches_for_review()

    print("\n📋 리뷰 배치 정보:")
    for i, batch in enumerate(batches[:5]):
        print(f"   배치 {batch['batch_id']}: {batch['start_idx']+1}~{batch['end_idx']}번")
    print(f"   ... (총 {len(batches)}개 배치)")
