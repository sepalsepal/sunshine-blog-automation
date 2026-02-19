#!/usr/bin/env python3
"""
캡션 최종 재생성 스크립트
- 인스타: INSTAGRAM_RULE v1.1 (한영 병행, 3단계 급여량)
- 블로그: BLOG_RULE v3.0 (2000자 이상, 9개 이미지 마커)
- 쓰레드: THREADS_RULE v1.1 (영문 우선, 500자)

김부장 지시사항:
- food_data.json의 현재 safety 값을 파일명에 반영
- OLD 경로와 NEW 경로 모두에 저장
"""

import json
from pathlib import Path

BASE_DIR = Path(__file__).parent.parent
CONTENTS_DIR = BASE_DIR / "01_contents"
FOOD_DATA_PATH = BASE_DIR / "config" / "food_data.json"

# B안 감성 후킹 패턴 (한영 병행)
HOOKING_PATTERNS = {
    "SAFE": {
        "ko": '"{name}", 강아지한테 줘도 될까? 🤔 한 번쯤 검색해본 적 있으시죠?',
        "en": 'If you\'ve ever googled "can my dog eat {en_name}?" — you\'re a great pet parent.'
    },
    "CAUTION": {
        "ko": '"{name}", 강아지한테 줘도 될까? 🤔 괜찮을 것 같으면서도 한 번 더 확인하고 싶은 음식이죠.',
        "en": 'Most people think {en_name} is safe... but there\'s a catch.'
    },
    "DANGER": {
        "ko": '"{name}", 강아지한테 줘도 될까? ⚠️ 알고 있는 것과 모르는 것, 그 차이가 우리 아이를 지킵니다.',
        "en": 'What you know vs what you don\'t — it can protect your dog from the ER.'
    },
    "FORBIDDEN": {
        "ko": '"{name}", 강아지한테 줘도 될까? 🚫 혹시 이미 줬더라도 괜찮아요. 몰랐다면 지금부터 알면 됩니다.',
        "en": 'If you didn\'t know {en_name} is toxic to dogs, now you do. There\'s no safe amount.'
    }
}

CONCLUSION_EMOJI = {"SAFE": "✅", "CAUTION": "⚠️", "DANGER": "🚨", "FORBIDDEN": "🚫"}
CONCLUSION_TEXT_KO = {"SAFE": "급여 가능!", "CAUTION": "조건부 급여 가능!", "DANGER": "급여 비권장!", "FORBIDDEN": "절대 급여 금지!"}
CONCLUSION_TEXT_EN = {"SAFE": "Safe to feed!", "CAUTION": "Conditional feeding OK!", "DANGER": "Not recommended!", "FORBIDDEN": "Never feed!"}

def load_food_data():
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def find_folder(num: int) -> Path:
    for folder in CONTENTS_DIR.iterdir():
        if folder.is_dir() and folder.name.startswith(f"{num:03d}_"):
            return folder
    return None

def extract_nutrients(food_data: dict) -> list:
    nutrients = food_data.get("nutrients", [])
    result = []
    for n in nutrients[:5]:
        if isinstance(n, dict):
            name = n.get("name", "")
            benefit = n.get("benefit", "")
            if name and benefit:
                result.append({"name": name, "benefit": benefit})
    return result if result else [{"name": "영양소", "benefit": "건강 유지"}]

def extract_precautions(food_data: dict) -> list:
    precautions = food_data.get("precautions", [])
    result = []
    for p in precautions[:5]:
        if isinstance(p, dict):
            result.append(p.get("title", "주의 필요"))
        elif isinstance(p, str):
            result.append(p)
    return result if result else ["과다 급여 주의", "알레르기 확인", "처음엔 소량으로"]


