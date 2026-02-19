#!/usr/bin/env python3
"""
Threads Caption v1.1 Batch Converter
021번 ~ 175번까지 144개 파일 일괄 변환

v1.1 규칙:
1. 영문 먼저 시작 (한글은 마지막 문장으로)
2. #CanMyDogEatThis 필수 (마지막에)
3. 해시태그 2개 이하
4. 500자 이하
5. 안전도별 톤:
   - SAFE: 긍정적, 급여량 포함
   - CAUTION: 조건부 안전, 주의사항 강조
   - DANGER: 경고 톤
   - FORBIDDEN: 경고, 절대 금지 강조
"""

import json
import os
from pathlib import Path

BASE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine")
CONTENTS_DIR = BASE_DIR / "01_contents"
FOOD_DATA_PATH = BASE_DIR / "config" / "food_data.json"

# 한국어 -> 영어 번역 매핑
BENEFIT_TRANSLATIONS = {
    "눈 건강": "eye health",
    "장 건강": "digestive health",
    "면역력 강화": "immune support",
    "항산화": "antioxidant",
    "심장 건강": "heart health",
    "수분 보충": "hydration",
    "혈액 응고": "blood clotting",
    "저칼로리": "low calorie",
    "건강 유지": "overall health",
    "피부 건강": "skin health",
    "뼈 건강": "bone health",
    "근육 강화": "muscle support",
    "에너지 공급": "energy boost",
    "체중 관리": "weight management",
    "소화 개선": "better digestion",
    "신경 독성": "neurotoxin",
    "소화 장애": "digestive issues",
    "심박 이상": "heart rate issues",
    "비만/당뇨 위험": "obesity/diabetes risk",
    "알레르기 유발 가능": "potential allergen",
    "심근 독성": "cardiac toxicity",
    "췌장염 위험": "pancreatitis risk",
    "적혈구 파괴": "destroys red blood cells",
    "용혈성 빈혈": "hemolytic anemia",
    "용혈성 빈혈 유발": "causes hemolytic anemia",
    "신장 손상": "kidney damage",
    "간 손상": "liver damage",
    "중추신경 장애": "CNS damage",
    "혈당 급상승": "blood sugar spike",
    "고농도 나트륨": "high sodium content",
    "신장 문제": "kidney problems",
    "유당 불내증": "lactose intolerance",
    "독성 물질": "toxic substances",
    "당분 과다": "excess sugar",
    "카페인": "caffeine",
    "테오브로민": "theobromine",
    "알코올": "alcohol",
    "자일리톨": "xylitol",
    "탄산": "carbonation",
    "인공 감미료": "artificial sweeteners",
    "고지방": "high fat",
    "고염분": "high sodium",
    "양념": "seasonings",
    "발효": "fermentation",
    "심장 독성": "cardiac toxicity",
    "신경 독성": "neurotoxicity",
    "간독성": "liver toxicity",
    "신독성": "kidney toxicity",
    "위장 장애": "gastrointestinal issues",
    "구토 유발": "causes vomiting",
    "설사 유발": "causes diarrhea",
    "발작 유발": "can cause seizures",
    "고칼로리": "high calorie",
    "당 과다": "excess sugar",
    "염분 과다": "excess sodium",
    "지방 과다": "excess fat",
    "급성 신부전 유발": "causes acute kidney failure",
    "소화기 손상": "digestive system damage",
    "피모 건강": "skin & coat health",
    "근육 형성": "muscle development",
    "오메가3": "omega-3 fatty acids",
    "DHA": "brain health (DHA)",
    "EPA": "anti-inflammatory (EPA)",
    "단백질": "protein",
    "비타민 D": "vitamin D",
    "비타민 E": "vitamin E",
    "비타민 B12": "vitamin B12",
    "철분": "iron",
    "아연": "zinc",
    "셀레늄": "selenium",
    "칼슘": "calcium",
    "마그네슘": "magnesium",
    "인": "phosphorus",
    "요오드": "iodine",
    "콜라겐": "collagen",
    "타우린": "taurine",
    "관절 건강": "joint health",
    "치아 건강": "dental health",
    "두뇌 발달": "brain development",
    "노화 방지": "anti-aging",
    "탈수 방지": "prevents dehydration",
    "포만감": "satiety",
    "저당": "low sugar",
    "저지방": "low fat",
    "고단백": "high protein",
    "무첨가": "no additives",
}

def convert_korean_amount_to_english(amount: str) -> str:
    """한국어 급여량을 영어로 변환"""
    # 한글 단위 -> 영문 단위 변환
    conversions = {
        "알": " berries",
        "개": " pieces",
        "조각": " pieces",
        "스푼": " spoons",
        "장": " leaves",
        "컵": " cups",
        "봉지": " packets",
        "숟가락": " tablespoons",
    }
    result = amount
    for kor, eng in conversions.items():
        result = result.replace(kor, eng)
    return result

def translate_benefit(korean: str) -> str:
    """한국어 효능을 영어로 번역"""
    return BENEFIT_TRANSLATIONS.get(korean, korean)

