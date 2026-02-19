#!/usr/bin/env python3
"""
batch_caption_all.py - 인스타 + 블로그 캡션 전체 배치 생성
§18 작업 순서 규칙: 번호 오름차순 처리
"""

import os
import requests
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv

PROJECT_ROOT = Path(__file__).parent.parent
load_dotenv(PROJECT_ROOT / ".env")

NOTION_API_KEY = os.getenv("NOTION_API_KEY")
NOTION_DATABASE_ID = os.getenv("NOTION_DATABASE_ID")
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["4_posted", "3_approved", "2_body_ready", "1_cover_only"]

# 안전도별 기본 문구
SAFETY_CONFIG = {
    "SAFE": {
        "emoji": "🟢",
        "title_emoji": "🍎",
        "conclusion": "급여 가능합니다!",
        "tone": "긍정적",
        "base_caution": "안전하지만 과다 섭취는 피하세요. 처음 급여 시 소량으로 시작하고, 알러지 반응이 없는지 확인하세요."
    },
    "CAUTION": {
        "emoji": "🟡",
        "title_emoji": "🍋",
        "conclusion": "주의해서 급여하세요!",
        "tone": "신중",
        "base_caution": "적정량을 지켜주세요. 과다 섭취 시 소화 장애나 건강 문제가 발생할 수 있어요."
    },
    "DANGER": {
        "emoji": "🔴",
        "title_emoji": "🚨",
        "conclusion": "급여하지 마세요!",
        "tone": "경고",
        "base_caution": "강아지에게 위험한 성분이 포함되어 있어요. 절대 급여하지 마세요."
    },
    "FORBIDDEN": {
        "emoji": "⛔",
        "title_emoji": "⛔",
        "conclusion": "절대 급여 금지!",
        "tone": "금지",
        "base_caution": "독성 성분이 포함되어 있어 강아지에게 치명적일 수 있어요. 소량도 위험합니다."
    }
}

# 음식 카테고리별 기본 정보
FOOD_CATEGORIES = {
    # 과일
    "fruit": ["apple", "banana", "blueberry", "cherry", "grape", "kiwi", "mango", "melon", "orange",
              "papaya", "peach", "pear", "pineapple", "plum", "pomegranate", "raspberry", "strawberry",
              "watermelon", "coconut", "grapefruit", "lemon", "blackberry", "raisin", "korean_melon"],
    # 채소
    "vegetable": ["broccoli", "carrot", "cucumber", "pumpkin", "spinach", "sweet_potato", "zucchini",
                  "potato", "cauliflower", "bean_sprouts", "lotus_root", "burdock", "cabbage", "asparagus",
                  "beet", "napa_cabbage", "lettuce", "celery", "green_beans", "peas", "kale", "onion", "garlic", "green_onion"],
    # 육류
    "meat": ["chicken", "beef", "duck", "chicken_breast", "bacon", "samgyeopsal", "bulgogi"],
    # 해산물
    "seafood": ["salmon", "mackerel", "tuna", "shrimp", "squid", "anchovy", "white_fish", "dried_fish", "dried_pollack", "pollack"],
    # 유제품/달걀
    "dairy_egg": ["milk", "yogurt", "cheese", "egg_yolk", "boiled_egg", "poached_egg", "quail_egg"],
    # 곡물/빵
    "grain": ["rice", "oatmeal", "bread", "baguette", "toast", "croissant", "pasta"],
    # 가공식품
    "processed": ["sausage", "meatball", "kimbap", "bibimbap", "pizza", "sandwich", "pancake", "waffle"],
    # 과자/스낵
    "snack": ["pringles", "cheetos", "doritos", "lays", "ritz", "kitkat", "skittles", "starburst", "reeses", "brownie", "muffin", "cake", "donut", "icecream", "cereal", "granola"],
    # 음료
    "drink": ["coca_cola", "sprite", "fanta", "milkis", "banana_milk", "budweiser", "cass_beer", "soju", "starbucks_coffee", "perrier"],
    # 한식
    "korean": ["kimchi", "tteokguk", "jjajangmyeon", "udon", "kalguksu", "naengmyeon", "ramen", "fried_chicken", "yangnyeom_chicken", "dakgangjeong", "chicken_skewer", "red_bean_bread", "tteok"],
    # 기타
    "others": ["olive", "nuts", "almonds", "tofu", "avocado", "mushroom", "seaweed", "coconut_oil", "sweet_pumpkin"]
}