# ============================================================
# 인스타그램 캡션 생성 (한영 병행)
# ============================================================
def generate_insta_caption(num: int, food_data: dict) -> str:
    name = food_data.get("name", f"음식{num}")
    en_name = food_data.get("english_name", name).split("_")[0].lower()
    safety = food_data.get("safety", "CAUTION")
    nutrients = extract_nutrients(food_data)
    precautions = extract_precautions(food_data)

    hooking_ko = HOOKING_PATTERNS[safety]["ko"].format(name=name, en_name=en_name)
    hooking_en = HOOKING_PATTERNS[safety]["en"].format(name=name, en_name=en_name)
    hooking = f"{hooking_ko}\n{hooking_en}"

    # 급여량 (3단계)
    dosages = food_data.get("dosages", {})
    if safety == "FORBIDDEN":
        dosage_text = """
📏 급여량 Serving Size
⚠️ 급여 금지 / Do NOT feed"""
    else:
        small = dosages.get("소형견", {}).get("amount", "소량")
        medium = dosages.get("중형견", {}).get("amount", "적당량")
        large = dosages.get("대형견", {}).get("amount", "적당량")
        dosage_text = f"""
📏 급여량 Serving Size
• 소형견 Small (~7kg): {small}
• 중형견 Medium (7~15kg): {medium}
• 대형견 Large (15kg+): {large}"""

    # 장점/주의사항
    if safety == "FORBIDDEN":
        info = f"""
❌ 급여 불가 이유 Why NOT
{chr(10).join(f"• {p}" for p in precautions[:3])}

⚠️ 섭취 시 증상 Symptoms
• 구토, 설사, 무기력 Vomiting, diarrhea, lethargy
• 증상 발견 시 즉시 동물병원 See a vet immediately"""
    else:
        benefit_text = "\n".join(f"• {n['name']} - {n['benefit']}" for n in nutrients[:3])
        precaution_text = "\n".join(f"• {p}" for p in precautions[:3])
        info = f"""
🍎 급여 시 장점 Benefits
{benefit_text}

⚠️ 주의사항 Caution
{precaution_text}"""

    emoji = CONCLUSION_EMOJI[safety]
    conclusion_ko = CONCLUSION_TEXT_KO[safety]
    conclusion_en = CONCLUSION_TEXT_EN[safety]
    conclusion = f"{emoji} 결론: {name}, {conclusion_ko}\n{emoji} Conclusion: {en_name.capitalize()}, {conclusion_en}"

    vet_text = "\n💬 우리 아이에게 맞는 급여량은 수의사 선생님과 상담하세요!\n💬 Consult your vet for the right serving size for your dog!"

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


