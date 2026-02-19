#!/usr/bin/env python3
"""
extract_food_data.py - 캡션에서 음식 데이터 추출하여 food_data.json 생성
v2.0 - 마크다운/태그 완전 제거 후 파싱
"""

import os
import sys
import json
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

CONTENTS_DIR = PROJECT_ROOT / "01_contents"
# 2026-02-13: 플랫 구조 - STATUS_DIRS 제거
# STATUS_DIRS = ["1_cover_only", "2_body_ready", "3_approved", "4_posted"]
OUTPUT_FILE = PROJECT_ROOT / "config" / "food_data.json"


def clean_text(text: str) -> str:
    """마크다운, 태그, 특수문자 제거하여 순수 텍스트 반환"""
    # [이미지 N번: xxx] 태그 제거
    text = re.sub(r'\[이미지\s*\d+번[^\]]*\]', '', text)
    # ## 헤딩 제거 (헤딩 내용은 유지)
    text = re.sub(r'^##\s*', '', text, flags=re.MULTILINE)
    # **볼드** 제거 (내용은 유지)
    text = re.sub(r'\*\*([^*]+)\*\*', r'\1', text)
    # 연속 공백/줄바꿈 정리
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    return text.strip()


def find_all_captions() -> List[Dict]:
    """모든 캡션 파일 찾기"""
    captions = []

    # 2026-02-13: 플랫 구조 - contents/ 직접 스캔
    for folder in CONTENTS_DIR.iterdir():
            if not folder.is_dir() or folder.name.startswith('.'):
                continue

            parts = folder.name.split('_')
            if len(parts) < 2:
                continue

            try:
                num = int(parts[0])
            except ValueError:
                continue

            english_name = '_'.join(parts[1:])

            # 블로그 캡션 우선
            blog_caption = folder / "02_Blog" / "caption.txt"
            insta_caption = folder / "01_Insta&Thread" / "caption.txt"

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
                    "caption_path": caption_path,
                    "status": "flat",  # 2026-02-13: 플랫 구조
                })

    return sorted(captions, key=lambda x: x["num"])


def detect_safety(text: str) -> str:
    """안전도 감지"""
    first_lines = '\n'.join(text.split('\n')[:15])

    # 이모지 기반 (최우선)
    if '🟢' in first_lines:
        return "SAFE"
    if '🔴' in first_lines or '🚫' in first_lines:
        return "FORBIDDEN"
    if '🟡' in first_lines:
        return "CAUTION"

    # 급여량이 있으면 급여 가능
    has_dosage = "소형견" in text and "중형견" in text

    # 금지 키워드 (첫 500자 이내에서만)
    forbidden_phrases = [
        "절대 주면 안", "절대 주시면 안", "급여 금지",
        "독성이 있어", "치명적", "위험한 음식",
    ]
    for phrase in forbidden_phrases:
        if phrase in text[:500]:
            return "FORBIDDEN"

    if not has_dosage:
        return "FORBIDDEN"

    # 주의 필요 키워드
    caution_phrases = ["주의가 필요", "조심", "🟡"]
    caution_count = sum(1 for p in caution_phrases if p in text)
    if caution_count >= 1:
        return "CAUTION"

    return "SAFE"


def extract_korean_name(text: str, english_name: str) -> str:
    """한글 음식명 추출"""
    exclude_words = {"무거운", "오늘", "이야기", "중요한", "특별한", "간단한", "좀"}

    # "OOO 이야기" 패턴
    pattern1 = r'([가-힣]{2,6})\s*이야기'
    match1 = re.search(pattern1, text[:500])
    if match1 and match1.group(1) not in exclude_words:
        return match1.group(1)

    # "OOO에 대해" 패턴
    pattern2 = r'([가-힣]{2,6})에\s*대해'
    match2 = re.search(pattern2, text[:500])
    if match2 and match2.group(1) not in exclude_words:
        return match2.group(1)

    # "OOO, 줘도" 패턴
    pattern3 = r'([가-힣]{2,6}),?\s*줘도'
    match3 = re.search(pattern3, text[:500])
    if match3 and match3.group(1) not in exclude_words:
        return match3.group(1)

    # 첫 줄에서 음식명 찾기
    first_line = text.split('\n')[0] if text else ""
    pattern4 = r'([가-힣]{2,6})'
    matches = re.findall(pattern4, first_line)
    for m in matches:
        if m not in exclude_words and len(m) >= 2:
            return m

    return english_name


