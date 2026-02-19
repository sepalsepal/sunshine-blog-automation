#!/usr/bin/env python3
"""
fix_forbidden_food_data.py - FORBIDDEN 음식 데이터 독성 정보로 수정
WO-OVERNIGHT Task 3

대상: 36개 FORBIDDEN 음식 (127 대파 제외 - 이미 수정됨)
수정 내용:
- nutrients 배열을 독성 화합물 정보로 교체
- benefit 필드를 위험 효과로 변경
- toxicity_mapping.json 기반 데이터 적용

사용법:
    python scripts/fix_forbidden_food_data.py --dry-run
    python scripts/fix_forbidden_food_data.py --execute
"""

import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional
from copy import deepcopy

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
TOXICITY_MAPPING_PATH = PROJECT_ROOT / "config" / "toxicity_mapping.json"
LOGS_DIR = PROJECT_ROOT / "logs" / "fix_food_data"

# 이미 수정된 항목 (건너뛰기)
ALREADY_FIXED = [127]

# =============================================================================
# 독성 카테고리별 nutrients 템플릿
# =============================================================================

TOXICITY_NUTRIENTS = {
    "ALLIUM": [
        {"name": "알리신", "benefit": "적혈구 파괴", "value": "고농도", "unit": ""},
        {"name": "티오설페이트", "benefit": "용혈성 빈혈 유발", "value": "다량", "unit": ""},
        {"name": "N-프로필 이황화물", "benefit": "산화 스트레스", "value": "함유", "unit": ""},
        {"name": "유기황 화합물", "benefit": "소화기 자극", "value": "다량", "unit": ""},
    ],
    "GRAPE_TOXIN": [
        {"name": "타르타르산", "benefit": "급성 신부전 유발", "value": "고농도", "unit": ""},
        {"name": "탄닌", "benefit": "소화기 손상", "value": "다량", "unit": ""},
        {"name": "미확인 독성물질", "benefit": "신장 독성", "value": "함유", "unit": ""},
        {"name": "과당", "benefit": "소화 장애", "value": "다량", "unit": ""},
    ],
    "THEOBROMINE": [
        {"name": "테오브로민", "benefit": "심장 독성", "value": "고농도", "unit": ""},
        {"name": "카페인", "benefit": "신경 독성", "value": "함유", "unit": ""},
        {"name": "과당", "benefit": "비만/당뇨 위험", "value": "다량", "unit": ""},
        {"name": "지방", "benefit": "췌장염 위험", "value": "고함량", "unit": ""},
    ],
    "CAFFEINE": [
        {"name": "카페인", "benefit": "신경 독성", "value": "고농도", "unit": ""},
        {"name": "탄닌", "benefit": "소화 장애", "value": "함유", "unit": ""},
        {"name": "자극성 물질", "benefit": "심박 이상", "value": "함유", "unit": ""},
    ],
    "ALCOHOL": [
        {"name": "에탄올", "benefit": "중추신경 억제", "value": "고농도", "unit": "%"},
        {"name": "아세트알데히드", "benefit": "간 독성", "value": "대사산물", "unit": ""},
        {"name": "알코올", "benefit": "저혈당 유발", "value": "함유", "unit": ""},
    ],
    "PERSIN": [
        {"name": "퍼신", "benefit": "심근 독성", "value": "함유", "unit": ""},
        {"name": "지방산", "benefit": "췌장염 위험", "value": "고함량", "unit": ""},
        {"name": "독성 물질", "benefit": "구토/설사 유발", "value": "함유", "unit": ""},
    ],
    "LACTOSE": [
        {"name": "유당", "benefit": "소화 장애", "value": "고함량", "unit": ""},
        {"name": "유지방", "benefit": "비만 위험", "value": "함유", "unit": ""},
        {"name": "카세인", "benefit": "알레르기 유발 가능", "value": "함유", "unit": ""},
    ],
    "HIGH_SODIUM_FAT": [
        {"name": "나트륨", "benefit": "신장/심장 부담", "value": "과다", "unit": "mg"},
        {"name": "포화지방", "benefit": "췌장염 위험", "value": "고함량", "unit": ""},
        {"name": "인공 조미료", "benefit": "소화기 자극", "value": "함유", "unit": ""},
        {"name": "칼로리", "benefit": "비만 위험", "value": "고칼로리", "unit": ""},
    ],
    "CITRUS_TOXIN": [
        {"name": "푸라노쿠마린", "benefit": "약물 대사 방해", "value": "함유", "unit": ""},
        {"name": "시트르산", "benefit": "위장 자극", "value": "고농도", "unit": ""},
        {"name": "리모넨", "benefit": "소화기 자극", "value": "함유", "unit": ""},
        {"name": "소랄렌", "benefit": "광독성", "value": "함유", "unit": ""},
    ],
    "SUGAR_ADDITIVES": [
        {"name": "과당", "benefit": "비만/당뇨 위험", "value": "고함량", "unit": ""},
        {"name": "인공 착색료", "benefit": "알레르기 유발 가능", "value": "함유", "unit": ""},
        {"name": "인공 감미료", "benefit": "소화 장애", "value": "함유", "unit": ""},
        {"name": "방부제", "benefit": "장기 독성 우려", "value": "함유", "unit": ""},
    ],
    "XYLITOL": [
        {"name": "자일리톨", "benefit": "급성 저혈당", "value": "치명적", "unit": ""},
        {"name": "인슐린 과분비", "benefit": "저혈당 쇼크", "value": "유발", "unit": ""},
        {"name": "간 독성", "benefit": "간 손상 위험", "value": "고위험", "unit": ""},
    ],
}

