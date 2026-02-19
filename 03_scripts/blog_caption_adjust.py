#!/usr/bin/env python3
"""
블로그 캡션 글자수 개별 조정
초과: FAQ 줄이기, 부족: 내용 추가
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"

TARGET_MIN = 1620
TARGET_MAX = 1980

def load_food_data():
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def get_folder(num: int) -> Path:
    pattern = f"{num:03d}_*"
    matches = list(CONTENTS_DIR.glob(pattern))
    return matches[0] if matches else None

def find_blog_caption(folder: Path) -> Path:
    new_path = folder / "blog" / "caption.txt"
    if new_path.exists():
        return new_path
    old_dir = folder / "02_Blog"
    if old_dir.exists():
        for f in old_dir.glob("*_Blog_Caption.txt"):
            return f
    return None

def shorten_caption(content: str, target: int = 1900) -> str:
    """캡션 줄이기 (FAQ 축소)"""
    # Q3 질문/답변 제거
    content = re.sub(r'\n\nQ3\.[^\n]+\nA3\.[^\n]+', '', content)

    if len(content) <= target:
        return content

    # 추가 축소: 긴 문장 축소
    content = content.replace("11살 골든리트리버 햇살이를 키우면서 얻은 경험과 수의사 선생님의 조언을 바탕으로 정리했습니다.",
                             "11살 햇살이를 키우며 얻은 경험을 바탕으로 정리했습니다.")
    content = content.replace("이러한 영양소들이 강아지의 건강 유지에 도움을 줄 수 있어요.",
                             "강아지 건강에 도움이 돼요.")
    content = content.replace("강아지마다 개체 차이가 있으므로 처음 급여 시에는 반드시 소량부터 시작하고 반응을 관찰해주세요.",
                             "개체 차이가 있으니 소량부터 시작하세요.")

    return content

def lengthen_caption(content: str, food_name: str, safety: str, target: int = 1700) -> str:
    """캡션 늘리기 (내용 추가)"""
    current_len = len(content)
    needed = target - current_len

    if needed <= 0:
        return content

    # 추가할 내용
    additions = []

    if safety in ["DANGER", "FORBIDDEN"]:
        # DANGER/FORBIDDEN 추가 내용
        extra_warning = f"""

강아지의 건강은 보호자의 관심에서 시작됩니다. {food_name}처럼 위험한 음식은 미리 알고 피하는 것이 중요해요. 저희 햇살이도 11년 동안 건강하게 지낼 수 있었던 건 위험 음식을 철저히 피했기 때문이에요.

혹시 모르는 사이에 {food_name}이 포함된 음식을 줬을 수도 있어요. 그래서 항상 성분표를 확인하는 습관이 중요합니다. 특히 사람이 먹는 가공식품이나 간식에는 예상치 못한 성분이 들어있을 수 있으니 주의하세요."""
        additions.append(extra_warning)

        extra_tips = """

보호자님들께 드리는 팁: 강아지가 접근할 수 있는 곳에 위험한 음식을 두지 마세요. 특히 테이블 위나 낮은 선반은 강아지가 쉽게 닿을 수 있어요. 안전한 보관이 사고를 예방합니다."""
        additions.append(extra_tips)

    else:
        # SAFE/CAUTION 추가 내용
        extra_info = f"""

저희 햇살이는 {food_name}을 가끔 간식으로 받으면 정말 좋아해요. 처음 줬을 때 반응이 좋아서 지금까지 가끔씩 급여하고 있어요. 물론 적정량을 지키는 게 중요하답니다."""
        additions.append(extra_info)

    # 필요한 만큼 추가
    for add in additions:
        if len(content) >= target:
            break
        # [이미지 9번 앞에 삽입
        if "[이미지 9번" in content:
            content = content.replace("[이미지 9번", add + "\n\n[이미지 9번")
        else:
            content += add

    return content

def save_caption(folder: Path, content: str, safety: str):
    new_dir = folder / "blog"
    new_dir.mkdir(exist_ok=True)
    new_path = new_dir / "caption.txt"

    old_dir = folder / "02_Blog"
    old_dir.mkdir(exist_ok=True)
    folder_parts = folder.name.split("_", 1)
    eng_name = folder_parts[1] if len(folder_parts) > 1 else "Food"
    old_path = old_dir / f"{eng_name}_{safety}_Blog_Caption.txt"

    with open(new_path, "w", encoding="utf-8") as f:
        f.write(content)
    with open(old_path, "w", encoding="utf-8") as f:
        f.write(content)

def main():
    food_data = load_food_data()

    # 범위 밖 건들
    out_of_range = {
        # 초과 (줄여야 함)
        8: "초과", 9: "초과", 10: "초과", 11: "초과", 12: "초과", 13: "초과",
        14: "초과", 15: "초과", 16: "초과", 17: "초과", 18: "초과", 19: "초과",
        21: "초과", 24: "초과", 25: "초과", 26: "초과", 90: "초과",
        108: "초과", 111: "초과", 115: "초과", 169: "초과",
        # 부족 (늘려야 함)
        23: "부족", 138: "부족", 144: "부족", 157: "부족", 158: "부족",
        159: "부족", 162: "부족", 166: "부족", 170: "부족", 171: "부족"
    }

    print("=" * 60)
    print("📝 블로그 캡션 글자수 개별 조정")
    print("=" * 60)

    adjusted = 0
    still_out = []

    for num, direction in out_of_range.items():
        food = food_data.get(str(num), {})
        if not food:
            continue

        safety = food.get("safety", "SAFE")
        name = food.get("name", f"음식{num}")

        folder = get_folder(num)
        if not folder:
            continue

        caption_path = find_blog_caption(folder)
        if not caption_path:
            continue

        with open(caption_path, "r", encoding="utf-8") as f:
            content = f.read()

        original_len = len(content)

        if direction == "초과":
            content = shorten_caption(content, 1900)
        else:
            content = lengthen_caption(content, name, safety, 1700)

        new_len = len(content)

        save_caption(folder, content, safety)

        if TARGET_MIN <= new_len <= TARGET_MAX:
            status = "✅"
            adjusted += 1
        else:
            status = "⚠️"
            still_out.append((num, name, new_len, direction))

        print(f"  {status} {num:03d} {name}: {original_len}→{new_len}자 ({direction})")

    print("\n" + "=" * 60)
    print(f"📊 조정 완료: {adjusted}건 범위 내")

    if still_out:
        print(f"\n⚠️ 여전히 범위 밖: {len(still_out)}건")
        for num, name, count, direction in still_out:
            print(f"   {num:03d} {name}: {count}자")

    print("=" * 60)

if __name__ == "__main__":
    main()
