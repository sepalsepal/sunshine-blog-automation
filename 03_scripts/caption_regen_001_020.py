#!/usr/bin/env python3
"""
caption_regen_001_020.py - 001~020 캡션 재생성
WO-2026-0216-CAPTION-REGEN

골든 샘플 기반으로 인스타, 쓰레드 캡션 v1.1 형식으로 재생성
"""

import os
import sys
import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"

# ============================================================
# 후킹 패턴 (B안)
# ============================================================

HOOKING_KO = {
    "SAFE": '"이거 줘도 되나?" 검색해본 적 있다면, 당신은 좋은 보호자예요.',
    "CAUTION": "사랑하니까 한 번 더 확인하는 거예요.",
    "DANGER": "알고 있는 것과 모르는 것, 그 차이가 우리 아이를 지켜요.",
    "FORBIDDEN": "몰랐다면 괜찮아요. 지금 알았으니까요."
}

HOOKING_EN = {
    "SAFE": 'If you\'ve ever googled "can my dog eat this?" — you\'re a great pet parent.',
    "CAUTION": "You double-check because you care.",
    "DANGER": "What you know can protect your dog.",
    "FORBIDDEN": "It's okay you didn't know — now you do."
}

# 안전도별 결론 이모지/텍스트
CONCLUSION = {
    "SAFE": ("✅", "안전합니다!", "Yes, it's safe!"),
    "CAUTION": ("🟡", "조건부 안전 — 적당량만!", "Safe in moderation!"),
    "DANGER": ("🔴", "위험 — 주의 필요!", "Dangerous — caution required!"),
    "FORBIDDEN": ("⛔", "절대 금지! 소량도 위험합니다.", "Absolutely NOT! Even small amounts are dangerous.")
}

# 쓰레드 후킹 패턴
THREADS_HOOK = {
    "SAFE": 'You\'ve definitely googled "can my dog eat {food_en}" at least once',
    "CAUTION": "{food_en} is safe for dogs — but there's a catch",
    "DANGER": "🚨 Most people don't know {food_en} is dangerous for dogs",
    "FORBIDDEN": "🚫 {food_en} can kill your dog. Not \"make them sick.\" Kill."
}


