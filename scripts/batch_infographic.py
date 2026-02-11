#!/usr/bin/env python3
"""
batch_infographic.py - 전체 콘텐츠 인포그래픽 배치 생성
R7 Phase 2: 블로그 본문 인포그래픽 (3~7장) 일괄 생성

사용법: python3 scripts/batch_infographic.py [--dry-run] [--start N] [--end N]
"""

import os
import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Optional

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from scripts.infographic_generator import (
    generate_nutrition_info,
    generate_do_dont,
    generate_dosage_table,
    generate_precautions,
    generate_cooking_method,
)

# 콘텐츠 폴더
CONTENTS_DIR = PROJECT_ROOT / "contents"
STATUS_DIRS = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]

# 콘텐츠 데이터 파일
FOOD_DATA_FILE = PROJECT_ROOT / "config" / "food_data.json"


def load_food_data() -> Dict:
    """음식 데이터 로드"""
    if not FOOD_DATA_FILE.exists():
        print(f"⚠️ 음식 데이터 파일 없음: {FOOD_DATA_FILE}")
        print("   기본 템플릿으로 진행합니다.")
        return {}

    with open(FOOD_DATA_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_default_data(food_name: str, safety: str = "SAFE") -> Dict:
    """기본 템플릿 데이터 생성"""
    return {
        "name": food_name,
        "safety": safety,
        "nutrients": [
            {"name": "주요 영양소 1", "benefit": "효능 설명", "value": "100", "unit": "mg"},
            {"name": "주요 영양소 2", "benefit": "효능 설명", "value": "50", "unit": "g"},
            {"name": "비타민", "benefit": "건강 효능", "value": "10", "unit": "mg"},
            {"name": "미네랄", "benefit": "건강 효능", "value": "5", "unit": "mg"},
            {"name": "식이섬유", "benefit": "소화 건강", "value": "2", "unit": "g"},
            {"name": "칼로리", "benefit": "에너지", "value": "30", "unit": "kcal"},
        ],
        "dosages": {
            "소형견": {"weight": "5kg 이하", "amount": "10~20g", "desc": "작은 조각 2~3개"},
            "중형견": {"weight": "5~15kg", "amount": "20~40g", "desc": "작은 조각 4~5개"},
            "대형견": {"weight": "15~30kg", "amount": "40~60g", "desc": "작은 조각 6~7개"},
            "초대형견": {"weight": "30kg 이상", "amount": "60~80g", "desc": "작은 조각 8~10개"},
        },
        "do_items": [
            "깨끗이 씻어서 급여",
            "작게 잘라서 급여",
            "익혀서 급여 가능",
            "간식으로 소량 급여",
            "식힌 후 급여",
        ],
        "dont_items": [
            "과다 급여 금지",
            "양념된 것 급여 금지",
            "통째로 급여 금지",
            "매일 급여 금지",
            "가공품 급여 금지",
        ],
        "precautions": [
            {"title": "적정량 준수", "desc": "하루 칼로리의 10% 이내로 급여"},
            {"title": "처음 급여 시 주의", "desc": "소량부터 시작하여 반응 확인"},
            {"title": "알러지 확인", "desc": "첫 급여 후 24시간 관찰"},
            {"title": "신선한 것만", "desc": "상한 것은 급여 금지"},
        ],
        "cooking_steps": [
            {"title": "깨끗이 씻기", "desc": "흐르는 물에 깨끗이 세척"},
            {"title": "손질하기", "desc": "먹을 수 없는 부분 제거"},
            {"title": "작게 썰기", "desc": "먹기 좋은 크기로 자르기"},
            {"title": "조리하기", "desc": "필요시 익혀서 준비"},
            {"title": "식혀서 급여", "desc": "적당히 식힌 후 급여"},
        ],
        "nutrition_footnote": "개체별 차이가 있으므로 반응을 보며 조절하세요",
        "dosage_warning": ["하루 칼로리의 10% 이내로 급여해주세요", "처음 급여 시 소량부터 시작하세요"],
        "dosage_footnote": "개체별 차이가 있으므로 반응을 보며 조절하세요",
        "precaution_emergency": "이상 증상 발견 시 즉시 수의사와 상담하세요",
        "cooking_tip": "신선한 재료로 간단하게 준비해주세요",
    }


def find_content_folders(food_data: Dict = None) -> List[Dict]:
    """모든 콘텐츠 폴더 찾기"""
    contents = []

    for status_dir in STATUS_DIRS:
        status_path = CONTENTS_DIR / status_dir
        if not status_path.exists():
            continue

        for folder in status_path.iterdir():
            if not folder.is_dir() or folder.name.startswith('.'):
                continue

            # 폴더명 파싱: 033_baguette 또는 001_apple_사과
            parts = folder.name.split('_')
            if len(parts) < 2:
                continue

            try:
                num = int(parts[0])
            except ValueError:
                continue

            # 한글명: food_data.json에서 가져오기, 없으면 영문명 사용
            korean_name = None
            if food_data and str(num) in food_data:
                korean_name = food_data[str(num)].get("name")

            if not korean_name:
                # 폴더명에 한글이 있으면 사용 (예: 001_apple_사과)
                if len(parts) >= 3:
                    korean_name = parts[-1]
                else:
                    # 영문명을 사용
                    korean_name = '_'.join(parts[1:])

            contents.append({
                "num": num,
                "folder": folder,
                "korean_name": korean_name,
                "status": status_dir,
            })

    return sorted(contents, key=lambda x: x["num"])


def generate_infographics_for_content(
    content: Dict,
    food_data: Dict,
    dry_run: bool = False
) -> Dict[str, bool]:
    """단일 콘텐츠의 인포그래픽 생성"""
    results = {}
    folder = content["folder"]
    blog_dir = folder / "blog"

    # blog 폴더 확인/생성
    if not blog_dir.exists():
        if dry_run:
            print(f"   [DRY-RUN] blog 폴더 생성: {blog_dir}")
        else:
            blog_dir.mkdir(parents=True, exist_ok=True)

    # 음식 데이터 가져오기
    food_name = content["korean_name"]
    data = food_data.get(str(content["num"]), get_default_data(food_name))

    # 이미 존재하는 이미지 확인
    existing = {
        "3_영양정보.png": (blog_dir / "3_영양정보.png").exists(),
        "4_급여가능불가.png": (blog_dir / "4_급여가능불가.png").exists(),
        "5_급여량표.png": (blog_dir / "5_급여량표.png").exists(),
        "6_주의사항.png": (blog_dir / "6_주의사항.png").exists(),
        "7_조리방법.png": (blog_dir / "7_조리방법.png").exists(),
    }

    # 3. 영양정보
    if not existing["3_영양정보.png"]:
        output_path = None if dry_run else blog_dir / "3_영양정보.png"
        if dry_run:
            print(f"   [DRY-RUN] 생성 예정: 3_영양정보.png")
            results["3_영양정보"] = True
        else:
            try:
                generate_nutrition_info(
                    food_name,
                    data.get("nutrients", []),
                    data.get("safety", "SAFE"),
                    data.get("nutrition_footnote", ""),
                    output_path
                )
                results["3_영양정보"] = True
            except Exception as e:
                print(f"   ❌ 3_영양정보 실패: {e}")
                results["3_영양정보"] = False
    else:
        results["3_영양정보"] = "skip"

    # 4. 급여 DO/DON'T
    if not existing["4_급여가능불가.png"]:
        output_path = None if dry_run else blog_dir / "4_급여가능불가.png"
        if dry_run:
            print(f"   [DRY-RUN] 생성 예정: 4_급여가능불가.png")
            results["4_급여가능불가"] = True
        else:
            try:
                generate_do_dont(
                    food_name,
                    data.get("do_items", []),
                    data.get("dont_items", []),
                    output_path
                )
                results["4_급여가능불가"] = True
            except Exception as e:
                print(f"   ❌ 4_급여가능불가 실패: {e}")
                results["4_급여가능불가"] = False
    else:
        results["4_급여가능불가"] = "skip"

    # 5. 급여량표
    if not existing["5_급여량표.png"]:
        output_path = None if dry_run else blog_dir / "5_급여량표.png"
        if dry_run:
            print(f"   [DRY-RUN] 생성 예정: 5_급여량표.png")
            results["5_급여량표"] = True
        else:
            try:
                generate_dosage_table(
                    data.get("dosages", {}),
                    data.get("dosage_warning", []),
                    data.get("dosage_footnote", ""),
                    output_path
                )
                results["5_급여량표"] = True
            except Exception as e:
                print(f"   ❌ 5_급여량표 실패: {e}")
                results["5_급여량표"] = False
    else:
        results["5_급여량표"] = "skip"

    # 6. 주의사항
    if not existing["6_주의사항.png"]:
        output_path = None if dry_run else blog_dir / "6_주의사항.png"
        if dry_run:
            print(f"   [DRY-RUN] 생성 예정: 6_주의사항.png")
            results["6_주의사항"] = True
        else:
            try:
                generate_precautions(
                    food_name,
                    data.get("precautions", []),
                    data.get("precaution_emergency", ""),
                    output_path
                )
                results["6_주의사항"] = True
            except Exception as e:
                print(f"   ❌ 6_주의사항 실패: {e}")
                results["6_주의사항"] = False
    else:
        results["6_주의사항"] = "skip"

    # 7. 조리방법
    if not existing["7_조리방법.png"]:
        output_path = None if dry_run else blog_dir / "7_조리방법.png"
        if dry_run:
            print(f"   [DRY-RUN] 생성 예정: 7_조리방법.png")
            results["7_조리방법"] = True
        else:
            try:
                generate_cooking_method(
                    food_name,
                    data.get("cooking_steps", []),
                    data.get("cooking_tip", ""),
                    output_path
                )
                results["7_조리방법"] = True
            except Exception as e:
                print(f"   ❌ 7_조리방법 실패: {e}")
                results["7_조리방법"] = False
    else:
        results["7_조리방법"] = "skip"

    return results


def main():
    parser = argparse.ArgumentParser(description="인포그래픽 배치 생성")
    parser.add_argument("--dry-run", action="store_true", help="실제 생성 없이 시뮬레이션")
    parser.add_argument("--start", type=int, default=1, help="시작 콘텐츠 번호")
    parser.add_argument("--end", type=int, default=999, help="종료 콘텐츠 번호")
    parser.add_argument("--content", type=int, help="특정 콘텐츠만 처리")
    args = parser.parse_args()

    print("=" * 60)
    print("📊 인포그래픽 배치 생성")
    if args.dry_run:
        print("   🔍 DRY-RUN 모드 (실제 생성 없음)")
    print("=" * 60)

    # 음식 데이터 로드
    food_data = load_food_data()

    # 콘텐츠 폴더 찾기 (food_data에서 한글명 참조)
    contents = find_content_folders(food_data)
    print(f"\n📁 발견된 콘텐츠: {len(contents)}개")

    # 범위 필터링
    if args.content:
        contents = [c for c in contents if c["num"] == args.content]
    else:
        contents = [c for c in contents if args.start <= c["num"] <= args.end]

    print(f"📋 처리 대상: {len(contents)}개 (#{args.start}~#{args.end})")

    # 통계
    stats = {
        "total": len(contents),
        "processed": 0,
        "created": 0,
        "skipped": 0,
        "failed": 0,
    }

    # 배치 처리
    print("\n🔄 처리 중...")
    for content in contents:
        num = content["num"]
        name = content["korean_name"]

        print(f"\n   #{num:03d} {name}:")

        results = generate_infographics_for_content(content, food_data, args.dry_run)
        stats["processed"] += 1

        for img_name, result in results.items():
            if result == "skip":
                stats["skipped"] += 1
            elif result is True:
                stats["created"] += 1
            else:
                stats["failed"] += 1

    # 결과 보고
    print("\n" + "=" * 60)
    print("📊 배치 처리 완료")
    print("=" * 60)
    print(f"📁 전체 콘텐츠: {stats['total']}개")
    print(f"✅ 생성됨: {stats['created']}개")
    print(f"⏭️ 스킵 (이미 존재): {stats['skipped']}개")
    print(f"❌ 실패: {stats['failed']}개")

    if args.dry_run:
        print("\n💡 실제 실행하려면 --dry-run 옵션을 제거하세요")

    print("=" * 60)


if __name__ == "__main__":
    main()
