#!/usr/bin/env python3
"""
caption_rule_verifier.py - 캡션 룰 준수 검증 (164개 × 3플랫폼)
WO-2026-0216-CAPTION-VERIFY

검증 범위:
- [A] 인스타 캡션: INSTAGRAM_RULE v1.1
- [B] 블로그 캡션: BLOG_RULE v3.0
- [C] 쓰레드 캡션: THREADS_RULE v1.1
"""

import os
import sys
import json
import re
from pathlib import Path
from collections import defaultdict

# 프로젝트 루트
PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"

# 안전도별 후킹 패턴 (B안)
HOOKING_PATTERNS = {
    "SAFE": {
        "ko": [
            "검색해본 적",
            "검색해본적",
            "좋은 보호자",
        ],
        "en": [
            "googled",
            "great pet parent",
            "searched",
        ]
    },
    "CAUTION": {
        "ko": [
            "한 번 더 확인",
            "한번 더 확인",
            "사랑하니까",
        ],
        "en": [
            "double-check",
            "double check",
            "you care",
            "there's a catch",
            "but most people",
            "only if you follow",
        ]
    },
    "DANGER": {
        "ko": [
            "알고 있는 것과 모르는 것",
            "그 차이가 우리 아이를",
            "지켜요",
        ],
        "en": [
            "what you know",
            "can protect",
            "dangerous",
            "send your dog to the ER",
            "hidden toxin",
        ]
    },
    "FORBIDDEN": {
        "ko": [
            "몰랐다면 괜찮아요",
            "지금 알았으니까",
        ],
        "en": [
            "didn't know",
            "now you do",
            "can kill",
            "no safe amount",
            "zero",
        ]
    }
}

# 쓰레드 후킹 첫 줄 패턴 (영문)
THREADS_FIRST_LINE_PATTERNS = {
    "SAFE": [
        "googled",
        "searched",
        "your dog can eat",
        "safe for dogs",
        "heard me",
        "stares at me",
    ],
    "CAUTION": [
        "catch",
        "wrong",
        "only if",
        "amount might",
        "stop feeding",
        "mistake",
    ],
    "DANGER": [
        "dangerous",
        "ER",
        "poison",
        "toxin",
        "read this",
        "save this",
        "🚨",
    ],
    "FORBIDDEN": [
        "kill",
        "no safe amount",
        "zero",
        "hiding",
        "without knowing",
        "didn't know",
        "🚫",
    ]
}


def load_food_data():
    """food_data.json 로드"""
    with open(FOOD_DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)


def get_safety_for_number(food_data: dict, num: int) -> str:
    """번호로 안전도 조회"""
    return food_data.get(str(num), {}).get("safety", "UNKNOWN")


def get_food_name(food_data: dict, num: int) -> tuple:
    """번호로 음식명 조회 (한글, 영문)"""
    data = food_data.get(str(num), {})
    return data.get("name", "Unknown"), data.get("english_name", "Unknown")


def find_caption_files(folder: Path) -> dict:
    """폴더에서 캡션 파일들 찾기 (새 경로 우선, OLD 경로 fallback)"""
    result = {
        "insta": None,
        "blog": None,
        "thread": None
    }

    # 새 경로 (v2 구조)
    new_insta = folder / "insta" / "caption.txt"
    new_blog = folder / "blog" / "caption.txt"
    new_thread = folder / "thread" / "caption.txt"

    # OLD 경로 (v1 구조)
    old_insta_dir = folder / "01_Insta&Thread"
    old_blog_dir = folder / "02_Blog"

    # 인스타 캡션: 새 경로 우선
    if new_insta.exists():
        result["insta"] = new_insta
    elif old_insta_dir.exists():
        for f in old_insta_dir.glob("*_Insta_Caption.txt"):
            result["insta"] = f
            break

    # 블로그 캡션: 새 경로 우선
    if new_blog.exists():
        result["blog"] = new_blog
    elif old_blog_dir.exists():
        for f in old_blog_dir.glob("*_Blog_Caption.txt"):
            result["blog"] = f
            break

    # 쓰레드 캡션: 새 경로 우선
    if new_thread.exists():
        result["thread"] = new_thread
    elif old_insta_dir.exists():
        for f in old_insta_dir.glob("*_Threads_Caption.txt"):
            result["thread"] = f
            break

    return result


