#!/usr/bin/env python3
"""
expand_blog_captions.py - 블로그 캡션 글자수 확충
목표: 1,620~1,980자
"""

import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"

# 햇살이 경험담 추가 문구 (안전도별)
HAESSARI_ADDITIONS = {
    "SAFE": [
        "햇살이는 {name} 냄새만 맡아도 꼬리를 흔들어요. 11년째 키우면서 느낀 건데, 자연 간식만큼 좋은 게 없더라고요.",
        "요즘 햇살이가 나이가 들어서 소화력이 예전 같지 않은데, {name}은 잘 소화하더라고요. 어르신 강아지한테도 추천해요.",
    ],
    "CAUTION": [
        "햇살이한테 처음 {name} 줬을 때 조금 걱정했었어요. 하지만 주의사항만 잘 지키니까 탈 없이 잘 먹더라고요.",
        "11살 시니어견인 햇살이도 {name}은 잘 먹어요. 다만 저는 항상 소량만 주고 반응을 꼭 확인해요.",
    ],
    "DANGER": [
        "솔직히 햇살이한테 {name}은 거의 안 줘요. 위험 부담이 있어서 다른 안전한 간식으로 대체하고 있어요.",
        "수의사 선생님도 {name}은 조심하라고 하셨어요. 굳이 위험을 감수할 필요 없잖아요.",
    ],
    "FORBIDDEN": [
        "햇살이한테 {name}은 절대 안 줘요. 한 번의 실수가 큰 사고로 이어질 수 있으니까요.",
        "주변에서 모르고 {name} 주셨다가 병원 갔다는 이야기 들으면 정말 마음이 아파요.",
    ]
}

# 추가 정보 문구
EXTRA_INFO = {
    "SAFE": """
저도 처음엔 '이거 줘도 되나?' 고민 많이 했어요. 인터넷에 정보가 너무 많아서 헷갈리더라고요. 직접 수의사 상담도 받고, 햇살이한테 조금씩 먹여보면서 정리한 내용이에요.

중요한 건 어떤 음식이든 '처음엔 소량, 반응 확인 후 늘리기'예요. 우리 아이들 체질이 다 다르니까요.
""",
    "CAUTION": """
보호자로서 항상 조심스럽게 접근하는 게 좋은 것 같아요. 저도 햇살이한테 새로운 음식 줄 때는 항상 수의사 선생님께 여쭤보고, 소량부터 시작해요.

'괜찮겠지'라는 생각보다는 '혹시 모르니까 조심하자'가 우리 아이들 건강을 지키는 방법이에요.
""",
    "DANGER": """
제가 이런 정보를 공유하는 이유는, 저도 처음엔 몰랐던 것들이 많았기 때문이에요. 11년 동안 햇살이 키우면서 배운 것들을 나누고 싶어요.

위험한 음식은 피하고, 안전한 대체 간식을 찾아주는 게 현명한 선택이에요.
""",
    "FORBIDDEN": """
이 글을 쓰는 이유는 정말 많은 분들이 모르고 급여하시기 때문이에요. 저도 처음엔 몰랐어요.

우리 아이들 건강을 위해 꼭 알아두셔야 할 정보라서 공유해요. 주변에 반려견 키우시는 분들께도 꼭 알려주세요!
"""
}

# 추가 경험담 (더 많은 글자수 확보용)
MORE_EXPERIENCE = {
    "SAFE": """
11년간 햇살이와 함께하면서 정말 많은 음식을 시도해봤어요. 처음엔 뭘 줘야 할지, 뭘 피해야 할지 막막했는데, 이제는 어느 정도 감이 생겼답니다.

강아지마다 체질이 다르니까, 새로운 음식을 줄 때는 항상 소량부터 시작하는 게 좋아요. 저도 햇살이한테 새 간식 줄 때는 콩알만큼만 주고 24시간 관찰해요.

우리 아이들 건강은 보호자의 작은 관심에서 시작된다고 생각해요. 이 글이 여러분과 반려견에게 도움이 되길 바라요!
""",
    "CAUTION": """
강아지 음식 정보는 정말 신중하게 확인해야 해요. 인터넷에 잘못된 정보도 많고, 강아지마다 반응이 다르거든요.

저는 새로운 음식을 줄 때 항상 이 세 가지를 확인해요: 1) 수의사 의견, 2) 햇살이 반응, 3) 변 상태. 이 세 가지만 체크해도 대부분의 문제를 예방할 수 있어요.

11살 시니어견인 햇살이도 이제 소화력이 예전 같지 않아서, 새로운 음식은 더 조심스럽게 급여하고 있어요.
""",
    "DANGER": """
위험한 음식 정보는 꼭 알아두셔야 해요. 저도 처음엔 몰랐던 것들이 많았어요. 11년 동안 햇살이 키우면서 배운 것들을 공유해요.

주변에서 모르고 급여했다가 응급실 갔다는 이야기를 종종 들어요. 사전에 알고 있었다면 피할 수 있었을 텐데 하는 마음이 들어요.

우리 아이들 건강을 위해 위험한 음식은 아예 손이 닿지 않는 곳에 보관하는 습관을 들이세요!
""",
    "FORBIDDEN": """
절대 급여 금지 음식은 정말 조심해야 해요. 소량이라도 독성이 있어서 한 번의 실수가 큰 사고로 이어질 수 있어요.

주변에서 모르고 급여했다가 병원에 입원했다는 이야기를 들을 때마다 마음이 아파요. 이런 일이 없도록 정보를 널리 알려야 해요.

저도 처음에는 이런 정보를 몰랐어요. 반려견을 키우기 시작하면서 하나씩 배워갔죠. 이 글이 다른 보호자분들께 도움이 되길 바라요.
"""
}