# FORBIDDEN용 do_items, dont_items, precautions 템플릿
FORBIDDEN_DO_ITEMS = [
    "절대 급여하지 마세요",
    "다른 음식에 섞이지 않았는지 확인하세요",
    "반려견 접근 불가 장소에 보관하세요",
    "섭취 시 즉시 수의사에게 연락하세요",
    "섭취량과 시간을 기록해두세요",
]

FORBIDDEN_DONT_ITEMS = [
    "어떤 형태로든 급여 금지",
    "조리해도 독성 남아있음",
    "소량도 위험할 수 있음",
    "다른 음식과 섞어 급여 금지",
    "간식으로도 급여 금지",
]

FORBIDDEN_PRECAUTIONS = [
    {
        "title": "즉시 수의사 방문",
        "desc": "섭취 확인 시 즉시 동물병원 방문"
    },
    {
        "title": "구토 유도 금지",
        "desc": "전문가 지시 없이 구토 유도하지 마세요"
    },
    {
        "title": "증상 관찰",
        "desc": "구토, 설사, 무기력, 떨림 등 관찰"
    },
    {
        "title": "섭취 정보 기록",
        "desc": "섭취량, 시간, 제품명 기록 후 수의사에게 전달"
    },
    {
        "title": "24시간 동물병원 확인",
        "desc": "야간/휴일에도 응급 진료 가능한 병원 확인"
    },
]


# =============================================================================
# 유틸리티
# =============================================================================

def load_json(path: Path) -> Dict:
    """JSON 파일 로드"""
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path: Path, data: Dict):
    """JSON 파일 저장"""
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def get_forbidden_ids(food_data: Dict) -> List[int]:
    """FORBIDDEN 음식 ID 목록"""
    forbidden = []
    for food_id, data in food_data.items():
        if data.get("safety", "").upper() == "FORBIDDEN":
            fid = int(food_id)
            if fid not in ALREADY_FIXED:
                forbidden.append(fid)
    return sorted(forbidden)


# =============================================================================
# 수정 로직
# =============================================================================

