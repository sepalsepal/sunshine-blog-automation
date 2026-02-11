#!/usr/bin/env python3
"""
extract_food_data.py - 캡션에서 음식 데이터 추출하여 food_data.json 생성
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CONTENTS_DIR = PROJECT_ROOT / "contents"
STATUS_DIRS = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]
OUTPUT_FILE = PROJECT_ROOT / "config" / "food_data.json"

# 안전도 키워드
SAFETY_KEYWORDS = {
    "SAFE": ["안전", "좋아요", "먹어도 돼요", "🟢", "문제없어요"],
    "CAUTION": ["주의", "조심", "적당량", "🟡", "과다 섭취"],
    "DANGER": ["위험", "금지", "🔴", "독성", "절대"],
    "FORBIDDEN": ["금지", "절대 안 돼요", "🚫", "독성이 강해"],
}


def find_all_captions() -> List[Dict]:
    """모든 캡션 파일 찾기"""
    captions = []

    for status_dir in STATUS_DIRS:
        status_path = CONTENTS_DIR / status_dir
        if not status_path.exists():
            continue

        for folder in status_path.iterdir():
            if not folder.is_dir() or folder.name.startswith('.'):
                continue

            # 폴더명 파싱
            parts = folder.name.split('_')
            if len(parts) < 2:
                continue

            try:
                num = int(parts[0])
            except ValueError:
                continue

            # 영문명, 한글명 추출
            english_name = '_'.join(parts[1:-1]) if len(parts) > 2 else parts[1]
            korean_name = parts[-1] if len(parts) > 2 else parts[1]

            # 블로그 캡션 파일 찾기
            blog_caption = folder / "blog" / "caption.txt"
            insta_caption = folder / "insta" / "caption.txt"

            caption_path = None
            if blog_caption.exists():
                caption_path = blog_caption
            elif insta_caption.exists():
                caption_path = insta_caption

            if caption_path:
                captions.append({
                    "num": num,
                    "folder": folder,
                    "english_name": english_name,
                    "korean_name": korean_name,
                    "caption_path": caption_path,
                    "status": status_dir,
                })

    return sorted(captions, key=lambda x: x["num"])


def detect_safety(text: str) -> str:
    """텍스트에서 안전도 감지 - 첫 섹션과 이모지 기준"""
    # 첫 10줄에서 이모지 확인 (가장 정확)
    first_lines = '\n'.join(text.split('\n')[:15])

    # 이모지 기반 감지 (최우선)
    if '🟢' in first_lines:
        return "SAFE"
    if '🔴' in first_lines or '🚫' in first_lines:
        return "FORBIDDEN"
    if '🟡' in first_lines:
        return "CAUTION"

    # 급여량이 있으면 기본적으로 SAFE 또는 CAUTION (완전 금지가 아님)
    has_dosage = "소형견" in text and "중형견" in text and "대형견" in text

    # 첫 섹션 (## 앞부분)에서 판단
    intro_section = text.split('##')[0] if '##' in text else first_lines

    # 음식 자체가 금지인 경우 (양념 금지 등은 제외)
    forbidden_phrases = [
        "절대 주면 안",
        "절대 주시면 안",
        "급여 금지",
        "독성이 있어",
        "먹이면 안 돼",
        "치명적",
        "위험한 음식",
        "아예 안 되는",
        "신장을 망가",
        "급성 신부전",
    ]

    # 전체 텍스트에서 강력한 금지 키워드 확인
    for phrase in forbidden_phrases:
        if phrase in text[:1000]:  # 첫 1000자 내에서 확인
            return "FORBIDDEN"

    # 급여량이 없으면 대체로 FORBIDDEN (완전 급여 불가)
    if not has_dosage:
        # 추가 확인: "얼마나" 섹션이 전혀 없으면 FORBIDDEN
        if "얼마나" not in text and "급여량" not in text:
            return "FORBIDDEN"

    # 급여량이 있으면 최소 SAFE (급여 가능함)
    if has_dosage:
        # 주의 필요 키워드가 많으면 CAUTION
        caution_count = 0
        caution_phrases = ["주의가 필요", "조심", "적당량", "과다 섭취", "주의해서", "🟡"]
        for phrase in caution_phrases:
            if phrase in text:
                caution_count += 1

        if caution_count >= 2:
            return "CAUTION"

        return "SAFE"

    return "CAUTION"  # 기본값


def extract_dosages(text: str) -> Dict[str, Dict[str, str]]:
    """급여량 추출"""
    dosages = {}

    # 패턴: **소형견 (5kg 이하)** — 15~20g (작은 조각 2~3개)
    patterns = [
        r'\*\*소형견\s*\(5kg\s*이하\)\*\*\s*[—-]\s*(\d+[~\-]?\d*g?)\s*\(([^)]+)\)',
        r'\*\*중형견\s*\(5[~\-]15kg\)\*\*\s*[—-]\s*(\d+[~\-]?\d*g?)\s*\(([^)]+)\)',
        r'\*\*대형견\s*\(15[~\-]30kg\)\*\*\s*[—-]\s*(\d+[~\-]?\d*g?)\s*\(([^)]+)\)',
        r'\*\*초대형견\s*\(30kg\s*이상\)\*\*\s*[—-]\s*(\d+[~\-]?\d*g?)\s*\(([^)]+)\)',
    ]

    dog_sizes = ["소형견", "중형견", "대형견", "초대형견"]
    weights = ["5kg 이하", "5~15kg", "15~30kg", "30kg 이상"]

    for i, (pattern, size, weight) in enumerate(zip(patterns, dog_sizes, weights)):
        match = re.search(pattern, text)
        if match:
            amount = match.group(1)
            if not amount.endswith('g'):
                amount += 'g'
            desc = match.group(2)
            dosages[size] = {
                "weight": weight,
                "amount": amount,
                "desc": desc
            }

    # 패턴 매치 실패 시 기본값
    if not dosages:
        # 간단한 패턴 시도
        simple_patterns = [
            (r'소형견[^—\-]*[—\-]\s*(\d+[~\-]?\d*g?)', "소형견", "5kg 이하"),
            (r'중형견[^—\-]*[—\-]\s*(\d+[~\-]?\d*g?)', "중형견", "5~15kg"),
            (r'대형견[^—\-]*[—\-]\s*(\d+[~\-]?\d*g?)', "대형견", "15~30kg"),
            (r'초대형견[^—\-]*[—\-]\s*(\d+[~\-]?\d*g?)', "초대형견", "30kg 이상"),
        ]

        for pattern, size, weight in simple_patterns:
            match = re.search(pattern, text)
            if match:
                amount = match.group(1)
                if not amount.endswith('g'):
                    amount += 'g'
                dosages[size] = {
                    "weight": weight,
                    "amount": amount,
                    "desc": ""
                }

    return dosages


def extract_nutrients(text: str, food_name: str) -> List[Dict[str, str]]:
    """영양소 정보 추출"""
    nutrients = []

    # 영양소 패턴 (비타민 A, C, E 등)
    vitamin_pattern = r'비타민\s*([A-Z][0-9]?)'
    vitamins = re.findall(vitamin_pattern, text)

    # 일반적인 영양소 키워드
    nutrient_keywords = {
        "베타카로틴": ("눈 건강", "μg"),
        "식이섬유": ("장 건강", "g"),
        "비타민 A": ("피부 보호", "μg"),
        "비타민 B": ("에너지 대사", "mg"),
        "비타민 C": ("항산화", "mg"),
        "비타민 E": ("피부 건강", "mg"),
        "비타민 K": ("혈액 응고", "μg"),
        "칼륨": ("심장 건강", "mg"),
        "칼슘": ("뼈 건강", "mg"),
        "철분": ("빈혈 예방", "mg"),
        "마그네슘": ("근육 이완", "mg"),
        "아연": ("면역력", "mg"),
        "오메가": ("피부/모질", "mg"),
        "단백질": ("근육 형성", "g"),
        "항산화": ("노화 방지", ""),
        "수분": ("수분 보충", "%"),
        "라이코펜": ("항산화", "mg"),
    }

    found_nutrients = []
    for nutrient, (benefit, unit) in nutrient_keywords.items():
        if nutrient in text:
            found_nutrients.append({
                "name": nutrient,
                "benefit": benefit,
                "value": "-",
                "unit": unit
            })

    # 비타민 추가
    for vitamin in set(vitamins):
        vit_name = f"비타민 {vitamin}"
        if not any(n["name"] == vit_name for n in found_nutrients):
            found_nutrients.append({
                "name": vit_name,
                "benefit": "건강 유지",
                "value": "-",
                "unit": "mg"
            })

    # 최소 3개, 최대 6개
    if len(found_nutrients) < 3:
        defaults = [
            {"name": "주요 영양소", "benefit": "건강 유지", "value": "-", "unit": ""},
            {"name": "식이섬유", "benefit": "소화 건강", "value": "-", "unit": "g"},
            {"name": "수분", "benefit": "수분 보충", "value": "-", "unit": "%"},
        ]
        for d in defaults:
            if len(found_nutrients) < 3 and not any(n["name"] == d["name"] for n in found_nutrients):
                found_nutrients.append(d)

    return found_nutrients[:6]


def extract_precautions(text: str) -> List[Dict[str, str]]:
    """주의사항 추출"""
    precautions = []

    # ✅ 패턴 찾기
    check_pattern = r'✅\s*([^\n✅]+)'
    checks = re.findall(check_pattern, text)

    for check in checks[:6]:
        check = check.strip()
        if check:
            precautions.append({
                "title": check[:20] if len(check) > 20 else check,
                "desc": check if len(check) > 20 else ""
            })

    # • 패턴도 찾기
    bullet_pattern = r'•\s*([^\n•]+)'
    bullets = re.findall(bullet_pattern, text)

    for bullet in bullets:
        bullet = bullet.strip()
        if bullet and len(precautions) < 6:
            if not any(p["title"] in bullet or bullet in p["title"] for p in precautions):
                precautions.append({
                    "title": bullet[:20] if len(bullet) > 20 else bullet,
                    "desc": bullet if len(bullet) > 20 else ""
                })

    # 기본 주의사항
    if len(precautions) < 4:
        defaults = [
            {"title": "적정량 준수", "desc": "하루 칼로리의 10% 이내로 급여"},
            {"title": "처음 급여 시 주의", "desc": "소량부터 시작하여 반응 확인"},
            {"title": "알러지 확인", "desc": "첫 급여 후 24시간 관찰"},
            {"title": "신선한 것만", "desc": "상한 것은 급여 금지"},
        ]
        for d in defaults:
            if len(precautions) < 4:
                precautions.append(d)

    return precautions[:6]


def extract_cooking_steps(text: str) -> List[Dict[str, str]]:
    """조리방법 추출"""
    steps = []

    # "어떻게 줘야 할까요?" 섹션 찾기
    cooking_section = re.search(r'어떻게 줘야 할까요\?([^#]+)', text)

    if cooking_section:
        section_text = cooking_section.group(1)

        # • 패턴
        bullet_pattern = r'•\s*([^\n•]+)'
        bullets = re.findall(bullet_pattern, section_text)

        for i, bullet in enumerate(bullets[:5], 1):
            bullet = bullet.strip()
            if bullet:
                steps.append({
                    "title": bullet[:15] if len(bullet) > 15 else bullet,
                    "desc": bullet
                })

    # 문장 기반 추출
    if not steps:
        sentences = re.split(r'[.。]', text)
        cooking_keywords = ["씻", "썰", "잘라", "껍질", "제거", "익혀", "삶", "찌", "냉동", "냉장"]

        for sentence in sentences:
            sentence = sentence.strip()
            if any(kw in sentence for kw in cooking_keywords) and len(steps) < 5:
                steps.append({
                    "title": sentence[:15] if len(sentence) > 15 else sentence,
                    "desc": sentence
                })

    # 기본값
    if len(steps) < 3:
        defaults = [
            {"title": "깨끗이 씻기", "desc": "흐르는 물에 깨끗이 세척"},
            {"title": "적당히 손질", "desc": "먹기 좋은 크기로 준비"},
            {"title": "소량씩 급여", "desc": "처음에는 소량으로 시작"},
        ]
        for d in defaults:
            if len(steps) < 5:
                steps.append(d)

    return steps[:5]


def extract_do_dont(text: str, food_name: str) -> Tuple[List[str], List[str]]:
    """DO/DON'T 추출"""
    do_items = []
    dont_items = []

    # 긍정 키워드
    positive_keywords = ["줘도 돼요", "좋아요", "가능해요", "권장", "추천", "익혀서", "씻어서", "잘라서"]
    # 부정 키워드
    negative_keywords = ["금지", "안 돼요", "피해", "주의", "과다", "절대", "독성", "위험"]

    sentences = re.split(r'[.。\n]', text)

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence or len(sentence) < 5:
            continue

        # 부정 문장 체크
        is_negative = any(kw in sentence for kw in negative_keywords)
        is_positive = any(kw in sentence for kw in positive_keywords)

        if is_negative and len(dont_items) < 5:
            # 짧게 요약
            short = sentence[:30] + "..." if len(sentence) > 30 else sentence
            if not any(short[:10] in d for d in dont_items):
                dont_items.append(short)
        elif is_positive and len(do_items) < 5:
            short = sentence[:30] + "..." if len(sentence) > 30 else sentence
            if not any(short[:10] in d for d in do_items):
                do_items.append(short)

    # 기본 DO 항목
    if len(do_items) < 3:
        defaults = [
            f"깨끗이 씻어서 급여",
            f"작게 잘라서 급여",
            f"간식으로 소량 급여",
        ]
        for d in defaults:
            if len(do_items) < 5 and d not in do_items:
                do_items.append(d)

    # 기본 DON'T 항목
    if len(dont_items) < 3:
        defaults = [
            "과다 급여 금지",
            "양념된 것 급여 금지",
            "상한 것 급여 금지",
        ]
        for d in defaults:
            if len(dont_items) < 5 and d not in dont_items:
                dont_items.append(d)

    return do_items[:5], dont_items[:5]