# FAQ 추가
FAQ_TEMPLATES = {
    "SAFE": """
## 자주 묻는 질문

**Q. {name} 매일 줘도 되나요?**
A. 매일 급여는 권장하지 않아요. 간식은 하루 칼로리의 10% 이내로, 주 2~3회가 적당해요.

**Q. 강아지가 {name} 안 먹으면 어떡하나요?**
A. 강아지마다 기호가 달라요. 억지로 먹이지 말고 다른 간식으로 대체해주세요.
""",
    "CAUTION": """
## 자주 묻는 질문

**Q. {name} 얼마나 자주 줘도 되나요?**
A. 주 1~2회 이내로 제한하세요. CAUTION 식품은 자주 급여하지 않는 게 좋아요.

**Q. {name} 먹고 토하면 어떡하나요?**
A. 즉시 급여를 중단하고, 증상이 지속되면 동물병원에 방문하세요.
""",
    "DANGER": """
## 자주 묻는 질문

**Q. {name} 정말 안 되나요?**
A. 소량 급여는 가능하지만 위험 부담이 있어요. 가급적 피하시는 게 좋아요.

**Q. 실수로 {name} 먹었어요, 어떡하죠?**
A. 소량이면 관찰하시고, 증상이 나타나면 즉시 동물병원에 방문하세요.
""",
    "FORBIDDEN": """
## 자주 묻는 질문

**Q. {name} 조금만 줘도 안 되나요?**
A. 네, 소량이라도 절대 급여하면 안 돼요. 독성이 축적될 수 있어요.

**Q. 실수로 {name} 먹었어요!**
A. 당황하지 마시고, 먹은 양과 시간을 기억한 후 즉시 동물병원으로 가세요.
"""
}


# 슬라이드 3 - DogWithFood 장면 추가 문구 (주인이 조리하고 강아지가 보는 모습)
# 이미지 네이밍: {음식명}_Common_03_DogWithFood.png
# 저장 경로: 콘텐츠 폴더 루트 (Common_01, Common_02와 동일)
SLIDE3_COOKING_PREP = {
    "SAFE": """
[이미지 3번: DogWithFood - 햇살이가 보호자의 조리 과정을 지켜보는 모습]

우리 햇살이는 제가 {name} 손질할 때마다 옆에 와서 지켜봐요. "엄마, 그거 나 주는 거지?" 하는 눈빛으로요. 11년을 함께해도 간식 앞에서는 여전히 아기 강아지 같아요.

{name} 급여 전에는 꼭 깨끗이 씻고, 강아지에게 맞게 손질해주세요. 저도 햇살이 주기 전에 항상 한 번 더 확인해요.
""",
    "CAUTION": """
[이미지 3번: DogWithFood - 햇살이가 조심스럽게 기다리는 모습]

햇살이가 제 옆에서 조리 과정을 지켜볼 때면, '우리 아이한테 안전하게 줘야지' 하는 마음이 더 커져요. CAUTION 등급 음식은 특히 더 꼼꼼하게 준비해요.

{name}은(는) 반드시 주의사항을 지켜서 급여해야 해요. 저도 햇살이한테 줄 때는 항상 적정량만 덜어서 줍니다.
""",
    "DANGER": """
[이미지 3번: DogWithFood - 음식 손질 시 주의가 필요한 상황]

저도 처음엔 모르고 {name}을(를) 줄 뻔했어요. 하지만 위험성을 알고 나서는 햇살이 눈앞에서 먹지 않으려고 해요. 강아지들은 보호자가 먹는 걸 보면 자기도 먹고 싶어하거든요.

혹시 {name}을(를) 드실 때는 강아지가 접근하지 못하는 곳에서 드시는 게 좋아요.
""",
    "FORBIDDEN": """
[이미지 3번: DogWithFood - 강아지 접근 금지 상황]

햇살이가 제가 뭘 먹든 옆에서 지켜보곤 해요. 하지만 {name}만큼은 절대 줄 수 없어요. 눈빛이 아무리 간절해도요.

{name}은(는) 강아지에게 독성이 있어서 절대 급여하면 안 돼요. 조리하실 때도 강아지가 접근하지 못하게 주의해주세요.
"""
}

