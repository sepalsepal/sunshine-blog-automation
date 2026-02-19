#!/usr/bin/env python3
"""
블로그 캡션 배치 재생성 v2
글자수 1,620~1,980 범위 맞춤
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"

HOOKING = {
    "SAFE": '"이거 줘도 되나?" 검색해본 적 있다면, 당신은 좋은 보호자예요.',
    "CAUTION": "사랑하니까 한 번 더 확인하는 거예요.",
    "DANGER": "알고 있는 것과 모르는 것, 그 차이가 우리 아이를 지켜요.",
    "FORBIDDEN": "몰랐다면 괜찮아요. 지금 알았으니까요."
}

EMOJI = {"SAFE": "🟢", "CAUTION": "🟡", "DANGER": "🟠", "FORBIDDEN": "⛔"}

def load_food_data():
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_folder(num: int) -> Path:
    pattern = f"{num:03d}_*"
    matches = list(CONTENTS_DIR.glob(pattern))
    return matches[0] if matches else None

def generate_safe_caution(food: dict, safety: str) -> str:
    name = food["name"]
    emoji = EMOJI[safety]
    hooking = HOOKING[safety]

    nutrients = food.get("nutrients", [])[:4]
    nut_lines = [f"• {n['name']}: {n['benefit']}" for n in nutrients]

    dosages = food.get("dosages", {})
    dos_lines = []
    for s in ["소형견", "중형견", "대형견", "초대형견"]:
        if s in dosages:
            d = dosages[s]
            dos_lines.append(f"• {s}({d['weight']}): {d['amount']}")

    precautions = food.get("precautions", [])[:3]
    pre_lines = [f"• {p['title']}" for p in precautions]

    do_items = food.get("do_items", [])[:4]
    dont_items = food.get("dont_items", [])[:4]

    cooking_steps = food.get("cooking_steps", [])[:4]
    cook_lines = [f"{i}. {s['title']}" for i, s in enumerate(cooking_steps, 1)]

    caution_note = "⚠️ 주 1~2회로 횟수를 제한해주세요.\n" if safety == "CAUTION" else ""

    return f'''"{name}", 강아지한테 줘도 될까? 🤔 {hooking}

[이미지 1번: 햇살이와 {name} 표지]

안녕하세요, 햇살이네입니다! 🐕
오늘은 '{name}' 급여에 대해 알아볼게요.
11살 골든리트리버 햇살이를 키우면서 얻은 경험을 바탕으로 정리했습니다.

[이미지 2번: {name} 음식 사진]

## 🍽️ {name}, 강아지에게 어떤 음식일까요?

{name}은 보호자분들이 급여 가능 여부를 궁금해하는 음식이에요.

[이미지 3번: 햇살이와 {name} 함께]

## 📊 {name}의 영양 정보

{chr(10).join(nut_lines)}

[이미지 4번: {name} 영양정보 인포그래픽]

## {emoji} 결론: {name}, 조건부 급여 가능!

주의사항을 지키면 급여 가능해요. 처음엔 소량부터 시작하세요.

✅ 이렇게 주세요
{chr(10).join(["• " + item for item in do_items])}

❌ 이렇게는 안 돼요
{chr(10).join(["• " + item for item in dont_items])}

[이미지 5번: {name} 급여가능/불가 인포그래픽]

## 📏 체중별 급여량

{chr(10).join(dos_lines)}

{caution_note}※ 하루 칼로리의 10% 이내로 급여해주세요.

[이미지 6번: {name} 급여량표 인포그래픽]

## ⚠️ 주의사항

{chr(10).join(pre_lines)}

개체 차이가 있으니 소량부터 시작하고 반응을 관찰하세요.

[이미지 7번: {name} 주의사항 인포그래픽]

## 👨‍🍳 급여 방법

{chr(10).join(cook_lines)}

[이미지 8번: {name} 조리방법 인포그래픽]

## ❓ 자주 묻는 질문

Q1. 처음 줄 때 주의할 점은?
A1. 소량부터 시작해서 알레르기 반응 확인하세요.

Q2. 자주 줘도 되나요?
A2. 주 2~3회가 적당해요.

[이미지 9번: 햇살이 마무리 CTA 이미지]

오늘도 우리 아이 건강 챙기는 보호자님들 응원합니다! 💕

💬 급여량은 수의사 선생님과 상담하세요!

#강아지{name} #{name}급여 #강아지간식 #반려견영양 #강아지먹어도되는음식 #반려견간식 #강아지건강 #반려견건강 #펫영양 #햇살이네 #강아지음식 #반려견음식
'''.strip()


def generate_danger(food: dict) -> str:
    name = food["name"]
    hooking = HOOKING["DANGER"]

    toxicity = food.get("toxicity", [{"name": "특정 성분", "effect": "소화 문제"}])[:2]
    tox_lines = [f"• {t.get('name', '성분')}: {t.get('effect', '위험')}" for t in toxicity]

    symptoms = food.get("symptoms", ["구토", "설사", "무기력"])[:4]
    sym_lines = [f"• {s}" for s in symptoms]

    alternatives = food.get("alternatives", ["수의사 상담 후 대안 선택"])[:2]
    alt_lines = [f"• {a}" for a in alternatives]

    return f'''"{name}", 강아지한테 줘도 될까? 🤔 {hooking}

[이미지 1번: 햇살이와 {name} 표지]

안녕하세요, 햇살이네입니다! 🐕
오늘은 '{name}' 급여에 대해 알아볼게요.

[이미지 2번: {name} 음식 사진]

## ⚠️ {name}, 왜 위험할까요?

{name}은 강아지에게 권장하지 않는 음식이에요.

[이미지 3번: 햇살이와 {name} 함께]

## 🔬 위험 성분

{chr(10).join(tox_lines)}

[이미지 4번: {name} 독성성분 인포그래픽]

## 🟠 결론: {name}, 급여 비권장!

실수로 섭취했다면 증상을 관찰하고 수의사와 상담하세요.

⚠️ 주의
• 의도적 급여 금지
• 실수 섭취 시 양 파악
• 증상 시 즉시 병원

[이미지 5번: {name} 급여금지 인포그래픽]

## 🚨 중독 증상

{chr(10).join(sym_lines)}

증상이 나타나면 즉시 수의사와 상담하세요.

[이미지 6번: {name} 중독증상 인포그래픽]

## 🏥 응급 대처법

1. 섭취량 파악
2. 상태 관찰
3. 수의사 연락
4. 구토 유발은 지시 후에만

[이미지 7번: {name} 응급대처 인포그래픽]

## ✅ 안전한 대안

{chr(10).join(alt_lines)}

[이미지 8번: {name} 대안식품 인포그래픽]

## ❓ 자주 묻는 질문

Q1. 조금 먹었는데 괜찮을까요?
A1. 소량이라도 24시간 관찰하세요.

Q2. 토했어요.
A2. 방어 반응일 수 있어요. 추가 증상 관찰하세요.

[이미지 9번: 햇살이 마무리 CTA 이미지]

오늘도 우리 아이 건강 챙기는 보호자님들 응원합니다! 💕

💬 이상 증상 시 즉시 수의사와 상담하세요!

#강아지{name} #{name}급여금지 #강아지음식주의 #반려견건강 #강아지먹으면안되는음식 #반려견주의 #강아지건강 #펫영양 #햇살이네 #강아지음식 #반려견음식
'''.strip()


def generate_forbidden(food: dict) -> str:
    name = food["name"]
    hooking = HOOKING["FORBIDDEN"]

    toxicity = food.get("toxicity", [{"name": "독성 성분", "effect": "심각한 위험"}])[:2]
    tox_lines = [f"• {t.get('name', '성분')}: {t.get('effect', '위험')}" for t in toxicity]

    symptoms = food.get("symptoms", ["구토", "설사", "경련", "호흡곤란"])[:4]
    sym_lines = [f"• {s}" for s in symptoms]

    hidden = food.get("hidden_dangers", ["가공식품에 포함 가능", "양념에 숨어있을 수 있음"])[:3]
    hid_lines = [f"• {h}" for h in hidden]

    return f'''"{name}", 강아지한테 줘도 될까? ⛔ {hooking}

[이미지 1번: 햇살이와 {name} 표지]

안녕하세요, 햇살이네입니다! 🐕
오늘은 반드시 알아야 할 '{name}' 급여에 대해 알려드릴게요.

[이미지 2번: {name} 음식 사진]

## ⛔ {name}, 절대 주지 마세요!

{name}은 강아지에게 매우 위험한 음식이에요.

[이미지 3번: 햇살이와 {name} 함께]

## 🔬 독성 메커니즘

{chr(10).join(tox_lines)}

[이미지 4번: {name} 독성메커니즘 인포그래픽]

## ⛔ 결론: {name}, 절대 급여 금지!

어떤 상황에서도 급여해서는 안 돼요. 실수로 섭취했다면 즉시 병원 방문하세요.

⛔ 절대 금지
• 어떤 형태로든 급여 금지
• 조리해도 독성 제거 안 됨
• 소량도 위험함

[이미지 5번: {name} 숨은위험 인포그래픽]

## 🚨 중독 증상

{chr(10).join(sym_lines)}

위 증상이 나타나면 즉시 동물병원으로 이동하세요.

[이미지 6번: {name} 중독증상 인포그래픽]

## 🏥 응급 대처법

1. 즉시 동물병원 연락
2. 섭취량과 시간 파악
3. 임의 구토 유발 금지
4. 남은 음식 가져가기

[이미지 7번: {name} 응급대처 인포그래픽]

## ⚠️ 숨어있는 위험

{chr(10).join(hid_lines)}

항상 성분표를 확인하세요.

[이미지 8번: {name} 경고메시지 인포그래픽]

## ❓ 자주 묻는 질문

Q1. 조금 먹었는데 괜찮을까요?
A1. 소량이라도 위험해요. 즉시 병원 연락하세요.

Q2. 괜찮아 보이는데요?
A2. 증상이 늦게 나타날 수 있어요. 48시간 관찰하세요.

[이미지 9번: 햇살이 마무리 CTA 이미지]

오늘도 우리 아이 건강 챙기는 보호자님들 응원합니다! 💕

💬 이상 증상 시 즉시 동물병원을 방문하세요!

#강아지{name} #{name}급여금지 #강아지독성음식 #반려견건강 #강아지먹으면안되는음식 #반려견주의 #강아지건강 #펫영양 #햇살이네 #강아지음식주의 #반려견음식주의
'''.strip()


def save_caption(folder: Path, content: str, food_name: str, safety: str):
    new_dir = folder / "blog"
    new_dir.mkdir(exist_ok=True)
    new_path = new_dir / "caption.txt"

    old_dir = folder / "02_Blog"
    old_dir.mkdir(exist_ok=True)
    folder_parts = folder.name.split("_", 1)
    eng_name = folder_parts[1] if len(folder_parts) > 1 else food_name
    old_path = old_dir / f"{eng_name}_{safety}_Blog_Caption.txt"

    with open(new_path, "w", encoding="utf-8") as f:
        f.write(content)
    with open(old_path, "w", encoding="utf-8") as f:
        f.write(content)

    return new_path, old_path


def main():
    food_data = load_food_data()

    # 글자수 문제 있는 건들
    fail_nums = [
        8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20,
        21, 23, 24, 25, 26, 90, 108, 111, 115,
        138, 144, 153, 154, 157, 158, 159,
        161, 162, 163, 164, 165, 166, 168, 169, 170, 171
    ]

    print("=" * 60)
    print("📝 블로그 캡션 배치 재생성 v2 (글자수 최적화)")
    print("=" * 60)

    success = 0
    out_of_range = []

    for num in fail_nums:
        food = food_data.get(str(num), {})
        if not food:
            continue

        safety = food.get("safety", "SAFE")
        name = food.get("name", f"음식{num}")

        folder = get_folder(num)
        if not folder:
            continue

        if safety in ["SAFE", "CAUTION"]:
            caption = generate_safe_caution(food, safety)
        elif safety == "DANGER":
            caption = generate_danger(food)
        else:
            caption = generate_forbidden(food)

        char_count = len(caption)
        status = "✅" if 1620 <= char_count <= 1980 else "⚠️"

        if char_count < 1620 or char_count > 1980:
            out_of_range.append((num, name, safety, char_count))

        save_caption(folder, caption, name, safety)
        print(f"  {status} {num:03d} {name} ({safety}): {char_count}자")
        success += 1

    print("\n" + "=" * 60)
    print(f"📊 완료: {success}건")

    if out_of_range:
        print(f"\n⚠️ 글자수 범위 밖: {len(out_of_range)}건")
        for num, name, safety, count in out_of_range:
            direction = "초과" if count > 1980 else "부족"
            print(f"   {num:03d} {name}: {count}자 ({direction})")

    print("=" * 60)

if __name__ == "__main__":
    main()
