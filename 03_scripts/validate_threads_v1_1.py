#!/usr/bin/env python3
"""
Threads Caption v1.1 Validator
변환된 캡션이 v1.1 규칙을 준수하는지 검증
"""

import os
from pathlib import Path

BASE_DIR = Path("/Users/al02399300/Desktop/Jun_AI/Dog_Contents/project_sunshine")
CONTENTS_DIR = BASE_DIR / "01_contents"

def validate_caption(file_path: Path) -> dict:
    """단일 캡션 파일 검증"""
    results = {
        'file': str(file_path),
        'checks': {},
        'passed': True,
        'errors': []
    }

    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()

    lines = content.strip().split('\n')
    first_line = lines[0] if lines else ""
    last_line = lines[-1] if lines else ""

    # 1. 500자 이하 체크
    char_count = len(content)
    results['checks']['char_count'] = char_count
    if char_count > 500:
        results['passed'] = False
        results['errors'].append(f"500자 초과: {char_count}자")

    # 2. 영문 시작 체크 (첫 줄이 영어로 시작)
    first_char = first_line[0] if first_line else ""
    is_english_start = first_char.isascii() or first_char in "🚫🚨🟡✅"
    results['checks']['english_start'] = is_english_start
    if not is_english_start:
        results['passed'] = False
        results['errors'].append(f"영문 시작 아님: {first_line[:30]}")

    # 3. #CanMyDogEatThis 해시태그 필수 체크
    has_required_hashtag = "#CanMyDogEatThis" in content
    results['checks']['required_hashtag'] = has_required_hashtag
    if not has_required_hashtag:
        results['passed'] = False
        results['errors'].append("#CanMyDogEatThis 해시태그 누락")

    # 4. 해시태그 2개 이하 체크
    hashtag_count = content.count('#')
    results['checks']['hashtag_count'] = hashtag_count
    if hashtag_count > 2:
        results['passed'] = False
        results['errors'].append(f"해시태그 {hashtag_count}개 (2개 이하 필요)")

    # 5. 한글 에피소드 포함 체크
    has_korean = any('\uac00' <= c <= '\ud7a3' for c in content)
    results['checks']['has_korean'] = has_korean
    if not has_korean:
        results['passed'] = False
        results['errors'].append("한글 에피소드 누락")

    # 6. 이모지 체크 (🐾 포함 권장)
    has_paw_emoji = "🐾" in content
    results['checks']['has_paw_emoji'] = has_paw_emoji

    return results

def main():
    print("=" * 60)
    print("Threads Caption v1.1 Validator")
    print("=" * 60)

    # 검증 결과 집계
    total = 0
    passed = 0
    failed = 0
    failed_items = []

    # 021~175 폴더 순회
    for folder in sorted(CONTENTS_DIR.iterdir()):
        if not folder.is_dir():
            continue

        try:
            folder_num = int(folder.name.split('_')[0])
        except:
            continue

        if folder_num < 21 or folder_num > 175:
            continue

        # 캡션 파일 찾기
        insta_dir = folder / "01_Insta&Thread"
        if not insta_dir.exists():
            continue

        for f in insta_dir.iterdir():
            if f.name.endswith('_Threads_Caption.txt'):
                total += 1
                result = validate_caption(f)

                if result['passed']:
                    passed += 1
                else:
                    failed += 1
                    failed_items.append(result)

    # 결과 출력
    print(f"\n검증 완료: {total}개 파일")
    print(f"통과: {passed}개 ({passed/total*100:.1f}%)")
    print(f"실패: {failed}개 ({failed/total*100:.1f}%)")

    if failed_items:
        print("\n실패 항목 상세:")
        for item in failed_items[:10]:
            print(f"\n  파일: {Path(item['file']).name}")
            for err in item['errors']:
                print(f"    ❌ {err}")
        if len(failed_items) > 10:
            print(f"\n  ... 외 {len(failed_items) - 10}개")

    print("\n" + "=" * 60)
    print("v1.1 규칙 체크 항목:")
    print("  ✅ 500자 이하")
    print("  ✅ 영문 시작")
    print("  ✅ #CanMyDogEatThis 필수")
    print("  ✅ 해시태그 2개 이하")
    print("  ✅ 한글 에피소드 포함")
    print("=" * 60)

    return passed == total

if __name__ == "__main__":
    main()
