#!/usr/bin/env python3
"""
WO-2026-0209-024: 캡션 자동 수정 유틸리티

TOP 5 실패 패턴 대응:
1. FAIL_TYPE_04 (91%): 급여량 정보 누락 → 템플릿 강제 섹션
2. FAIL_TYPE_02 (84%): 주의사항 리스트 부족 → 최소 3개 검증
3. FAIL_TYPE_08 (82%): 해시태그 수 미달 → 자동 보충
4. FAIL_TYPE_01 (56%): 안전도 이모지 누락 → 자동 삽입
5. FAIL_TYPE_03 (29%): 절대 금지 항목 누락 → CAUTION+ 필수

사용법:
    python validators/caption_fixer.py --check 030
    python validators/caption_fixer.py --fix 030 --dry-run
"""

import sys
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


# ============================================================
# 상수 정의
# ============================================================

SAFETY_EMOJIS = {
    'SAFE': ('🍎', '✅', '급여 가능합니다! 🟢'),
    'CAUTION': ('🍋', '⚠️', '주의해서 급여하세요! 🟡'),
    'DANGER': ('🚨', '❌', '급여하지 마세요! 🔴'),
    'FORBIDDEN': ('⛔', '⛔', '절대 급여 금지! 🔴'),
}

SAFETY_EMOJI_DETECT = {
    'SAFE': ('✅', '🟢', '🍎'),
    'CAUTION': ('⚠️', '🟡', '🍋'),
    'DANGER': ('🚨', '🔴'),
    'FORBIDDEN': ('⛔', '🔴'),
}

DEFAULT_HASHTAGS = [
    "#강아지음식", "#반려견건강", "#강아지간식",
    "#골든리트리버", "#시니어견", "#강아지영양",
    "#반려견음식", "#강아지먹이", "#펫푸드",
    "#강아지사료", "#독푸드", "#햇살이",
    "#dogfood", "#doghealth", "#petcare", "#goldensofinstagram"
]

SIZE_KEYWORDS = ['소형견', '중형견', '대형견', '소형', '중형', '대형']
FORBIDDEN_KEYWORDS = ['금지', '🚫', '절대', '위험', '독성']


# ============================================================
# 자동 수정 함수
# ============================================================

def fix_safety_emoji(caption: str, safety_level: str) -> Tuple[str, bool]:
    """
    FAIL_TYPE_01: 안전도 이모지 자동 삽입

    Returns:
        (수정된 캡션, 수정 여부)
    """
    safety = safety_level.upper()
    if safety not in SAFETY_EMOJIS:
        return caption, False

    # 이미 올바른 이모지가 있는지 확인
    expected_emojis = SAFETY_EMOJI_DETECT.get(safety, ())
    if any(e in caption for e in expected_emojis):
        return caption, False

    # 첫 줄에 이모지 삽입
    lines = caption.split('\n')
    first_line = lines[0] if lines else ''

    emoji, _, _ = SAFETY_EMOJIS[safety]

    # 첫 줄 시작에 이모지 추가
    if not first_line.startswith(emoji):
        lines[0] = f"{emoji} {first_line}"

    return '\n'.join(lines), True


def fix_hashtags(caption: str, food_name: str = '') -> Tuple[str, bool]:
    """
    FAIL_TYPE_08: 해시태그 자동 보충 (12개 미만 시)

    Returns:
        (수정된 캡션, 수정 여부)
    """
    current_count = caption.count('#')

    if current_count >= 12:
        return caption, False

    # 기존 해시태그 추출
    existing = set(re.findall(r'#\w+', caption))

    # 음식별 해시태그 추가
    additional = []
    if food_name:
        food_tag = f"#강아지{food_name}"
        if food_tag not in existing:
            additional.append(food_tag)

    # 부족한 만큼 기본 해시태그에서 추가
    needed = 12 - current_count - len(additional)
    for tag in DEFAULT_HASHTAGS:
        if needed <= 0:
            break
        if tag not in existing and tag not in additional:
            additional.append(tag)
            needed -= 1

    if not additional:
        return caption, False

    # 캡션 끝에 해시태그 추가
    return caption.rstrip() + '\n' + ' '.join(additional), True