def load_food_data():
    """food_data.json 로드"""
    with open(FOOD_DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_english_food_name(english_name: str) -> str:
    """영문 이름 정규화 (언더스코어/한글 제거)"""
    # "blackberry_블랙베리" -> "blackberry"
    if '_' in english_name:
        parts = english_name.split('_')
        # 영어 부분만 추출 (한글 아닌 부분)
        for part in parts:
            if part.isascii():
                return part.lower()
    return english_name.lower()

def format_food_for_display(english_name: str) -> str:
    """표시용 영문명 (첫 글자 대문자)"""
    clean = get_english_food_name(english_name)
    # CamelCase 처리
    words = []
    current = ""
    for char in clean:
        if char.isupper() and current:
            words.append(current)
            current = char.lower()
        else:
            current += char.lower()
    if current:
        words.append(current)
    return ' '.join(w.capitalize() for w in words)

def generate_safe_caption(food_data: dict, folder_name: str) -> str:
    """SAFE 안전도 캡션 생성"""
    korean_name = food_data['name']
    english_name = format_food_for_display(food_data.get('english_name', folder_name))

    # 영양소 효능 추출 (영어로 번역)
    benefits = []
    for nutrient in food_data.get('nutrients', [])[:3]:
        benefit = nutrient.get('benefit', '')
        benefits.append(translate_benefit(benefit))

    # 급여량 추출 (영문화)
    dosages = food_data.get('dosages', {})
    small_amt = convert_korean_amount_to_english(dosages.get('소형견', {}).get('amount', '15-20g'))
    medium_amt = convert_korean_amount_to_english(dosages.get('중형견', {}).get('amount', '30-40g'))
    large_amt = convert_korean_amount_to_english(dosages.get('대형견', {}).get('amount', '50-70g'))

    caption = f"""You've definitely googled "can my dog eat {english_name.lower()}" at least once

Yes — {english_name.lower()} is safe for dogs.
→ Rich in nutrients, great for {benefits[0] if len(benefits) > 0 else 'overall health'}
→ Supports {benefits[1] if len(benefits) > 1 else 'digestion'}
→ Always wash and cut into small pieces

Serving: small dogs {small_amt}, medium {medium_amt}, large {large_amt}

우리 햇살이는 {korean_name} 먹을 때 눈이 반짝반짝해요 🐾

#CanMyDogEatThis #{english_name.replace(' ', '')}ForDogs"""

    return caption.strip()

def generate_caution_caption(food_data: dict, folder_name: str) -> str:
    """CAUTION 안전도 캡션 생성"""
    korean_name = food_data['name']
    english_name = format_food_for_display(food_data.get('english_name', folder_name))

    # 영양소 효능 (영어로 번역)
    benefits = []
    for nutrient in food_data.get('nutrients', [])[:2]:
        benefit = nutrient.get('benefit', '')
        benefits.append(translate_benefit(benefit))

    caption = f"""{english_name} is safe for dogs — but there's a catch

🟡 Conditions apply:
→ Small amounts only
→ Remove seeds, skin, or pits if applicable
→ Not for dogs with allergies or sensitive stomachs
→ Watch for digestive issues after first try

Good for {benefits[0] if benefits else 'nutrition'}, but moderation is key.

우리 햇살이도 {korean_name}은 조금씩만 줘요.
과하면 탈나니까 🐾

#CanMyDogEatThis #DogFoodSafety"""

    return caption.strip()

def generate_danger_caption(food_data: dict, folder_name: str) -> str:
    """DANGER 안전도 캡션 생성"""
    korean_name = food_data['name']
    english_name = format_food_for_display(food_data.get('english_name', folder_name))

    # 위험 이유
    precautions = food_data.get('precautions', [])
    danger_reason = precautions[0].get('desc', '위험할 수 있어요') if precautions else '위험할 수 있어요'

    caption = f"""🚨 Most people don't know {english_name.lower()} can be dangerous for dogs

The flesh? Maybe OK in tiny amounts.
But certain parts are toxic.

→ Even small amounts can cause problems
→ Symptoms: vomiting, diarrhea, lethargy
→ If your dog ate any → contact vet immediately

Safe alternative: check with your vet for dog-safe treats

햇살이한테는 절대 안 줘요.
아무리 눈빛으로 졸라도, 이건 엄마가 지켜야 할 선이에요 🐾

#CanMyDogEatThis #DogSafety"""

    return caption.strip()

def generate_forbidden_caption(food_data: dict, folder_name: str) -> str:
    """FORBIDDEN 안전도 캡션 생성"""
    korean_name = food_data['name']
    english_name = format_food_for_display(food_data.get('english_name', folder_name))

    # 독성 정보 (영어로 번역)
    nutrients = food_data.get('nutrients', [])
    toxin_info = []
    for n in nutrients[:2]:
        if n.get('benefit'):
            translated = translate_benefit(n.get('benefit'))
            toxin_info.append(translated)

    caption = f"""🚫 {english_name} can seriously harm your dog. Not "maybe." Definitely.

There is NO safe amount. Here's why:
→ {toxin_info[0] if toxin_info else 'Contains toxic compounds'}
→ {toxin_info[1] if len(toxin_info) > 1 else 'Can cause severe health issues'}
→ Symptoms may appear hours or days later

If your dog ate {english_name.lower()}:
→ Note the amount and time
→ Contact your vet immediately
→ Do NOT induce vomiting without vet guidance

11년째 키우면서 {korean_name}만큼은 철저하게 관리해요.
몰랐다면 괜찮아요. 지금 알았으니까요 🐾

#CanMyDogEatThis #ToxicFoodForDogs"""

    return caption.strip()

def find_caption_file(folder_path: Path) -> Path | None:
    """캡션 파일 찾기"""
    insta_thread_dir = folder_path / "01_Insta&Thread"
    if not insta_thread_dir.exists():
        return None

    for f in insta_thread_dir.iterdir():
        if f.name.endswith('_Threads_Caption.txt'):
            return f
    return None

def get_folder_number(folder_name: str) -> int:
    """폴더명에서 번호 추출"""
    try:
        return int(folder_name.split('_')[0])
    except:
        return 0

def main():
    print("=" * 60)
    print("Threads Caption v1.1 Batch Converter")
    print("범위: 021번 ~ 175번")
    print("=" * 60)

    # food_data 로드
    food_data = load_food_data()
    print(f"✓ food_data.json 로드 완료 ({len(food_data)}개 음식)")

    # 결과 집계
    results = {
        'success': [],
        'skip': [],
        'error': []
    }

    # 폴더 순회
    for folder in sorted(CONTENTS_DIR.iterdir()):
        if not folder.is_dir():
            continue

        folder_num = get_folder_number(folder.name)

        # 021 ~ 175 범위만 처리
        if folder_num < 21 or folder_num > 175:
            continue

        # food_data에서 해당 음식 정보 찾기
        food_info = food_data.get(str(folder_num))
        if not food_info:
            results['skip'].append((folder.name, "food_data에 정보 없음"))
            continue

        safety = food_info.get('safety', 'SAFE').upper()

        # 캡션 파일 찾기
        caption_file = find_caption_file(folder)
        if not caption_file:
            # 파일이 없으면 생성
            insta_thread_dir = folder / "01_Insta&Thread"
            if not insta_thread_dir.exists():
                insta_thread_dir.mkdir(parents=True, exist_ok=True)

            # 폴더명에서 영문 이름 추출
            food_english = folder.name.split('_', 1)[1] if '_' in folder.name else folder.name
            caption_file = insta_thread_dir / f"{food_english}_{safety}_Threads_Caption.txt"

        # 안전도별 캡션 생성
        try:
            if safety == 'SAFE':
                new_caption = generate_safe_caption(food_info, folder.name)
            elif safety == 'CAUTION':
                new_caption = generate_caution_caption(food_info, folder.name)
            elif safety == 'DANGER':
                new_caption = generate_danger_caption(food_info, folder.name)
            elif safety == 'FORBIDDEN':
                new_caption = generate_forbidden_caption(food_info, folder.name)
            else:
                results['error'].append((folder.name, f"알 수 없는 안전도: {safety}"))
                continue

            # 500자 체크
            if len(new_caption) > 500:
                print(f"⚠️ {folder.name}: {len(new_caption)}자 (500자 초과 - 자동 조정)")
                # 간단히 줄이기
                lines = new_caption.split('\n')
                while len('\n'.join(lines)) > 500 and len(lines) > 5:
                    # 중간 라인 제거
                    mid = len(lines) // 2
                    lines.pop(mid)
                new_caption = '\n'.join(lines)

            # 파일 저장
            with open(caption_file, 'w', encoding='utf-8') as f:
                f.write(new_caption)

            results['success'].append((folder.name, safety, str(caption_file)))
            print(f"✓ {folder.name} [{safety}] 변환 완료")

        except Exception as e:
            results['error'].append((folder.name, str(e)))
            print(f"✗ {folder.name} 에러: {e}")

    # 결과 요약
    print("\n" + "=" * 60)
    print("변환 결과 요약")
    print("=" * 60)
    print(f"성공: {len(results['success'])}개")
    print(f"스킵: {len(results['skip'])}개")
    print(f"에러: {len(results['error'])}개")

    # 안전도별 통계
    safety_counts = {}
    for item in results['success']:
        safety = item[1]
        safety_counts[safety] = safety_counts.get(safety, 0) + 1

    print("\n안전도별 분포:")
    for safety, count in sorted(safety_counts.items()):
        print(f"  {safety}: {count}개")

    if results['skip']:
        print("\n스킵된 폴더:")
        for item in results['skip'][:10]:
            print(f"  - {item[0]}: {item[1]}")
        if len(results['skip']) > 10:
            print(f"  ... 외 {len(results['skip']) - 10}개")

    if results['error']:
        print("\n에러 발생:")
        for item in results['error']:
            print(f"  - {item[0]}: {item[1]}")

    return results

if __name__ == "__main__":
    main()