def get_category(food_name):
    for cat, foods in FOOD_CATEGORIES.items():
        if food_name in foods:
            return cat
    return "others"

def get_category_benefits(category, korean):
    benefits_map = {
        "fruit": f"{korean}에는 비타민과 항산화 성분이 풍부해요. 수분 보충과 면역력 강화에 도움이 될 수 있어요.",
        "vegetable": f"{korean}에는 식이섬유와 비타민이 풍부해요. 소화 건강과 영양 보충에 좋아요.",
        "meat": f"{korean}은(는) 단백질이 풍부해요. 근육 유지와 에너지 공급에 좋아요.",
        "seafood": f"{korean}에는 오메가-3 지방산과 단백질이 풍부해요. 피부와 털 건강에 좋아요.",
        "dairy_egg": f"{korean}에는 단백질과 칼슘이 들어있어요. 뼈 건강에 도움이 될 수 있어요.",
        "grain": f"{korean}은(는) 탄수화물 공급원이에요. 에너지 보충에 좋지만 적당량만 주세요.",
        "processed": f"가공식품인 {korean}에는 다양한 영양소가 있지만, 첨가물에 주의해야 해요.",
        "snack": f"사람용 간식인 {korean}은(는) 강아지에게 영양적 이점이 거의 없어요.",
        "drink": f"{korean}은(는) 강아지에게 필요하지 않은 음료예요.",
        "korean": f"{korean}은(는) 한국 음식으로, 조미료와 양념에 주의해야 해요.",
        "others": f"{korean}에 대해 알아볼게요."
    }
    return benefits_map.get(category, f"{korean}에 대해 알아볼게요.")

def get_dosage_by_safety(safety):
    if safety == "FORBIDDEN" or safety == "DANGER":
        return {
            "small": ("0g", "금지"),
            "medium": ("0g", "금지"),
            "large": ("0g", "금지"),
            "xlarge": ("0g", "금지")
        }
    elif safety == "CAUTION":
        return {
            "small": ("5~10g", "아주 소량"),
            "medium": ("10~20g", "소량"),
            "large": ("20~30g", "소량"),
            "xlarge": ("30~40g", "소량")
        }
    else:  # SAFE
        return {
            "small": ("15~20g", "한 숟가락"),
            "medium": ("30~50g", "두세 숟가락"),
            "large": ("50~80g", "반 컵"),
            "xlarge": ("80~120g", "한 컵")
        }

def get_notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_API_KEY}",
        "Content-Type": "application/json",
        "Notion-Version": "2022-06-28"
    }

def fetch_all_contents():
    pages = []
    has_more = True
    start_cursor = None

    while has_more:
        url = f"https://api.notion.com/v1/databases/{NOTION_DATABASE_ID}/query"
        body = {}
        if start_cursor:
            body["start_cursor"] = start_cursor
        response = requests.post(url, headers=get_notion_headers(), json=body)
        data = response.json()
        pages.extend(data.get("results", []))
        has_more = data.get("has_more", False)
        start_cursor = data.get("next_cursor")

    contents = {}
    for page in pages:
        props = page.get("properties", {})
        num = props.get("번호", {}).get("number")
        if num is None:
            continue

        title_arr = props.get("이름", {}).get("title", [])
        name = title_arr[0].get("plain_text", "") if title_arr else ""

        korean_arr = props.get("한글명", {}).get("rich_text", [])
        korean = korean_arr[0].get("plain_text", "") if korean_arr else ""

        safety = props.get("안전도", {}).get("select", {})
        safety_name = safety.get("name", "CAUTION") if safety else "CAUTION"

        contents[num] = {
            "name": name,
            "korean": korean,
            "safety": safety_name,
            "page_id": page["id"]
        }
    return contents

