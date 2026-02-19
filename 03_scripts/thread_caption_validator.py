#!/usr/bin/env python3
"""
Thread Caption Validator v1.0
쓰레드 캡션 표준 §2.9 준수 여부 검증
"""

import os
import re
import json
from pathlib import Path

BASE_PATH = "/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine"

# 안전도별 톤 키워드
TONE_KEYWORDS = {
    "SAFE": {
        "required": ["좋아", "맘껏", "줘도 돼"],
        "forbidden": ["위험해요", "절대 안 돼", "조심해야"]
    },
    "CAUTION": {
        "required": ["조건", "✔", "❌"],
        "forbidden": ["절대 안 돼", "응급"]
    },
    "DANGER": {
        "required": ["조심", "병원", "⚠"],
        "forbidden": ["맘껏", "줘도 돼"]
    },
    "FORBIDDEN": {
        "required": ["절대", "동물병원", "🚨"],
        "forbidden": ["좋아해요", "맘껏", "줘도 돼"]
    }
}

# 안전도 매핑 (food_data.json의 safety_level)
SAFETY_MAPPING = {
    "SAFE": "SAFE",
    "CAUTION": "CAUTION",
    "DANGER": "DANGER",
    "FORBIDDEN": "FORBIDDEN",
    "safe": "SAFE",
    "caution": "CAUTION",
    "danger": "DANGER",
    "forbidden": "FORBIDDEN"
}


def count_lines(text):
    """텍스트 줄 수 (빈 줄 제외)"""
    lines = [l for l in text.strip().split('\n') if l.strip()]
    return len(lines)


def count_emojis(text):
    """이모지 개수 (실제 이모지만 카운트)"""
    # 일반적인 이모지 범위만 체크 (✔️❌⚠️🚨 제외 - UI 요소로 간주)
    emoji_chars = []
    for char in text:
        code = ord(char)
        # 주요 이모지 범위
        if (0x1F300 <= code <= 0x1F9FF or  # 이모지 주요 범위
            0x2600 <= code <= 0x26FF):      # 기호
            # UI 요소 제외 (체크마크, 경고 등)
            if char not in ['✔', '❌', '⚠', '🚨', 'ℹ']:
                emoji_chars.append(char)
    return len(emoji_chars)


def has_hashtags(text):
    """해시태그 포함 여부"""
    return bool(re.search(r'#\w+', text))


def has_jamo(text):
    """ㅋㅋ, ㅎㅎ 등 자음 포함 여부"""
    jamo_pattern = re.compile(r'[ㄱ-ㅎ]{2,}')
    return bool(jamo_pattern.search(text))


def has_ai_notice(text):
    """AI 고지 포함 여부"""
    return "AI" in text and ("생성" in text or "이미지" in text)


def has_cta(text):
    """CTA(질문) 포함 여부"""
    cta_patterns = [
        r'\?',
        '좋아하나요',
        '어떠세요',
        '해보세요',
        '공유해요'
    ]
    return any(re.search(p, text) for p in cta_patterns)


def has_haetsali(text):
    """햇살이 언급 여부"""
    return "햇살이" in text


def check_tone(text, safety_level):
    """안전도에 맞는 톤 사용 여부"""
    if safety_level not in TONE_KEYWORDS:
        return True, []

    keywords = TONE_KEYWORDS[safety_level]
    issues = []

    # 필수 키워드 중 하나라도 있어야 함
    has_required = any(kw in text for kw in keywords["required"])
    if not has_required:
        issues.append(f"필수 키워드 누락: {keywords['required']} 중 하나 필요")

    # 금지 키워드 체크
    for kw in keywords["forbidden"]:
        if kw in text:
            issues.append(f"금지 키워드 사용: '{kw}'")

    return len(issues) == 0, issues