# 해시태그 템플릿
HASHTAG_TEMPLATES = {
    "SAFE": "#강아지{name_no_space} #강아지간식 #반려견음식 #강아지건강 #펫푸드 #강아지케어 #골든리트리버 #시니어독 #강아지정보 #반려견가이드 #강아지음식가이드 #dogfood #doghealth #petcare #노령견간식 #강아지과일",
    "CAUTION": "#강아지{name_no_space} #강아지간식 #반려견음식 #강아지건강 #펫푸드 #강아지케어 #골든리트리버 #시니어독 #강아지정보 #반려견가이드 #강아지음식가이드 #dogfood #doghealth #petcare #강아지주의음식 #강아지간식추천",
    "DANGER": "#강아지{name_no_space} #강아지간식 #반려견음식 #강아지건강 #펫푸드 #강아지케어 #골든리트리버 #시니어독 #강아지정보 #반려견가이드 #강아지음식가이드 #dogfood #doghealth #petcare #강아지위험음식 #강아지음식주의",
    "FORBIDDEN": "#강아지금지음식 #강아지{name_no_space} #반려견음식 #강아지건강 #펫푸드 #강아지케어 #골든리트리버 #시니어독 #강아지정보 #반려견가이드 #강아지음식가이드 #dogfood #doghealth #petcare #강아지위험음식 #강아지과자금지"
}


def get_char_count(content: str) -> int:
    """글자수 계산 (공백, 줄바꿈 제외)"""
    return len(content.replace(" ", "").replace("\n", ""))


def fix_grammar(content: str, name: str) -> str:
    """조사 오류 수정"""
    # 받침 확인
    last_char = name[-1]
    has_batchim = (ord(last_char) - 44032) % 28 != 0 if '가' <= last_char <= '힣' else False

    # 을/를
    content = content.replace(f"{name}을(를)", f"{name}을" if has_batchim else f"{name}를")
    content = content.replace(f"{name}을 (를)", f"{name}을" if has_batchim else f"{name}를")

    # 은/는
    content = content.replace(f"{name}은(는)", f"{name}은" if has_batchim else f"{name}는")
    content = content.replace(f"{name}은 (는)", f"{name}은" if has_batchim else f"{name}는")

    # 이/가
    content = content.replace(f"{name}이(가)", f"{name}이" if has_batchim else f"{name}가")

    return content


def remove_ai_notice(content: str) -> str:
    """AI 고지 제거"""
    lines = content.split("\n")
    new_lines = []
    skip_next = False

    for line in lines:
        # AI 고지 패턴
        if "AI의 도움" in line or "AI로 생성" in line or "⚠️ 이 콘텐츠는 AI" in line:
            skip_next = True
            continue
        if skip_next and ("수의사와 상담" in line or "전문적인" in line):
            skip_next = False
            continue
        if "---" in line and len(line.strip()) <= 5:
            # 구분선도 체크
            continue
        new_lines.append(line)

    return "\n".join(new_lines)


def add_hashtags(content: str, name: str, safety: str) -> str:
    """해시태그 추가"""
    # 이미 해시태그가 있으면 스킵
    if re.search(r'#강아지\w+', content):
        return content

    name_no_space = name.replace(" ", "")
    hashtags = HASHTAG_TEMPLATES.get(safety, HASHTAG_TEMPLATES["SAFE"]).format(name_no_space=name_no_space)

    # 마지막에 추가
    content = content.rstrip()
    content += f"\n\n{hashtags}\n"

    return content