def check_bullet_points(caption: str) -> Tuple[int, List[str]]:
    """
    FAIL_TYPE_02: 주의사항 리스트 개수 확인

    Returns:
        (• 개수, 리스트 항목들)
    """
    bullets = re.findall(r'•\s*(.+)', caption)
    return len(bullets), bullets


def check_size_info(caption: str) -> bool:
    """
    FAIL_TYPE_04: 급여량 정보 존재 확인
    """
    return any(kw in caption for kw in SIZE_KEYWORDS)


def check_forbidden_section(caption: str, safety_level: str) -> bool:
    """
    FAIL_TYPE_03: 절대 금지 항목 확인 (CAUTION 이상)
    """
    if safety_level.upper() in ['SAFE']:
        return True  # SAFE는 면제

    return any(kw in caption for kw in FORBIDDEN_KEYWORDS)


def generate_size_template(food_name: str) -> str:
    """급여량 템플릿 생성"""
    return f"""
📏 급여 방법
• 소형견 (5kg 미만): 소량
• 중형견 (5~15kg): 적당량
• 대형견 (15kg 이상): 적당량
※ 처음 급여 시 소량으로 시작
""".strip()


def generate_forbidden_template() -> str:
    """절대 금지 템플릿 생성"""
    return """
❌ 절대 금지 항목
• 과다 급여
• 양념/조미료 추가
• 가공 제품
""".strip()


# ============================================================
# 통합 분석/수정 함수
# ============================================================

def analyze_caption(caption: str, safety_level: str) -> Dict:
    """
    캡션 문제점 분석
    """
    issues = []

    # FAIL_TYPE_01: 안전도 이모지
    safety = safety_level.upper()
    expected_emojis = SAFETY_EMOJI_DETECT.get(safety, ())
    if not any(e in caption for e in expected_emojis):
        issues.append({
            'type': 'FAIL_TYPE_01',
            'desc': '안전도 이모지 누락',
            'fix': 'auto'
        })

    # FAIL_TYPE_02: 주의사항 리스트
    bullet_count, _ = check_bullet_points(caption)
    if bullet_count < 3:
        issues.append({
            'type': 'FAIL_TYPE_02',
            'desc': f'주의사항 리스트 부족 ({bullet_count}/3)',
            'fix': 'manual'
        })

    # FAIL_TYPE_03: 절대 금지 항목
    if not check_forbidden_section(caption, safety_level):
        issues.append({
            'type': 'FAIL_TYPE_03',
            'desc': '절대 금지 항목 누락',
            'fix': 'template'
        })

    # FAIL_TYPE_04: 급여량 정보
    if not check_size_info(caption):
        issues.append({
            'type': 'FAIL_TYPE_04',
            'desc': '급여량 정보 누락',
            'fix': 'template'
        })

    # FAIL_TYPE_08: 해시태그
    hashtag_count = caption.count('#')
    if hashtag_count < 12:
        issues.append({
            'type': 'FAIL_TYPE_08',
            'desc': f'해시태그 수 미달 ({hashtag_count}/12)',
            'fix': 'auto'
        })

    return {
        'total_issues': len(issues),
        'issues': issues,
        'auto_fixable': len([i for i in issues if i['fix'] == 'auto']),
        'template_needed': len([i for i in issues if i['fix'] == 'template']),
        'manual_needed': len([i for i in issues if i['fix'] == 'manual'])
    }


