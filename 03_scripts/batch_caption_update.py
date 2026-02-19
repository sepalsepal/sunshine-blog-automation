#!/usr/bin/env python3
"""
batch_caption_update.py - 전체 캡션 일괄 업데이트
00_rules/01_Caption_rules/CAPTION_RULE.md 준수

변경사항:
- AI 고지 제거
- 인스타: CAPTION_RULE.md §2 인스타그램 규칙 준수
- 쓰레드: CAPTION_RULE.md §3 쓰레드 규칙 준수
"""

import json
import os
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"

# 게시 완료 항목 (제외)
POSTED_ITEMS = ["033"]  # 바게트

# 안전도별 이모지
SAFETY_EMOJI = {
    "SAFE": "🎉",
    "CAUTION": "⚠️",
    "DANGER": "🚨",
    "FORBIDDEN": "⛔"
}

# 안전도별 답변
SAFETY_ANSWER = {
    "SAFE": "네, {name}는 강아지에게 급여 가능해요!",
    "CAUTION": "{name}는 조건부로 급여 가능해요. 주의사항을 확인하세요!",
    "DANGER": "{name}는 주의가 필요해요! 소량만 급여하세요.",
    "FORBIDDEN": "{name}는 강아지에게 절대 급여하면 안 돼요!"
}

def get_food_emoji(name):
    """음식별 이모지 반환"""
    emoji_map = {
        "호박": "🎃", "당근": "🥕", "블루베리": "🫐", "체리": "🍒",
        "고구마": "🍠", "사과": "🍎", "파인애플": "🍍", "바나나": "🍌",
        "브로콜리": "🥦", "수박": "🍉", "딸기": "🍓", "망고": "🥭",
        "오렌지": "🍊", "배": "🍐", "키위": "🥝", "파파야": "🍈",
        "복숭아": "🍑", "쌀밥": "🍚", "오이": "🥒", "프링글스": "🥔",
        "소시지": "🌭", "아보카도": "🥑", "콜라": "🥤", "올리브": "🫒",
        "블랙베리": "🫐", "시금치": "🥬", "애호박": "🥒", "닭고기": "🍗",
        "수란": "🥚", "견과류": "🥜", "삶은달걀": "🥚", "우유": "🥛",
        "바게트": "🥖", "팥빵": "🍞", "감자": "🥔", "소고기": "🥩",
        "콜리플라워": "🥦", "콩나물": "🌱", "요거트": "🥛", "연근": "🌰",
        "우엉": "🥕", "오트밀": "🥣", "멜론": "🍈", "아몬드": "🌰",
        "달걀노른자": "🥚", "석류": "🍎", "고등어": "🐟", "두부": "🧈",
        "연어": "🐟", "자두": "🍑", "양파": "🧅", "바나나우유": "🥛",
        "마늘": "🧄", "단호박": "🎃", "포도": "🍇", "건포도": "🍇",
        "초콜릿": "🍫", "김치": "🥬", "메추리알": "🥚", "치킨": "🍗",
        "양념치킨": "🍗", "떡국": "🍜", "육포": "🥓", "김밥": "🍙",
        "비빔밥": "🍚", "짜장면": "🍜", "우동": "🍜", "칼국수": "🍜",
        "냉면": "🍜", "라면": "🍜", "토스트": "🍞", "샌드위치": "🥪",
        "삼겹살": "🥓", "불고기": "🥩", "케이크": "🎂", "도넛": "🍩",
        "아이스크림": "🍦", "브라우니": "🍫", "머핀": "🧁", "팬케이크": "🥞",
        "와플": "🧇", "시리얼": "🥣", "그래놀라": "🥣", "닭꼬치": "🍢",
        "닭강정": "🍗", "미트볼": "🍖", "베이컨": "🥓", "맥주": "🍺",
        "카스": "🍺", "치토스": "🧀", "크루아상": "🥐", "도리토스": "🌮",
        "환타": "🥤", "킷캣": "🍫", "레이즈": "🥔", "밀키스": "🥛",
        "페리에": "💧", "피자": "🍕", "리세스": "🍫", "리츠": "🍪",
        "스키틀즈": "🍬", "소주": "🍶", "스타벅스커피": "☕", "스타버스트": "🍬",
        "치즈": "🧀", "흰살생선": "🐟", "스프라이트": "🥤", "닭가슴살": "🍗",
        "새우": "🦐", "라즈베리": "🍇", "코코넛": "🥥", "자몽": "🍊",
        "레몬": "🍋", "양배추": "🥬", "아스파라거스": "🌿", "비트": "🥕",
        "배추": "🥬", "상추": "🥬", "참치": "🐟", "셀러리": "🥬",
        "그린빈스": "🫛", "오리": "🦆", "떡": "🍡", "완두콩": "🫛",
        "황태": "🐟", "버섯": "🍄", "파": "🌿", "오징어": "🦑",
        "멸치": "🐟", "미역": "🌿", "명태": "🐟", "케일": "🥬",
        "파스타": "🍝", "빵": "🍞", "코코넛오일": "🥥", "참외": "🍈",
    }
    return emoji_map.get(name, "🐕")