def load_food_data():
    with open(FOOD_DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_content_folder(num: int) -> Path:
    pattern = f"{num:03d}_*"
    matches = list(CONTENTS_DIR.glob(pattern))
    return matches[0] if matches else None


def get_food_emoji(food_name: str) -> str:
    """음식별 이모지"""
    emoji_map = {
        "호박": "🎃", "당근": "🥕", "블루베리": "🫐", "체리": "🍒",
        "고구마": "🍠", "사과": "🍎", "파인애플": "🍍", "바나나": "🍌",
        "브로콜리": "🥦", "수박": "🍉", "딸기": "🍓", "망고": "🥭",
        "오렌지": "🍊", "배": "🍐", "키위": "🥝", "파파야": "🍈",
        "복숭아": "🍑", "흰쌀밥": "🍚", "오이": "🥒", "프링글스": "🥔"
    }
    return emoji_map.get(food_name, "🍽️")


# ============================================================
# 인스타 캡션 생성
# ============================================================

def generate_insta_caption(num: int, food_data: dict) -> str:
    """인스타 캡션 v1.1 형식 생성"""
    item = food_data.get(str(num), {})
    name_ko = item.get("name", "음식")
    name_en = item.get("english_name", "food").split("_")[0].title()
    safety = item.get("safety", "CAUTION")
    emoji = get_food_emoji(name_ko)

    hook_ko = HOOKING_KO.get(safety, HOOKING_KO["CAUTION"])
    hook_en = HOOKING_EN.get(safety, HOOKING_EN["CAUTION"])
    concl_emoji, concl_ko, concl_en = CONCLUSION.get(safety, CONCLUSION["CAUTION"])

    # 영양소/주의사항 추출
    nutrients = item.get("nutrients", [])[:3]
    do_items = item.get("do_items", [])[:3]
    dont_items = item.get("dont_items", [])[:3]
    dosages = item.get("dosages", {})
    precautions = item.get("precautions", [])[:2]

    lines = []

    # [1] 감성 후킹
    lines.append(hook_ko)
    lines.append(hook_en)
    lines.append("")

    # [2] 질문 + 결론
    lines.append(f"{emoji} {name_ko}, 강아지가 먹어도 될까요?")
    lines.append(f"Can dogs eat {name_en.lower()}?")
    lines.append("")
    lines.append(f"{concl_emoji} {concl_ko}")
    lines.append(f"{concl_emoji} {concl_en}")
    lines.append("")

    if safety == "FORBIDDEN":
        # FORBIDDEN: 위험성 강조, 급여량 없음
        lines.append("☠️ 왜 위험한가요? Why is it dangerous?")
        for dont in dont_items:
            lines.append(f"• {dont}")
        lines.append("")

        lines.append("🚨 증상 Symptoms")
        for prec in precautions:
            if isinstance(prec, dict):
                lines.append(f"• {prec.get('title', '')}: {prec.get('desc', '')}")
            else:
                lines.append(f"• {prec}")
        lines.append("")

        lines.append("🆘 응급 대처 Emergency")
        lines.append("• 섭취 확인 시 즉시 동물병원 If ingested → vet immediately")
        lines.append("")

    else:
        # SAFE/CAUTION/DANGER: 주의사항 + 급여량
        if safety in ["SAFE", "CAUTION"]:
            lines.append("🟡 주의사항 Tips")
        else:
            lines.append("⚠️ 왜 주의해야 하나요? Why caution?")

        for do in do_items[:2]:
            lines.append(f"• {do}")
        lines.append("")

        lines.append("❌ 금지 항목 Never")
        for dont in dont_items[:2]:
            lines.append(f"• {dont}")
        lines.append("")

        # 급여량 (3단계)
        lines.append("📏 급여량 Serving Size")
        if "소형견" in dosages:
            d = dosages["소형견"]
            lines.append(f"• 소형견 Small: {d.get('amount', '10~20g')}")
        if "중형견" in dosages:
            d = dosages["중형견"]
            lines.append(f"• 중형견 Medium: {d.get('amount', '20~40g')}")
        if "대형견" in dosages:
            d = dosages["대형견"]
            lines.append(f"• 대형견 Large: {d.get('amount', '40~60g')}")
        lines.append("")

    # [5] 햇살이 에피소드
    episodes = {
        "호박": "우리 햇살이는 호박 냄새만 맡아도 꼬리가 프로펠러가 돼요 🐾",
        "당근": "햇살이는 당근 아삭아삭 씹는 소리가 참 좋대요 🐾",
        "블루베리": "우리 햇살이는 블루베리 하나하나 핥아먹는 재미로 살아요 🐾",
        "체리": "햇살이 앞에서 체리 먹을 때면 눈빛이 간절해져요 🐾",
        "고구마": "햇살이는 고구마 삶는 냄새에 부엌 앞을 서성여요 🐾",
        "사과": "우리 햇살이는 사과 깎는 소리만 들어도 달려와요 🐾",
        "파인애플": "햇살이는 파인애플 향에 코가 씰룩씰룩해요 🐾",
        "바나나": "햇살이는 바나나만 보면 꼬리가 헬리콥터가 돼요 🐾",
        "브로콜리": "햇살이는 브로콜리를 나무처럼 아작아작 먹어요 🐾",
        "수박": "여름엔 햇살이도 시원한 수박을 기다려요 🐾",
        "딸기": "햇살이는 딸기 하나에도 행복해하는 천사예요 🐾",
        "망고": "햇살이는 망고 향에 코가 벌름벌름해요 🐾",
        "오렌지": "햇살이는 오렌지 껍질 냄새에 재채기해요 🐾",
        "배": "햇살이는 배 과즙에 입가가 반짝반짝해요 🐾",
        "키위": "햇살이는 새콤한 키위에 혀를 날름거려요 🐾",
        "파파야": "햇살이는 열대과일 향에 신기해하는 표정이에요 🐾",
        "복숭아": "햇살이는 복숭아 즙이 코에 묻으면 핥아요 🐾",
        "흰쌀밥": "햇살이는 따끈한 밥 냄새에 침을 꿀꺽 삼켜요 🐾",
        "오이": "햇살이는 아삭한 오이 식감을 좋아해요 🐾",
        "프링글스": "이건 햇살이에게 절대 줄 수 없는 간식이에요 🐾",
    }
    episode_ko = episodes.get(name_ko, f"우리 햇살이는 {name_ko}을(를) 참 좋아해요 🐾")
    lines.append(episode_ko)
    lines.append(f"Haetsal loves {name_en.lower()} time 🐾")
    lines.append("")

    # [6] CTA + 수의사 상담
    lines.append("💾 Save & Share!")
    lines.append("")
    lines.append("🏥 이상 증상이 보이면 수의사와 상담하세요.")
    lines.append("If you notice any symptoms, consult your vet.")
    lines.append("")

    # 해시태그 15개
    food_tag_en = name_en.lower().replace(" ", "")
    food_tag_ko = name_ko.replace(" ", "")

    hashtags = [
        "#dogfood", "#caninenutrition", f"#{food_tag_en}fordogs",
        "#petcare", "#goldenretriever", "#seniordogs", "#doghealth",
        "#dogtreats", "#safefoodfordogs", "#pethealth",
        f"#강아지{food_tag_ko}", "#강아지간식", "#반려견음식",
        "#골든리트리버", "#햇살이네음식연구소"
    ]
    lines.append(" ".join(hashtags))

    return "\n".join(lines)


# ============================================================
# 쓰레드 캡션 생성
# ============================================================

def generate_thread_caption(num: int, food_data: dict) -> str:
    """쓰레드 캡션 v1.1 형식 생성"""
    item = food_data.get(str(num), {})
    name_ko = item.get("name", "음식")
    name_en = item.get("english_name", "food").split("_")[0].title()
    safety = item.get("safety", "CAUTION")
    emoji = get_food_emoji(name_ko)

    hook = THREADS_HOOK.get(safety, THREADS_HOOK["CAUTION"])
    hook = hook.format(food_en=name_en.lower())

    dosages = item.get("dosages", {})
    do_items = item.get("do_items", [])[:2]
    dont_items = item.get("dont_items", [])[:2]

    lines = []

    # 첫 줄: 영문 후킹
    lines.append(f"{hook} {emoji}")
    lines.append("")

    if safety == "SAFE":
        lines.append(f"Yes — {name_en.lower()} is safe for dogs.")
        for do in do_items:
            lines.append(f"→ {do}")
        lines.append("")
        # 급여량
        small = dosages.get("소형견", {}).get("amount", "10~20g")
        medium = dosages.get("중형견", {}).get("amount", "20~40g")
        large = dosages.get("대형견", {}).get("amount", "40~60g")
        lines.append(f"Serving: small dogs {small}, medium {medium}, large {large}")

    elif safety == "CAUTION":
        lines.append(f"🟡 {name_en} requires caution")
        for do in do_items:
            lines.append(f"→ {do}")
        for dont in dont_items[:1]:
            lines.append(f"→ {dont}")
        lines.append("")
        small = dosages.get("소형견", {}).get("amount", "10~20g")
        lines.append(f"Max serving: {small} for small dogs, 2-3x per week")

    elif safety == "DANGER":
        lines.append(f"The flesh? OK in tiny amounts.")
        lines.append(f"But seeds, stems, leaves? Toxic.")
        lines.append("")
        for dont in dont_items[:2]:
            lines.append(f"→ {dont}")
        lines.append("→ If your dog ate it → vet IMMEDIATELY")
        lines.append("")
        lines.append("Safe alternative: blueberries 🫐")

    else:  # FORBIDDEN
        lines.append(f"There is NO safe amount. Raw, cooked, powdered — all toxic.")
        lines.append("")
        for dont in dont_items[:2]:
            lines.append(f"→ {dont}")
        lines.append("→ If your dog ate ANY amount → vet NOW")

    lines.append("")

    # 햇살이 에피소드 (한국어)
    episodes = {
        "호박": "우리 햇살이는 호박 냄새에 꼬리를 흔들어요 🐾",
        "당근": "햇살이는 익힌 당근을 아삭아삭 잘 먹어요 🐾",
        "블루베리": "햇살이는 블루베리 하나에도 행복해요 🐾",
        "체리": "이건 엄마가 지켜야 할 선이에요 🐾",
        "고구마": "햇살이는 고구마 삶는 냄새를 좋아해요 🐾",
        "사과": "우리 햇살이는 사과 깎는 소리에 달려와요 🐾",
        "파인애플": "햇살이는 새콤달콤한 걸 좋아해요 🐾",
        "바나나": "햇살이 꼬리가 프로펠러가 돼요 🐾",
        "브로콜리": "햇살이는 브로콜리를 나무처럼 먹어요 🐾",
        "수박": "여름엔 시원한 수박 타임이에요 🐾",
        "딸기": "햇살이의 최애 간식이에요 🐾",
        "망고": "햇살이는 달콤한 향에 코가 벌름벌름 🐾",
        "오렌지": "향은 좋지만 조심해야 해요 🐾",
        "배": "배 과즙에 입가가 반짝여요 🐾",
        "키위": "새콤함에 혀를 내밀어요 🐾",
        "파파야": "열대과일은 특별해요 🐾",
        "복숭아": "복숭아 향에 눈이 초롱초롱 🐾",
        "흰쌀밥": "밥 냄새에 부엌 앞을 서성여요 🐾",
        "오이": "아삭한 식감을 좋아해요 🐾",
        "프링글스": "이건 절대 줄 수 없어요 🐾",
    }
    episode = episodes.get(name_ko, f"우리 햇살이는 {name_ko}을(를) 좋아해요 🐾")
    lines.append(episode)
    lines.append("")

    # 해시태그 2~3개
    food_tag = name_en.lower().replace(" ", "")
    if safety == "FORBIDDEN":
        lines.append(f"#CanMyDogEatThis #ToxicFoodForDogs")
    elif safety == "DANGER":
        lines.append(f"#CanMyDogEatThis #DogSafety")
    else:
        lines.append(f"#CanMyDogEatThis #{food_tag.capitalize()}ForDogs")

    return "\n".join(lines)


# ============================================================
# 메인
# ============================================================

def main():
    print("=" * 60)
    print("WO-2026-0216-CAPTION-REGEN 실행")
    print("대상: 001~020 인스타 + 쓰레드 캡션")
    print("=" * 60)

    food_data = load_food_data()

    stats = {"insta": 0, "thread": 0, "fail": []}

    for num in range(1, 21):
        folder = find_content_folder(num)
        if not folder:
            print(f"  ⚠️ {num:03d}: 폴더 없음")
            stats["fail"].append(num)
            continue

        item = food_data.get(str(num), {})
        name_ko = item.get("name", "?")
        safety = item.get("safety", "?")

        # 인스타 캡션 재생성
        insta_dir = folder / "01_Insta&Thread"
        insta_dir.mkdir(exist_ok=True)

        # 기존 파일 찾기
        old_insta = list(insta_dir.glob("*_Insta_Caption.txt"))

        # 새 파일명
        food_en = item.get("english_name", "food").split("_")[0].title()
        new_insta_name = f"{food_en}_{safety}_Insta_Caption.txt"
        new_insta_path = insta_dir / new_insta_name

        # 생성
        insta_content = generate_insta_caption(num, food_data)
        with open(new_insta_path, 'w', encoding='utf-8') as f:
            f.write(insta_content)
        stats["insta"] += 1

        # 기존 파일 삭제 (새 파일과 다른 경우만)
        for old in old_insta:
            if old != new_insta_path:
                old.unlink()

        # 쓰레드 캡션 재생성
        old_thread = list(insta_dir.glob("*_Threads_Caption.txt"))

        new_thread_name = f"{food_en}_{safety}_Threads_Caption.txt"
        new_thread_path = insta_dir / new_thread_name

        thread_content = generate_thread_caption(num, food_data)
        with open(new_thread_path, 'w', encoding='utf-8') as f:
            f.write(thread_content)
        stats["thread"] += 1

        for old in old_thread:
            if old != new_thread_path:
                old.unlink()

        print(f"  ✅ {num:03d}_{name_ko} ({safety})")

    print("\n" + "=" * 60)
    print("===== WO-2026-0216-CAPTION-REGEN 완료 보고 =====")
    print("=" * 60)
    print(f"\n재생성 대상: {stats['insta'] + stats['thread']}건")
    print(f"  ├─ 인스타: {stats['insta']}건")
    print(f"  └─ 쓰레드: {stats['thread']}건")

    if stats["fail"]:
        print(f"\n⚠️ 실패: {stats['fail']}")

    print("=" * 60)


if __name__ == "__main__":
    main()
