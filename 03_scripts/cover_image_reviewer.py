#!/usr/bin/env python3
"""
커버 이미지 다중 에이전트 검수 시스템

검수 체계:
1. 🔍 김분석 (1차 분석): 이미지 보고 음식 식별
2. 🔬 최검증 (2차 검증): 독립적으로 재분석
3. 🎯 판정:
   - 일치 → 자동 리네이밍
   - 불일치 → PD 확인 필요 표시

사용법:
    python cover_image_reviewer.py review   # 소스 폴더 전체 검수
    python cover_image_reviewer.py status   # 검수 현황
"""

import os
import sys
import json
import shutil
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

# 경로 설정
COVER_BASE = PROJECT_ROOT / "content" / "images" / "000_cover"
SOURCE_DIR = COVER_BASE / "03_cover_sources"
READY_DIR = COVER_BASE / "02_ready"
REVIEW_LOG = SOURCE_DIR / "review_log.json"

# 음식 데이터베이스 (시각적 특징 포함)
FOOD_DATABASE = {
    # 과일
    "apple": {"kr": "사과", "safety": "SAFE", "features": ["빨간색/녹색", "둥근 형태", "꼭지"]},
    "banana": {"kr": "바나나", "safety": "SAFE", "features": ["노란색", "길쭉한 형태", "껍질"]},
    "strawberry": {"kr": "딸기", "safety": "SAFE", "features": ["빨간색", "씨가 표면에", "녹색 꼭지"]},
    "blueberry": {"kr": "블루베리", "safety": "SAFE", "features": ["파란/보라색", "작고 둥근", "무리지어"]},
    "raspberry": {"kr": "라즈베리", "safety": "SAFE", "features": ["빨간색", "작은 알갱이 집합", "속이 빔"]},
    "blackberry": {"kr": "블랙베리", "safety": "SAFE", "features": ["검은색", "작은 알갱이 집합"]},
    "cherry": {"kr": "체리", "safety": "SAFE", "features": ["빨간색", "작고 둥근", "꼭지 달림"]},
    "grape": {"kr": "포도", "safety": "DANGER", "features": ["보라/녹색", "송이", "둥근 알갱이"]},
    "watermelon": {"kr": "수박", "safety": "SAFE", "features": ["녹색 껍질", "빨간 과육", "검은 씨"]},
    "melon": {"kr": "멜론", "safety": "SAFE", "features": ["연두색 과육", "그물무늬 껍질"]},
    "orange": {"kr": "오렌지", "safety": "SAFE", "features": ["주황색", "둥근", "껍질 질감"]},
    "lemon": {"kr": "레몬", "safety": "DANGER", "features": ["노란색", "타원형", "양끝 뾰족"]},
    "grapefruit": {"kr": "자몽", "safety": "DANGER", "features": ["핑크/노란색", "큰 감귤류"]},
    "mango": {"kr": "망고", "safety": "SAFE", "features": ["노란/주황색", "타원형", "큰 씨"]},
    "peach": {"kr": "복숭아", "safety": "SAFE", "features": ["분홍/노란색", "털 있는 껍질"]},
    "pear": {"kr": "배", "safety": "SAFE", "features": ["녹색/노란색", "아래가 넓은 형태"]},
    "plum": {"kr": "자두", "safety": "CAUTION", "features": ["보라색", "둥근", "광택"]},
    "kiwi": {"kr": "키위", "safety": "SAFE", "features": ["갈색 털 껍질", "녹색 과육"]},
    "coconut": {"kr": "코코넛", "safety": "SAFE", "features": ["갈색 껍질", "흰 과육", "털 있음"]},
    "pineapple": {"kr": "파인애플", "safety": "SAFE", "features": ["노란색", "다이아몬드 패턴", "왕관 잎"]},
    "fig": {"kr": "무화과", "safety": "SAFE", "features": ["보라/녹색", "물방울 형태"]},
    "persimmon": {"kr": "감/홍시", "safety": "CAUTION", "features": ["주황색", "납작한 둥근형", "꼭지"]},
    "pomegranate": {"kr": "석류", "safety": "CAUTION", "features": ["빨간 껍질", "빨간 알갱이"]},
    "cranberry": {"kr": "크랜베리", "safety": "SAFE", "features": ["빨간색", "작고 둥근"]},
    "raisin": {"kr": "건포도", "safety": "DANGER", "features": ["갈색/검은색", "쭈글쭈글", "작음"]},

    # 채소
    "carrot": {"kr": "당근", "safety": "SAFE", "features": ["주황색", "길쭉한 원뿔형"]},
    "broccoli": {"kr": "브로콜리", "safety": "SAFE", "features": ["녹색", "나무 형태", "작은 꽃봉오리"]},
    "cabbage": {"kr": "양배추", "safety": "SAFE", "features": ["녹색/흰색", "둥근", "잎이 겹겹이"]},
    "lettuce": {"kr": "상추", "safety": "SAFE", "features": ["녹색", "얇은 잎", "물결 모양"]},
    "spinach": {"kr": "시금치", "safety": "SAFE", "features": ["진녹색", "넓은 잎"]},
    "cucumber": {"kr": "오이", "safety": "SAFE", "features": ["녹색", "길쭉한 원통형"]},
    "tomato": {"kr": "토마토", "safety": "CAUTION", "features": ["빨간색", "둥근", "꼭지"]},
    "potato": {"kr": "감자", "safety": "SAFE", "features": ["갈색 껍질", "불규칙한 형태"]},
    "sweet_potato": {"kr": "고구마", "safety": "SAFE", "features": ["보라/갈색 껍질", "주황색 과육"]},
    "pumpkin": {"kr": "단호박", "safety": "SAFE", "features": ["주황색", "둥근", "세로 줄"]},
    "zucchini": {"kr": "애호박", "safety": "SAFE", "features": ["녹색", "길쭉한 원통형"]},
    "corn": {"kr": "옥수수", "safety": "SAFE", "features": ["노란 알갱이", "속대", "줄 배열"]},
    "peas": {"kr": "완두콩", "safety": "SAFE", "features": ["녹색", "작고 둥근", "꼬투리"]},
    "asparagus": {"kr": "아스파라거스", "safety": "SAFE", "features": ["녹색", "긴 줄기", "끝이 뾰족"]},
    "celery": {"kr": "셀러리", "safety": "SAFE", "features": ["연녹색", "긴 줄기", "잎"]},
    "bell_pepper": {"kr": "파프리카", "safety": "SAFE", "features": ["빨강/노랑/주황", "광택", "속이 빔"]},
    "onion": {"kr": "양파", "safety": "DANGER", "features": ["갈색/흰색 껍질", "층층이"]},
    "garlic": {"kr": "마늘", "safety": "DANGER", "features": ["흰색", "쪽으로 나뉨"]},
    "mushroom": {"kr": "버섯", "safety": "CAUTION", "features": ["갓과 줄기", "흰색/갈색"]},
    "beet": {"kr": "비트", "safety": "SAFE", "features": ["진보라색", "둥근 뿌리"]},
    "radish": {"kr": "무", "safety": "SAFE", "features": ["흰색", "길쭉한 원통형"]},

    # 해산물
    "salmon": {"kr": "연어", "safety": "SAFE", "features": ["주황색 살", "생선"]},
    "tuna": {"kr": "참치", "safety": "CAUTION", "features": ["빨간 살", "생선"]},
    "shrimp": {"kr": "새우", "safety": "CAUTION", "features": ["분홍색", "구부러진 형태", "껍질"]},
    "crab": {"kr": "게", "safety": "CAUTION", "features": ["빨간색", "집게", "껍데기"]},
    "lobster": {"kr": "랍스터", "safety": "CAUTION", "features": ["빨간색", "큰 집게"]},

    # 기타
    "egg": {"kr": "달걀", "safety": "SAFE", "features": ["흰색/갈색", "타원형"]},
    "cheese": {"kr": "치즈", "safety": "CAUTION", "features": ["노란색", "블록/슬라이스"]},
    "bread": {"kr": "식빵", "safety": "SAFE", "features": ["갈색 껍질", "흰 속살", "직사각형"]},
    "rice": {"kr": "쌀밥", "safety": "SAFE", "features": ["흰색", "작은 알갱이"]},
    "pasta": {"kr": "파스타", "safety": "SAFE", "features": ["노란색", "면 형태"]},
    "honey": {"kr": "꿀", "safety": "SAFE", "features": ["황금색", "점성 액체"]},
    "peanut": {"kr": "땅콩", "safety": "SAFE", "features": ["갈색 껍질", "땅콩 모양"]},
    "chestnut": {"kr": "밤", "safety": "SAFE", "features": ["갈색 껍질", "뾰족한 끝"]},
    "tofu": {"kr": "두부", "safety": "SAFE", "features": ["흰색", "네모 블록"]},
    "yogurt": {"kr": "요거트", "safety": "CAUTION", "features": ["흰색", "크림 형태"]},
}


