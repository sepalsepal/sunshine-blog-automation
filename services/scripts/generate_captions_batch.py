#!/usr/bin/env python3
"""
WO-2026-0206-018: 26건 캡션/메타데이터 일괄 생성

캡션 규칙 v1 (파스타 스타일) 적용
"""

import json
from pathlib import Path
from datetime import datetime

PROJECT_ROOT = Path(__file__).parent.parent.parent

# 음식 정보 데이터베이스
FOOD_DATA = {
    "poached_egg": {
        "kr": "수란",
        "safety": "SAFE",
        "benefits": ["양질의 단백질 공급", "비타민 D 풍부", "소화 흡수 용이"],
        "cautions": ["완전히 익혀서 급여", "소금/양념 없이 조리", "알레르기 주의"],
        "serving": {"small": "1/4개", "medium": "1/2개", "large": "1개"},
        "tip": "삶아서, 양념 없이, 소량씩!"
    },
    "milk": {
        "kr": "우유",
        "safety": "CAUTION",
        "benefits": ["칼슘 공급", "단백질 함유"],
        "cautions": ["유당불내증 주의", "설사 유발 가능", "소량만 급여", "락토프리 우유 권장"],
        "forbidden": ["유당불내증이 있는 개"],
        "serving": {"small": "1~2 스푼", "medium": "3~4 스푼", "large": "5~6 스푼"},
        "tip": "소량만, 반응 확인 필수!"
    },
    "potato": {
        "kr": "감자",
        "safety": "SAFE",
        "benefits": ["탄수화물 에너지원", "비타민 C 함유", "식이섬유 풍부"],
        "cautions": ["반드시 익혀서 급여", "싹난 부분 제거 필수", "양념 없이 조리"],
        "forbidden": ["생감자 (솔라닌 독성)", "싹난 감자"],
        "serving": {"small": "1~2 조각", "medium": "3~4 조각", "large": "5~6 조각"},
        "tip": "익혀서, 싹 제거, 양념 없이!"
    },
    "bean_sprouts": {
        "kr": "숙주나물",
        "safety": "SAFE",
        "benefits": ["저칼로리 건강식", "비타민 C 풍부", "식이섬유 함유"],
        "cautions": ["익혀서 급여 권장", "양념 없이 조리", "소량부터 시작"],
        "serving": {"small": "1~2 스푼", "medium": "3~4 스푼", "large": "5~6 스푼"},
        "tip": "데쳐서, 양념 없이!"
    },
    "yogurt": {
        "kr": "요거트",
        "safety": "SAFE",
        "benefits": ["프로바이오틱스 함유", "장 건강 도움", "칼슘 공급"],
        "cautions": ["무가당 플레인만", "첨가물 확인 필수", "소량부터 시작"],
        "forbidden": ["자일리톨 함유 제품"],
        "serving": {"small": "1~2 스푼", "medium": "2~3 스푼", "large": "3~4 스푼"},
        "tip": "무가당 플레인만, 자일리톨 확인!"
    },
    "melon": {
        "kr": "멜론",
        "safety": "SAFE",
        "benefits": ["수분 보충 효과", "비타민 A, C 풍부", "저칼로리 간식"],
        "cautions": ["씨와 껍질 제거", "소량만 급여", "당분 주의"],
        "serving": {"small": "1~2 조각", "medium": "3~4 조각", "large": "5~6 조각"},
        "tip": "씨 빼고, 껍질 벗기고, 소량만!"
    },
    "mackerel": {
        "kr": "고등어",
        "safety": "SAFE",
        "benefits": ["오메가-3 풍부", "단백질 공급", "피부/털 건강"],
        "cautions": ["뼈 완전히 제거", "익혀서 급여", "소금 없이 조리"],
        "serving": {"small": "20~30g", "medium": "40~50g", "large": "60~80g"},
        "tip": "뼈 제거, 익혀서, 소금 없이!"
    },
    "banana_milk": {
        "kr": "바나나우유",
        "safety": "CAUTION",
        "benefits": ["에너지 공급"],
        "cautions": ["당분 과다", "첨가물 다량 함유", "유당불내증 주의", "비추천 간식"],
        "forbidden": ["자일리톨 함유 제품", "인공감미료 제품"],
        "serving": {"small": "맛보기만", "medium": "1~2 스푼", "large": "2~3 스푼"},
        "tip": "되도록 피하고, 줘도 극소량만!"
    },
    "garlic": {
        "kr": "마늘",
        "safety": "FORBIDDEN",
        "benefits": [],
        "cautions": ["절대 급여 금지", "소량도 독성", "파/양파류 모두 위험"],
        "forbidden": ["모든 형태의 마늘 (생/익힌/가루)", "마늘이 들어간 음식"],
        "serving": {"small": "금지", "medium": "금지", "large": "금지"},
        "tip": "절대 금지! 소량도 위험!"
    },
    "kimchi": {
        "kr": "김치",
        "safety": "DANGER",
        "benefits": [],
        "cautions": ["마늘/파 함유", "소금 과다", "양념 자극적"],
        "forbidden": ["모든 종류의 김치", "김치 양념이 묻은 음식"],
        "serving": {"small": "금지", "medium": "금지", "large": "금지"},
        "tip": "급여 금지! 마늘/소금 위험!"
    },
    "quail_egg": {
        "kr": "메추리알",
        "safety": "SAFE",
        "benefits": ["고단백 간식", "비타민 풍부", "작은 크기로 급여 편리"],
        "cautions": ["완전히 익혀서 급여", "소금 없이 조리", "알레르기 주의"],
        "serving": {"small": "1개", "medium": "2개", "large": "3개"},
        "tip": "삶아서, 양념 없이!"
    },
    "kimbap": {
        "kr": "김밥",
        "safety": "CAUTION",
        "benefits": ["에너지 공급"],
        "cautions": ["소금/양념 과다", "단무지 피할 것", "속 재료 확인 필수"],
        "forbidden": ["단무지 (착색료)", "우엉조림 (양념)", "맛살 (첨가물)"],
        "serving": {"small": "밥알만 조금", "medium": "1/4줄", "large": "1/2줄"},
        "tip": "밥만 조금, 속재료 주의!"
    },
    "naengmyeon": {
        "kr": "냉면",
        "safety": "CAUTION",
        "benefits": ["탄수화물 에너지원"],
        "cautions": ["양념장/육수 위험", "면만 소량 가능", "소금 과다"],
        "forbidden": ["양념장", "겨자", "식초"],
        "serving": {"small": "면만 조금", "medium": "면만 소량", "large": "면만 적당량"},
        "tip": "면만 헹궈서, 양념 절대 금지!"
    },
    "bulgogi": {
        "kr": "불고기",
        "safety": "CAUTION",
        "benefits": ["단백질 공급"],
        "cautions": ["양념 과다", "마늘/파 함유 가능", "소금 과다"],
        "forbidden": ["양념이 많이 밴 부분", "파/마늘이 보이는 부분"],
        "serving": {"small": "1~2 조각", "medium": "2~3 조각", "large": "3~4 조각"},
        "tip": "양념 최대한 털어내고, 소량만!"
    },
    "cake": {
        "kr": "케이크",
        "safety": "DANGER",
        "benefits": [],
        "cautions": ["설탕 과다", "초콜릿/자일리톨 위험", "유제품 포함"],
        "forbidden": ["초콜릿 케이크", "자일리톨 함유 제품", "마카다미아/포도 장식"],
        "serving": {"small": "금지 권장", "medium": "금지 권장", "large": "금지 권장"},
        "tip": "급여 피할 것! 독성 재료 주의!"
    },
    "meatball": {
        "kr": "미트볼",
        "safety": "CAUTION",
        "benefits": ["단백질 공급"],
        "cautions": ["양념/소금 과다", "양파/마늘 함유 가능", "첨가물 확인"],
        "forbidden": ["양파/마늘이 들어간 미트볼", "소스가 많이 묻은 것"],
        "serving": {"small": "1/4개", "medium": "1/2개", "large": "1개"},
        "tip": "무양념 직접 만든 것만, 소량!"
    },
    "bacon": {
        "kr": "베이컨",
        "safety": "DANGER",
        "benefits": [],
        "cautions": ["소금 과다", "지방 과다", "아질산나트륨 함유"],
        "forbidden": ["모든 가공 베이컨", "훈제 제품"],
        "serving": {"small": "금지 권장", "medium": "금지 권장", "large": "금지 권장"},
        "tip": "급여 피할 것! 소금/지방 위험!"
    },
    "croissant": {
        "kr": "크루아상",
        "safety": "CAUTION",
        "benefits": [],
        "cautions": ["버터/지방 과다", "소금 함유", "소화 부담"],
        "forbidden": ["초콜릿 크루아상", "아몬드 크루아상"],
        "serving": {"small": "맛보기만", "medium": "1/4개", "large": "1/2개"},
        "tip": "플레인만, 극소량, 자주 주지 말 것!"
    },
    "doritos": {
        "kr": "도리토스",
        "safety": "DANGER",
        "benefits": [],
        "cautions": ["소금 과다", "양파/마늘 파우더", "인공 향료"],
        "forbidden": ["모든 맛 도리토스"],
        "serving": {"small": "금지", "medium": "금지", "large": "금지"},
        "tip": "절대 급여 금지! 양념 위험!"
    },
    "ritz": {
        "kr": "리츠",
        "safety": "CAUTION",
        "benefits": [],
        "cautions": ["소금 함유", "지방 함유", "영양가 낮음"],
        "forbidden": ["치즈맛/양념맛 리츠"],
        "serving": {"small": "1/2개", "medium": "1개", "large": "1~2개"},
        "tip": "오리지널만, 극소량, 간식으로 부적합!"
    },
    "skittles": {
        "kr": "스키틀즈",
        "safety": "FORBIDDEN",
        "benefits": [],
        "cautions": ["설탕 과다", "인공 색소", "자일리톨 가능성"],
        "forbidden": ["모든 스키틀즈 제품", "모든 사탕류"],
        "serving": {"small": "금지", "medium": "금지", "large": "금지"},
        "tip": "절대 금지! 설탕/첨가물 위험!"
    },
    "sprite": {
        "kr": "스프라이트",
        "safety": "DANGER",
        "benefits": [],
        "cautions": ["설탕 과다", "카페인 없지만 탄산 자극", "인공 감미료 가능"],
        "forbidden": ["모든 탄산음료"],
        "serving": {"small": "금지", "medium": "금지", "large": "금지"},
        "tip": "급여 금지! 설탕/탄산 위험!"
    },
    "raspberry": {
        "kr": "라즈베리",
        "safety": "SAFE",
        "benefits": ["항산화 성분 풍부", "비타민 C 함유", "식이섬유 풍부"],
        "cautions": ["소량만 급여", "씻어서 급여", "당분 주의"],
        "serving": {"small": "2~3알", "medium": "4~5알", "large": "6~8알"},
        "tip": "씻어서, 소량만!"
    },
    "asparagus": {
        "kr": "아스파라거스",
        "safety": "SAFE",
        "benefits": ["비타민 K 풍부", "식이섬유 함유", "저칼로리"],
        "cautions": ["익혀서 급여", "작게 잘라서", "양념 없이"],
        "serving": {"small": "1~2 조각", "medium": "2~3 조각", "large": "3~4 조각"},
        "tip": "익혀서, 작게 잘라서!"
    },
    "beet": {
        "kr": "비트",
        "safety": "SAFE",
        "benefits": ["항산화 성분", "철분 함유", "식이섬유 풍부"],
        "cautions": ["익혀서 급여", "소량부터 시작", "소변 색 변화 정상"],
        "serving": {"small": "1~2 조각", "medium": "2~3 조각", "large": "3~4 조각"},
        "tip": "익혀서, 소량씩! 소변 색 변해도 정상!"
    },
    "duck": {
        "kr": "오리고기",
        "safety": "SAFE",
        "benefits": ["고단백 저알레르기", "필수 아미노산 풍부", "피부/털 건강"],
        "cautions": ["뼈 제거 필수", "껍질 제거 권장", "익혀서 급여"],
        "serving": {"small": "30~40g", "medium": "50~70g", "large": "80~100g"},
        "tip": "뼈 빼고, 껍질 빼고, 익혀서!"
    },
}

