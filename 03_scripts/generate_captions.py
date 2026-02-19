#!/usr/bin/env python3
"""
generate_captions.py - 인스타/블로그 캡션 배치 생성
RULES.md §2.7, §2.8 템플릿 준수
"""

import json
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
# 2026-02-13: 플랫 구조로 변경 - STATUS_DIRS 제거
# 이제 contents/ 직접 스캔


def load_food_data():
    """음식 데이터 로드"""
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)


def find_content_folder(num: int) -> Path:
    """번호로 콘텐츠 폴더 찾기 (플랫 구조)"""
    num_str = f"{num:03d}"
    # 2026-02-13: contents/ 직접 스캔 (플랫 구조)
    for item in CONTENTS_DIR.iterdir():
        if item.is_dir() and item.name.startswith(num_str):
            return item
    return None


def generate_insta_caption(data: dict) -> str:
    """인스타 캡션 템플릿 v1.0 생성"""
    emoji = data.get("emoji", "🍽️")
    korean = data["korean"]
    answer = data["answer"]
    dosage = data["dosage"]
    tips = data["tips"]
    story = data["story"]
    name = data["name"]

    # 급여량 포맷
    dosage_text = f"""소형견 (5kg 이하) — {dosage['small']['g']} ({dosage['small']['unit']})
중형견 (5~15kg) — {dosage['medium']['g']} ({dosage['medium']['unit']})
대형견 (15~30kg) — {dosage['large']['g']} ({dosage['large']['unit']})
초대형견 (30kg 이상) — {dosage['xlarge']['g']} ({dosage['xlarge']['unit']})"""

    # 팁 포맷
    tips_text = "\n".join([f"• {tip}" for tip in tips])

    caption = f"""{emoji} 강아지 {korean}, 줘도 되나요?

{answer}

📏 체중별 급여량

{dosage_text}

✅ 급여 팁
{tips_text}

{story}

처음 주실 땐 조금만! 반응 보고 늘려주세요.

#강아지{korean} #강아지간식 #반려견음식 #골든리트리버 #펫푸드 #강아지건강간식 #시니어독 #강아지먹어도되는음식"""

    return caption


def generate_blog_caption(data: dict) -> str:
    """블로그 캡션 템플릿 v1.0 생성"""
    emoji = data.get("emoji", "🍽️")
    korean = data["korean"]
    answer = data["answer"]
    dosage = data["dosage"]
    tips = data["tips"]
    story = data["story"]
    safety = data.get("safety", "SAFE")

    # 안전도별 제목
    if safety == "SAFE":
        q1 = f"{korean}, 줘도 되나요?"
        intro = f"{korean} 이야기 한번 해볼게요. {story.split(chr(10))[0]}"
    elif safety == "CAUTION":
        q1 = f"{korean}, 줘도 되나요?"
        intro = f"{korean} 이야기 한번 해볼게요. 결론부터 말씀드리면, 소량이면 괜찮아요. 근데 '소량'이라는 게 중요해요."
    elif safety == "FORBIDDEN":
        q1 = f"왜 {korean}가 위험한가요?"
        intro = f"오늘은 좀 무거운 이야기를 해야 할 것 같아요. {korean}에 관한 건데, 이건 정말 중요해서 꼭 알려드리고 싶었어요."
    else:
        q1 = f"{korean}, 줘도 되나요?"
        intro = f"{korean} 이야기예요."

    # 급여량 포맷
    dosage_text = f"""**소형견 (5kg 이하)** — {dosage['small']['g']} ({dosage['small']['unit']})
**중형견 (5~15kg)** — {dosage['medium']['g']} ({dosage['medium']['unit']})
**대형견 (15~30kg)** — {dosage['large']['g']} ({dosage['large']['unit']})
**초대형견 (30kg 이상)** — {dosage['xlarge']['g']} ({dosage['xlarge']['unit']})"""

    # 팁 포맷
    tips_text = "\n".join([f"• {tip}" for tip in tips])

    # 주의사항
    caution_list = data.get("caution", [])
    caution_text = ""
    for c in caution_list[:3]:
        caution_text += f"**{c['title']}** — {c['desc']}\n\n"

    # 조리법
    cooking = data.get("cooking", [])
    cooking_text = ""
    for i, step in enumerate(cooking[:5], 1):
        cooking_text += f"{i}. {step['step']} — {step['desc']}\n"

    tip_box = data.get("tip_box", "")

    caption = f"""[이미지 1번: 표지]

안녕하세요, 11살 골든리트리버 햇살이 엄마예요.

{intro}

[이미지 2번: {korean} 사진]


## {q1}

{answer}

[이미지 3번: 영양 정보]


## 어떻게 주면 좋을까요?

{tips_text}

[이미지 4번: 급여 방법]


## 얼마나 주면 될까요?

{dosage_text}

[이미지 5번: 급여량 표]


## 주의할 점

{caution_text}
[이미지 6번: 주의사항]


## 간단 조리법

{cooking_text}
TIP: {tip_box}

[이미지 7번: 조리 방법]


{story}

궁금한 음식 있으시면 댓글로 남겨주세요!

[이미지 8번: 햇살이 실사]

ℹ️ 일부 이미지는 AI로 생성되었습니다.

#강아지{korean} #강아지간식 #반려견음식 #골든리트리버 #시니어독 #강아지급여량 #펫푸드 #반려견영양"""

    return caption


