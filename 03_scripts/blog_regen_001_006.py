#!/usr/bin/env python3
"""
blog_regen_001_006.py - 블로그 001~006 캡션 재생성
BLOG_RULE v3.0 형식으로 재생성
"""

import os
import sys
import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"


def load_food_data():
    with open(FOOD_DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def find_content_folder(num: int) -> Path:
    pattern = f"{num:03d}_*"
    matches = list(CONTENTS_DIR.glob(pattern))
    return matches[0] if matches else None


# ============================================================
# 후킹 패턴 (B안)
# ============================================================

HOOKING = {
    "SAFE": '"이거 줘도 되나?" 검색해본 적 있다면, 당신은 좋은 보호자예요.',
    "CAUTION": "사랑하니까 한 번 더 확인하는 거예요.",
    "DANGER": "알고 있는 것과 모르는 것, 그 차이가 우리 아이를 지켜요.",
    "FORBIDDEN": "몰랐다면 괜찮아요. 지금 알았으니까요."
}

CONCLUSION_EMOJI = {
    "SAFE": "🟢",
    "CAUTION": "🟡",
    "DANGER": "🟠",
    "FORBIDDEN": "⛔"
}

CONCLUSION_TEXT = {
    "SAFE": ("안전합니다! 간식으로 급여 가능해요.", "SAFE"),
    "CAUTION": ("조건부 안전이에요. 적당량만 주세요!", "조건부 안전"),
    "DANGER": ("위험 등급이에요. 극소량만 가끔, 또는 피하는 것이 좋아요.", "위험"),
    "FORBIDDEN": ("절대 금지예요. 소량도 위험합니다.", "절대 금지")
}


def get_food_emoji(food_name: str) -> str:
    emoji_map = {
        "호박": "🎃", "당근": "🥕", "블루베리": "🫐", "체리": "🍒",
        "고구마": "🍠", "사과": "🍎"
    }
    return emoji_map.get(food_name, "🍽️")


# ============================================================
# 블로그 캡션 생성
# ============================================================

def generate_blog_caption(num: int, food_data: dict) -> str:
    """블로그 캡션 v3.0 형식 생성"""
    item = food_data.get(str(num), {})
    name_ko = item.get("name", "음식")
    name_en = item.get("english_name", "food").split("_")[0].title()
    safety = item.get("safety", "CAUTION")
    emoji = get_food_emoji(name_ko)

    hook = HOOKING.get(safety, HOOKING["CAUTION"])
    concl_emoji = CONCLUSION_EMOJI.get(safety, "🟡")
    concl_text, concl_grade = CONCLUSION_TEXT.get(safety, CONCLUSION_TEXT["CAUTION"])

    nutrients = item.get("nutrients", [])
    do_items = item.get("do_items", [])
    dont_items = item.get("dont_items", [])
    dosages = item.get("dosages", {})
    precautions = item.get("precautions", [])
    cooking_steps = item.get("cooking_steps", [])
    dosage_warning = item.get("dosage_warning", [])

    lines = []

    # ========== [이미지 1번: 표지] ==========
    lines.append("[이미지 1번: 표지]")
    lines.append("")
    lines.append("안녕하세요, 11살 골든리트리버 햇살이 엄마예요.")
    lines.append("")
    lines.append(hook)
    lines.append("")

    # 음식 도입
    intro_texts = {
        "호박": "오늘은 많은 분들이 궁금해하시는 '호박' 급여에 대해 이야기해볼게요.\n우리 햇살이도 호박을 정말 좋아하는데요, 달콤한 향에 코를 킁킁거리는 모습이 너무 귀여워요!",
        "당근": "오늘은 '당근' 급여에 대해 이야기해볼게요.\n우리 햇살이가 당근을 정말 좋아하는데, 아삭아삭 씹는 소리가 참 좋대요.",
        "블루베리": "오늘은 작지만 영양 가득한 '블루베리' 급여에 대해 이야기해볼게요.\n우리 햇살이는 블루베리 하나하나 핥아먹는 재미로 살아요!",
        "체리": "오늘은 의외로 주의가 필요한 과일, '체리'에 대해 이야기할게요.\n예쁘고 맛있어 보이지만, 강아지에게는 조심해야 할 부분이 있어요.",
        "고구마": "오늘은 강아지 간식으로 인기 만점인 '고구마' 급여에 대해 이야기해볼게요.\n우리 햇살이는 고구마 삶는 냄새에 부엌 앞을 서성여요!",
        "사과": "오늘은 많은 분들이 궁금해하시는 '사과' 급여에 대해 이야기해볼게요.\n우리 햇살이도 사과를 정말 좋아하는데요, 처음 줬을 때 아삭아삭 씹는 소리가 아직도 기억나요!"
    }
    lines.append(intro_texts.get(name_ko, f"오늘은 '{name_ko}' 급여에 대해 이야기해볼게요."))
    lines.append("")
    lines.append("")

    # ========== [이미지 2번: 음식 사진] ==========
    lines.append("[이미지 2번: 음식 사진]")
    lines.append("")
    lines.append(f"## 강아지 {name_ko}, 먹어도 되나요?")
    lines.append("")
    lines.append(f"{concl_emoji} 결론부터 말씀드리면, {concl_grade} 등급이에요.")
    lines.append("")

    if safety == "SAFE":
        lines.append(f"{name_ko}은(는) 강아지에게 안전한 음식이에요. 영양도 풍부하고 간식으로 주기 좋아요.")
        lines.append("다만 처음 급여할 때는 소량부터 시작해서 반응을 살펴보세요.")
    elif safety == "CAUTION":
        lines.append(f"{name_ko}은(는) 강아지에게 줄 수 있지만, 주의사항을 꼭 지켜야 해요.")
        lines.append("적정량을 지키고, 올바른 방법으로 급여하면 안전해요.")
    lines.append("")
    lines.append("")

    # ========== [이미지 3번: DogWithFood] ==========
    lines.append("[이미지 3번: DogWithFood]")
    lines.append("")

    episode_texts = {
        "호박": "우리 햇살이는 제가 호박 손질할 때마다 옆에 와서 지켜봐요. \"엄마, 그거 나 주는 거지?\" 하는 눈빛으로요. 11년을 함께해도 간식 앞에서는 여전히 아기 강아지 같아요.",
        "당근": "우리 햇살이는 당근 아삭아삭 씹는 소리를 정말 좋아해요. 손질할 때 옆에서 조각 하나 떨어지길 기다리는 눈빛이란...",
        "블루베리": "우리 햇살이는 블루베리를 손에서 하나씩 받아먹어요. 11살인데도 블루베리만 보면 꼬리가 팔랑팔랑해져요.",
        "체리": "저도 여름에 체리를 먹다가 햇살이가 간절한 눈으로 쳐다본 적이 있어요. 주고 싶은 마음은 굴뚝같았지만, 씨 분리가 완벽하지 않을 수 있어서 조심스러워요.",
        "고구마": "우리 햇살이는 고구마 익는 냄새에 부엌 앞을 빙빙 돌아요. 김이 모락모락 나는 고구마를 기다리는 모습이 너무 귀여워요.",
        "사과": "우리 햇살이는 제가 사과 손질할 때마다 옆에 와서 지켜봐요. \"엄마, 그거 나 주는 거지?\" 하는 눈빛으로요."
    }
    lines.append(episode_texts.get(name_ko, f"우리 햇살이는 {name_ko}을(를) 참 좋아해요."))
    lines.append("")

    # 영양소 정보
    lines.append(f"{name_ko}에는 다양한 영양소가 들어있어요:")
    for nut in nutrients[:5]:
        if isinstance(nut, dict):
            lines.append(f"- {nut.get('name', '')}: {nut.get('value', '')}{nut.get('unit', '')} ({nut.get('benefit', '')})")
    lines.append("")
    lines.append("")

    # ========== [이미지 4번: 영양정보] ==========
    lines.append("[이미지 4번: 영양정보]")
    lines.append("")

    nutrition_texts = {
        "호박": "특히 호박의 베타카로틴은 눈 건강에 도움을 주고, 식이섬유가 풍부해 장 건강에도 좋아요.\n호박은 저칼로리 채소라 체중 관리가 필요한 강아지에게도 좋은 간식이 될 수 있어요.",
        "당근": "특히 당근의 베타카로틴은 체내에서 비타민 A로 전환되어 눈 건강에 도움을 줘요.\n다만 생당근은 소화가 어려울 수 있으니, 익혀서 주는 것이 좋아요.",
        "블루베리": "특히 블루베리의 안토시아닌은 강력한 항산화 성분으로, 노령견의 인지 기능에 도움을 줄 수 있어요.\n작은 크기라 훈련 간식으로도 활용하기 좋아요.",
        "체리": "체리 과육에는 비타민과 항산화 성분이 풍부해요. 하지만 씨앗, 줄기, 잎에는 시안화물이 소량 포함되어 있어 주의가 필요해요.\n씨를 완벽히 제거하기 어려우니 신중하게 급여하세요.",
        "고구마": "특히 고구마의 베타카로틴과 식이섬유는 눈 건강과 장 건강에 모두 도움을 줘요.\n달콤한 맛 때문에 강아지들이 특히 좋아하는 간식이에요.",
        "사과": "특히 사과의 펙틴 성분은 장 건강에 도움을 주고, 치아 건강에도 좋다고 알려져 있어요.\n사과는 저칼로리 과일이라 체중 관리가 필요한 강아지에게도 좋은 간식이 될 수 있어요."
    }
    lines.append(nutrition_texts.get(name_ko, f"{name_ko}은(는) 다양한 영양소가 풍부해요."))
    lines.append("")
    lines.append(f"{name_ko} 급여 전에는 꼭 깨끗이 씻고, 강아지에게 맞게 손질해주세요.")
    lines.append("")
    lines.append("")

    # ========== [이미지 5번: 급여가능/불가] ==========
    lines.append("[이미지 5번: 급여가능/불가]")
    lines.append("")
    lines.append("## 급여 시 이렇게 하세요")
    lines.append("")

    for do in do_items[:5]:
        lines.append(f"✅ {do}")
    lines.append("")

    for dont in dont_items[:5]:
        lines.append(f"❌ {dont}")
    lines.append("")
    lines.append("")

    # ========== [이미지 6번: 급여량 표] ==========
    lines.append("[이미지 6번: 급여량 표]")
    lines.append("")
    lines.append("## 체중별 급여량")
    lines.append("")
    lines.append(f"{name_ko}은(는) 간식으로 급여하며, 하루 칼로리의 10% 이내로 제한해주세요.")
    lines.append("")

    # 4단계 급여량
    if "소형견" in dosages:
        d = dosages["소형견"]
        lines.append(f"**소형견 (5kg 이하)** — {d.get('amount', '15~20g')} ({d.get('desc', '작은 조각 2~3개')})")
    if "중형견" in dosages:
        d = dosages["중형견"]
        lines.append(f"**중형견 (5~15kg)** — {d.get('amount', '30~50g')} ({d.get('desc', '조각 3~4개')})")
    if "대형견" in dosages:
        d = dosages["대형견"]
        lines.append(f"**대형견 (15~30kg)** — {d.get('amount', '60~80g')} ({d.get('desc', '조각 5~6개')})")
    if "초대형견" in dosages:
        d = dosages["초대형견"]
        lines.append(f"**초대형견 (30kg 이상)** — {d.get('amount', '100~120g')} ({d.get('desc', '조각 7~8개')})")

    lines.append("")
    lines.append("처음 급여할 때는 위 양의 절반부터 시작해서 반응을 살펴보세요.")

    if safety == "CAUTION":
        lines.append("※ 주 2~3회 이하로 급여를 제한해주세요.")
    lines.append("")
    lines.append("")

    # ========== [이미지 7번: 주의사항] ==========
    lines.append("[이미지 7번: 주의사항]")
    lines.append("")
    lines.append("## 주의사항")
    lines.append("")

    for prec in precautions[:5]:
        if isinstance(prec, dict):
            lines.append(f"⚠️ {prec.get('title', '')}: {prec.get('desc', '')}")
        else:
            lines.append(f"⚠️ {prec}")
    lines.append("")
    lines.append("")

    # ========== [이미지 8번: 조리방법] ==========
    lines.append("[이미지 8번: 조리방법]")
    lines.append("")
    lines.append("## 간단 레시피")
    lines.append("")

    for i, step in enumerate(cooking_steps[:5], 1):
        if isinstance(step, dict):
            lines.append(f"{i}. {step.get('desc', '')}")
        else:
            lines.append(f"{i}. {step}")

    tip = item.get("cooking_tip", f"{name_ko}은(는) 신선한 것으로 간단하게 준비해주세요.")
    lines.append("")
    lines.append(f"TIP: {tip}")
    lines.append("")
    lines.append("")

    # ========== [이미지 9번: CTA] ==========
    lines.append("[이미지 9번: CTA]")
    lines.append("")

    cta_texts = {
        "호박": "저도 처음엔 '이거 줘도 되나?' 고민 많이 했어요. 인터넷에 정보가 너무 많아서 헷갈리더라고요. 직접 수의사 상담도 받고, 햇살이한테 조금씩 먹여보면서 정리한 내용이에요.",
        "당근": "저도 처음엔 생당근을 그냥 줬다가 소화를 못 하는 걸 보고 익혀서 주기 시작했어요. 작은 경험들이 쌓여서 이렇게 정리하게 됐네요.",
        "블루베리": "블루베리는 햇살이가 제일 좋아하는 간식 중 하나예요. 훈련할 때도 딱이고, 시니어독에게 좋은 항산화 성분까지 있어서 자주 줘요.",
        "체리": "체리는 과육만 소량 줄 수는 있지만, 씨 분리가 번거롭고 위험할 수 있어요. 저는 안전하게 블루베리로 대체해서 줘요.",
        "고구마": "고구마는 강아지들이 정말 좋아하는 간식이에요. 달콤하면서도 영양가 있어서, 햇살이 생일에도 고구마 케이크를 만들어줬던 기억이 나요.",
        "사과": "저도 처음엔 '이거 줘도 되나?' 고민 많이 했어요. 인터넷에 정보가 너무 많아서 헷갈리더라고요. 직접 수의사 상담도 받고, 햇살이한테 조금씩 먹여보면서 정리한 내용이에요."
    }
    lines.append(cta_texts.get(name_ko, "직접 수의사 상담도 받고 정리한 내용이에요."))
    lines.append("")
    lines.append("중요한 건 어떤 음식이든 '처음엔 소량, 반응 확인 후 늘리기'예요. 우리 아이들 체질이 다 다르니까요.")
    lines.append("")

    # FAQ
    lines.append("## 자주 묻는 질문")
    lines.append("")

    faq_data = {
        "호박": [
            ("Q. 호박 매일 줘도 되나요?", "A. 매일은 권장하지 않아요. 주 2~3회, 하루 칼로리의 10% 이내가 적당해요."),
            ("Q. 호박씨도 먹어도 되나요?", "A. 호박씨는 소화가 어려울 수 있어요. 제거하고 과육만 주세요."),
            ("Q. 생호박도 급여 가능한가요?", "A. 익힌 호박이 소화가 더 잘 돼요. 생으로 줄 땐 아주 작게 잘라주세요."),
            ("Q. 단호박과 일반 호박 중 어떤 게 좋나요?", "A. 둘 다 좋아요. 단호박이 더 달콤해서 강아지들이 더 좋아해요."),
        ],
        "당근": [
            ("Q. 당근 매일 줘도 되나요?", "A. 매일은 권장하지 않아요. 주 2~3회가 적당해요."),
            ("Q. 생당근도 괜찮나요?", "A. 생당근은 소화가 어려워요. 익혀서 주는 것이 좋아요."),
            ("Q. 당근 껍질도 먹어도 되나요?", "A. 네, 깨끗이 씻으면 껍질째 줘도 괜찮아요."),
            ("Q. 당근주스는 어떤가요?", "A. 직접 갈아서 소량만 줄 수 있어요. 시판 주스는 당분이 많아 피해주세요."),
        ],
        "블루베리": [
            ("Q. 블루베리 매일 줘도 되나요?", "A. 매일 소량은 괜찮지만, 주 3~4회 정도가 적당해요."),
            ("Q. 냉동 블루베리도 급여 가능한가요?", "A. 네, 냉동 블루베리도 좋아요. 여름철 시원한 간식으로 딱이에요."),
            ("Q. 블루베리잼은 어떤가요?", "A. 시판 블루베리잼은 설탕이 많아 피해주세요. 생과일로 주세요."),
            ("Q. 블루베리 알러지도 있나요?", "A. 드물지만 있어요. 처음 줄 때 소량으로 시작하세요."),
        ],
        "체리": [
            ("Q. 체리 과육만 발라서 주면 안 되나요?", "A. 가능은 하지만 권장하지 않아요. 씨 파편이 남을 수 있고, 블루베리가 훨씬 안전해요."),
            ("Q. 체리 씨를 실수로 먹었어요. 어떡하나요?", "A. 1~2개면 대부분 괜찮지만, 반응을 관찰하고 이상 시 병원에 가세요."),
            ("Q. 말린 체리는 괜찮나요?", "A. 씨가 제거된 건조 체리는 소량 괜찮지만, 당분이 높으니 주의하세요."),
            ("Q. 체리 대신 뭘 줄 수 있나요?", "A. 블루베리, 딸기, 수박 등이 훨씬 안전하고 맛있어요."),
        ],
        "고구마": [
            ("Q. 고구마 매일 줘도 되나요?", "A. 매일은 권장하지 않아요. 주 2~3회, 하루 칼로리의 10% 이내가 적당해요."),
            ("Q. 고구마 껍질도 먹어도 되나요?", "A. 껍질은 소화가 어려울 수 있어요. 깎아서 주는 것이 좋아요."),
            ("Q. 생고구마도 급여 가능한가요?", "A. 익힌 고구마가 소화가 더 잘 돼요. 생으로는 주지 마세요."),
            ("Q. 군고구마도 괜찮나요?", "A. 네, 군고구마도 좋아요. 다만 양념 없이 순수 고구마만 주세요."),
        ],
        "사과": [
            ("Q. 사과 매일 줘도 되나요?", "A. 매일은 권장하지 않아요. 주 2~3회, 하루 칼로리의 10% 이내가 적당해요."),
            ("Q. 사과 껍질도 먹어도 되나요?", "A. 네, 깨끗이 씻으면 껍질째 줘도 괜찮아요. 소화가 약한 아이는 깎아서 주세요."),
            ("Q. 냉동 사과도 급여 가능한가요?", "A. 네, 여름철 시원한 간식으로 좋아요. 너무 딱딱하면 살짝 해동 후 주세요."),
            ("Q. 사과즙은 어떤가요?", "A. 시판 사과즙은 당분이 많아 피해주세요. 직접 갈아서 소량만 줄 수 있어요."),
        ]
    }

    for q, a in faq_data.get(name_ko, [])[:4]:
        lines.append(f"**{q}**")
        lines.append(a)
        lines.append("")

    lines.append("궁금한 점이 있으시면 댓글로 남겨주세요 💛")
    lines.append("")

    # 해시태그 12~16개
    food_tag_ko = name_ko.replace(" ", "")
    food_tag_en = name_en.lower().replace(" ", "")

    hashtags = [
        f"#강아지{food_tag_ko}", "#강아지간식", "#반려견음식", "#강아지건강",
        "#펫푸드", "#강아지케어", "#골든리트리버", "#시니어독",
        "#강아지정보", "#반려견가이드", "#강아지음식가이드",
        "#dogfood", "#doghealth", "#petcare", "#노령견간식", f"#강아지{food_tag_ko}간식"
    ]
    lines.append(" ".join(hashtags[:16]))

    return "\n".join(lines)


# ============================================================
# 메인
# ============================================================

def main():
    print("=" * 60)
    print("블로그 001~006 캡션 재생성")
    print("BLOG_RULE v3.0 형식 적용")
    print("=" * 60)

    food_data = load_food_data()
    stats = {"success": 0, "fail": []}

    for num in range(1, 7):
        folder = find_content_folder(num)
        if not folder:
            print(f"  ⚠️ {num:03d}: 폴더 없음")
            stats["fail"].append(num)
            continue

        item = food_data.get(str(num), {})
        name_ko = item.get("name", "?")
        safety = item.get("safety", "?")
        name_en = item.get("english_name", "food").split("_")[0].title()

        # 블로그 캡션 재생성
        blog_dir = folder / "02_Blog"
        blog_dir.mkdir(exist_ok=True)

        # 기존 파일 찾기
        old_files = list(blog_dir.glob("*_Blog_Caption.txt"))

        # 새 파일명
        new_name = f"{name_en}_{safety}_Blog_Caption.txt"
        new_path = blog_dir / new_name

        # 생성
        content = generate_blog_caption(num, food_data)
        with open(new_path, 'w', encoding='utf-8') as f:
            f.write(content)

        # 글자수 확인
        char_count = len(content)

        # 기존 파일 삭제 (새 파일과 다른 경우만)
        for old in old_files:
            if old != new_path:
                old.unlink()

        stats["success"] += 1
        print(f"  ✅ {num:03d}_{name_ko} ({safety}) - {char_count}자")

    print("\n" + "=" * 60)
    print("===== 블로그 001~006 캡션 재생성 완료 =====")
    print("=" * 60)
    print(f"\n재생성 완료: {stats['success']}건")

    if stats["fail"]:
        print(f"⚠️ 실패: {stats['fail']}")

    print("=" * 60)


if __name__ == "__main__":
    main()