def extract_korean_name(text: str, folder_korean: str) -> str:
    """캡션에서 한글 음식명 추출"""
    # 제외할 단어들 (음식이 아닌 일반 단어)
    exclude_words = {"무거운", "오늘", "이야기", "중요한", "특별한", "간단한"}

    # ## OOO, 줘도 되나요? 패턴 (가장 정확)
    pattern3 = r'##\s*([가-힣]+),?\s*(줘도|뭐가|어떤)'
    match3 = re.search(pattern3, text[:1500])
    if match3 and match3.group(1) not in exclude_words:
        return match3.group(1)

    # "OOO에 관한" 또는 "OOO에 대한" 패턴
    pattern4 = r'([가-힣]+)에\s*(관한|대한)'
    match4 = re.search(pattern4, text[:500])
    if match4 and match4.group(1) not in exclude_words:
        return match4.group(1)

    # "OOO 이야기" 패턴 (무거운 이야기 같은 것 제외)
    pattern = r'([가-힣]+)\s*이야기'
    matches = re.findall(pattern, text[:800])
    for m in matches:
        if m not in exclude_words and len(m) >= 2:
            return m

    # "오늘은 OOO을/를" 패턴
    pattern2 = r'오늘은[^가-힣]*([가-힣]{2,})'
    match2 = re.search(pattern2, text[:500])
    if match2 and match2.group(1) not in exclude_words:
        return match2.group(1)

    # 폴더명에서 한글이 있으면 사용
    if re.match(r'^[가-힣]+', folder_korean):
        # 한글 부분만 추출
        korean_part = re.search(r'[가-힣]+', folder_korean)
        if korean_part:
            return korean_part.group()

    return folder_korean


