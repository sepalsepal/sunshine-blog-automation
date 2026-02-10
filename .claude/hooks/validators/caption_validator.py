#!/usr/bin/env python3
"""
caption_validator.py - 캡션 Validator
WO-036: RULES.md §6.2~§6.6 기준 PASS/FAIL 판정

사용법: python3 caption_validator.py <file_path>
Exit 0: PASS
Exit 1: FAIL
"""

import sys
import re
from pathlib import Path

def validate_caption(file_path: str) -> tuple[bool, list[str]]:
    """
    캡션 검증
    RULES.md §6.2 캡션 규칙 (파스타 규칙) 기준
    """
    fails = []
    passes = []

    if not Path(file_path).exists():
        return False, ["파일이 존재하지 않음"]

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return False, [f"파일 읽기 실패: {e}"]

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §6.2.1 안전 이모지 (🟢/🟡/🔴)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    safety_emoji = re.search(r'[🟢🟡🔴]', content)
    if safety_emoji:
        passes.append("안전 이모지 PASS")
    else:
        fails.append("안전 이모지 FAIL: 🟢/🟡/🔴 중 하나 필요 (§6.2.1)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §6.2.5 CTA (행동 유도)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    cta_patterns = [
        r'저장|팔로우|공유|댓글|좋아요',
        r'프로필|링크|확인',
        r'같이 보면 좋|함께 읽'
    ]
    cta_found = any(re.search(p, content) for p in cta_patterns)
    if cta_found:
        passes.append("CTA 표현 PASS")
    else:
        fails.append("CTA FAIL: 저장/팔로우/공유 등 행동유도 필요 (§6.2.5)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §6.2.6 AI 공시
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    ai_disclosure = re.search(r'AI|인공지능|자동 생성|GPT|Claude', content, re.IGNORECASE)
    if ai_disclosure:
        passes.append("AI 공시 PASS")
    else:
        fails.append("AI 공시 FAIL: AI 생성 명시 필요 (§6.2.6)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §6.2.7 해시태그 12~16개
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    hashtags = re.findall(r'#\w+', content)
    hashtag_count = len(hashtags)

    if 12 <= hashtag_count <= 16:
        passes.append(f"해시태그 {hashtag_count}개 PASS (12~16)")
    else:
        fails.append(f"해시태그 FAIL: {hashtag_count}개 (12~16 필요)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §6.3 보호자 동질감 규칙
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 마무리 "같은 보호자" 메시지
    guardian_msg = re.search(r'같은 고민|같은 보호자|도움이 되', content)
    if guardian_msg:
        passes.append("보호자 동질감 메시지 PASS")
    else:
        fails.append("보호자 동질감 FAIL: '같은 보호자' 메시지 필요 (§6.3)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 결과
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    all_passed = len(fails) == 0

    return all_passed, passes + fails


def main():
    if len(sys.argv) < 2:
        print("사용법: python3 caption_validator.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    passed, messages = validate_caption(file_path)

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"CAPTION VALIDATOR: {'PASS' if passed else 'FAIL'}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"파일: {file_path}")
    print("")

    for msg in messages:
        prefix = "✅" if "PASS" in msg else "❌"
        print(f"  {prefix} {msg}")

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    sys.exit(0 if passed else 1)


if __name__ == "__main__":
    main()