def add_slide3_cooking_prep(content: str, name: str, safety: str) -> str:
    """슬라이드 3 (DogWithFood 장면) 추가

    주인이 음식을 조리/손질하는 것을 강아지가 지켜보는 장면.
    이미지 네이밍: {음식명}_Common_03_DogWithFood.png
    저장 경로: 콘텐츠 폴더 루트 (Common_01, Common_02와 동일)

    기존 [이미지 3번: 영양 정보] 를 DogWithFood 장면으로 교체 또는 보강.
    """
    # 이미 슬라이드 3 DogWithFood 내용이 있으면 스킵
    if "DogWithFood" in content or "손질할 때" in content:
        return content

    slide3_text = SLIDE3_COOKING_PREP.get(safety, SLIDE3_COOKING_PREP["SAFE"]).format(name=name).strip()

    # [이미지 3번: 영양 정보] 패턴 찾기
    pattern = r'\[이미지\s*3번[:\s][^\]]*\]'
    match = re.search(pattern, content)

    if match:
        # 기존 [이미지 3번] 태그를 슬라이드 3 내용으로 교체
        content = re.sub(pattern, slide3_text, content, count=1)
    else:
        # [이미지 2번] 다음에 슬라이드 3 삽입
        pattern2 = r'(\[이미지\s*2번[^\]]*\])'
        match2 = re.search(pattern2, content)
        if match2:
            insert_pos = match2.end()
            content = content[:insert_pos] + "\n\n" + slide3_text + "\n" + content[insert_pos:]

    return content


def fix_dosage_format(content: str) -> str:
    """급여량 형식 수정 - 직관적 단위 추가

    변환 전: - 소형견 (5kg 이하): 5~10g - 아주 소량
    변환 후: **소형견 (5kg 이하)** — 5~10g (아주 소량)
    """
    # 패턴 1: "- 소형견 (5kg 이하): 5~10g - 아주 소량" 형식
    pattern1 = r'-\s*(소형견|중형견|대형견|초대형견)\s*\(([^)]+)\)\s*:\s*(\d+[~\-]\d+g)\s*-\s*(.+?)(?=\n|$)'

    def replace_format1(match):
        size = match.group(1)
        weight = match.group(2)
        amount = match.group(3)
        desc = match.group(4).strip()
        return f"**{size} ({weight})** — {amount} ({desc})"

    content = re.sub(pattern1, replace_format1, content)

    # 패턴 2: "- 소형견 (5kg 이하): 5~10g (설명)" 형식 (이미 괄호 있음)
    pattern2 = r'-\s*(소형견|중형견|대형견|초대형견)\s*\(([^)]+)\)\s*:\s*(\d+[~\-]\d+g)\s*\(([^)]+)\)'

    def replace_format2(match):
        size = match.group(1)
        weight = match.group(2)
        amount = match.group(3)
        desc = match.group(4).strip()
        return f"**{size} ({weight})** — {amount} ({desc})"

    content = re.sub(pattern2, replace_format2, content)

    # 패턴 3: "소형견 (5kg 이하): 5~10g - 설명" 형식 (하이픈 없이 시작)
    pattern3 = r'(?<!\*)\b(소형견|중형견|대형견|초대형견)\s*\(([^)]+)\)\s*:\s*(\d+[~\-]\d+g)\s*-\s*(.+?)(?=\n|$)'

    def replace_format3(match):
        size = match.group(1)
        weight = match.group(2)
        amount = match.group(3)
        desc = match.group(4).strip()
        return f"**{size} ({weight})** — {amount} ({desc})"

    content = re.sub(pattern3, replace_format3, content)

    return content