def find_content_folder(num: int) -> Path:
    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    num_str = f"{num:03d}"
    for item in CONTENTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith(num_str):
            return item
    return None

def generate_insta_caption(num: int, name: str, korean: str, safety: str) -> str:
    """인스타그램 캡션 생성"""
    config = SAFETY_CONFIG.get(safety, SAFETY_CONFIG["CAUTION"])
    category = get_category(name)
    dosage = get_dosage_by_safety(safety)

    if safety == "FORBIDDEN" or safety == "DANGER":
        caption = f"""{config['title_emoji']} {korean}, 강아지가 먹어도 될까요?

{config['emoji']} 결론: {config['conclusion']}

🔴 왜 위험한가요?
• {config['base_caution']}
• 소량도 건강에 해로울 수 있어요
• 섭취 시 즉시 수의사 상담 필요

❌ 절대 금지 항목
• {korean} 급여 금지
• {korean}이(가) 들어간 음식도 금지
• 실수로 먹었다면 즉시 병원

📌 기억하세요
"{korean}은(는) 강아지에게 위험해요. 절대 주지 마세요!"

💾 저장해두고 주변에 공유하세요!
건강한 반려 생활을 위해 함께해요 🐶

ℹ️ 일부 이미지는 AI로 생성되었습니다.
ℹ️ Some images were generated by AI.

#강아지{korean.replace(' ', '')} #강아지금지음식 #반려견주의 #강아지건강
#펫푸드 #강아지케어 #골든리트리버 #시니어독
#강아지정보 #반려견가이드 #펫스타그램 #멍스타그램
#dogfood #doghealth #petcare #goldensofinstagram"""
    else:
        caption = f"""{config['title_emoji']} {korean}, 강아지가 먹어도 될까요?

{config['emoji']} 결론: {config['conclusion']}

🟡 {korean} 급여 시 주의사항
• {config['base_caution']}
• 처음 급여 시 소량으로 시작하세요
• 알러지 반응이 없는지 확인하세요
• 신선한 것으로 준비해주세요

📏 급여 방법
• 소형견 (5kg 미만): {dosage['small'][0]} ({dosage['small'][1]})
• 중형견 (5~15kg): {dosage['medium'][0]} ({dosage['medium'][1]})
• 대형견 (15kg 이상): {dosage['large'][0]} ({dosage['large'][1]})
※ 처음 급여 시 소량으로 시작

📌 기억하세요
"적당량을 지켜서 건강하게 급여하세요!"

💾 저장해두고 주변에 공유하세요!
건강한 간식 정보, 함께 나눠요 🐶

ℹ️ 일부 이미지는 AI로 생성되었습니다.
ℹ️ Some images were generated by AI.

#강아지{korean.replace(' ', '')} #강아지간식 #반려견음식 #강아지건강
#펫푸드 #강아지케어 #골든리트리버 #시니어독
#강아지정보 #반려견가이드 #펫스타그램 #멍스타그램
#dogfood #doghealth #petcare #goldensofinstagram"""

    return caption