def get_conclusion(safety: str) -> str:
    """안전도별 결론 문구"""
    conclusions = {
        "SAFE": "✅ 결론: 급여 가능합니다!🟢",
        "CAUTION": "⚠️ 결론: 주의가 필요합니다!🟡",
        "DANGER": "🚨 결론: 위험할 수 있습니다!🔴",
        "FORBIDDEN": "⛔ 결론: 절대 금지!🔴"
    }
    return conclusions.get(safety, conclusions["CAUTION"])

def generate_caption(food_id: str, data: dict) -> str:
    """캡션 생성 (파스타 스타일 v1)"""
    kr_name = data["kr"]
    safety = data["safety"]

    lines = []

    # 1. 결론
    lines.append(get_conclusion(safety))
    lines.append("")

    # 2. 급여 시 주의사항
    lines.append(f"{kr_name} 급여 시 주의사항")
    for item in data.get("cautions", [])[:5]:
        lines.append(f"• {item}")
    lines.append("")

    # 3. 절대 금지 (해당 시)
    if data.get("forbidden") and safety in ["CAUTION", "DANGER", "FORBIDDEN"]:
        lines.append("❌ 절대 금지")
        for item in data["forbidden"][:3]:
            lines.append(f"• {item}")
        lines.append("")

    # 4. 급여 방법 (FORBIDDEN 제외)
    if safety != "FORBIDDEN" and data["serving"]["small"] != "금지":
        lines.append("📏 급여 방법")
        lines.append(f"• 소형견: {data['serving']['small']}")
        lines.append(f"• 중형견: {data['serving']['medium']}")
        lines.append(f"• 대형견: {data['serving']['large']}")
        if safety in ["SAFE", "CAUTION"]:
            lines.append("※ 처음엔 소량으로 시작")
            lines.append("※ 알레르기 반응 확인")
        lines.append("")

    # 5. 핵심 메시지
    lines.append("📌 기억하세요")
    lines.append(f'"{data["tip"]}"')
    lines.append("")

    # 6. CTA
    lines.append("💾 저장해두고 주변에 공유하세요!")
    lines.append("건강한 간식 정보, 함께 나눠요 🐶")
    lines.append("")

    # 7. AI 고지
    lines.append("ℹ️ 일부 이미지는 AI로 생성되었습니다.")
    lines.append("ℹ️ Some images were generated by AI.")
    lines.append("")

    # 8. 해시태그
    hashtags = [
        f"#강아지{kr_name}", "#강아지간식", "#반려견음식", "#강아지건강",
        "#펫푸드", "#강아지케어", "#골든리트리버", "#시니어독",
        "#강아지정보", "#반려견가이드", "#펫스타그램", "#멍스타그램",
        "#dogfood", "#doghealth", "#petcare", "#goldensofinstagram"
    ]
    lines.append(" ".join(hashtags[:16]))

    return "\n".join(lines)