def generate_captions_batch(nums: list, caption_type: str = "insta", dry_run: bool = False):
    """배치 캡션 생성"""
    food_data = load_food_data()

    generated = []
    skipped = []
    no_data = []

    for num in nums:
        num_str = f"{num:03d}"

        # 데이터 확인
        if num_str not in food_data:
            no_data.append(num)
            continue

        data = food_data[num_str]
        folder = find_content_folder(num)

        if not folder:
            skipped.append(num)
            continue

        # 캡션 디렉토리 (새 구조 + PascalCase)
        safety = data.get("safety", "SAFE")
        food_en = folder.name.split("_")[1] if "_" in folder.name else "Food"

        if caption_type == "insta":
            caption_dir = folder / "01_Insta&Thread"
            caption_file = caption_dir / f"{food_en}_{safety}_Insta_Caption.txt"
            caption_content = generate_insta_caption(data)
        else:
            caption_dir = folder / "02_Blog"
            caption_file = caption_dir / f"{food_en}_{safety}_Blog_Caption.txt"
            caption_content = generate_blog_caption(data)

        # 이미 존재하면 스킵
        if caption_file.exists():
            skipped.append(num)
            continue

        # 생성
        if not dry_run:
            caption_dir.mkdir(exist_ok=True)
            caption_file.write_text(caption_content, encoding="utf-8")

        generated.append(num)
        print(f"✅ #{num:03d} {data['korean']} - {caption_type} 캡션 생성")

    return {
        "generated": generated,
        "skipped": skipped,
        "no_data": no_data
    }


def main():
    import sys

    if len(sys.argv) < 2:
        print("사용법: python generate_captions.py [insta|blog] [start] [end]")
        print("예시: python generate_captions.py insta 33 52")
        return

    caption_type = sys.argv[1]
    start = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    end = int(sys.argv[3]) if len(sys.argv) > 3 else 136

    dry_run = "--dry-run" in sys.argv

    nums = list(range(start, end + 1))

    print(f"{'🔍 DRY RUN - ' if dry_run else ''}캡션 생성: {caption_type} #{start:03d}~#{end:03d}")
    print("━" * 50)

    result = generate_captions_batch(nums, caption_type, dry_run)

    print("━" * 50)
    print(f"✅ 생성: {len(result['generated'])}개")
    print(f"⏭️ 스킵 (이미 존재): {len(result['skipped'])}개")
    print(f"❌ 데이터 없음: {len(result['no_data'])}개")

    if result['no_data']:
        print(f"\n데이터 필요: {result['no_data'][:10]}...")


if __name__ == "__main__":
    main()