# ============================================================
# 블로그 캡션 생성 (2000자 이상)
# ============================================================
def generate_blog_caption(num: int, food_data: dict) -> str:
    name = food_data.get("name", f"음식{num}")
    en_name = food_data.get("english_name", name).split("_")[0]
    safety = food_data.get("safety", "CAUTION")
    nutrients = extract_nutrients(food_data)
    precautions = extract_precautions(food_data)
    do_items = food_data.get("do_items", ["신선한 것으로 선택", "적정량 급여", "잘게 썰어서 제공", "반응 관찰하기", "간식으로만 활용"])
    dont_items = food_data.get("dont_items", ["과다 급여", "양념된 것 급여", "상한 것 급여", "통째로 급여", "주식으로 대체"])

    hooking = HOOKING_PATTERNS[safety]["ko"].format(name=name, en_name=en_name)

    # 이미지 마커들
    img1 = f"[이미지 1번: 햇살이와 {name}]"
    img2 = f"[이미지 2번: {name} 음식 사진]"
    img3 = f"[이미지 3번: {name} 영양정보 인포그래픽]"
    img4 = f"[이미지 4번: {name} 급여 가능 여부 인포그래픽]"
    img5 = f"[이미지 5번: {name} 급여량표 인포그래픽]"
    img6 = f"[이미지 6번: {name} 주의사항 인포그래픽]"
    img7 = f"[이미지 7번: {name} 조리방법 인포그래픽]"
    img8 = f"[이미지 8번: {name} FAQ 인포그래픽]"
    img9 = f"[이미지 9번: 햇살이 마무리 이미지]"

    intro = f"""안녕하세요, 햇살이네입니다! 🐕
오늘은 많은 보호자분들이 궁금해하시는 '{name}' 급여에 대해 알아볼게요.
11살 골든리트리버 햇살이를 키우면서 얻은 경험과 수의사 선생님의 조언을 바탕으로 정리했습니다."""

    # 영양 정보
    nutrient_text = ", ".join(n["name"] for n in nutrients[:5])
    nutrient_detail = "\n".join(f"• {n['name']}: {n['benefit']}" for n in nutrients[:5])
    nutrition_section = f"""📊 {name}의 영양 정보

{name}에는 {nutrient_text} 등이 풍부하게 들어있어요.

{nutrient_detail}

이러한 영양소들이 강아지의 건강 유지에 도움을 줄 수 있습니다."""

    # 결론 섹션 (safety별 상세)
    emoji = CONCLUSION_EMOJI[safety]
    conclusion = CONCLUSION_TEXT_KO[safety]

    if safety == "SAFE":
        verdict = f"""{emoji} 결론: {name}, 강아지 {conclusion}

{name}은 강아지에게 안전하게 급여할 수 있는 음식이에요.
적정량을 지켜서 간식으로 활용하시면 좋습니다.
처음 급여할 때는 소량부터 시작해서 알레르기 반응이 없는지 확인해주세요."""

    elif safety == "CAUTION":
        verdict = f"""{emoji} 결론: {name}, 강아지 {conclusion}

{name}은 주의사항을 지키면 급여 가능한 음식이에요.
아래 주의사항을 꼭 확인하시고, 적정량을 지켜주세요.
처음 급여할 때는 극소량부터 시작하는 것을 권장합니다."""

    elif safety == "DANGER":
        verdict = f"""{emoji} 결론: {name}, 강아지 {conclusion}

{name}은 가급적 급여를 피하는 것이 좋아요. 위험 요소가 있습니다.

⚠️ 섭취 시 나타날 수 있는 증상:
• 구토, 설사
• 무기력, 식욕부진
• 복통, 떨림
• 심한 경우 탈수나 쇼크

🚨 응급 상황 시:
섭취 후 이상 증상이 보이면 즉시 동물병원을 방문하세요.
섭취량과 시간을 정확히 기록해두면 진료에 도움이 됩니다.

🔄 안전한 대체 식품:
사과, 당근, 블루베리, 고구마 등 SAFE 등급 식품을 권장합니다."""

    else:  # FORBIDDEN
        verdict = f"""{emoji} 결론: {name}, 강아지 {conclusion}

{name}은 강아지에게 절대 급여해서는 안 되는 음식이에요!
아주 소량이라도 중독 증상을 일으킬 수 있습니다.

⚠️ 섭취 시 나타날 수 있는 증상:
• 구토, 설사
• 무기력, 식욕부진
• 심한 경우 생명 위험
• 신경계 이상, 경련

🚨 응급 상황 시:
즉시 동물병원에 연락하세요. 섭취량과 시간을 정확히 알려주세요.
자가 유도 구토는 위험할 수 있으니 수의사 지시를 따르세요.

🔄 안전한 대체 식품:
사과, 당근, 블루베리, 수박 등 SAFE 등급 식품을 급여해주세요."""

    # 급여량 섹션
    dosages = food_data.get("dosages", {})
    if safety not in ["FORBIDDEN", "DANGER"]:
        small = dosages.get("소형견", {}).get("amount", "소량")
        small_desc = dosages.get("소형견", {}).get("desc", "")
        medium = dosages.get("중형견", {}).get("amount", "적당량")
        medium_desc = dosages.get("중형견", {}).get("desc", "")
        large = dosages.get("대형견", {}).get("amount", "적당량")
        large_desc = dosages.get("대형견", {}).get("desc", "")
        xlarge = dosages.get("초대형견", {}).get("amount", large)
        xlarge_desc = dosages.get("초대형견", {}).get("desc", "")

        dosage_section = f"""📏 체중별 하루 급여량

• 소형견(~7kg): {small} {f'({small_desc})' if small_desc else ''}
• 중형견(7~15kg): {medium} {f'({medium_desc})' if medium_desc else ''}
• 대형견(15~25kg): {large} {f'({large_desc})' if large_desc else ''}
• 초대형견(25kg~): {xlarge} {f'({xlarge_desc})' if xlarge_desc else ''}

※ 처음 급여 시에는 소량으로 시작해서 반응을 살펴주세요.
※ 하루 칼로리의 10%를 넘지 않도록 해주세요.
※ 간식은 주식을 대체할 수 없습니다."""
    elif safety == "DANGER":
        dosage_section = """📏 급여량 안내

⚠️ 이 음식은 급여를 권장하지 않습니다.
불가피하게 급여해야 한다면 아주 극소량만, 그리고 반드시 수의사와 상담 후 결정하세요.
가능하다면 안전한 대체 식품을 선택하는 것이 좋습니다."""
    else:
        dosage_section = """⚠️ 급여량 안내

이 음식은 어떤 양이든 강아지에게 급여해서는 안 됩니다.
실수로 섭취했다면 즉시 동물병원을 방문해주세요.
섭취량에 관계없이 위험할 수 있습니다."""

    # 주의사항 섹션
    precaution_list = "\n".join(f"• {p}" for p in precautions[:5])
    precaution_section = f"""⚠️ 주의사항

{precaution_list}

위 사항들을 꼭 지켜주세요. 강아지마다 개체 차이가 있으므로
처음 급여 시에는 반드시 소량부터 시작하고 반응을 관찰해주세요."""

    # DO/DON'T 섹션
    if safety not in ["FORBIDDEN", "DANGER"]:
        do_text = "\n".join(f"✅ {d}" for d in do_items[:5])
        dont_text = "\n".join(f"❌ {d}" for d in dont_items[:5])
        do_dont_section = f"""✅ 이렇게 주세요
{do_text}

❌ 이렇게는 안 돼요
{dont_text}"""
    else:
        do_dont_section = """❌ 급여 금지

이 음식은 어떤 형태로든 강아지에게 급여해서는 안 됩니다.
조리법, 가공 여부에 관계없이 위험합니다."""

    # 레시피/조리법 섹션
    recipe = food_data.get("recipe", "")
    if safety not in ["FORBIDDEN", "DANGER"] and recipe:
        recipe_section = f"""👨‍🍳 강아지용 {name} 조리법

{recipe}

TIP: 양념이나 소금은 절대 넣지 마세요!"""
    elif safety not in ["FORBIDDEN", "DANGER"]:
        recipe_section = f"""👨‍🍳 강아지용 {name} 급여 팁

1. 신선한 {name}을 준비해요
2. 깨끗이 씻어주세요
3. 적당한 크기로 썰어주세요 (기도 막힘 방지)
4. 그대로 또는 살짝 익혀서 급여해요
5. 양념이나 소금은 절대 넣지 마세요

TIP: 냉동 보관했다면 완전히 해동 후 급여하세요!"""
    else:
        recipe_section = """⚠️ 조리법 없음

이 음식은 급여 금지/비권장 식품으로, 조리법을 제공하지 않습니다.
안전한 대체 식품을 선택해주세요."""

    # FAQ 섹션
    if safety == "SAFE":
        faq_section = f"""❓ 자주 묻는 질문

Q1. {name}을 매일 줘도 되나요?
A1. 간식으로 적당량이라면 괜찮아요. 단, 주식의 10%를 넘지 않게 해주세요. 다양한 간식을 로테이션하는 것이 좋습니다.

Q2. {name} 껍질도 먹어도 되나요?
A2. 껍질에도 영양소가 있지만, 소화가 어려울 수 있어 제거 후 급여를 권장해요. 특히 어린 강아지나 시니어 강아지는 껍질 없이 주세요.

Q3. 강아지가 {name}을 싫어하면 어떡하나요?
A3. 기호성은 개체마다 달라요. 억지로 먹이지 말고 다른 간식을 시도해보세요. 다른 SAFE 등급 음식도 많습니다.

Q4. {name}을 얼려서 줘도 되나요?
A4. 냉동 {name}도 괜찮지만, 이빨이 약한 아이는 해동 후 급여해주세요. 너무 차가우면 소화에 부담이 될 수 있어요.

Q5. 처음 주는데 얼마나 줘야 하나요?
A5. 처음에는 권장량의 절반 이하로 시작하세요. 24시간 관찰 후 이상이 없으면 점차 늘려도 됩니다."""

    elif safety == "CAUTION":
        faq_section = f"""❓ 자주 묻는 질문

Q1. {name}을 처음 줄 때 주의할 점은?
A1. 아주 소량부터 시작해서 알레르기 반응이 없는지 확인해주세요. 24시간 이상 관찰 후 이상이 없으면 조금씩 늘려도 됩니다.

Q2. {name}을 자주 줘도 되나요?
A2. 주 2-3회 정도가 적당해요. 너무 자주 주면 특정 영양소 과다 섭취가 될 수 있어요. 다른 간식과 로테이션하세요.

Q3. {name}과 함께 주면 안 되는 음식이 있나요?
A3. 특별히 금기는 없지만, 한 번에 여러 새 음식을 주는 건 피해주세요. 알레르기 원인 파악이 어려워집니다.

Q4. 어린 강아지에게도 {name}을 줘도 되나요?
A4. 생후 6개월 이후, 소량부터 시작하는 것을 권장해요. 어린 강아지는 소화 기관이 약하므로 더 주의가 필요합니다.

Q5. 먹고 나서 설사를 해요.
A5. 급여량을 줄이거나 중단하세요. 지속되면 수의사 상담을 권장합니다. 개체 차이로 맞지 않을 수 있어요."""

    elif safety == "DANGER":
        faq_section = f"""❓ 자주 묻는 질문

Q1. 조금만 줘도 위험한가요?
A1. 소량이라도 건강에 영향을 줄 수 있어 급여를 피하는 것이 좋아요. 안전한 대체 식품을 선택하세요.

Q2. 실수로 먹었는데 어떡하나요?
A2. 섭취량을 파악하고, 이상 증상이 보이면 즉시 동물병원을 방문하세요. 섭취 시간과 양을 정확히 기록해두세요.

Q3. 비슷한 대체 식품이 있나요?
A3. 수의사 선생님과 상담 후 안전한 대체 식품을 추천받으세요. SAFE 등급의 과일/채소가 많습니다.

Q4. 왜 위험한 건가요?
A4. 강아지의 소화기관과 대사 체계가 사람과 달라 특정 성분이 해로울 수 있어요. 자세한 내용은 위 본문을 참고하세요.

Q5. 증상이 얼마 후에 나타나나요?
A5. 음식에 따라 다르지만, 보통 섭취 후 1-6시간 내에 증상이 나타날 수 있어요. 24시간 관찰을 권장합니다."""

    else:  # FORBIDDEN
        faq_section = f"""❓ 자주 묻는 질문

Q1. 정말 조금도 안 되나요?
A1. 네, 아주 소량이라도 중독 증상을 일으킬 수 있어 절대 급여 금지입니다. 체중 대비 소량도 위험합니다.

Q2. 실수로 먹었어요, 어떡하나요?
A2. 즉시 동물병원에 연락하세요. 섭취량과 시간을 정확히 알려주세요. 자가 유도 구토는 위험할 수 있습니다.

Q3. 중독 증상은 어떤 게 있나요?
A3. 구토, 설사, 무기력, 식욕부진, 떨림 등이 나타날 수 있어요. 심한 경우 경련, 호흡 곤란도 발생합니다.

Q4. 안전한 대체 식품이 있나요?
A4. 사과, 당근, 블루베리, 수박 등 강아지에게 안전한 과일/채소를 급여해주세요. SAFE 등급 식품을 확인하세요.

Q5. 조리하면 괜찮나요?
A5. 아니요, 조리 여부와 관계없이 위험합니다. 어떤 형태로든 급여하지 마세요."""

    # 마무리
    outro = f"""오늘도 우리 아이 건강 챙기는 보호자님들 응원합니다! 💕
궁금한 점은 댓글로 남겨주세요.

💬 우리 아이에게 맞는 급여량은 수의사 선생님과 상담하세요!
💬 이 글이 도움이 되셨다면 저장하고 공유해주세요!

햇살이와 함께하는 11년, 앞으로도 건강한 정보로 찾아뵐게요. 🐾"""

    hashtags = f"#강아지{name} #개{name} #{name}급여 #강아지간식 #반려견영양 #강아지먹어도되는음식 #개먹어도되는음식 #반려견간식 #펫푸드 #강아지건강 #반려견건강 #개간식 #펫영양 #햇살이네 #강아지음식 #반려견음식"

    # 전체 조립
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