def fix_food_entry(
    food_id: int,
    food_data: Dict,
    toxicity_mapping: Dict,
) -> Tuple[Dict, List[str]]:
    """
    단일 음식 항목 수정

    Returns:
        (수정된 데이터, 변경 내역)
    """
    food_id_str = str(food_id)
    original = food_data[food_id_str]
    fixed = deepcopy(original)
    changes = []

    # toxicity_mapping에서 정보 가져오기
    tox_info = toxicity_mapping.get("food_mapping", {}).get(food_id_str, {})
    primary_toxin = tox_info.get("primary_toxin", "HIGH_SODIUM_FAT")
    secondary_toxin = tox_info.get("secondary_toxin")

    # 1. nutrients 교체
    old_nutrients = original.get("nutrients", [])
    new_nutrients = TOXICITY_NUTRIENTS.get(primary_toxin, TOXICITY_NUTRIENTS["HIGH_SODIUM_FAT"])

    # secondary toxin이 있으면 일부 추가
    if secondary_toxin and secondary_toxin in TOXICITY_NUTRIENTS:
        secondary_nutrients = TOXICITY_NUTRIENTS[secondary_toxin][:2]
        new_nutrients = new_nutrients + secondary_nutrients

    fixed["nutrients"] = new_nutrients
    changes.append(f"nutrients 교체: {len(old_nutrients)}개 → {len(new_nutrients)}개 ({primary_toxin})")

    # 2. do_items 교체
    if original.get("do_items") != FORBIDDEN_DO_ITEMS:
        fixed["do_items"] = FORBIDDEN_DO_ITEMS
        changes.append("do_items 교체: FORBIDDEN 템플릿 적용")

    # 3. dont_items 교체
    if original.get("dont_items") != FORBIDDEN_DONT_ITEMS:
        fixed["dont_items"] = FORBIDDEN_DONT_ITEMS
        changes.append("dont_items 교체: FORBIDDEN 템플릿 적용")

    # 4. precautions 교체
    if original.get("precautions") != FORBIDDEN_PRECAUTIONS:
        fixed["precautions"] = FORBIDDEN_PRECAUTIONS
        changes.append("precautions 교체: FORBIDDEN 템플릿 적용")

    # 5. dosages를 0으로 설정
    if original.get("dosages"):
        fixed["dosages"] = {
            "소형견": {"weight": "모든 체중", "amount": "0g", "desc": "절대 급여 금지"},
            "중형견": {"weight": "모든 체중", "amount": "0g", "desc": "절대 급여 금지"},
            "대형견": {"weight": "모든 체중", "amount": "0g", "desc": "절대 급여 금지"},
            "초대형견": {"weight": "모든 체중", "amount": "0g", "desc": "절대 급여 금지"},
        }
        changes.append("dosages 교체: 0g (절대 급여 금지)")

    # 6. cooking_steps 제거/교체
    fixed["cooking_steps"] = [
        {"title": "급여 금지", "desc": "어떤 조리법으로도 급여하지 마세요"},
        {"title": "섭취 시 대처", "desc": "즉시 수의사에게 연락하세요"},
        {"title": "증상 관찰", "desc": "구토, 설사, 무기력 등 관찰"},
        {"title": "정보 기록", "desc": "섭취량, 시간 기록"},
        {"title": "응급 연락처", "desc": "24시간 동물병원 연락처 확보"},
    ]
    changes.append("cooking_steps 교체: 응급 대처법")

    # 7. footnotes 수정
    fixed["nutrition_footnote"] = f"{original.get('name', '')}은(는) 반려견에게 독성이 있어 절대 급여 금지입니다"
    fixed["dosage_warning"] = [
        "어떤 양도 급여하지 마세요",
        "소량도 독성 반응을 일으킬 수 있습니다"
    ]
    fixed["dosage_footnote"] = "급여량 0g - 절대 급여 금지"
    fixed["precaution_emergency"] = tox_info.get("emergency_action", "섭취 시 즉시 수의사에게 연락하세요")
    fixed["cooking_tip"] = "조리 여부와 관계없이 급여 금지"
    changes.append("footnotes 수정: 경고 문구")

    return fixed, changes


