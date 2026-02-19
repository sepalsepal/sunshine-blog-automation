#!/usr/bin/env python3
"""
블로그 007~020 캡션 재생성
BLOG_RULE v3.0 형식 적용
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CONTENTS_DIR = BASE_DIR / "01_contents"
FOOD_DATA_PATH = BASE_DIR / "config" / "food_data.json"

TARGET_RANGE = range(7, 21)

HOOKING_PATTERNS = {
    "SAFE": '"{name}", 강아지한테 줘도 될까? 🤔 한 번쯤 검색해본 적 있으시죠?',
    "CAUTION": '"{name}", 강아지한테 줘도 될까? 🤔 괜찮을 것 같으면서도 한 번 더 확인하고 싶은 음식이죠.',
    "DANGER": '"{name}", 강아지한테 줘도 될까? ⚠️ 알고 있는 것과 모르는 것, 그 차이가 우리 아이를 지킵니다.',
    "FORBIDDEN": '"{name}", 강아지한테 줘도 될까? 🚫 혹시 이미 줬더라도 괜찮아요. 몰랐다면 지금부터 알면 됩니다.'
}

CONCLUSION_EMOJI = {"SAFE": "✅", "CAUTION": "⚠️", "DANGER": "🚨", "FORBIDDEN": "🚫"}
CONCLUSION_TEXT = {"SAFE": "급여 가능!", "CAUTION": "조건부 급여 가능!", "DANGER": "급여 비권장!", "FORBIDDEN": "절대 급여 금지!"}

def load_food_data():
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def find_folder(num: int) -> Path:
    """01_contents/ 바로 아래에서 숫자로 시작하는 폴더 찾기"""
    for folder in CONTENTS_DIR.iterdir():
        if folder.is_dir() and folder.name.startswith(f"{num:03d}_"):
            return folder
    return None

def extract_nutrients(food_data: dict) -> list:
    nutrients = food_data.get("nutrients", [])
    result = []
    for n in nutrients[:5]:
        if isinstance(n, dict):
            result.append(n.get("name", ""))
    return [r for r in result if r] or ["비타민", "미네랄", "식이섬유"]

def extract_precautions(food_data: dict) -> list:
    precautions = food_data.get("precautions", [])
    result = []
    for p in precautions[:5]:
        if isinstance(p, dict):
            result.append(p.get("title", ""))
        elif isinstance(p, str):
            result.append(p)
    return [r for r in result if r] or ["과다 급여 주의", "알레르기 확인", "처음엔 소량으로"]

def generate_blog_caption(num: int, food_data: dict) -> str:
    name = food_data.get("name", f"음식{num}")
    safety = food_data.get("safety", "CAUTION")
    nutrients = extract_nutrients(food_data)
    precautions = extract_precautions(food_data)
    do_items = food_data.get("do_items", ["신선한 것으로 선택", "적정량 급여", "잘게 썰어서 제공", "반응 관찰하기", "간식으로만 활용"])
    dont_items = food_data.get("dont_items", ["과다 급여", "양념된 것 급여", "상한 것 급여", "통째로 급여", "주식으로 대체"])

    hooking = HOOKING_PATTERNS[safety].format(name=name)
    img1 = f"[이미지 1번: 햇살이와 {name}]"
    intro = f"안녕하세요, 햇살이네입니다! 🐕\n오늘은 많은 보호자분들이 궁금해하시는 '{name}' 급여에 대해 알아볼게요."
    img2 = f"[이미지 2번: {name} 음식 사진]"

    nutrient_text = ", ".join(nutrients[:5])
    nutrition_section = f"""📊 {name}의 영양 정보

{name}에는 {nutrient_text} 등이 풍부하게 들어있어요."""

    img3 = f"[이미지 3번: {name} 영양정보 인포그래픽]"

    emoji = CONCLUSION_EMOJI[safety]
    conclusion = CONCLUSION_TEXT[safety]

    if safety == "SAFE":
        verdict = f"""{emoji} 결론: {name}, 강아지 {conclusion}

{name}은 강아지에게 안전하게 급여할 수 있는 음식이에요."""
    elif safety == "CAUTION":
        verdict = f"""{emoji} 결론: {name}, 강아지 {conclusion}

{name}은 주의사항을 지키면 급여 가능한 음식이에요."""
    elif safety == "DANGER":
        verdict = f"""{emoji} 결론: {name}, 강아지 {conclusion}

{name}은 가급적 급여를 피하는 것이 좋아요. 위험 요소가 있습니다.

⚠️ 섭취 시 나타날 수 있는 증상:
• 구토, 설사
• 무기력, 식욕부진
• 복통, 떨림