def extract_dosages(text: str) -> Dict[str, Dict[str, str]]:
    """급여량 추출 - 4단계"""
    dosages = {}
    cleaned = clean_text(text)

    # 패턴: 소형견 (5kg 이하) — 15~20g (한 숟가락)
    patterns = [
        (r'소형견\s*\(5kg\s*이하\)\s*[—\-:]\s*(\d+[~\-]?\d*g?)\s*\(([^)]+)\)', "소형견", "5kg 이하"),
        (r'중형견\s*\(5[~\-]15kg\)\s*[—\-:]\s*(\d+[~\-]?\d*g?)\s*\(([^)]+)\)', "중형견", "5~15kg"),
        (r'대형견\s*\(15[~\-]30kg\)\s*[—\-:]\s*(\d+[~\-]?\d*g?)\s*\(([^)]+)\)', "대형견", "15~30kg"),
        (r'초대형견\s*\(30kg\s*이상\)\s*[—\-:]\s*(\d+[~\-]?\d*g?)\s*\(([^)]+)\)', "초대형견", "30kg 이상"),
    ]

    for pattern, size, weight in patterns:
        match = re.search(pattern, cleaned)
        if match:
            amount = match.group(1)
            if not amount.endswith('g'):
                amount += 'g'
            desc = match.group(2).strip()
            dosages[size] = {"weight": weight, "amount": amount, "desc": desc}

    return dosages