def validate_thread_caption(caption_text, safety_level="SAFE"):
    """쓰레드 캡션 검증"""
    results = {
        "passed": True,
        "checks": [],
        "safety_level": safety_level
    }

    # 1. 줄 수 (5-7줄)
    line_count = count_lines(caption_text)
    check1 = {
        "name": "줄 수 (5-7줄)",
        "value": line_count,
        "passed": 5 <= line_count <= 7
    }
    results["checks"].append(check1)

    # 2. 이모지 (3개 이하)
    emoji_count = count_emojis(caption_text)
    check2 = {
        "name": "이모지 (3개 이하)",
        "value": emoji_count,
        "passed": emoji_count <= 3
    }
    results["checks"].append(check2)

    # 3. 해시태그 없음
    has_hash = has_hashtags(caption_text)
    check3 = {
        "name": "해시태그 없음",
        "value": "있음" if has_hash else "없음",
        "passed": not has_hash
    }
    results["checks"].append(check3)

    # 4. 자음(ㅋㅋ/ㅎㅎ) 없음
    has_j = has_jamo(caption_text)
    check4 = {
        "name": "자음(ㅋㅋ/ㅎㅎ) 없음",
        "value": "있음" if has_j else "없음",
        "passed": not has_j
    }
    results["checks"].append(check4)

    # 5. AI 고지 포함
    has_ai = has_ai_notice(caption_text)
    check5 = {
        "name": "AI 고지 포함",
        "value": "있음" if has_ai else "없음",
        "passed": has_ai
    }
    results["checks"].append(check5)

    # 6. CTA(질문) 포함
    has_c = has_cta(caption_text)
    check6 = {
        "name": "CTA(질문) 포함",
        "value": "있음" if has_c else "없음",
        "passed": has_c
    }
    results["checks"].append(check6)

    # 7. 햇살이 언급
    has_h = has_haetsali(caption_text)
    check7 = {
        "name": "햇살이 언급 포함",
        "value": "있음" if has_h else "없음",
        "passed": has_h
    }
    results["checks"].append(check7)

    # 8. 안전도 톤 체크
    tone_ok, tone_issues = check_tone(caption_text, safety_level)
    check8 = {
        "name": f"안전도({safety_level}) 톤 적합",
        "value": "적합" if tone_ok else ", ".join(tone_issues),
        "passed": tone_ok
    }
    results["checks"].append(check8)

    # 전체 결과
    results["passed"] = all(c["passed"] for c in results["checks"])

    return results


def print_result(content_name, result):
    """결과 출력"""
    status = "✅ PASS" if result["passed"] else "❌ FAIL"
    print(f"\n{'='*50}")
    print(f"📋 {content_name} [{result['safety_level']}]")
    print(f"{'='*50}")
    print(f"결과: {status}")
    print("-"*50)

    for check in result["checks"]:
        mark = "✅" if check["passed"] else "❌"
        print(f"{mark} {check['name']}: {check['value']}")

    print("="*50)


def validate_folder(folder_path, safety_level="SAFE"):
    """폴더 내 쓰레드 캡션 검증"""
    thread_caption_path = os.path.join(folder_path, "thread", "caption.txt")

    # thread/caption.txt가 없으면 insta/caption.txt 사용 (쓰레드는 인스타와 별도)
    if not os.path.exists(thread_caption_path):
        # 쓰레드 전용 캡션이 없음
        return None

    with open(thread_caption_path, 'r', encoding='utf-8') as f:
        caption = f.read()

    return validate_thread_caption(caption, safety_level)


def main():
    """전체 콘텐츠 검증"""
    print("="*50)
    print("Thread Caption Validator v1.0")
    print("§2.9 쓰레드 캡션 표준 검증")
    print("="*50)

    # food_data.json에서 안전도 로드
    food_data_path = os.path.join(BASE_PATH, "config", "food_data.json")
    food_data = {}
    if os.path.exists(food_data_path):
        with open(food_data_path, 'r', encoding='utf-8') as f:
            food_data = json.load(f)

    # 테스트 캡션 (예시)
    test_captions = {
        "SAFE_example": {
            "text": """사과 강아지한테 줘도 되나요? 🍎
우리 햇살이 사과 완전 좋아해요!

사과는 강아지한테 정말 좋은 간식이에요.
비타민도 풍부하고 치아 건강에도 좋아요.
간식으로 맘껏 줘도 돼요~ 🐕

여러분 강아지도 사과 좋아하나요?
ℹ️ 일부 이미지는 AI로 생성되었습니다""",
            "safety": "SAFE"
        },
        "CAUTION_example": {
            "text": """호박 강아지한테 줘도 될까요? 🎃
우리 햇살이는 찐 호박 좋아해요!

소화에 좋지만, 조건이 있어요!
✔️ 꼭 익혀서 ✔️ 씨 제거 ❌ 생호박 금지

여러분 강아지는 호박 좋아하나요? 🐕
ℹ️ 일부 이미지는 AI로 생성되었습니다""",
            "safety": "CAUTION"
        },
        "FORBIDDEN_example": {
            "text": """포도 강아지한테 절대 주면 안 돼요! 🍇
우리 햇살이도 절대 안 줘요!

신부전 위험! 몇 알만 먹어도 위험해요.
🚨 먹었다면 → 즉시 동물병원! (먹은 양/시간 기억)

모르고 주시는 분들 많아서 공유해요.
ℹ️ 일부 이미지는 AI로 생성되었습니다""",
            "safety": "FORBIDDEN"
        }
    }

    passed = 0
    failed = 0

    for name, data in test_captions.items():
        result = validate_thread_caption(data["text"], data["safety"])
        print_result(name, result)
        if result["passed"]:
            passed += 1
        else:
            failed += 1

    print(f"\n{'='*50}")
    print(f"총 결과: PASS {passed} / FAIL {failed}")
    print("="*50)


if __name__ == "__main__":
    main()