def extract_food_data(caption_info: Dict) -> Dict:
    """단일 캡션에서 데이터 추출"""
    caption_path = caption_info["caption_path"]

    with open(caption_path, 'r', encoding='utf-8') as f:
        text = f.read()

    # 한글명 추출 (캡션에서)
    food_name = extract_korean_name(text, caption_info["korean_name"])

    # 안전도 감지
    safety = detect_safety(text)

    # 급여량 추출
    dosages = extract_dosages(text)

    # 영양소 추출
    nutrients = extract_nutrients(text, food_name)

    # 주의사항 추출
    precautions = extract_precautions(text)

    # 조리방법 추출
    cooking_steps = extract_cooking_steps(text)

    # DO/DON'T 추출
    do_items, dont_items = extract_do_dont(text, food_name)

    return {
        "name": food_name,
        "english_name": caption_info["english_name"],
        "safety": safety,
        "nutrients": nutrients,
        "dosages": dosages,
        "do_items": do_items,
        "dont_items": dont_items,
        "precautions": precautions,
        "cooking_steps": cooking_steps,
        "nutrition_footnote": f"{food_name}는 개체별 차이가 있으므로 반응을 보며 조절하세요",
        "dosage_warning": ["하루 칼로리의 10% 이내로 급여해주세요", "처음 급여 시 소량부터 시작하세요"],
        "dosage_footnote": "개체별 차이가 있으므로 반응을 보며 조절하세요",
        "precaution_emergency": "이상 증상 발견 시 즉시 수의사와 상담하세요",
        "cooking_tip": f"{food_name}는 신선한 것으로 간단하게 준비해주세요",
    }