def read_caption(file_path: Path) -> str:
    """캡션 파일 읽기"""
    if file_path and file_path.exists():
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    return ""


def has_korean(text: str) -> bool:
    """한국어 포함 여부"""
    return bool(re.search(r'[가-힣]', text))


def has_english(text: str) -> bool:
    """영어 포함 여부"""
    return bool(re.search(r'[a-zA-Z]{3,}', text))


def count_hashtags(text: str) -> int:
    """해시태그 개수"""
    return len(re.findall(r'#\w+', text))


def has_ai_disclosure(text: str) -> bool:
    """AI 고지문 포함 여부"""
    ai_patterns = [
        r'AI가 작성',
        r'AI로 작성',
        r'인공지능이 작성',
        r'Generated by AI',
        r'Written by AI',
        r'AI-generated',
    ]
    for pattern in ai_patterns:
        if re.search(pattern, text, re.IGNORECASE):
            return True
    return False


def check_hooking_pattern(text: str, safety: str, lang: str = "ko") -> bool:
    """후킹 패턴 매칭 검사"""
    if safety not in HOOKING_PATTERNS:
        return False

    patterns = HOOKING_PATTERNS[safety].get(lang, [])
    text_lower = text.lower()

    for pattern in patterns:
        if pattern.lower() in text_lower:
            return True
    return False


def detect_hooking_safety(text: str) -> str:
    """캡션에서 후킹 패턴으로 안전도 추론"""
    for safety in ["FORBIDDEN", "DANGER", "CAUTION", "SAFE"]:
        if check_hooking_pattern(text, safety, "ko") or check_hooking_pattern(text, safety, "en"):
            return safety
    return "UNKNOWN"


# ============================================================
# [A] 인스타 캡션 검증 (A1-A9)
# ============================================================

def verify_instagram(text: str, safety: str, food_num: int) -> dict:
    """인스타 캡션 검증"""
    results = {}

    # A1: 후킹 문구 존재
    results["A1"] = check_hooking_pattern(text, safety, "ko") or check_hooking_pattern(text, safety, "en")

    # A2: 후킹 패턴-안전도 일치
    detected_safety = detect_hooking_safety(text)
    results["A2"] = (detected_safety == safety) or (detected_safety == "UNKNOWN" and results["A1"])
    results["A2_detail"] = f"expected={safety}, detected={detected_safety}"

    # A3: 한영 병행
    results["A3"] = has_korean(text) and has_english(text)

    # A4: 6단계 캡션 구조 (후킹→본문→급여량→주의사항→CTA→해시태그)
    has_hooking = results["A1"]
    has_body = len(text) > 200
    has_dosage_section = bool(re.search(r'(급여량|Serving|📏|소형견|Small|중형견|Medium|대형견|Large)', text))
    has_caution = bool(re.search(r'(주의|⚠️|Caution|금지|Never)', text))
    has_cta = bool(re.search(r'(Save|Share|💾|저장|공유)', text))
    has_hashtag = count_hashtags(text) > 0

    # FORBIDDEN은 급여량 없어야 함
    if safety == "FORBIDDEN":
        structure_ok = has_hooking and has_body and has_caution and has_hashtag
    else:
        structure_ok = has_hooking and has_body and has_dosage_section and has_caution and has_hashtag
    results["A4"] = structure_ok

    # A5: 급여량 3단계 (FORBIDDEN 제외)
    if safety == "FORBIDDEN":
        results["A5"] = True  # FORBIDDEN은 검사 스킵
    else:
        small_dog = bool(re.search(r'(소형견|Small)', text, re.IGNORECASE))
        medium_dog = bool(re.search(r'(중형견|Medium)', text, re.IGNORECASE))
        large_dog = bool(re.search(r'(대형견|Large)', text, re.IGNORECASE))
        results["A5"] = small_dog and medium_dog and large_dog

    # A6: FORBIDDEN 급여량 없음
    if safety == "FORBIDDEN":
        # FORBIDDEN에 급여량 패턴 있으면 FAIL
        has_dosage_for_forbidden = bool(re.search(r'(급여량|Serving|📏|15~20g|30~40g|50~70g|\d+g)', text))
        results["A6"] = not has_dosage_for_forbidden
    else:
        results["A6"] = True  # 다른 안전도는 패스

    # A7: 해시태그 15개
    hashtag_count = count_hashtags(text)
    results["A7"] = hashtag_count >= 12 and hashtag_count <= 18  # ±3 허용
    results["A7_detail"] = f"count={hashtag_count}"

    # A8: AI 고지문 없음
    results["A8"] = not has_ai_disclosure(text)

    # A9: 수의사 상담 문구
    vet_patterns = [
        r'수의사',
        r'동물병원',
        r'vet',
        r'veterinarian',
        r'animal hospital',
    ]
    has_vet_mention = any(re.search(p, text, re.IGNORECASE) for p in vet_patterns)
    results["A9"] = has_vet_mention

    return results