def generate_insta_caption(food_id, food_data):
    """인스타그램 캡션 생성 (CAPTION_RULE.md §2 준수)"""
    name = food_data.get("name", "")
    safety = food_data.get("safety", "SAFE")
    dosages = food_data.get("dosages", {})
    dont_items = food_data.get("dont_items", [])[:2]
    do_items = food_data.get("do_items", [])[:3]
    toxic_reason = food_data.get("toxic_reason", f"{name}는 강아지에게 해로운 성분이 있어요")
    symptoms = food_data.get("symptoms", ["구토", "설사", "무기력"])

    emoji = get_food_emoji(name)

    # 해시태그 (12~16개)
    hashtags = f"#강아지{name.replace(' ', '')} #강아지간식 #반려견음식 #강아지건강 #펫푸드 #강아지케어 #골든리트리버 #시니어독 #강아지정보 #반려견가이드 #강아지음식가이드 #dogfood #petcare #햇살이네음식연구소"

    if safety == "FORBIDDEN":
        # FORBIDDEN 템플릿 (CAPTION_RULE.md §2.2)
        symptom_text = ", ".join(symptoms[:3]) if symptoms else "구토, 설사, 무기력"

        caption = f"""{emoji} {name}, 강아지가 먹어도 될까요?

⛔ 결론: 절대 금지!

🔴 {name} 위험 이유
{toxic_reason}

🚨 응급 상황 대처
• 즉시 동물병원 방문
• 구토 유도 시도하지 마세요
• 증상: {symptom_text}

📌 기억하세요
"{name} = 절대 금지"
모르고 주시는 분들 많아서 공유해요 🐕

{hashtags}"""

    else:
        # SAFE/CAUTION/DANGER 템플릿 (CAPTION_RULE.md §2.1)
        # 결론 뱃지
        if safety == "SAFE":
            badge = "✅ 결론: 안전합니다!"
        elif safety == "CAUTION":
            badge = "⚠️ 결론: 주의가 필요합니다!"
        else:  # DANGER
            badge = "🔴 결론: 위험합니다!"

        # 주의사항
        caution_items = []
        for item in do_items[:3]:
            caution_items.append(item)
        if not caution_items:
            caution_items = ["소량씩 급여하세요", "반응을 확인하세요", "간식으로만 주세요"]

        # 금지 항목
        forbidden_items = []
        for item in dont_items[:2]:
            forbidden_items.append(item)
        if not forbidden_items:
            forbidden_items = ["과다 급여 (소화 문제)", "양념된 것 (자극 성분)"]

        # 급여량
        dosage_lines = []
        for size in ["소형견", "중형견", "대형견"]:
            d = dosages.get(size, {})
            amount = d.get("amount", "소량")
            desc = d.get("desc", "조금씩")
            dosage_lines.append(f"• {size}: {amount} ({desc})")

        # 조리법
        cooking = "깨끗이 씻어서 급여"
        for item in do_items:
            if "익혀" in item or "삶" in item:
                cooking = "익혀서 급여"
                break
            elif "생" in item:
                cooking = "생으로 급여 가능"
                break

        caption = f"""{emoji} {name}, 강아지가 먹어도 될까요?

{badge}

🟡 {name} 급여 시 주의사항
{''.join([f"• {c}{chr(10)}" for c in caution_items])}
❌ 절대 금지 항목
{''.join([f"• {f}{chr(10)}" for f in forbidden_items])}
📏 급여 방법
{chr(10).join(dosage_lines)}
※ {cooking}
※ 가끔 간식으로만 OK

📌 기억하세요
"적당히, 가끔만!"

💾 저장해두고 주변에 공유하세요!
건강한 간식 정보, 함께 나눠요 🐶

{hashtags}"""

    return caption.strip()


