#!/usr/bin/env python3
"""
캡션 전수조사 스크립트 - WO-RULES-001 BLOCK B

캡션규칙 v1 검증 항목:
- 구조: 결론 → 주의 → 금지 → 급여 → 핵심 → CTA → AI고지 → 해시태그
- 제목: "강아지 OOO 먹어도 되나요?" 질문형
- 해시태그: 12~16개 (인스타/블로그), 없음 (쓰레드)
- CTA, AI 고지 존재
- 안전도 일치 (FORBIDDEN에 급여법 금지)
"""

import os
import json
import re
from pathlib import Path
from datetime import datetime

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
OUTPUT_PATH = PROJECT_ROOT / "caption_audit_result.json"

def load_food_data():
    """food_data.json 로드"""
    with open(FOOD_DATA_PATH, 'r', encoding='utf-8') as f:
        return json.load(f)

def get_safety_from_filename(filename):
    """파일명에서 안전도 추출"""
    filename_upper = filename.upper()
    for safety in ['FORBIDDEN', 'DANGER', 'CAUTION', 'SAFE']:
        if safety in filename_upper:
            return safety
    return None

def get_platform_from_filename(filename):
    """파일명에서 플랫폼 추출"""
    filename_lower = filename.lower()
    if 'insta' in filename_lower:
        return 'Insta'
    elif 'thread' in filename_lower:
        return 'Thread'
    elif 'blog' in filename_lower:
        return 'Blog'
    return None

def count_hashtags(content):
    """해시태그 개수 세기"""
    hashtags = re.findall(r'#\S+', content)
    return len(hashtags)

def check_title_format(content):
    """제목 형식 검사: '강아지 OOO 먹어도 되나요?' 또는 유사 질문형"""
    # 여러 질문형 패턴 허용
    patterns = [
        r'강아지.*먹어도.*되나요',
        r'강아지.*줘도.*되나요',
        r'강아지.*줘도.*될까요',
        r'강아지한테.*줘도.*되나요',
        r'강아지한테.*줘도.*될까요',
    ]
    for pattern in patterns:
        if re.search(pattern, content):
            return True
    return False

def check_ai_notice(content):
    """AI 고지 존재 여부"""
    patterns = [
        r'AI.*생성',
        r'AI로.*생성',
        r'일부.*이미지.*AI',
    ]
    for pattern in patterns:
        if re.search(pattern, content):
            return True
    return False

def check_cta(content):
    """CTA (Call to Action) 존재 여부"""
    cta_patterns = [
        r'좋아하나요\?',
        r'해보세요',
        r'주세요',
        r'알려주세요',
        r'공유해요',
        r'댓글',
        r'팔로우',
    ]
    for pattern in cta_patterns:
        if re.search(pattern, content):
            return True
    return False

def check_dosage_4_levels(content):
    """급여량 4단계 존재 여부"""
    levels = ['소형견', '중형견', '대형견', '초대형견']
    found = sum(1 for level in levels if level in content)
    return found >= 4

def check_forbidden_violation(content, safety):
    """FORBIDDEN 안전도에 급여법/조리법 포함 여부"""
    if safety != 'FORBIDDEN':
        return False

    # 급여법/조리법 관련 키워드
    forbidden_keywords = [
        r'급여.*방법',
        r'조리.*방법',
        r'주시면.*좋아요',
        r'괜찮아요',
        r'줄 수 있어요',
        r'급여량',
        r'주셔도',
    ]
    for pattern in forbidden_keywords:
        if re.search(pattern, content):
            return True
    return False

def check_thread_no_hashtags(content, platform):
    """쓰레드에 해시태그 없는지 확인"""
    if platform != 'Thread':
        return True
    hashtag_count = count_hashtags(content)
    return hashtag_count == 0

def check_thread_line_count(content, platform):
    """쓰레드 줄 수 확인 (5-10줄)"""
    if platform != 'Thread':
        return True
    lines = [l for l in content.strip().split('\n') if l.strip()]
    return 5 <= len(lines) <= 10

def audit_caption(file_path, food_data):
    """단일 캡션 파일 검사"""
    violations = []
    warnings = []

    filename = os.path.basename(file_path)
    safety = get_safety_from_filename(filename)
    platform = get_platform_from_filename(filename)

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        return {'violations': [f'파일 읽기 오류: {str(e)}'], 'warnings': []}

    # 1. 제목 형식 검사
    if not check_title_format(content):
        violations.append('제목 형식 불일치 (질문형 아님)')

    # 2. AI 고지 검사
    if not check_ai_notice(content):
        violations.append('AI 고지 누락')

    # 3. CTA 검사
    if not check_cta(content):
        warnings.append('CTA 미발견')

    # 4. 해시태그 검사 (플랫폼별)
    hashtag_count = count_hashtags(content)
    if platform in ['Insta', 'Blog']:
        if hashtag_count < 12:
            warnings.append(f'해시태그 부족 ({hashtag_count}개)')
        elif hashtag_count > 16:
            warnings.append(f'해시태그 과다 ({hashtag_count}개)')
    elif platform == 'Thread':
        if hashtag_count > 0:
            violations.append(f'쓰레드에 해시태그 사용 ({hashtag_count}개)')

    # 5. 급여량 4단계 검사 (FORBIDDEN 제외)
    if safety not in ['FORBIDDEN', 'DANGER']:
        if not check_dosage_4_levels(content):
            warnings.append('급여량 4단계 미포함')

    # 6. FORBIDDEN 위반 검사
    if check_forbidden_violation(content, safety):
        violations.append('FORBIDDEN 음식에 급여법/조리법 포함')

    # 7. 쓰레드 줄 수 검사
    if platform == 'Thread':
        lines = [l for l in content.strip().split('\n') if l.strip()]
        if len(lines) > 10:
            warnings.append(f'쓰레드 길이 초과 ({len(lines)}줄)')

    return {
        'violations': violations,
        'warnings': warnings,
        'safety': safety,
        'platform': platform,
        'hashtag_count': hashtag_count
    }