def generate_metadata(food_id: str, data: dict) -> dict:
    """메타데이터 생성"""
    return {
        "food_name_en": food_id,
        "food_name_kr": data["kr"],
        "safety_level": data["safety"],
        "status": "body_ready",
        "created_date": datetime.now().strftime("%Y-%m-%d"),
        "caption_version": "v1_pasta_style",
        "work_order": "WO-2026-0206-018"
    }

def main():
    body_ready_dir = PROJECT_ROOT / "contents" / "2_body_ready"

    results = {"success": [], "failed": []}

    # 우선순위: SAFE → CAUTION → DANGER → FORBIDDEN
    priority_order = ["SAFE", "CAUTION", "DANGER", "FORBIDDEN"]

    # 폴더 목록
    folders = sorted([f for f in body_ready_dir.iterdir() if f.is_dir() and not f.name.startswith('.')])

    # 안전도별 정렬
    def get_priority(folder):
        parts = folder.name.split('_')
        if len(parts) >= 2:
            food_id = parts[1]
            if food_id in FOOD_DATA:
                safety = FOOD_DATA[food_id]["safety"]
                return priority_order.index(safety) if safety in priority_order else 99
        return 99

    folders = sorted(folders, key=get_priority)

    print("=" * 70)
    print(f"🚀 WO-2026-0206-018: 캡션/메타데이터 일괄 생성")
    print(f"   대상: {len(folders)}건")
    print("=" * 70)

    for folder in folders:
        parts = folder.name.split('_')
        if len(parts) < 2:
            continue

        num = parts[0]
        food_id = parts[1]

        if food_id not in FOOD_DATA:
            print(f"  ⚠️ {num} {food_id}: 데이터 없음 - 건너뜀")
            results["failed"].append({"num": num, "food_id": food_id, "reason": "데이터 없음"})
            continue

        data = FOOD_DATA[food_id]
        safety = data["safety"]

        print(f"\n[{num}] {food_id} ({data['kr']}) - {safety}")

        try:
            # 캡션 생성
            caption = generate_caption(food_id, data)

            # caption_instagram.txt 저장
            caption_insta_path = folder / "caption_instagram.txt"
            with open(caption_insta_path, 'w', encoding='utf-8') as f:
                f.write(caption)
            print(f"  ✅ caption_instagram.txt")

            # caption_threads.txt 저장 (동일)
            caption_threads_path = folder / "caption_threads.txt"
            with open(caption_threads_path, 'w', encoding='utf-8') as f:
                f.write(caption)
            print(f"  ✅ caption_threads.txt")

            # 메타데이터 생성/업데이트
            metadata_path = folder / "metadata.json"
            metadata = generate_metadata(food_id, data)

            # 기존 메타데이터가 있으면 병합
            if metadata_path.exists():
                with open(metadata_path, 'r', encoding='utf-8') as f:
                    existing = json.load(f)
                existing.update(metadata)
                metadata = existing

            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, ensure_ascii=False, indent=2)
            print(f"  ✅ metadata.json")

            results["success"].append({"num": num, "food_id": food_id, "safety": safety})

        except Exception as e:
            print(f"  ❌ 에러: {e}")
            results["failed"].append({"num": num, "food_id": food_id, "reason": str(e)})

    # 결과 요약
    print(f"\n{'='*70}")
    print(f"📋 결과 요약")
    print(f"{'='*70}")
    print(f"  성공: {len(results['success'])}건")
    print(f"  실패: {len(results['failed'])}건")

    if results["failed"]:
        print(f"\n  실패 항목:")
        for item in results["failed"]:
            print(f"    - {item['num']} {item['food_id']}: {item['reason']}")

    return results

if __name__ == "__main__":
    main()