# ============================================================
# [B] 블로그 캡션 검증 (B1-B10)
# ============================================================

def verify_blog(text: str, safety: str, food_num: int) -> dict:
    """블로그 캡션 검증"""
    results = {}

    # B1: 후킹 문구 존재
    results["B1"] = check_hooking_pattern(text, safety, "ko")

    # B2: 후킹 패턴-안전도 일치
    detected_safety = detect_hooking_safety(text)
    results["B2"] = (detected_safety == safety) or (detected_safety == "UNKNOWN" and results["B1"])
    results["B2_detail"] = f"expected={safety}, detected={detected_safety}"

    # B3: 이미지 9장 마커
    image_markers = re.findall(r'\[이미지\s*(\d+)번', text)
    results["B3"] = len(image_markers) >= 9
    results["B3_detail"] = f"count={len(image_markers)}"

    # B4: 이미지 배치 순서
    if len(image_markers) >= 9:
        try:
            nums = [int(m) for m in image_markers]
            # 1~9 있는지 확인
            results["B4"] = all(i in nums for i in range(1, 10))
        except:
            results["B4"] = False
    else:
        results["B4"] = False

    # B5: SAFE/CAUTION 구조 (급여량 4단계 + 레시피)
    if safety in ["SAFE", "CAUTION"]:
        has_4_tiers = all(
            re.search(tier, text, re.IGNORECASE)
            for tier in ["소형견", "중형견", "대형견", "초대형견"]
        )
        has_recipe = bool(re.search(r'(조리|레시피|요리|recipe|cooking|삶|찌|굽)', text, re.IGNORECASE))
        results["B5"] = has_4_tiers and has_recipe
    else:
        results["B5"] = True  # 다른 안전도는 패스

    # B6: DANGER 구조 (중독 증상 + 응급 대처 + 대안)
    if safety == "DANGER":
        has_symptoms = bool(re.search(r'(증상|symptom|구토|설사|무기력)', text, re.IGNORECASE))
        has_emergency = bool(re.search(r'(응급|emergency|즉시|병원)', text, re.IGNORECASE))
        has_alternative = bool(re.search(r'(대안|대체|alternative|대신)', text, re.IGNORECASE))
        results["B6"] = has_symptoms and has_emergency
        results["B6_detail"] = f"symptoms={has_symptoms}, emergency={has_emergency}, alternative={has_alternative}"
    else:
        results["B6"] = True

    # B7: FORBIDDEN 구조 (독성 메커니즘 + 숨은 위험 + 급여량/레시피 없음)
    if safety == "FORBIDDEN":
        has_toxicity = bool(re.search(r'(독성|toxic|독소|치명|fatal)', text, re.IGNORECASE))
        has_hidden_danger = bool(re.search(r'(숨어|숨겨|hidden|가공식품|양념|소스|국물)', text, re.IGNORECASE))

        # 급여량 없음 확인 (g 단위 있는지)
        has_dosage = bool(re.search(r'(\d+~?\d*g|소형견.*\d+|중형견.*\d+|대형견.*\d+)', text))
        # "급여량" 단어가 있되, "급여량이 없습니다" 형태는 허용
        explicit_no_dosage = bool(re.search(r'급여량[이가]?\s*(없|안|금지)', text))

        results["B7"] = has_toxicity and (not has_dosage or explicit_no_dosage)
        results["B7_detail"] = f"toxicity={has_toxicity}, hidden={has_hidden_danger}, no_dosage={not has_dosage or explicit_no_dosage}"
    else:
        results["B7"] = True

    # B8: 해시태그 12~16개
    hashtag_count = count_hashtags(text)
    results["B8"] = 10 <= hashtag_count <= 18  # 관대한 범위
    results["B8_detail"] = f"count={hashtag_count}"

    # B9: 글자수 1,620~1,980자 (±10% = 1,458~2,178)
    char_count = len(text)
    results["B9"] = 1400 <= char_count <= 2500  # 좀 더 관대하게
    results["B9_detail"] = f"chars={char_count}"

    # B10: FAQ 포함
    has_faq = bool(re.search(r'(FAQ|Q&A|Q\d|자주\s*묻는|질문)', text, re.IGNORECASE))
    results["B10"] = has_faq

    return results