def run_audit():
    """전수조사 실행"""
    print("━━━━━ BLOCK B: 캡션 전수조사 ━━━━━")

    food_data = load_food_data()

    results = {
        'timestamp': datetime.now().isoformat(),
        'total': 0,
        'pass': 0,
        'fail': 0,
        'warnings_only': 0,
        'fail_rate': 0,
        'failures': [],
        'warnings_list': [],
        'violation_summary': {},
        'by_platform': {'Insta': {'pass': 0, 'fail': 0}, 'Thread': {'pass': 0, 'fail': 0}, 'Blog': {'pass': 0, 'fail': 0}},
        'by_safety': {'SAFE': {'pass': 0, 'fail': 0}, 'CAUTION': {'pass': 0, 'fail': 0}, 'DANGER': {'pass': 0, 'fail': 0}, 'FORBIDDEN': {'pass': 0, 'fail': 0}}
    }

    # 캡션 파일 찾기
    caption_files = []
    for root, dirs, files in os.walk(CONTENTS_DIR):
        for f in files:
            if f.endswith('_Caption.txt') or 'caption' in f.lower():
                caption_files.append(os.path.join(root, f))

    results['total'] = len(caption_files)
    print(f"총 캡션 파일: {len(caption_files)}개")

    folder_results = {}

    for idx, filepath in enumerate(sorted(caption_files)):
        rel_path = os.path.relpath(filepath, CONTENTS_DIR)
        folder_name = rel_path.split(os.sep)[0]
        filename = os.path.basename(filepath)

        audit_result = audit_caption(filepath, food_data)

        platform = audit_result.get('platform', 'Unknown')
        safety = audit_result.get('safety', 'Unknown')
        violations = audit_result.get('violations', [])
        warnings = audit_result.get('warnings', [])

        # 폴더별 결과 집계
        if folder_name not in folder_results:
            folder_results[folder_name] = {'Insta': '?', 'Thread': '?', 'Blog': '?'}

        if violations:
            results['fail'] += 1
            folder_results[folder_name][platform] = '❌'
            if platform in results['by_platform']:
                results['by_platform'][platform]['fail'] += 1
            if safety in results['by_safety']:
                results['by_safety'][safety]['fail'] += 1

            results['failures'].append({
                'folder': folder_name,
                'file': filename,
                'platform': platform,
                'safety': safety,
                'violations': violations,
                'warnings': warnings
            })

            # 위반 유형 집계
            for v in violations:
                v_key = v.split('(')[0].strip()
                results['violation_summary'][v_key] = results['violation_summary'].get(v_key, 0) + 1
        elif warnings:
            results['warnings_only'] += 1
            folder_results[folder_name][platform] = '⚠️'
            results['pass'] += 1
            if platform in results['by_platform']:
                results['by_platform'][platform]['pass'] += 1
            if safety in results['by_safety']:
                results['by_safety'][safety]['pass'] += 1

            results['warnings_list'].append({
                'folder': folder_name,
                'file': filename,
                'platform': platform,
                'warnings': warnings
            })
        else:
            results['pass'] += 1
            folder_results[folder_name][platform] = '✅'
            if platform in results['by_platform']:
                results['by_platform'][platform]['pass'] += 1
            if safety in results['by_safety']:
                results['by_safety'][safety]['pass'] += 1

        # 진행 상황 출력 (50개마다)
        if (idx + 1) % 50 == 0:
            print(f"  검사 진행: {idx + 1}/{len(caption_files)}")

    # 불합격률 계산
    if results['total'] > 0:
        results['fail_rate'] = round(results['fail'] / results['total'] * 100, 1)

    # 결과 저장
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    # 결과 출력
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("전수조사 완료")
    print(f"  총: {results['total']}개")
    print(f"  합격: {results['pass']}개")
    print(f"  불합격: {results['fail']}개 ({results['fail_rate']}%)")
    print(f"  경고만: {results['warnings_only']}개")
    print()
    print("플랫폼별:")
    for platform, counts in results['by_platform'].items():
        print(f"  {platform}: PASS {counts['pass']}, FAIL {counts['fail']}")
    print()
    print("위반 유형 TOP 5:")
    sorted_violations = sorted(results['violation_summary'].items(), key=lambda x: x[1], reverse=True)[:5]
    for v_type, count in sorted_violations:
        print(f"  - {v_type}: {count}건")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print(f"\n결과 저장: {OUTPUT_PATH}")

    return results

if __name__ == "__main__":
    run_audit()