def main():
    print("=" * 60)
    print("📊 캡션 → food_data.json 변환")
    print("=" * 60)

    # 캡션 찾기
    captions = find_all_captions()
    print(f"\n📁 발견된 캡션: {len(captions)}개")

    # 데이터 추출
    food_data = {}
    success = 0
    failed = 0

    print("\n🔄 데이터 추출 중...")
    for caption_info in captions:
        num = caption_info["num"]
        name = caption_info["korean_name"]

        try:
            data = extract_food_data(caption_info)
            food_data[str(num)] = data
            success += 1

            # 급여량 추출 여부 표시
            dosage_count = len(data.get("dosages", {}))
            nutrient_count = len(data.get("nutrients", []))
            print(f"   ✅ #{num:03d} {name}: 급여량 {dosage_count}단계, 영양소 {nutrient_count}개, 안전도 {data['safety']}")

        except Exception as e:
            failed += 1
            print(f"   ❌ #{num:03d} {name}: {e}")

    # 저장
    OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_FILE, 'w', encoding='utf-8') as f:
        json.dump(food_data, f, ensure_ascii=False, indent=2)

    # 결과
    print("\n" + "=" * 60)
    print("📊 추출 완료")
    print("=" * 60)
    print(f"✅ 성공: {success}개")
    print(f"❌ 실패: {failed}개")
    print(f"📁 저장: {OUTPUT_FILE}")

    # 통계
    safety_counts = {"SAFE": 0, "CAUTION": 0, "DANGER": 0, "FORBIDDEN": 0}
    dosage_complete = 0

    for data in food_data.values():
        safety_counts[data["safety"]] = safety_counts.get(data["safety"], 0) + 1
        if len(data.get("dosages", {})) == 4:
            dosage_complete += 1

    print(f"\n📈 안전도 분포:")
    for safety, count in safety_counts.items():
        if count > 0:
            print(f"   {safety}: {count}개")

    print(f"\n📈 급여량 4단계 완성: {dosage_complete}/{len(food_data)}개")
    print("=" * 60)


if __name__ == "__main__":
    main()