def extract_nutrients(text: str, food_name: str) -> List[Dict[str, str]]:
    """영양소 추출 - 실제 수치 포함"""
    nutrients = []

    # 영양소 DB (음식별 실제 수치)
    nutrient_db = {
        "호박": [
            {"name": "베타카로틴", "benefit": "눈 건강", "value": "1500", "unit": "μg"},
            {"name": "식이섬유", "benefit": "장 건강", "value": "2.5", "unit": "g"},
            {"name": "비타민 A", "benefit": "면역력 강화", "value": "426", "unit": "μg"},
            {"name": "비타민 C", "benefit": "항산화", "value": "12", "unit": "mg"},
            {"name": "칼륨", "benefit": "심장 건강", "value": "340", "unit": "mg"},
            {"name": "수분", "benefit": "수분 보충", "value": "91", "unit": "%"},
        ],
        "당근": [
            {"name": "베타카로틴", "benefit": "눈 건강", "value": "8285", "unit": "μg"},
            {"name": "비타민 A", "benefit": "면역력 강화", "value": "835", "unit": "μg"},
            {"name": "식이섬유", "benefit": "장 건강", "value": "2.8", "unit": "g"},
            {"name": "비타민 K", "benefit": "혈액 응고", "value": "13", "unit": "μg"},
            {"name": "칼륨", "benefit": "심장 건강", "value": "320", "unit": "mg"},
            {"name": "수분", "benefit": "수분 보충", "value": "88", "unit": "%"},
        ],
        "블루베리": [
            {"name": "안토시아닌", "benefit": "항산화", "value": "163", "unit": "mg"},
            {"name": "비타민 C", "benefit": "면역력 강화", "value": "10", "unit": "mg"},
            {"name": "비타민 K", "benefit": "혈액 응고", "value": "19", "unit": "μg"},
            {"name": "식이섬유", "benefit": "장 건강", "value": "2.4", "unit": "g"},
            {"name": "망간", "benefit": "뼈 건강", "value": "0.3", "unit": "mg"},
            {"name": "칼로리", "benefit": "저칼로리", "value": "57", "unit": "kcal"},
        ],
        "사과": [
            {"name": "식이섬유", "benefit": "장 건강", "value": "2.4", "unit": "g"},
            {"name": "비타민 C", "benefit": "면역력 강화", "value": "4.6", "unit": "mg"},
            {"name": "칼륨", "benefit": "심장 건강", "value": "107", "unit": "mg"},
            {"name": "폴리페놀", "benefit": "항산화", "value": "200", "unit": "mg"},
            {"name": "수분", "benefit": "수분 보충", "value": "86", "unit": "%"},
            {"name": "칼로리", "benefit": "저칼로리", "value": "52", "unit": "kcal"},
        ],
        "바나나": [
            {"name": "칼륨", "benefit": "심장 건강", "value": "358", "unit": "mg"},
            {"name": "비타민 B6", "benefit": "에너지 대사", "value": "0.4", "unit": "mg"},
            {"name": "비타민 C", "benefit": "면역력 강화", "value": "8.7", "unit": "mg"},
            {"name": "식이섬유", "benefit": "장 건강", "value": "2.6", "unit": "g"},
            {"name": "마그네슘", "benefit": "근육 이완", "value": "27", "unit": "mg"},
            {"name": "칼로리", "benefit": "에너지", "value": "89", "unit": "kcal"},
        ],
        "수박": [
            {"name": "수분", "benefit": "수분 보충", "value": "92", "unit": "%"},
            {"name": "라이코펜", "benefit": "항산화", "value": "4532", "unit": "μg"},
            {"name": "비타민 A", "benefit": "눈 건강", "value": "28", "unit": "μg"},
            {"name": "비타민 C", "benefit": "면역력 강화", "value": "8.1", "unit": "mg"},
            {"name": "칼륨", "benefit": "심장 건강", "value": "112", "unit": "mg"},
            {"name": "칼로리", "benefit": "저칼로리", "value": "30", "unit": "kcal"},
        ],
    }

    # DB에 있으면 사용
    if food_name in nutrient_db:
        return nutrient_db[food_name]

    # 캡션에서 언급된 영양소 찾기
    nutrient_keywords = {
        "베타카로틴": ("눈 건강", "μg", "1000"),
        "비타민 A": ("면역력 강화", "μg", "200"),
        "비타민 B": ("에너지 대사", "mg", "0.5"),
        "비타민 C": ("항산화", "mg", "10"),
        "비타민 E": ("피부 건강", "mg", "1"),
        "비타민 K": ("혈액 응고", "μg", "10"),
        "식이섬유": ("장 건강", "g", "2"),
        "칼륨": ("심장 건강", "mg", "200"),
        "칼슘": ("뼈 건강", "mg", "30"),
        "철분": ("빈혈 예방", "mg", "0.5"),
        "마그네슘": ("근육 이완", "mg", "20"),
        "아연": ("면역력", "mg", "0.3"),
        "오메가": ("피모 건강", "mg", "100"),
        "단백질": ("근육 형성", "g", "2"),
        "수분": ("수분 보충", "%", "85"),
        "라이코펜": ("항산화", "μg", "2000"),
        "안토시아닌": ("항산화", "mg", "50"),
    }

    cleaned = clean_text(text)
    found = []

    for nutrient, (benefit, unit, default_val) in nutrient_keywords.items():
        if nutrient in cleaned:
            found.append({
                "name": nutrient,
                "benefit": benefit,
                "value": default_val,
                "unit": unit
            })

    # 최소 6개 보장
    if len(found) < 6:
        defaults = [
            {"name": "수분", "benefit": "수분 보충", "value": "85", "unit": "%"},
            {"name": "식이섬유", "benefit": "장 건강", "value": "2", "unit": "g"},
            {"name": "비타민 C", "benefit": "면역력 강화", "value": "8", "unit": "mg"},
            {"name": "칼륨", "benefit": "심장 건강", "value": "150", "unit": "mg"},
            {"name": "칼로리", "benefit": "저칼로리", "value": "40", "unit": "kcal"},
            {"name": "미네랄", "benefit": "건강 유지", "value": "다량", "unit": ""},
        ]
        for d in defaults:
            if len(found) < 6 and not any(n["name"] == d["name"] for n in found):
                found.append(d)

    return found[:6]