def auto_fix_caption(caption: str, safety_level: str, food_name: str = '') -> Tuple[str, List[str]]:
    """
    자동 수정 가능한 항목 수정

    Returns:
        (수정된 캡션, 수정된 항목 목록)
    """
    fixed = []
    result = caption

    # FAIL_TYPE_01: 안전도 이모지
    result, was_fixed = fix_safety_emoji(result, safety_level)
    if was_fixed:
        fixed.append('FAIL_TYPE_01: 안전도 이모지 추가')

    # FAIL_TYPE_08: 해시태그
    result, was_fixed = fix_hashtags(result, food_name)
    if was_fixed:
        fixed.append('FAIL_TYPE_08: 해시태그 보충')

    return result, fixed


# ============================================================
# CLI
# ============================================================

def main():
    import argparse
    from validators.caption_validator import find_caption_file, read_caption_file, get_sheet_data

    parser = argparse.ArgumentParser(description="캡션 자동 수정 유틸리티")
    parser.add_argument("--check", type=str, help="캡션 분석 (번호)")
    parser.add_argument("--fix", type=str, help="캡션 자동 수정 (번호)")
    parser.add_argument("--dry-run", action="store_true", help="실제 저장 안 함")

    args = parser.parse_args()

    if args.check:
        content_num = args.check.zfill(3)

        # 캡션 파일 찾기
        caption_file = find_caption_file(content_num, 'instagram')
        if not caption_file:
            print(f"❌ 캡션 파일 없음: {content_num}")
            return

        caption = read_caption_file(caption_file)

        # 시트에서 안전도 가져오기
        sheet_data = get_sheet_data()
        safety_level = 'SAFE'
        food_name = ''
        for item in sheet_data:
            if item['num'] == content_num:
                safety_level = item['safety_level']
                food_name = item['eng_name']
                break

        # 분석
        analysis = analyze_caption(caption, safety_level)

        print(f"\n{'='*60}")
        print(f"캡션 분석: {content_num} ({food_name})")
        print(f"안전도: {safety_level}")
        print(f"{'='*60}")

        if analysis['total_issues'] == 0:
            print("✅ 문제 없음")
        else:
            print(f"❌ 문제 발견: {analysis['total_issues']}건")
            print(f"   - 자동 수정 가능: {analysis['auto_fixable']}건")
            print(f"   - 템플릿 필요: {analysis['template_needed']}건")
            print(f"   - 수동 수정 필요: {analysis['manual_needed']}건")
            print()
            for issue in analysis['issues']:
                fix_type = {'auto': '🔧', 'template': '📝', 'manual': '✋'}[issue['fix']]
                print(f"   {fix_type} {issue['type']}: {issue['desc']}")

    elif args.fix:
        content_num = args.fix.zfill(3)

        # 캡션 파일 찾기
        caption_file = find_caption_file(content_num, 'instagram')
        if not caption_file:
            print(f"❌ 캡션 파일 없음: {content_num}")
            return

        caption = read_caption_file(caption_file)

        # 시트에서 안전도 가져오기
        sheet_data = get_sheet_data()
        safety_level = 'SAFE'
        food_name = ''
        for item in sheet_data:
            if item['num'] == content_num:
                safety_level = item['safety_level']
                food_name = item['eng_name']
                break

        # 자동 수정
        fixed_caption, fixes = auto_fix_caption(caption, safety_level, food_name)

        print(f"\n{'='*60}")
        print(f"캡션 자동 수정: {content_num} ({food_name})")
        print(f"{'='*60}")

        if not fixes:
            print("✅ 자동 수정할 항목 없음")
        else:
            print(f"🔧 수정 항목:")
            for fix in fixes:
                print(f"   - {fix}")

            if args.dry_run:
                print(f"\n[DRY-RUN] 실제 저장하지 않음")
                print(f"\n수정된 캡션 미리보기:")
                print("-" * 40)
                print(fixed_caption[:500] + "..." if len(fixed_caption) > 500 else fixed_caption)
            else:
                with open(caption_file, 'w', encoding='utf-8') as f:
                    f.write(fixed_caption)
                print(f"\n✅ 저장 완료: {caption_file}")

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