def generate_blog_caption(num: int, name: str, korean: str, safety: str) -> str:
    """블로그 캡션 생성"""
    config = SAFETY_CONFIG.get(safety, SAFETY_CONFIG["CAUTION"])
    category = get_category(name)
    benefits = get_category_benefits(category, korean)
    dosage = get_dosage_by_safety(safety)

    if safety == "FORBIDDEN" or safety == "DANGER":
        caption = f"""[이미지 1번: 표지]
안녕하세요, 11살 골든리트리버 햇살이 엄마예요.
{korean} 이야기 한번 해볼게요...
많은 분들이 {korean}을(를) 강아지에게 줘도 되는지 궁금해하시는데요, 결론부터 말씀드릴게요.

[이미지 2번: 음식 사진]
## {korean}, 강아지에게 줘도 될까요? {config['emoji']}
❌ {config['conclusion']}
{korean}은(는) 강아지에게 위험한 음식이에요.

[이미지 3번: 영양 정보]
## 왜 위험한가요?
{config['base_caution']}
• 소량도 건강에 심각한 영향을 줄 수 있어요
• 구토, 설사, 무기력 등의 증상이 나타날 수 있어요
• 심한 경우 생명에 위협이 될 수 있어요

[이미지 4번: 급여 방법]
## 급여량
**모든 체급** — {dosage['small'][1]}
{korean}은(는) 어떤 양이든 강아지에게 주면 안 돼요.

[이미지 5번: 급여량 표]
## 만약 먹었다면?
• 섭취량 확인
• 증상 관찰 (구토, 설사, 무기력, 경련 등)
• 즉시 동물병원 방문
• 먹은 양과 시간을 수의사에게 알려주세요

[이미지 6번: 조리 방법]
## 대체 간식 추천
{korean} 대신 강아지에게 안전한 간식을 주세요:
• 삶은 고구마
• 당근
• 사과 (씨 제거)
• 블루베리

[이미지 7번: 주의사항]
솔직히 햇살이에게는 {korean}을(를) 절대 주지 않아요.
위험한 음식은 아예 접근하지 못하게 하는 게 최선이에요.
우리 강아지 건강이 최우선이니까요!

[이미지 8번: 햇살이 실사]
ℹ️ 일부 이미지는 AI로 생성되었습니다.
#강아지{korean.replace(' ', '')} #강아지금지음식 #반려견주의 #강아지건강 #펫푸드 #강아지케어 #골든리트리버 #시니어독 #강아지정보 #반려견가이드 #펫스타그램 #멍스타그램"""
    else:
        caption = f"""[이미지 1번: 표지]
안녕하세요, 11살 골든리트리버 햇살이 엄마예요.
{korean} 이야기 한번 해볼게요...
많은 분들이 {korean}을(를) 강아지에게 줘도 되는지 궁금해하시죠? 오늘 자세히 알려드릴게요.

[이미지 2번: 음식 사진]
## {korean}, 뭐가 좋은 걸까요? {config['emoji']}
{benefits}
{config['conclusion']}

[이미지 3번: 영양 정보]
## 그런데 왜 주의가 필요할까요?
{config['base_caution']}
• 처음 급여 시에는 소량으로 시작하세요
• 알러지 반응이 없는지 24시간 관찰하세요
• 과다 섭취는 피해주세요

[이미지 4번: 급여 방법]
## 얼마나 주면 될까요?
**소형견 (5kg 이하)** — {dosage['small'][0]} ({dosage['small'][1]})
**중형견 (5~15kg)** — {dosage['medium'][0]} ({dosage['medium'][1]})
**대형견 (15~30kg)** — {dosage['large'][0]} ({dosage['large'][1]})
**초대형견 (30kg 이상)** — {dosage['xlarge'][0]} ({dosage['xlarge'][1]})

[이미지 5번: 급여량 표]
## 어떻게 줘야 할까요?
• 신선한 것으로 준비해주세요
• 깨끗이 씻어서 주세요
• 적당한 크기로 잘라주세요
• 처음에는 소량으로 시작하세요

[이미지 6번: 조리 방법]
## 처음 줬을 때 이것만 확인하세요
✅ 구토나 설사가 없는지 확인
✅ 알러지 반응(가려움, 발진) 체크
✅ 변 상태 관찰
✅ 24시간 동안 모니터링

[이미지 7번: 주의사항]
햇살이도 {korean}을(를) 잘 먹어요.
처음 줄 때는 조금만 주고 반응을 살펴봤는데, 다행히 잘 맞더라고요.
여러분도 처음에는 소량으로 시작해보세요!

[이미지 8번: 햇살이 실사]
ℹ️ 일부 이미지는 AI로 생성되었습니다.
#강아지{korean.replace(' ', '')} #강아지간식 #반려견음식 #강아지건강 #펫푸드 #강아지케어 #골든리트리버 #시니어독 #강아지정보 #반려견가이드 #펫스타그램 #멍스타그램"""

    return caption