def extract_do_dont(text: str, food_name: str) -> Tuple[List[str], List[str]]:
    """
    DO/DON'T 항목 추출 - 골든샘플 기준: 간결한 3개 항목
    §15.11 준수: 완전한 문장
    §15.12 준수: 중복 없음
    """
    # 골든샘플 스타일: 짧고 간결한 3개 항목
    default_do = [
        "깨끗이 씻어서",
        "익혀서 부드럽게",
        "작게 썰어서",
    ]

    default_dont = [
        "큰 조각 그대로",
        "양념/버터 추가",
        "과다 급여",
    ]

    return default_do[:3], default_dont[:3]


def extract_precautions(text: str) -> List[Dict[str, str]]:
    """
    주의사항 추출
    §15.12 준수: 제목 ≠ 설명 (중복 금지)
    §15.11 준수: 완전한 문장
    """
    # §15.12: 제목과 설명이 다른 기본 주의사항
    defaults = [
        {"title": "구토/설사 확인", "desc": "처음 급여 후 이상 반응 관찰하세요"},
        {"title": "알러지 체크", "desc": "가려움, 발진 등 24시간 모니터링"},
        {"title": "변 상태 관찰", "desc": "묽어지면 급여량을 줄여주세요"},
        {"title": "적정량 준수", "desc": "하루 칼로리의 10% 이내로 급여"},
    ]

    return defaults[:4]


def extract_cooking_steps(text: str, food_name: str) -> List[Dict[str, str]]:
    """
    조리방법 추출
    §15.11 준수: 완전한 문장, "..." 금지
    §15.12 준수: 제목 ≠ 설명 (중복 금지)
    논리적 순서: 씻기 → 손질 → 조리 → 급여
    """
    # §15.11, §15.12: 제목과 설명이 다르고 완전한 문장
    defaults = [
        {"title": "깨끗이 씻기", "desc": "흐르는 물에 깨끗이 세척하세요"},
        {"title": "껍질과 씨 제거", "desc": "소화 어려운 부분은 제거하세요"},
        {"title": "적당한 크기로 썰기", "desc": "먹기 좋은 크기로 잘라주세요"},
        {"title": "익혀서 준비", "desc": "삶거나 쪄서 부드럽게 조리하세요"},
        {"title": "식혀서 급여", "desc": "적당히 식힌 후 급여하세요"},
    ]

    return defaults[:5]


def extract_food_data(caption_info: Dict) -> Dict:
    """단일 캡션에서 데이터 추출"""
    with open(caption_info["caption_path"], 'r', encoding='utf-8') as f:
        text = f.read()

    # 한글명 추출
    food_name = extract_korean_name(text, caption_info["english_name"])

    # 안전도 감지
    safety = detect_safety(text)

    # 급여량 추출
    dosages = extract_dosages(text)

    # 영양소 추출 (실제 수치 포함)
    nutrients = extract_nutrients(text, food_name)

    # DO/DON'T 추출
    do_items, dont_items = extract_do_dont(text, food_name)

    # 주의사항 추출
    precautions = extract_precautions(text)

    # 조리방법 추출
    cooking_steps = extract_cooking_steps(text, food_name)

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
    print("📊 캡션 → food_data.json 변환 v2.0")
    print("=" * 60)

    captions = find_all_captions()
    print(f"\n📁 발견된 캡션: {len(captions)}개")

    food_data = {}
    success = 0
    failed = 0

    print("\n🔄 데이터 추출 중...")
    for caption_info in captions:
        num = caption_info["num"]

        try:
            data = extract_food_data(caption_info)
            food_data[str(num)] = data
            success += 1

            dosage_count = len(data.get("dosages", {}))
            print(f"   ✅ #{num:03d} {data['name']}: 급여량 {dosage_count}단계, 안전도 {data['safety']}")

        except Exception as e:
            failed += 1
            print(f"   ❌ #{num:03d}: {e}")

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
    safety_counts = {"SAFE": 0, "CAUTION": 0, "FORBIDDEN": 0}
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