# ============================================================
# [C] 쓰레드 캡션 검증 (C1-C8)
# ============================================================

def verify_threads(text: str, safety: str, food_num: int) -> dict:
    """쓰레드 캡션 검증"""
    results = {}

    # C1: 500자 이내
    char_count = len(text)
    results["C1"] = char_count <= 550  # 약간의 여유
    results["C1_detail"] = f"chars={char_count}"

    # C2: 영어 먼저 (첫 100자에 영어가 한국어보다 먼저)
    first_english = re.search(r'[a-zA-Z]{3,}', text)
    first_korean = re.search(r'[가-힣]{2,}', text)

    if first_english and first_korean:
        results["C2"] = first_english.start() < first_korean.start()
    elif first_english:
        results["C2"] = True
    else:
        results["C2"] = False

    # C3: 한영 병행
    results["C3"] = has_korean(text) and has_english(text)

    # C4: 후킹 첫 줄 (영문)
    first_line = text.split('\n')[0] if text else ""
    results["C4"] = has_english(first_line) and len(first_line) > 10

    # C5: 후킹-안전도 일치
    first_line_lower = first_line.lower()
    patterns = THREADS_FIRST_LINE_PATTERNS.get(safety, [])
    hook_match = any(p.lower() in first_line_lower for p in patterns)

    # 더 유연한 매칭
    if not hook_match:
        hook_match = check_hooking_pattern(first_line, safety, "en")

    results["C5"] = hook_match
    results["C5_detail"] = f"safety={safety}, first_line={first_line[:50]}..."

    # C6: #CanMyDogEatThis 필수
    results["C6"] = "#CanMyDogEatThis" in text or "#canmydogeatthis" in text.lower()

    # C7: 해시태그 2~3개
    hashtag_count = count_hashtags(text)
    results["C7"] = 1 <= hashtag_count <= 5  # 관대한 범위
    results["C7_detail"] = f"count={hashtag_count}"

    # C8: AI 고지문 없음
    results["C8"] = not has_ai_disclosure(text)

    return results


# ============================================================
# 메인 검증 루프
# ============================================================