def run_fix(
    dry_run: bool = True,
    target: Optional[int] = None,
    verbose: bool = True,
) -> Dict:
    """
    FORBIDDEN 음식 데이터 수정 실행

    Args:
        dry_run: True면 미리보기만
        target: 특정 food_id만 (None이면 전체)
        verbose: 상세 출력
    """
    print("=" * 60)
    print(f"FORBIDDEN 음식 데이터 수정 {'(DRY-RUN)' if dry_run else '(EXECUTE)'}")
    print("=" * 60)

    # 데이터 로드
    food_data = load_json(FOOD_DATA_PATH)
    toxicity_mapping = load_json(TOXICITY_MAPPING_PATH)

    # 대상 결정
    if target:
        food_ids = [target]
    else:
        food_ids = get_forbidden_ids(food_data)

    print(f"\n대상: {len(food_ids)}개 FORBIDDEN 음식")
    print(f"제외: {ALREADY_FIXED} (이미 수정됨)\n")

    stats = {
        "total": len(food_ids),
        "fixed": 0,
        "failed": 0,
        "changes": [],
    }

    # 수정 적용
    for food_id in food_ids:
        food_id_str = str(food_id)

        if food_id_str not in food_data:
            print(f"  #{food_id:03d}: SKIP (데이터 없음)")
            stats["failed"] += 1
            continue

        try:
            fixed_entry, changes = fix_food_entry(food_id, food_data, toxicity_mapping)

            if not dry_run:
                food_data[food_id_str] = fixed_entry

            stats["fixed"] += 1
            stats["changes"].append({
                "food_id": food_id,
                "name": food_data[food_id_str].get("name", "Unknown"),
                "changes": changes,
            })

            if verbose:
                name = food_data[food_id_str].get("name", "Unknown")
                print(f"  #{food_id:03d} {name}: {len(changes)} changes")
                for change in changes[:2]:
                    print(f"      - {change}")

        except Exception as e:
            print(f"  #{food_id:03d}: ERROR - {e}")
            stats["failed"] += 1

    # 저장
    if not dry_run:
        # 백업 생성
        backup_path = FOOD_DATA_PATH.with_suffix(".json.bak")
        original_data = load_json(FOOD_DATA_PATH)
        save_json(backup_path, original_data)
        print(f"\n백업 생성: {backup_path}")

        # 수정본 저장
        save_json(FOOD_DATA_PATH, food_data)
        print(f"저장 완료: {FOOD_DATA_PATH}")

    # 로그 저장
    log_path = save_fix_log(stats, dry_run)

    # 요약
    print("\n" + "=" * 60)
    print("결과 요약")
    print("=" * 60)
    print(f"총 대상: {stats['total']}개")
    print(f"수정됨: {stats['fixed']}개")
    print(f"실패: {stats['failed']}개")
    print(f"\n로그: {log_path}")

    if dry_run and stats["fixed"] > 0:
        print("\n💡 실제 적용하려면: --execute 옵션 사용")

    return stats


def save_fix_log(stats: Dict, dry_run: bool) -> Path:
    """수정 로그 저장"""
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

    date_str = datetime.now().strftime("%Y%m%d")
    time_str = datetime.now().strftime("%H%M%S")
    mode = "dryrun" if dry_run else "execute"
    log_path = LOGS_DIR / f"{date_str}_{time_str}_{mode}.log"

    with open(log_path, "w", encoding="utf-8") as f:
        f.write("=" * 60 + "\n")
        f.write("FORBIDDEN Food Data Fix Log\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"Timestamp: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"Mode: {'DRY-RUN' if dry_run else 'EXECUTE'}\n")
        f.write(f"Total: {stats['total']}\n")
        f.write(f"Fixed: {stats['fixed']}\n")
        f.write(f"Failed: {stats['failed']}\n\n")

        f.write("[CHANGES DETAIL]\n")
        for item in stats["changes"]:
            f.write(f"\n#{item['food_id']:03d} {item['name']}:\n")
            for change in item["changes"]:
                f.write(f"  - {change}\n")

        f.write("\n" + "=" * 60 + "\n")

    return log_path


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(description="FORBIDDEN 음식 데이터 수정")
    parser.add_argument("--dry-run", action="store_true", help="미리보기 모드")
    parser.add_argument("--execute", action="store_true", help="실제 수정 실행")
    parser.add_argument("--target", type=int, help="특정 food_id만 수정")
    parser.add_argument("-q", "--quiet", action="store_true", help="간략 출력")

    args = parser.parse_args()

    dry_run = not args.execute

    run_fix(
        dry_run=dry_run,
        target=args.target,
        verbose=not args.quiet,
    )


if __name__ == "__main__":
    main()