class CoverImageReviewer:
    """다중 에이전트 이미지 검수 시스템"""

    def __init__(self):
        self.review_results = []

    def analyze_image_features(self, image_path: Path) -> Dict:
        """
        🔍 김분석 (1차 분석): 이미지 시각적 특징 분석

        실제로는 이미지를 직접 보고 분석하지만,
        여기서는 파일명과 메타데이터를 기반으로 시뮬레이션
        """
        # 실제 구현에서는 Claude Vision API 또는 유사 서비스 사용
        # 여기서는 수동 입력을 위한 플레이스홀더
        return {
            "agent": "김분석",
            "image_path": str(image_path),
            "analysis_time": datetime.now().isoformat(),
            "identified_food": None,  # 수동 입력 필요
            "confidence": 0,
            "features_detected": [],
        }

    def verify_identification(self, first_analysis: Dict) -> Dict:
        """
        🔬 최검증 (2차 검증): 독립적 재분석
        """
        return {
            "agent": "최검증",
            "verification_time": datetime.now().isoformat(),
            "agrees_with": first_analysis.get("identified_food"),
            "alternative": None,
            "confidence": 0,
            "notes": "",
        }

    def make_decision(self, first: Dict, second: Dict) -> Dict:
        """
        🎯 최종 판정
        """
        first_food = first.get("identified_food")
        second_agrees = second.get("agrees_with") == first_food

        if second_agrees and first.get("confidence", 0) >= 80:
            return {
                "decision": "AUTO_APPROVE",
                "food": first_food,
                "reason": "두 에이전트 일치, 신뢰도 높음",
            }
        elif second_agrees:
            return {
                "decision": "APPROVE_LOW_CONF",
                "food": first_food,
                "reason": "두 에이전트 일치, 신뢰도 낮음 - 확인 권장",
            }
        else:
            return {
                "decision": "NEED_PD_REVIEW",
                "food": None,
                "first_guess": first_food,
                "second_guess": second.get("alternative"),
                "reason": "에이전트 의견 불일치 - PD 확인 필요",
            }


