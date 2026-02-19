#!/usr/bin/env python3
"""
인스타그램 FAIL 17건 재생성
INSTAGRAM_RULE v1.1 형식 적용
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CONTENTS_DIR = BASE_DIR / "01_contents"
FOOD_DATA_PATH = BASE_DIR / "config" / "food_data.json"

# FAIL 대상 목록
FAIL_TARGETS = [
    21, 22, 23, 24, 25, 26, 27, 28, 29, 34,  # v1.0 형식
    100, 138, 144, 157, 161, 162, 171  # 안전도 감지 불일치
]

# B안 감성 후킹 패턴
HOOKING_PATTERNS = {
    "SAFE": '"{name}", 강아지한테 줘도 될까? 🤔 한 번쯤 검색해본 적 있으시죠?',
    "CAUTION": '"{name}", 강아지한테 줘도 될까? 🤔 괜찮을 것 같으면서도 한 번 더 확인하고 싶은 음식이죠.',
    "DANGER": '"{name}", 강아지한테 줘도 될까? ⚠️ 알고 있는 것과 모르는 것, 그 차이가 우리 아이를 지킵니다.',
    "FORBIDDEN": '"{name}", 강아지한테 줘도 될까? 🚫 혹시 이미 줬더라도 괜찮아요. 몰랐다면 지금부터 알면 됩니다.'
}

CONCLUSIONS = {
    "SAFE": "✅ 결론: {name}, 강아지 급여 가능!",
    "CAUTION": "⚠️ 결론: {name}, 조건부 급여 가능!",
    "DANGER": "🚨 결론: {name}, 급여 비권장!",
    "FORBIDDEN": "🚫 결론: {name}, 절대 급여 금지!"
}

def load_food_data():
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def find_folder(num: int) -> Path:
    """01_contents/ 바로 아래에서 숫자로 시작하는 폴더 찾기"""
    for folder in CONTENTS_DIR.iterdir():
        if folder.is_dir() and folder.name.startswith(f"{num:03d}_"):
            return folder
    return None

def get_dosage_text(safety: str, food_data: dict) -> str:
    """3단계 급여량 (소형/중형/대형)"""
    if safety == "FORBIDDEN":
        return ""

    dosages = food_data.get("dosages", {})
    small = dosages.get("소형견", {}).get("amount", "소량")
    medium = dosages.get("중형견", {}).get("amount", "적당량")
    large = dosages.get("대형견", {}).get("amount", "적당량")

    return f"""
📏 체중별 하루 급여량
• 소형견(~7kg): {small}
• 중형견(7~15kg): {medium}
• 대형견(15kg~): {large}"""

def extract_benefits(food_data: dict) -> list:
    """nutrients에서 benefit 추출"""
    nutrients = food_data.get("nutrients", [])
    benefits = []
    for n in nutrients[:3]:
        if isinstance(n, dict):
            name = n.get("name", "")
            benefit = n.get("benefit", "")
            if name and benefit:
                benefits.append(f"{name} - {benefit}")
    return benefits if benefits else ["영양 보충에 도움"]

def extract_precautions(food_data: dict) -> list:
    """precautions에서 title 추출"""
    precautions = food_data.get("precautions", [])
    result = []
    for p in precautions[:3]:
        if isinstance(p, dict):
            result.append(p.get("title", "주의 필요"))
        elif isinstance(p, str):
            result.append(p)
    return result if result else ["과다 급여 주의"]

def generate_insta_caption(num: int, food_data: dict) -> str:
    name = food_data.get("name", f"음식{num}")
    safety = food_data.get("safety", "CAUTION")
    benefits = extract_benefits(food_data)
    precautions = extract_precautions(food_data)

    hooking = HOOKING_PATTERNS[safety].format(name=name)

    if safety == "FORBIDDEN":
        info = f"""
❌ 급여 불가 이유
{chr(10).join(f"• {p}" for p in precautions[:3])}

⚠️ 섭취 시 증상
• 구토, 설사, 무기력
• 증상 발견 시 즉시 동물병원 방문"""
    else:
        benefit_text = "\n".join(f"• {b}" for b in benefits[:3])
        precaution_text = "\n".join(f"• {p}" for p in precautions[:3])

        info = f"""
🍎 급여 시 장점
{benefit_text}

⚠️ 주의사항
{precaution_text}"""

    dosage_text = get_dosage_text(safety, food_data)
    conclusion = CONCLUSIONS[safety].format(name=name)
    vet_text = "\n\n💬 우리 아이에게 맞는 급여량은 수의사 선생님과 상담하세요!"

    hashtags = f"""
#강아지{name} #개{name} #{name}급여 #강아지간식 #반려견영양
#강아지먹어도되는음식 #개먹어도되는음식 #반려견간식 #펫푸드
#강아지건강 #반려견건강 #개간식 #펫영양 #햇살이네 #강아지정보"""

    caption = f"""{hooking}
{info}
{dosage_text}

{conclusion}
{vet_text}
{hashtags}"""

    return caption.strip()

def main():
    print("=" * 60)
    print("인스타그램 FAIL 17건 재생성")
    print("INSTAGRAM_RULE v1.1 형식 적용")
    print("=" * 60)

    food_data_all = load_food_data()
    success_count = 0

    for num in FAIL_TARGETS:
        food_info = food_data_all.get(str(num))

        if not food_info:
            print(f"  ❌ {num:03d}: food_data 없음")
            continue

        folder = find_folder(num)
        if not folder:
            print(f"  ❌ {num:03d}: 폴더 없음")
            continue

        caption = generate_insta_caption(num, food_info)

        insta_dir = folder / "insta"
        insta_dir.mkdir(exist_ok=True)

        caption_path = insta_dir / "caption.txt"
        with open(caption_path, "w", encoding="utf-8") as f:
            f.write(caption)

        name = food_info.get("name", "")
        safety = food_info.get("safety", "")
        print(f"  ✅ {num:03d}_{name} ({safety}) - {len(caption)}자")
        success_count += 1

    print()
    print("=" * 60)
    print(f"===== 인스타그램 FAIL 17건 재생성 완료 =====")
    print("=" * 60)
    print()
    print(f"재생성 완료: {success_count}건")
    print("=" * 60)

if __name__ == "__main__":
    main()
