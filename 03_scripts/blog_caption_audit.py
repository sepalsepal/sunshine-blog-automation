#!/usr/bin/env python3
"""
블로그 캡션 규칙 검수 스크립트
BLOG_RULE.md 기준 검수
"""

import json
import re
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"

# 안전도별 후킹 문구
HOOKING_PATTERNS = {
    "SAFE": "검색해본 적 있다면",
    "CAUTION": "사랑하니까 한 번 더 확인",
    "DANGER": "알고 있는 것과 모르는 것",
    "FORBIDDEN": "몰랐다면 괜찮아요"
}

# 안전도별 이모지
SAFETY_EMOJIS = {
    "SAFE": "🟢",
    "CAUTION": "🟡",
    "DANGER": "🟠",
    "FORBIDDEN": "⛔"
}

def load_food_data():
    with open(FOOD_DATA_PATH, "r", encoding="utf-8") as f:
        return json.load(f)

def find_blog_caption(folder: Path):
    """블로그 캡션 파일 찾기"""
    # 새 경로
    new_path = folder / "blog" / "caption.txt"
    if new_path.exists():
        return new_path

    # OLD 경로
    old_blog_dir = folder / "02_Blog"
    if old_blog_dir.exists():
        for f in old_blog_dir.glob("*_Blog_Caption.txt"):
            return f

    return None

def audit_blog_caption(content: str, safety: str, food_name: str):
    """블로그 캡션 검수"""
    issues = []

    # 1. 글자수 검사 (1,620~1,980)
    char_count = len(content)
    if char_count < 1620:
        issues.append(f"글자수 부족: {char_count}자 (최소 1,620자)")
    elif char_count > 1980:
        issues.append(f"글자수 초과: {char_count}자 (최대 1,980자)")

    # 2. 이미지 배치 검사 (9장)
    image_pattern = r'\[이미지\s*(\d+)번[:\s]'
    images = re.findall(image_pattern, content)
    image_nums = [int(n) for n in images]

    if len(image_nums) != 9:
        issues.append(f"이미지 개수 오류: {len(image_nums)}개 (9개 필요)")

    expected_order = [1, 2, 3, 4, 5, 6, 7, 8, 9]
    if image_nums != expected_order:
        issues.append(f"이미지 순서 오류: {image_nums} (1~9 순서 필요)")

    # 3. 후킹 문구 검사
    hooking = HOOKING_PATTERNS.get(safety, "")
    if hooking and hooking not in content:
        issues.append(f"후킹 문구 누락: '{hooking}' (안전도: {safety})")

    # 4. 안전 이모지 검사
    emoji = SAFETY_EMOJIS.get(safety, "")
    if emoji and emoji not in content:
        issues.append(f"안전 이모지 누락: {emoji} (안전도: {safety})")

    # 5. H2 개수 검사 (4개 이상)
    h2_count = len(re.findall(r'^##\s', content, re.MULTILINE))
    if h2_count < 4:
        issues.append(f"H2 부족: {h2_count}개 (최소 4개)")

    # 6. 해시태그 검사 (12~16개)
    hashtags = re.findall(r'#[^\s#]+', content)
    if len(hashtags) < 12:
        issues.append(f"해시태그 부족: {len(hashtags)}개 (최소 12개)")
    elif len(hashtags) > 16:
        issues.append(f"해시태그 초과: {len(hashtags)}개 (최대 16개)")

    # 7. FORBIDDEN 특별 검사
    if safety == "FORBIDDEN":
        # 급여량 있으면 안 됨
        if "급여량" in content and ("소형견" in content or "중형견" in content):
            if "급여량 없음" not in content and "급여하지 마세요" not in content:
                issues.append("FORBIDDEN: 급여량표가 포함됨 (금지)")

    return issues

def main():
    food_data = load_food_data()

    print("=" * 70)
    print("📋 블로그 캡션 규칙 검수 (008번 이후)")
    print("=" * 70)

    fails = []
    passes = []
    skipped = []

    for folder in sorted(CONTENTS_DIR.iterdir()):
        if not folder.is_dir():
            continue

        match = re.match(r'^(\d{3})_', folder.name)
        if not match:
            continue

        num = int(match.group(1))
        if num < 8 or num == 0 or num == 999:
            continue

        # food_data에서 안전도 가져오기
        food_info = food_data.get(str(num), {})
        safety = food_info.get("safety", "UNKNOWN")
        food_name = food_info.get("name", folder.name.split("_", 1)[1] if "_" in folder.name else folder.name)

        # 블로그 캡션 찾기
        caption_path = find_blog_caption(folder)
        if not caption_path:
            skipped.append((num, food_name, "캡션 파일 없음"))
            continue

        with open(caption_path, "r", encoding="utf-8") as f:
            content = f.read()

        issues = audit_blog_caption(content, safety, food_name)

        if issues:
            fails.append((num, food_name, safety, issues, caption_path))
        else:
            passes.append((num, food_name, safety))

    # 결과 출력
    print(f"\n✅ PASS: {len(passes)}건")
    print(f"❌ FAIL: {len(fails)}건")
    print(f"⏭️ SKIP: {len(skipped)}건")

    if fails:
        print("\n" + "=" * 70)
        print("❌ FAIL 상세")
        print("=" * 70)

        for num, name, safety, issues, path in fails:
            print(f"\n[{num:03d}] {name} ({safety})")
            print(f"     파일: {path.name}")
            for issue in issues:
                print(f"     ⚠️ {issue}")

    if skipped:
        print("\n" + "=" * 70)
        print("⏭️ SKIP 목록")
        print("=" * 70)
        for num, name, reason in skipped:
            print(f"  {num:03d} {name}: {reason}")

    # JSON 결과 저장
    result = {
        "total": len(passes) + len(fails),
        "pass_count": len(passes),
        "fail_count": len(fails),
        "skip_count": len(skipped),
        "passes": [{"num": n, "name": name, "safety": s} for n, name, s in passes],
        "fails": [{"num": n, "name": name, "safety": s, "issues": i, "path": str(p)} for n, name, s, i, p in fails],
        "skipped": [{"num": n, "name": name, "reason": r} for n, name, r in skipped]
    }

    with open(PROJECT_ROOT / "blog_caption_audit_result.json", "w", encoding="utf-8") as f:
        json.dump(result, f, ensure_ascii=False, indent=2)

    print(f"\n📊 결과 저장: blog_caption_audit_result.json")

    return len(fails)

if __name__ == "__main__":
    exit(main())