# ============================================================
# 쓰레드 캡션 생성 (영문 우선, 500자)
# ============================================================
def generate_thread_caption(num: int, food_data: dict) -> str:
    name = food_data.get("name", f"음식{num}")
    en_name = food_data.get("english_name", name).split("_")[0]
    safety = food_data.get("safety", "CAUTION")

    # 영문 후킹
    hooking_templates = {
        "SAFE": f'If you\'ve ever googled "can my dog eat {en_name}?" — you\'re a great pet parent. 🐾',
        "CAUTION": f'Most people think {en_name} is safe for dogs... but there\'s a catch. ⚠️',
        "DANGER": f'{en_name} could send your dog to the ER. What you know vs don\'t — it matters. 🚨',
        "FORBIDDEN": f'If you didn\'t know {en_name} can poison your dog, now you do. There\'s no safe amount. 🚫'
    }

    verdict_templates = {
        "SAFE": f"✅ {en_name.capitalize()}: Safe for dogs! Feed in moderation.",
        "CAUTION": f"⚠️ {en_name.capitalize()}: Conditional OK. Check precautions first.",
        "DANGER": f"🚨 {en_name.capitalize()}: Not recommended. Risky for dogs.",
        "FORBIDDEN": f"🚫 {en_name.capitalize()}: NEVER feed. Toxic to dogs."
    }

    hooking = hooking_templates[safety]
    verdict = verdict_templates[safety]

    caption = f"""{hooking}

{verdict}

💬 Always consult your vet!
Save & share to help other pet parents!

#CanMyDogEat{en_name.replace(' ', '')} #DogFood #PetNutrition #DogHealth #PetCare #GoldenRetriever #SeniorDog #DogTreats #PetSafety #HaetsalFoodLab"""

    return caption.strip()