def expand_blog_caption(content: str, name: str, safety: str) -> str:
    """블로그 캡션 확충 + 정리"""
    # 1. AI 고지 제거
    content = remove_ai_notice(content)

    # 2. 조사 오류 수정
    content = fix_grammar(content, name)

    # 3. 급여량 형식 수정 (직관적 단위)
    content = fix_dosage_format(content)

    # 4. 슬라이드 3 (조리 준비 장면) 추가
    content = add_slide3_cooking_prep(content, name, safety)

    # 5. 해시태그 추가
    content = add_hashtags(content, name, safety)

    current_count = get_char_count(content)

    if current_count >= 1620:
        return content  # 이미 충분함

    needed = 1750 - current_count  # 목표 1750자 (여유분 포함)
    additions = []

    # 1. 햇살이 경험담 추가 (마무리 섹션 앞에)
    haessari_text = HAESSARI_ADDITIONS.get(safety, HAESSARI_ADDITIONS["SAFE"])[0].format(name=name)
    additions.append(("haessari", haessari_text))

    # 2. 추가 정보 (주의사항 섹션 뒤에)
    extra_text = EXTRA_INFO.get(safety, EXTRA_INFO["SAFE"]).strip()
    additions.append(("extra", extra_text))

    # 3. FAQ (마무리 앞에)
    faq_text = FAQ_TEMPLATES.get(safety, FAQ_TEMPLATES["SAFE"]).format(name=name).strip()
    additions.append(("faq", faq_text))

    # 내용 삽입
    lines = content.split("\n")
    new_lines = []

    haessari_added = False
    extra_added = False
    faq_added = False

    for i, line in enumerate(lines):
        new_lines.append(line)

        # 주의사항 섹션 뒤에 추가 정보 삽입
        if "## 주의사항" in line and not extra_added:
            # 주의사항 섹션 내용 찾기 (다음 ## 전까지)
            for j in range(i+1, len(lines)):
                if lines[j].startswith("##") or "[이미지" in lines[j]:
                    # 이미지 태그 앞에 삽입
                    break

        # [이미지 6번] 뒤에 추가 정보 삽입
        if "[이미지 6번" in line and not extra_added:
            new_lines.append("")
            new_lines.append(extra_text)
            extra_added = True

        # ## 간단 레시피 앞에 FAQ 삽입
        if "## 간단 레시피" in line and not faq_added:
            # 앞에 삽입
            new_lines.pop()  # ## 간단 레시피 제거
            new_lines.append("")
            new_lines.append(faq_text)
            new_lines.append("")
            new_lines.append(line)  # ## 간단 레시피 다시 추가
            faq_added = True

        # ## 마무리 앞에 햇살이 경험담 추가
        if "## 마무리" in line and not haessari_added:
            new_lines.pop()
            new_lines.append("")
            new_lines.append(haessari_text)
            new_lines.append("")
            new_lines.append(line)
            haessari_added = True

    result = "\n".join(new_lines)

    # 글자수 부족하면 추가 경험담 삽입
    if get_char_count(result) < 1620:
        more_exp = MORE_EXPERIENCE.get(safety, MORE_EXPERIENCE["SAFE"]).strip()
        # [이미지 8번] 앞에 삽입
        if "[이미지 8번" in result:
            result = result.replace("[이미지 8번", f"{more_exp}\n\n[이미지 8번")
        else:
            # 마지막 해시태그 앞에 삽입
            lines = result.split("\n")
            new_lines = []
            inserted = False
            for line in lines:
                if line.startswith("#강아지") and not inserted:
                    new_lines.append(more_exp)
                    new_lines.append("")
                    inserted = True
                new_lines.append(line)
            result = "\n".join(new_lines)

    return result


def main():
    start_id = 6
    end_id = 20

    if len(sys.argv) >= 3:
        start_id = int(sys.argv[1])
        end_id = int(sys.argv[2])

    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    print("=" * 60)
    print(f"블로그 캡션 글자수 확충 ({start_id:03d}~{end_id:03d})")
    print("=" * 60)

    updated = 0
    skipped = 0

    for food_id in range(start_id, end_id + 1):
        food_id_str = str(food_id)

        if food_id_str not in food_data:
            continue

        data = food_data[food_id_str]
        name = data.get("name", "")
        safety = data.get("safety", "SAFE")

        folder_pattern = f"{food_id:03d}_*"
        matches = list(CONTENTS_DIR.glob(folder_pattern))

        if not matches:
            continue

        blog_folder = matches[0] / "02_Blog"
        caption_files = list(blog_folder.glob("*_Blog_Caption.txt"))

        if not caption_files:
            continue

        caption_file = caption_files[0]
        content = caption_file.read_text(encoding='utf-8')

        before_count = get_char_count(content)

        # 확충 + 정리 (AI 고지 제거, 조사 수정, 해시태그 추가)
        new_content = expand_blog_caption(content, name, safety)
        after_count = get_char_count(new_content)

        # 변경사항이 있으면 저장
        if new_content != content:
            caption_file.write_text(new_content, encoding='utf-8')
            print(f"[OK] {food_id:03d} {name}: {before_count}자 → {after_count}자 (+{after_count - before_count})")
            updated += 1
        else:
            print(f"[SKIP] {food_id:03d} {name}: 변경 없음 ({before_count}자)")
            skipped += 1

    print("=" * 60)
    print(f"완료: {updated}개 확충, {skipped}개 스킵")
    print("=" * 60)


if __name__ == "__main__":
    main()