🚨 응급 상황 시:
섭취 후 이상 증상이 보이면 즉시 동물병원을 방문하세요.

🔄 안전한 대체 식품:
사과, 당근, 블루베리 등 SAFE 등급 식품을 권장합니다."""
    else:
        verdict = f"""{emoji} 결론: {name}, 강아지 {conclusion}

{name}은 강아지에게 절대 급여해서는 안 되는 음식이에요!

⚠️ 섭취 시 나타날 수 있는 증상:
• 구토, 설사
• 무기력, 식욕부진
• 심한 경우 생명 위험

🚨 응급 상황 시:
즉시 동물병원에 연락하세요. 섭취량과 시간을 정확히 알려주세요.

🔄 안전한 대체 식품:
사과, 당근, 블루베리 등 SAFE 등급 식품을 급여해주세요."""

    img4 = f"[이미지 4번: {name} 급여 가능 여부 인포그래픽]"

    dosages = food_data.get("dosages", {})
    if safety not in ["FORBIDDEN", "DANGER"]:
        small = dosages.get("소형견", {}).get("amount", "소량")
        medium = dosages.get("중형견", {}).get("amount", "적당량")
        large = dosages.get("대형견", {}).get("amount", "적당량")
        xlarge = dosages.get("초대형견", {}).get("amount", large)
        dosage_section = f"""📏 체중별 하루 급여량

• 소형견(~7kg): {small}
• 중형견(7~15kg): {medium}
• 대형견(15~25kg): {large}
• 초대형견(25kg~): {xlarge}

※ 처음 급여 시에는 소량으로 시작해서 반응을 살펴주세요."""
    elif safety == "DANGER":
        dosage_section = """📏 급여량 안내

⚠️ 이 음식은 급여를 권장하지 않습니다.
불가피하게 급여해야 한다면 아주 극소량만, 그리고 반드시 수의사와 상담 후 결정하세요."""
    else:
        dosage_section = """⚠️ 급여량 안내

이 음식은 어떤 양이든 강아지에게 급여해서는 안 됩니다.
실수로 섭취했다면 즉시 동물병원을 방문해주세요."""

    img5 = f"[이미지 5번: {name} 급여량표 인포그래픽]"

    precaution_list = "\n".join(f"• {p}" for p in precautions[:5])
    precaution_section = f"""⚠️ 주의사항

{precaution_list}"""

    img6 = f"[이미지 6번: {name} 주의사항 인포그래픽]"

    if safety not in ["FORBIDDEN", "DANGER"]:
        do_text = "\n".join(f"✅ {d}" for d in do_items[:5])
        dont_text = "\n".join(f"❌ {d}" for d in dont_items[:5])
        do_dont_section = f"""✅ 이렇게 주세요
{do_text}

❌ 이렇게는 안 돼요
{dont_text}"""
    else:
        do_dont_section = """❌ 급여 금지

이 음식은 어떤 형태로든 강아지에게 급여해서는 안 됩니다."""

    img7 = f"[이미지 7번: {name} 조리방법 인포그래픽]"

    recipe = food_data.get("recipe", "")
    if safety not in ["FORBIDDEN", "DANGER"] and recipe:
        recipe_section = f"""👨‍🍳 강아지용 {name} 조리법

{recipe}"""
    elif safety not in ["FORBIDDEN", "DANGER"]:
        recipe_section = f"""👨‍🍳 강아지용 {name} 급여 팁

1. 신선한 {name}을 준비해요
2. 깨끗이 씻어주세요
3. 적당한 크기로 썰어주세요
4. 그대로 또는 살짝 익혀서 급여해요"""
    else:
        recipe_section = """⚠️ 조리법 없음

이 음식은 급여 금지/비권장 식품으로, 조리법을 제공하지 않습니다."""

    img8 = f"[이미지 8번: {name} FAQ 인포그래픽]"

    if safety == "SAFE":
        faq_section = f"""❓ 자주 묻는 질문

Q1. {name}을 매일 줘도 되나요?
A1. 간식으로 적당량이라면 괜찮아요. 단, 주식의 10%를 넘지 않게 해주세요.

Q2. {name} 껍질도 먹어도 되나요?
A2. 껍질에도 영양소가 있지만, 소화가 어려울 수 있어 제거 후 급여를 권장해요.

Q3. 강아지가 {name}을 싫어하면 어떡하나요?
A3. 기호성은 개체마다 달라요. 억지로 먹이지 말고 다른 간식을 시도해보세요.