# ============================================================
# 메인 실행
# ============================================================
def save_caption(folder: Path, platform: str, caption: str, name: str, en_name: str, safety: str):
    """캡션 저장 (NEW 경로 + OLD 경로)"""

    # NEW 경로
    new_dir = folder / platform
    new_dir.mkdir(exist_ok=True)
    new_path = new_dir / "caption.txt"
    with open(new_path, "w", encoding="utf-8") as f:
        f.write(caption)

    # OLD 경로 (김부장 조건: 파일명에 safety 반영)
    if platform == "insta":
        old_dir = folder / "01_Insta&Thread"
        old_dir.mkdir(exist_ok=True)
        old_filename = f"{en_name}_{safety}_Insta_Caption.txt"
    elif platform == "blog":
        old_dir = folder / "02_Blog"
        old_dir.mkdir(exist_ok=True)
        old_filename = f"{en_name}_{safety}_Blog_Caption.txt"
    elif platform == "thread":
        old_dir = folder / "01_Insta&Thread"
        old_dir.mkdir(exist_ok=True)
        old_filename = f"{en_name}_{safety}_Threads_Caption.txt"
    else:
        return

    old_path = old_dir / old_filename
    with open(old_path, "w", encoding="utf-8") as f:
        f.write(caption)


def main():
    # 대상 목록: 원래 29건 FAIL + Blog 007~020 추가
    insta_targets = [21, 22, 23, 24, 25, 26, 27, 28, 29, 34, 100, 138, 144, 157, 161, 162, 171]
    blog_targets = [7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 90, 138, 144, 157, 161, 162, 163, 164, 165, 168, 169, 171]
    thread_targets = []  # 쓰레드는 전부 PASS

    all_targets = sorted(set(insta_targets + blog_targets))

    print("=" * 60)
    print("캡션 최종 재생성")
    print("김부장 지시: 파일명에 safety 반영, OLD+NEW 경로 모두 저장")
    print("=" * 60)

    food_data_all = load_food_data()

    success_insta = 0
    success_blog = 0

    for num in all_targets:
        food_info = food_data_all.get(str(num))
        if not food_info:
            print(f"  ❌ {num:03d}: food_data 없음")
            continue

        folder = find_folder(num)
        if not folder:
            print(f"  ❌ {num:03d}: 폴더 없음")
            continue

        name = food_info.get("name", "")
        en_name = food_info.get("english_name", name).split("_")[0]
        safety = food_info.get("safety", "CAUTION")

        results = []

        # 인스타
        if num in insta_targets:
            caption = generate_insta_caption(num, food_info)
            save_caption(folder, "insta", caption, name, en_name, safety)
            results.append(f"Insta({len(caption)}자)")
            success_insta += 1

        # 블로그
        if num in blog_targets:
            caption = generate_blog_caption(num, food_info)
            save_caption(folder, "blog", caption, name, en_name, safety)
            results.append(f"Blog({len(caption)}자)")
            success_blog += 1

        print(f"  ✅ {num:03d}_{name} ({safety}) - {', '.join(results)}")

    print()
    print("=" * 60)
    print(f"완료: 인스타 {success_insta}건, 블로그 {success_blog}건")
    print("=" * 60)


if __name__ == "__main__":
    main()
