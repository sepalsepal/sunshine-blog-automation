#!/usr/bin/env python3
"""
body_validator.py - 블로그 본문 Validator
WO-036: RULES.md §2.1 BLOG_RENDER v2.0 기준 PASS/FAIL 판정

사용법: python3 body_validator.py <file_path>
Exit 0: PASS
Exit 1: FAIL
"""

import sys
import re
from pathlib import Path

def validate_body(file_path: str) -> tuple[bool, list[str]]:
    """
    블로그 본문 검증
    RULES.md §2.1 BLOG_RENDER v2.0 기준
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
    # §2.1 글자수: 1,800자 ±10% (1,620~1,980)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # HTML 태그 제거 후 글자수 계산
    text_only = re.sub(r'<[^>]+>', '', content)
    text_only = re.sub(r'\s+', ' ', text_only).strip()
    char_count = len(text_only)

    if 1620 <= char_count <= 1980:
        passes.append(f"글자수 {char_count}자 PASS (1,620~1,980)")
    else:
        fails.append(f"글자수 FAIL: {char_count}자 (1,620~1,980 필요)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §2.1 H2: 4개 이상
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    h2_count = len(re.findall(r'##\s+[^\n]+|<h2[^>]*>.*?</h2>', content, re.IGNORECASE))

    if h2_count >= 4:
        passes.append(f"H2 {h2_count}개 PASS (4개 이상)")
    else:
        fails.append(f"H2 FAIL: {h2_count}개 (4개 이상 필요)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §6.3 보호자 동질감 규칙 검증
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

    # 1. 도입부 검색 경험 표현
    search_exp = re.search(r'검색|고민|궁금|찾아봤', content)
    if search_exp:
        passes.append("도입부 검색/고민 경험 표현 PASS")
    else:
        fails.append("도입부 FAIL: 검색/고민 경험 표현 없음 (§6.3)")

    # 2. 햇살이 에피소드 (2회 이상)
    sunshine_mentions = len(re.findall(r'햇살이', content))
    if sunshine_mentions >= 2:
        passes.append(f"햇살이 언급 {sunshine_mentions}회 PASS (2회 이상)")
    else:
        fails.append(f"햇살이 언급 FAIL: {sunshine_mentions}회 (2회 이상 필요)")

    # 3. 경험 공유 톤 ("~더라고요" 등)
    exp_tone = re.search(r'더라고요|했었어요|해보니까|기억이 나요', content)
    if exp_tone:
        passes.append("경험 공유 톤 PASS")
    else:
        fails.append("경험 공유 톤 FAIL: '~더라고요' 등 표현 없음 (§6.3)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # §6.6 급여량 형식 (4줄 구조)
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    feeding_section = re.search(r'급여량.*?(?=##|$)', content, re.DOTALL)
    if feeding_section:
        section_text = feeding_section.group()
        size_keywords = ['소형견', '중형견', '대형견', '초대형견']
        found_sizes = sum(1 for kw in size_keywords if kw in section_text)

        if found_sizes >= 3:
            passes.append(f"급여량 체중별 구분 {found_sizes}개 PASS")
        else:
            fails.append(f"급여량 형식 FAIL: 체중별 구분 {found_sizes}개 (3개 이상 필요)")

    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    # 결과
    # ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
    all_passed = len(fails) == 0

    return all_passed, passes + fails


def main():
    if len(sys.argv) < 2:
        print("사용법: python3 body_validator.py <file_path>")
        sys.exit(1)

    file_path = sys.argv[1]
    passed, messages = validate_body(file_path)

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"BODY VALIDATOR: {'PASS' if passed else 'FAIL'}")
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