def generate_threads_caption(food_id, food_data):
    """쓰레드 캡션 생성 (§2.9 템플릿)"""
    name = food_data.get("name", "")
    safety = food_data.get("safety", "SAFE")
    nutrients = food_data.get("nutrients", [])

    emoji = get_food_emoji(name)

    # 효능 추출
    benefits = [n.get("benefit", "") for n in nutrients[:2] if n.get("benefit")]
    benefit_text = f"{benefits[0]}도 좋고 {benefits[1]}에도 좋아요" if len(benefits) >= 2 else "영양도 풍부해요"

    if safety == "SAFE":
        caption = f"""{name} 강아지한테 줘도 되나요? {emoji}
우리 햇살이 {name} 완전 좋아해요!

{name}은 강아지한테 정말 좋은 간식이에요.
{benefit_text}.
간식으로 맘껏 줘도 돼요~ 🐕

여러분 강아지도 {name} 좋아하나요?"""

    elif safety == "CAUTION":
        caption = f"""{name} 강아지한테 줘도 될까요? {emoji}
우리 햇살이는 잘 익힌 {name} 좋아해요!

{benefit_text}. 근데 조건이 있어요!
✔️ 소량만 ✔️ 잘 익혀서 ❌ 양념은 금지

여러분 강아지는 {name} 좋아하나요? 🐕"""

    elif safety == "DANGER":
        caption = f"""{name} 강아지한테 줘도 될까요? {emoji}
우리 햇살이한테는 거의 안 줘요!

{name}는 강아지한테 위험할 수 있어요.
⚠️ 소량만 급여
⚠️ 반응 꼭 확인
❌ 많이 주면 안 돼요

이상 증상 보이면 바로 병원 가세요!"""

    else:  # FORBIDDEN
        caption = f"""{name} 강아지한테 절대 주면 안 돼요! {emoji}
우리 햇살이도 절대 안 줘요!

{name}는 강아지한테 독성이 있어요.
소량만 먹어도 위험해요.
🚨 먹었다면 → 즉시 동물병원! (먹은 양/시간 기억)

모르고 주시는 분들 많아서 공유해요."""

    return caption.strip()


def update_captions():
    """전체 캡션 업데이트"""
    # food_data.json 로드
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    updated = 0
    skipped = 0
    errors = []

    for food_id, data in food_data.items():
        # 게시 완료 항목 스킵
        if food_id.zfill(3) in POSTED_ITEMS:
            print(f"[SKIP] {food_id}: 게시 완료")
            skipped += 1
            continue

        # 폴더 찾기
        folder_pattern = f"{food_id.zfill(3)}_*"
        matches = list(CONTENTS_DIR.glob(folder_pattern))

        if not matches:
            continue

        content_folder = matches[0]
        insta_folder = content_folder / "01_Insta&Thread"

        if not insta_folder.exists():
            continue

        name = data.get("name", "")
        english_name = data.get("english_name", "").replace(" ", "")
        safety = data.get("safety", "SAFE")

        # 캡션 파일명 결정
        name_part = english_name.title().replace("_", "")
        insta_file = insta_folder / f"{name_part}_{safety}_Insta_Caption.txt"
        threads_file = insta_folder / f"{name_part}_{safety}_Threads_Caption.txt"

        # 기존 파일 찾기
        existing_insta = list(insta_folder.glob("*_Insta_Caption.txt"))
        existing_threads = list(insta_folder.glob("*_Threads_Caption.txt"))

        if existing_insta:
            insta_file = existing_insta[0]
        if existing_threads:
            threads_file = existing_threads[0]

        try:
            # 인스타 캡션 생성
            insta_caption = generate_insta_caption(food_id, data)
            with open(insta_file, "w", encoding="utf-8") as f:
                f.write(insta_caption)

            # 쓰레드 캡션 생성
            threads_caption = generate_threads_caption(food_id, data)
            with open(threads_file, "w", encoding="utf-8") as f:
                f.write(threads_caption)

            print(f"[OK] {food_id.zfill(3)} {name}: 캡션 업데이트")
            updated += 1

        except Exception as e:
            errors.append(f"{food_id}: {e}")
            print(f"[ERR] {food_id}: {e}")

    print("\n" + "=" * 50)
    print(f"캡션 업데이트 완료")
    print(f"  업데이트: {updated}개")
    print(f"  스킵: {skipped}개")
    print(f"  오류: {len(errors)}개")
    print("=" * 50)

    if errors:
        print("\n오류 목록:")
        for e in errors:
            print(f"  - {e}")


if __name__ == "__main__":
    update_captions()