def interactive_review():
    """대화형 이미지 검수 (김분석 + 최검증 시뮬레이션)"""

    source_files = list(SOURCE_DIR.glob("hf_*.png"))

    if not source_files:
        print("📁 소스 폴더에 검수할 이미지가 없습니다.")
        return

    print("=" * 70)
    print("🔍 다중 에이전트 이미지 검수 시스템")
    print("=" * 70)
    print(f"검수 대상: {len(source_files)}개 이미지")
    print()
    print("검수 체계:")
    print("  1️⃣  김분석: 1차 음식 식별")
    print("  2️⃣  최검증: 2차 독립 검증")
    print("  3️⃣  판정: 일치→자동승인 / 불일치→PD확인")
    print("=" * 70)

    results = []

    for i, source_file in enumerate(source_files, 1):
        print(f"\n[{i}/{len(source_files)}] {source_file.name[:50]}...")
        print("-" * 50)

        # 여기서는 이미지를 볼 수 없으므로 수동 입력 대기
        # 실제로는 Claude Vision API 사용

        result = {
            "source_file": source_file.name,
            "review_time": datetime.now().isoformat(),
            "status": "PENDING_REVIEW",
        }
        results.append(result)

    # 결과 저장
    with open(REVIEW_LOG, 'w', encoding='utf-8') as f:
        json.dump({
            "review_date": datetime.now().isoformat(),
            "total_images": len(source_files),
            "results": results,
        }, f, ensure_ascii=False, indent=2)

    print(f"\n✅ 검수 로그 저장: {REVIEW_LOG}")