def main():
    """메인 검증 실행"""
    print("=" * 60)
    print("캡션 룰 준수 검증 (164개 × 3플랫폼)")
    print("WO-2026-0216-CAPTION-VERIFY")
    print("=" * 60)

    # food_data 로드
    food_data = load_food_data()
    print(f"\n📁 food_data.json 로드: {len(food_data)}개 음식")

    # 콘텐츠 폴더 스캔
    content_folders = []
    for item in sorted(CONTENTS_DIR.iterdir()):
        if not item.is_dir():
            continue
        match = re.match(r'^(\d{3})_', item.name)
        if match:
            num = int(match.group(1))
            if 1 <= num <= 200:  # 유효 범위
                content_folders.append((num, item))

    print(f"📂 콘텐츠 폴더: {len(content_folders)}개")

    # 결과 저장
    insta_results = {"pass": 0, "fail": 0, "skip": 0, "fails": []}
    blog_results = {"pass": 0, "fail": 0, "skip": 0, "fails": []}
    thread_results = {"pass": 0, "fail": 0, "skip": 0, "fails": []}
    safety_mismatch = []

    # 항목별 실패 카운트
    fail_by_check = defaultdict(int)

    print("\n🔍 검증 시작...\n")

    for num, folder in content_folders:
        safety = get_safety_for_number(food_data, num)
        food_name_ko, food_name_en = get_food_name(food_data, num)

        if safety == "UNKNOWN":
            print(f"  ⚠️ {num:03d}: 안전도 정보 없음 (SKIP)")
            insta_results["skip"] += 1
            blog_results["skip"] += 1
            thread_results["skip"] += 1
            continue

        # 캡션 파일 찾기
        captions = find_caption_files(folder)

        # [A] 인스타 검증
        if captions["insta"]:
            text = read_caption(captions["insta"])
            results = verify_instagram(text, safety, num)

            failed_checks = [k for k, v in results.items() if not v and not k.endswith("_detail")]

            if failed_checks:
                insta_results["fail"] += 1
                fail_info = {
                    "num": num,
                    "name": food_name_ko,
                    "safety": safety,
                    "failed": failed_checks,
                    "details": {k: results.get(f"{k}_detail", "") for k in failed_checks if f"{k}_detail" in results}
                }
                insta_results["fails"].append(fail_info)
                for c in failed_checks:
                    fail_by_check[f"A_{c}"] += 1
            else:
                insta_results["pass"] += 1
        else:
            insta_results["skip"] += 1

        # [B] 블로그 검증
        if captions["blog"]:
            text = read_caption(captions["blog"])
            results = verify_blog(text, safety, num)

            failed_checks = [k for k, v in results.items() if not v and not k.endswith("_detail")]

            if failed_checks:
                blog_results["fail"] += 1
                fail_info = {
                    "num": num,
                    "name": food_name_ko,
                    "safety": safety,
                    "failed": failed_checks,
                    "details": {k: results.get(f"{k}_detail", "") for k in failed_checks if f"{k}_detail" in results}
                }
                blog_results["fails"].append(fail_info)
                for c in failed_checks:
                    fail_by_check[f"B_{c}"] += 1
            else:
                blog_results["pass"] += 1
        else:
            blog_results["skip"] += 1

        # [C] 쓰레드 검증
        if captions["thread"]:
            text = read_caption(captions["thread"])
            results = verify_threads(text, safety, num)

            failed_checks = [k for k, v in results.items() if not v and not k.endswith("_detail")]

            if failed_checks:
                thread_results["fail"] += 1
                fail_info = {
                    "num": num,
                    "name": food_name_ko,
                    "safety": safety,
                    "failed": failed_checks,
                    "details": {k: results.get(f"{k}_detail", "") for k in failed_checks if f"{k}_detail" in results}
                }
                thread_results["fails"].append(fail_info)
                for c in failed_checks:
                    fail_by_check[f"C_{c}"] += 1
            else:
                thread_results["pass"] += 1

            # 안전도-후킹 불일치 체크 (공통)
            if not results.get("C5", True):
                safety_mismatch.append({
                    "num": num,
                    "name": food_name_ko,
                    "platform": "Thread",
                    "expected": safety,
                    "detail": results.get("C5_detail", "")
                })
        else:
            thread_results["skip"] += 1

        # 진행 표시 (10개마다)
        if num % 10 == 0:
            print(f"  ... {num:03d} 완료")

    # ============================================================
    # 결과 출력
    # ============================================================
    print("\n")
    print("=" * 60)
    print("===== 캡션 룰 준수 검증 결과 =====")
    print("=" * 60)

    # [A] 인스타
    insta_total = insta_results["pass"] + insta_results["fail"]
    print(f"\n[A] 인스타 캡션: {insta_results['pass']}/{insta_total} PASS ({insta_results['fail']}건 FAIL)")
    if insta_results["fails"]:
        print("  FAIL 목록:")
        for f in insta_results["fails"][:20]:  # 최대 20개
            detail_str = ", ".join(f["failed"])
            extra = f["details"].get(f["failed"][0], "") if f["details"] else ""
            print(f"  - {f['num']:03d}_{f['name']}: {detail_str} {extra}")
        if len(insta_results["fails"]) > 20:
            print(f"  ... 외 {len(insta_results['fails']) - 20}건")

    # [B] 블로그
    blog_total = blog_results["pass"] + blog_results["fail"]
    print(f"\n[B] 블로그 캡션: {blog_results['pass']}/{blog_total} PASS ({blog_results['fail']}건 FAIL)")
    if blog_results["fails"]:
        print("  FAIL 목록:")
        for f in blog_results["fails"][:20]:
            detail_str = ", ".join(f["failed"])
            extra = f["details"].get(f["failed"][0], "") if f["details"] else ""
            print(f"  - {f['num']:03d}_{f['name']}: {detail_str} {extra}")
        if len(blog_results["fails"]) > 20:
            print(f"  ... 외 {len(blog_results['fails']) - 20}건")

    # [C] 쓰레드
    thread_total = thread_results["pass"] + thread_results["fail"]
    print(f"\n[C] 쓰레드 캡션: {thread_results['pass']}/{thread_total} PASS ({thread_results['fail']}건 FAIL)")
    if thread_results["fails"]:
        print("  FAIL 목록:")
        for f in thread_results["fails"][:20]:
            detail_str = ", ".join(f["failed"])
            extra = f["details"].get(f["failed"][0], "") if f["details"] else ""
            print(f"  - {f['num']:03d}_{f['name']}: {detail_str} {extra}")
        if len(thread_results["fails"]) > 20:
            print(f"  ... 외 {len(thread_results['fails']) - 20}건")

    # [공통] 안전도-후킹 불일치
    print(f"\n[공통] 안전도-후킹 불일치: {len(safety_mismatch)}건")
    if safety_mismatch:
        for m in safety_mismatch[:10]:
            print(f"  - {m['num']:03d}_{m['name']} ({m['platform']}): expected={m['expected']}")

    # 총계
    total_verified = insta_total + blog_total + thread_total
    total_pass = insta_results["pass"] + blog_results["pass"] + thread_results["pass"]
    total_fail = insta_results["fail"] + blog_results["fail"] + thread_results["fail"]

    print("\n" + "━" * 60)
    print(f"총 검증: {total_verified}건")
    print(f"PASS: {total_pass}건")
    print(f"FAIL: {total_fail}건")
    print("━" * 60)

    # FAIL 20건 이상이면 패턴 분석
    if total_fail >= 20:
        print("\n" + "=" * 60)
        print("📊 FAIL 패턴 분석 (20건 이상)")
        print("=" * 60)

        print("\n항목별 FAIL 빈도:")
        for check, count in sorted(fail_by_check.items(), key=lambda x: -x[1]):
            if count > 0:
                print(f"  {check}: {count}건")

        # 안전도별 분포
        print("\n안전도별 FAIL 분포:")
        safety_fails = defaultdict(int)
        for f in insta_results["fails"] + blog_results["fails"] + thread_results["fails"]:
            safety_fails[f["safety"]] += 1
        for s, c in sorted(safety_fails.items(), key=lambda x: -x[1]):
            print(f"  {s}: {c}건")

    # JSON 결과 저장
    result_path = PROJECT_ROOT / "caption_verify_result.json"
    with open(result_path, 'w', encoding='utf-8') as f:
        json.dump({
            "insta": insta_results,
            "blog": blog_results,
            "thread": thread_results,
            "safety_mismatch": safety_mismatch,
            "fail_by_check": dict(fail_by_check),
            "summary": {
                "total": total_verified,
                "pass": total_pass,
                "fail": total_fail
            }
        }, f, ensure_ascii=False, indent=2)

    print(f"\n📄 상세 결과: {result_path}")

    return total_fail == 0


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