def update_notion(page_id: str, insta: bool = False, blog: bool = False):
    """노션 업데이트"""
    url = f"https://api.notion.com/v1/pages/{page_id}"
    payload = {"properties": {}}

    if insta:
        payload["properties"]["인스타캡션"] = {"checkbox": True}
    if blog:
        payload["properties"]["블로그캡션"] = {"checkbox": True}

    response = requests.patch(url, headers=get_notion_headers(), json=payload)
    return response.status_code == 200

def main():
    print("━" * 60)
    print("📝 인스타 + 블로그 캡션 전체 배치 생성")
    print(f"   {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("   §18 규칙: 번호 오름차순 처리")
    print("━" * 60)

    # 노션에서 전체 콘텐츠 로드
    print("\n📥 노션 데이터 로드 중...")
    contents = fetch_all_contents()
    print(f"   {len(contents)}개 콘텐츠 로드 완료")

    stats = {
        "insta_created": 0,
        "insta_skipped": 0,
        "blog_created": 0,
        "blog_skipped": 0,
        "folder_not_found": []
    }

    # 번호순 정렬
    sorted_nums = sorted(contents.keys())

    print(f"\n🚀 캡션 생성 시작 (#{sorted_nums[0]:03d}~#{sorted_nums[-1]:03d})")
    print()

    for num in sorted_nums:
        data = contents[num]
        name = data["name"]
        korean = data["korean"]
        safety = data["safety"] or "CAUTION"
        page_id = data["page_id"]

        if not korean:
            korean = name

        # 폴더 찾기
        folder = find_content_folder(num)
        if not folder:
            stats["folder_not_found"].append(f"#{num:03d}")
            continue

        # 인스타 캡션 - 2026-02-13: 플랫 구조 반영
        insta_folder = folder / "01_Insta&Thread"
        insta_file = insta_folder / "caption.txt"

        if not insta_file.exists():
            insta_folder.mkdir(exist_ok=True)
            caption = generate_insta_caption(num, name, korean, safety)
            with open(insta_file, "w", encoding="utf-8") as f:
                f.write(caption)
            stats["insta_created"] += 1
            update_notion(page_id, insta=True)
        else:
            stats["insta_skipped"] += 1

        # 블로그 캡션 - 2026-02-13: 플랫 구조 반영
        blog_folder = folder / "02_Blog"
        blog_file = blog_folder / "caption.txt"

        if not blog_file.exists():
            blog_folder.mkdir(exist_ok=True)
            caption = generate_blog_caption(num, name, korean, safety)
            with open(blog_file, "w", encoding="utf-8") as f:
                f.write(caption)
            stats["blog_created"] += 1
            update_notion(page_id, blog=True)
        else:
            stats["blog_skipped"] += 1

        # 진행 상황 (10개마다)
        if num % 10 == 0:
            print(f"   ✅ #{num:03d} {korean} 완료")

    # 최종 결과
    print("\n" + "━" * 60)
    print("📊 최종 결과")
    print("━" * 60)
    print(f"📱 인스타 캡션:")
    print(f"   ✅ 생성: {stats['insta_created']}개")
    print(f"   ⏭️ 스킵: {stats['insta_skipped']}개")
    print(f"📝 블로그 캡션:")
    print(f"   ✅ 생성: {stats['blog_created']}개")
    print(f"   ⏭️ 스킵: {stats['blog_skipped']}개")

    if stats["folder_not_found"]:
        print(f"\n⚠️ 폴더 없음: {len(stats['folder_not_found'])}개")

    print("━" * 60)
    print("✅ 전체 배치 완료!")

if __name__ == "__main__":
    main()