Q4. {name}을 얼려서 줘도 되나요?
A4. 냉동 {name}도 괜찮지만, 이빨이 약한 아이는 해동 후 급여해주세요."""
    elif safety == "CAUTION":
        faq_section = f"""❓ 자주 묻는 질문

Q1. {name}을 처음 줄 때 주의할 점은?
A1. 아주 소량부터 시작해서 알레르기 반응이 없는지 확인해주세요.

Q2. {name}을 자주 줘도 되나요?
A2. 주 2-3회 정도가 적당해요. 너무 자주 주면 좋지 않아요.

Q3. {name}과 함께 주면 안 되는 음식이 있나요?
A3. 특별히 금기는 없지만, 한 번에 여러 새 음식을 주는 건 피해주세요.

Q4. 어린 강아지에게도 {name}을 줘도 되나요?
A4. 생후 6개월 이후, 소량부터 시작하는 것을 권장해요."""
    elif safety == "DANGER":
        faq_section = f"""❓ 자주 묻는 질문

Q1. 조금만 줘도 위험한가요?
A1. 소량이라도 건강에 영향을 줄 수 있어 급여를 피하는 것이 좋아요.

Q2. 실수로 먹었는데 어떡하나요?
A2. 섭취량을 파악하고, 이상 증상이 보이면 즉시 동물병원을 방문하세요.

Q3. 비슷한 대체 식품이 있나요?
A3. 수의사 선생님과 상담 후 안전한 대체 식품을 추천받으세요.

Q4. 왜 위험한 건가요?
A4. 강아지의 소화기관과 대사 체계가 사람과 달라 특정 성분이 해로울 수 있어요."""
    else:
        faq_section = f"""❓ 자주 묻는 질문

Q1. 정말 조금도 안 되나요?
A1. 네, 아주 소량이라도 중독 증상을 일으킬 수 있어 절대 급여 금지입니다.

Q2. 실수로 먹었어요, 어떡하나요?
A2. 즉시 동물병원에 연락하세요. 섭취량과 시간을 정확히 알려주세요.

Q3. 중독 증상은 어떤 게 있나요?
A3. 구토, 설사, 무기력, 식욕부진, 떨림 등이 나타날 수 있어요.

Q4. 안전한 대체 식품이 있나요?
A4. 사과, 당근, 블루베리 등 강아지에게 안전한 과일/채소를 급여해주세요."""

    img9 = f"[이미지 9번: 햇살이 마무리 이미지]"

    outro = """오늘도 우리 아이 건강 챙기는 보호자님들 응원합니다! 💕
궁금한 점은 댓글로 남겨주세요.

💬 우리 아이에게 맞는 급여량은 수의사 선생님과 상담하세요!"""

    hashtags = f"""#강아지{name} #개{name} #{name}급여 #강아지간식 #반려견영양 #강아지먹어도되는음식 #개먹어도되는음식 #반려견간식 #펫푸드 #강아지건강 #반려견건강 #개간식 #펫영양 #햇살이네 #강아지음식 #반려견음식"""

    caption = f"""{hooking}

{img1}

{intro}

{img2}

{nutrition_section}

{img3}

{verdict}

{img4}

{dosage_section}

{img5}

{precaution_section}

{img6}

{do_dont_section}

{img7}

{recipe_section}

{img8}

{faq_section}

{img9}

{outro}

{hashtags}"""

    return caption.strip()

def main():
    print("=" * 60)
    print("블로그 007~020 캡션 재생성")
    print("BLOG_RULE v3.0 형식 적용")
    print("=" * 60)

    food_data_all = load_food_data()
    success_count = 0

    for num in TARGET_RANGE:
        food_info = food_data_all.get(str(num))

        if not food_info:
            print(f"  ❌ {num:03d}: food_data 없음")
            continue

        folder = find_folder(num)
        if not folder:
            print(f"  ❌ {num:03d}: 폴더 없음")
            continue

        caption = generate_blog_caption(num, food_info)

        blog_dir = folder / "blog"
        blog_dir.mkdir(exist_ok=True)

        caption_path = blog_dir / "caption.txt"
        with open(caption_path, "w", encoding="utf-8") as f:
            f.write(caption)

        name = food_info.get("name", "")
        safety = food_info.get("safety", "")
        print(f"  ✅ {num:03d}_{name} ({safety}) - {len(caption)}자")
        success_count += 1

    print()
    print("=" * 60)
    print(f"===== 블로그 007~020 캡션 재생성 완료 =====")
    print("=" * 60)
    print()
    print(f"재생성 완료: {success_count}건")
    print("=" * 60)

if __name__ == "__main__":
    main()
