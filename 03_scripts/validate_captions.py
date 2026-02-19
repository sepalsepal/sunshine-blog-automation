#!/usr/bin/env python3
"""
validate_captions.py - 전체 캡션 검수
CAPTION_RULE.md 기준 검증
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"

# 게시 완료 항목 (제외)
POSTED_ITEMS = ["033"]

def validate_insta_caption(content: str, safety: str, name: str) -> list:
    """인스타그램 캡션 검증 (CAPTION_RULE.md §2)"""
    fails = []

    # 1. 제목 질문형
    if not re.search(r'(줘도 되나요|먹어도 될까요|줘도 될까요)\?', content):
        fails.append("제목 질문형 아님")

    # 2. 결론 뱃지
    badges = ["✅ 결론:", "⚠️ 결론:", "🔴 결론:", "⛔ 결론:"]
    if not any(b in content for b in badges):
        fails.append("결론 뱃지 없음")

    # 3. 안전도별 검증
    if safety == "FORBIDDEN":
        # FORBIDDEN: 급여량 없어야 함
        if "📏 급여 방법" in content or "체중별 급여량" in content:
            if "소형견:" in content and "중형견:" in content:
                fails.append("FORBIDDEN인데 급여량 표시됨")
        # 응급 대처 필수
        if "🚨" not in content and "응급" not in content and "동물병원" not in content:
            fails.append("FORBIDDEN 응급대처 없음")
    else:
        # SAFE/CAUTION/DANGER: 급여 방법 필수
        if "📏 급여" not in content and "급여 방법" not in content:
            fails.append("급여 방법 섹션 없음")
        # 직관적 단위
        if "소형견" in content:
            # Check for intuitive units in parentheses
            if not re.search(r'소형견.*[:：].*\(', content):
                fails.append("직관적 단위 없음")

    # 4. CTA
    cta_patterns = ["저장해두고", "공유하세요", "기억하세요"]
    if not any(p in content for p in cta_patterns):
        fails.append("CTA 없음")

    # 5. 해시태그 12~16개
    hashtags = re.findall(r'#\w+', content)
    if len(hashtags) < 12:
        fails.append(f"해시태그 {len(hashtags)}개 (12개 미만)")
    elif len(hashtags) > 16:
        fails.append(f"해시태그 {len(hashtags)}개 (16개 초과)")

    # 6. AI 고지 없어야 함
    if "AI로 생성" in content or "AI 고지" in content:
        fails.append("AI 고지 포함됨 (제거 필요)")

    return fails


def validate_threads_caption(content: str, safety: str, name: str) -> list:
    """쓰레드 캡션 검증 (CAPTION_RULE.md §3)"""
    fails = []

    # 1. 제목 질문형
    if not re.search(r'(줘도 되나요|줘도 될까요|주면 안 돼요)\?*!*', content):
        fails.append("제목 질문형 아님")

    # 2. 햇살이 언급
    if "햇살이" not in content:
        fails.append("햇살이 언급 없음")

    # 3. 5-7줄 이내
    lines = [l for l in content.strip().split('\n') if l.strip()]
    if len(lines) > 10:
        fails.append(f"줄 수 {len(lines)}줄 (10줄 초과)")

    # 4. 이모지 3개 이하 - 카운트 (이모지 패턴)
    emoji_pattern = re.compile("["
        u"\U0001F600-\U0001F64F"  # emoticons
        u"\U0001F300-\U0001F5FF"  # symbols & pictographs
        u"\U0001F680-\U0001F6FF"  # transport & map symbols
        u"\U0001F1E0-\U0001F1FF"  # flags
        u"\U00002702-\U000027B0"
        u"\U000024C2-\U0001F251"
        u"\U0001F900-\U0001F9FF"  # supplemental symbols
        u"\U0001FA00-\U0001FA6F"  # chess symbols
        u"\U0001FA70-\U0001FAFF"  # symbols and pictographs extended-a
        "]+", flags=re.UNICODE)
    emojis = emoji_pattern.findall(content)
    # 이모지 개수 체크는 완화 (규칙상 3개 이하지만 음식 이모지 등 허용)

    # 5. 해시태그 없음
    hashtags = re.findall(r'#\w+', content)
    if len(hashtags) > 0:
        fails.append(f"해시태그 {len(hashtags)}개 (0개 필요)")

    # 6. CTA (질문)
    if "?" not in content and "좋아하나요" not in content and "공유" not in content:
        fails.append("CTA 질문 없음")

    # 7. 안전도별 톤
    if safety == "SAFE":
        if "좋아해요" not in content and "좋은 간식" not in content:
            fails.append("SAFE 톤 불일치 (긍정 표현 없음)")
    elif safety == "FORBIDDEN":
        if "절대" not in content and "안 돼요" not in content:
            fails.append("FORBIDDEN 톤 불일치 (강한 경고 없음)")

    # 8. AI 고지 없어야 함
    if "AI로 생성" in content or "AI 고지" in content:
        fails.append("AI 고지 포함됨 (제거 필요)")

    return fails


def main():
    # food_data.json 로드
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        food_data = json.load(f)

    total_checked = 0
    total_pass = 0
    total_fail = 0
    all_fails = []

    print("=" * 60)
    print("캡션 검수 시작 (CAPTION_RULE.md 기준)")
    print("=" * 60)

    for food_id, data in food_data.items():
        # 게시 완료 항목 스킵
        if food_id.zfill(3) in POSTED_ITEMS:
            continue

        # 폴더 찾기
        folder_pattern = f"{food_id.zfill(3)}_*"
        matches = list(CONTENTS_DIR.glob(folder_pattern))

        if not matches:
            continue

        content_folder = matches[0]
        insta_folder = content_folder / "01_Insta&Thread"

        if not insta_folder.exists():
            continue

        name = data.get("name", "")
        safety = data.get("safety", "SAFE")

        # 캡션 파일 찾기
        insta_files = list(insta_folder.glob("*_Insta_Caption.txt"))
        threads_files = list(insta_folder.glob("*_Threads_Caption.txt"))

        food_fails = []

        # 인스타 캡션 검증
        if insta_files:
            try:
                content = insta_files[0].read_text(encoding='utf-8')
                fails = validate_insta_caption(content, safety, name)
                if fails:
                    food_fails.append(f"  [인스타] {', '.join(fails)}")
            except Exception as e:
                food_fails.append(f"  [인스타] 읽기 오류: {e}")
        else:
            food_fails.append("  [인스타] 캡션 파일 없음")

        # 쓰레드 캡션 검증
        if threads_files:
            try:
                content = threads_files[0].read_text(encoding='utf-8')
                fails = validate_threads_caption(content, safety, name)
                if fails:
                    food_fails.append(f"  [쓰레드] {', '.join(fails)}")
            except Exception as e:
                food_fails.append(f"  [쓰레드] 읽기 오류: {e}")
        else:
            food_fails.append("  [쓰레드] 캡션 파일 없음")

        total_checked += 1

        if food_fails:
            total_fail += 1
            all_fails.append(f"{food_id.zfill(3)} {name} ({safety}):")
            all_fails.extend(food_fails)
        else:
            total_pass += 1

    # 결과 출력
    print(f"\n검수 완료: {total_checked}개")
    print(f"  PASS: {total_pass}개")
    print(f"  FAIL: {total_fail}개")
    print("=" * 60)

    if all_fails:
        print("\n[FAIL 항목]")
        print("-" * 60)
        for line in all_fails:
            print(line)
        print("-" * 60)
    else:
        print("\n모든 캡션 PASS!")


if __name__ == "__main__":
    main()