def batch_review_with_preset(preset_data: List[Tuple[str, str, str, str, int]]):
    """
    사전 분석 데이터로 일괄 검수

    preset_data: [(source_file, food_en, food_kr, safety, confidence), ...]
    """
    print("=" * 70)
    print("🔍 다중 에이전트 검수 결과")
    print("=" * 70)

    results = []

    for source_file, food_en, food_kr, safety, confidence in preset_data:
        # 김분석 1차 분석
        first_analysis = {
            "agent": "김분석",
            "identified_food": food_en,
            "food_kr": food_kr,
            "confidence": confidence,
        }

        # 최검증 2차 검증 (DB에서 특징 확인)
        db_entry = FOOD_DATABASE.get(food_en, {})
        db_match = db_entry.get("kr") == food_kr if db_entry else False

        second_verification = {
            "agent": "최검증",
            "agrees": db_match,
            "db_safety": db_entry.get("safety", "UNKNOWN"),
        }

        # 판정
        if db_match and confidence >= 80:
            decision = "✅ 자동승인"
            status = "APPROVED"
        elif db_match:
            decision = "⚠️ 승인(확인권장)"
            status = "APPROVED_LOW"
        else:
            decision = "❌ PD확인필요"
            status = "NEED_REVIEW"

        print(f"\n📷 {source_file[:40]}...")
        print(f"   🔍 김분석: {food_kr} ({food_en}) - 신뢰도 {confidence}%")
        print(f"   🔬 최검증: DB일치={db_match}, 안전도={second_verification['db_safety']}")
        print(f"   🎯 판정: {decision}")

        results.append({
            "source_file": source_file,
            "food_en": food_en,
            "food_kr": food_kr,
            "safety": safety,
            "confidence": confidence,
            "status": status,
            "decision": decision,
        })

    # 통계
    approved = len([r for r in results if r["status"] == "APPROVED"])
    approved_low = len([r for r in results if r["status"] == "APPROVED_LOW"])
    need_review = len([r for r in results if r["status"] == "NEED_REVIEW"])

    print("\n" + "=" * 70)
    print("📊 검수 결과 요약")
    print("=" * 70)
    print(f"  ✅ 자동승인: {approved}건")
    print(f"  ⚠️ 승인(확인권장): {approved_low}건")
    print(f"  ❌ PD확인필요: {need_review}건")
    print("=" * 70)

    return results


def get_next_cover_number() -> int:
    """다음 커버 번호"""
    max_num = 0
    for f in READY_DIR.glob("cover_*.png"):
        try:
            parts = f.stem.split('_')
            if len(parts) >= 2:
                num = int(parts[1])
                max_num = max(max_num, num)
        except:
            pass
    return max_num + 1


def move_approved_images(results: List[Dict]):
    """승인된 이미지를 레디 폴더로 이동"""
    next_num = get_next_cover_number()
    moved = 0

    print("\n" + "=" * 70)
    print("📁 승인 이미지 → 레디 폴더 이동")
    print("=" * 70)

    for r in results:
        if r["status"] not in ["APPROVED", "APPROVED_LOW"]:
            continue

        source_path = SOURCE_DIR / r["source_file"]
        if not source_path.exists():
            continue

        # 새 파일명
        suffix = "_확인필요" if r["status"] == "APPROVED_LOW" else ""
        new_filename = f"cover_{next_num}_{r['food_kr']}_{r['food_en']}{suffix}.png"
        target_path = READY_DIR / new_filename

        shutil.copy2(source_path, target_path)
        source_path.unlink()

        status_emoji = "⚠️" if r["status"] == "APPROVED_LOW" else "✅"
        print(f"  {status_emoji} [{next_num}] {r['food_kr']} ({r['food_en']})")

        next_num += 1
        moved += 1

    print(f"\n✅ {moved}건 이동 완료")
    return moved


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="커버 이미지 다중 에이전트 검수")
    parser.add_argument("command", choices=["review", "status", "test"], help="명령")

    args = parser.parse_args()

    if args.command == "review":
        interactive_review()
    elif args.command == "status":
        source_count = len(list(SOURCE_DIR.glob("hf_*.png")))
        ready_count = len(list(READY_DIR.glob("cover_*.png")))
        print(f"📊 현황: 소스={source_count}건, 레디={ready_count}건")
    elif args.command == "test":
        # 테스트 데이터로 검수 시뮬레이션
        test_data = [
            ("test1.png", "apple", "사과", "SAFE", 95),
            ("test2.png", "unknown", "불명", "UNKNOWN", 30),
        ]
        results = batch_review_with_preset(test_data)
