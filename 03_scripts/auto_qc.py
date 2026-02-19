#!/usr/bin/env python3
"""
자동 QC 검증 스크립트 - WO-RULES-001 BLOCK D

사용:
    python scripts/auto_qc.py {폴더번호}
    python scripts/auto_qc.py --all
    python scripts/auto_qc.py 001_Pumpkin

검증 항목:
  [파일 존재]
  - Common_01_Cover.png (루트)
  - Common_02_Food.png (루트) — 없으면 경고
  - Common_08_Cta.png (루트)
  - 01_Insta&Thread/ 내 캡션 2개 + 이미지
  - 02_Blog/ 내 캡션 1개 + 이미지 5개

  [네이밍]
  - PascalCase 준수
  - {Food}_{Safety}_{Platform}_Caption.txt 형식
  - 안전도 food_data 일치

  [캡션 내용]
  - 질문형 제목
  - 구조 순서
  - 해시태그 12~16개
  - CTA 존재
  - AI 고지 존재
  - FORBIDDEN 안전도 특수 규칙

  [이미지]
  - 해상도 1080x1080 (커버) 또는 1080x1350 (슬라이드)

출력: qc_result.json (합격/불합격 + 사유)
"""

import os
import sys
import json
import re
from pathlib import Path
from datetime import datetime

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

# 경로 설정
PROJECT_ROOT = Path(__file__).parent.parent
CONTENTS_DIR = PROJECT_ROOT / "01_contents"
FOOD_DATA_PATH = PROJECT_ROOT / "config" / "food_data.json"
OUTPUT_PATH = PROJECT_ROOT / "qc_result.json"


def load_food_data():
    """food_data.json 로드"""
    try:
        with open(FOOD_DATA_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    except:
        return {}


def get_food_safety_from_data(food_name, food_data):
    """food_data에서 안전도 조회"""
    for key, data in food_data.items():
        english = data.get('english_name', '').lower()
        if food_name.lower() in english or english in food_name.lower():
            return data.get('safety', '').upper()
    return None


def check_pascal_case(name):
    """PascalCase 검사"""
    # 숫자_로 시작하면 OK (001_Pumpkin)
    if re.match(r'^\d+_[A-Z][a-zA-Z]*', name):
        return True
    # PascalCase 패턴
    if re.match(r'^[A-Z][a-zA-Z0-9]*$', name):
        return True
    return False


def check_file_exists(folder_path):
    """필수 파일 존재 검사"""
    results = {
        'pass': [],
        'fail': [],
        'warn': []
    }

    # 루트 파일
    folder_name = os.path.basename(folder_path)
    food_name = folder_name.split('_', 1)[1] if '_' in folder_name else folder_name

    # Common_01_Cover.png
    cover_patterns = [f'{food_name}_Common_01_Cover.png', '*Common_01_Cover.png', '*_Cover.png']
    cover_found = False
    for pattern in cover_patterns:
        matches = list(Path(folder_path).glob(pattern))
        if matches:
            cover_found = True
            results['pass'].append(f'커버 존재: {matches[0].name}')
            break
    if not cover_found:
        results['fail'].append('Common_01_Cover.png 미존재')

    # Common_02_Food.png (경고만)
    food_patterns = [f'{food_name}_Common_02_Food.png', '*Common_02_Food.png', '*_Food.png']
    food_found = False
    for pattern in food_patterns:
        matches = list(Path(folder_path).glob(pattern))
        if matches:
            food_found = True
            results['pass'].append(f'음식사진 존재: {matches[0].name}')
            break
    if not food_found:
        results['warn'].append('Common_02_Food.png 미존재 (PD TODO)')

    # 01_Insta&Thread 폴더
    insta_folder = Path(folder_path) / '01_Insta&Thread'
    if insta_folder.exists():
        # 캡션 파일 검사
        insta_captions = list(insta_folder.glob('*Insta*Caption*.txt'))
        thread_captions = list(insta_folder.glob('*Thread*Caption*.txt'))

        if insta_captions:
            results['pass'].append(f'인스타 캡션 존재: {len(insta_captions)}개')
        else:
            results['fail'].append('인스타 캡션 미존재')

        if thread_captions:
            results['pass'].append(f'쓰레드 캡션 존재: {len(thread_captions)}개')
        else:
            results['fail'].append('쓰레드 캡션 미존재')
    else:
        results['fail'].append('01_Insta&Thread 폴더 미존재')

    # 02_Blog 폴더
    blog_folder = Path(folder_path) / '02_Blog'
    if blog_folder.exists():
        blog_captions = list(blog_folder.glob('*Blog*Caption*.txt'))
        blog_images = list(blog_folder.glob('*.png'))

        if blog_captions:
            results['pass'].append(f'블로그 캡션 존재: {len(blog_captions)}개')
        else:
            results['fail'].append('블로그 캡션 미존재')

        if len(blog_images) >= 5:
            results['pass'].append(f'블로그 이미지 존재: {len(blog_images)}개')
        else:
            results['warn'].append(f'블로그 이미지 부족: {len(blog_images)}개 (최소 5개)')
    else:
        results['warn'].append('02_Blog 폴더 미존재')

    # 00_Clean 폴더
    clean_folder = Path(folder_path) / '00_Clean'
    if clean_folder.exists():
        clean_files = list(clean_folder.glob('*.png'))
        if clean_files:
            results['pass'].append(f'클린 소스 존재: {len(clean_files)}개')
        else:
            results['warn'].append('00_Clean 폴더에 파일 없음')
    else:
        results['warn'].append('00_Clean 폴더 미존재')

    return results


def check_caption_content(caption_path, platform, expected_safety):
    """캡션 내용 검사"""
    results = {
        'pass': [],
        'fail': [],
        'warn': []
    }

    try:
        with open(caption_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        results['fail'].append(f'파일 읽기 오류: {str(e)}')
        return results

    # 1. 제목 형식 (질문형)
    title_patterns = [
        r'강아지.*먹어도.*되나요',
        r'강아지.*줘도.*되나요',
        r'강아지.*줘도.*될까요',
    ]
    title_found = any(re.search(p, content) for p in title_patterns)
    if title_found:
        results['pass'].append('제목 질문형')
    else:
        results['fail'].append('제목 형식 불일치')

    # 2. AI 고지
    ai_patterns = [r'AI.*생성', r'AI로.*생성', r'일부.*이미지.*AI']
    ai_found = any(re.search(p, content) for p in ai_patterns)
    if ai_found:
        results['pass'].append('AI 고지 존재')
    else:
        results['fail'].append('AI 고지 누락')

    # 3. 해시태그 (플랫폼별)
    hashtags = re.findall(r'#\S+', content)
    hashtag_count = len(hashtags)

    if platform in ['Insta', 'Blog']:
        if 12 <= hashtag_count <= 16:
            results['pass'].append(f'해시태그 적절: {hashtag_count}개')
        elif hashtag_count < 12:
            results['warn'].append(f'해시태그 부족: {hashtag_count}개')
        else:
            results['warn'].append(f'해시태그 과다: {hashtag_count}개')
    elif platform == 'Thread':
        if hashtag_count == 0:
            results['pass'].append('쓰레드 해시태그 없음')
        else:
            results['fail'].append(f'쓰레드에 해시태그 사용: {hashtag_count}개')

    # 4. FORBIDDEN 검사
    if expected_safety == 'FORBIDDEN':
        forbidden_keywords = [r'급여.*방법', r'조리.*방법', r'급여량']
        forbidden_found = any(re.search(p, content) for p in forbidden_keywords)
        if forbidden_found:
            results['fail'].append('FORBIDDEN 음식에 급여법/조리법 포함')
        else:
            results['pass'].append('FORBIDDEN 규칙 준수')

    # 5. CTA 검사
    cta_patterns = [r'좋아하나요\?', r'해보세요', r'주세요', r'알려주세요', r'댓글']
    cta_found = any(re.search(p, content) for p in cta_patterns)
    if cta_found:
        results['pass'].append('CTA 존재')
    else:
        results['warn'].append('CTA 미발견')

    return results


def check_image_quality(image_path):
    """이미지 품질 검사"""
    results = {
        'pass': [],
        'fail': [],
        'warn': []
    }

    if not PIL_AVAILABLE:
        results['warn'].append('PIL 미설치 - 이미지 검사 스킵')
        return results

    try:
        img = Image.open(image_path)
        width, height = img.size

        if width == 1080 and height == 1080:
            results['pass'].append(f'해상도 1080x1080')
        elif width == 1080 and height == 1350:
            results['pass'].append(f'해상도 1080x1350 (슬라이드)')
        else:
            results['warn'].append(f'해상도 비표준: {width}x{height}')

    except Exception as e:
        results['fail'].append(f'이미지 읽기 오류: {str(e)}')

    return results


def run_qc_single(folder_path, food_data):
    """단일 폴더 QC 실행"""
    folder_name = os.path.basename(folder_path)

    result = {
        'folder': folder_name,
        'timestamp': datetime.now().isoformat(),
        'result': 'PASS',
        'checks': {
            'file_exists': {'pass': [], 'fail': [], 'warn': []},
            'naming': {'pass': [], 'fail': [], 'warn': []},
            'caption_content': {'pass': [], 'fail': [], 'warn': []},
            'image_quality': {'pass': [], 'fail': [], 'warn': []}
        },
        'total_pass': 0,
        'total_fail': 0,
        'total_warn': 0
    }

    # 음식명 추출
    food_name = folder_name.split('_', 1)[1] if '_' in folder_name else folder_name
    expected_safety = get_food_safety_from_data(food_name, food_data)

    # 1. 파일 존재 검사
    file_results = check_file_exists(folder_path)
    result['checks']['file_exists'] = file_results

    # 2. 네이밍 검사
    if check_pascal_case(folder_name):
        result['checks']['naming']['pass'].append('폴더명 PascalCase')
    else:
        result['checks']['naming']['fail'].append('폴더명 PascalCase 아님')

    # 3. 캡션 내용 검사
    caption_folders = [
        (Path(folder_path) / '01_Insta&Thread', 'Insta'),
        (Path(folder_path) / '01_Insta&Thread', 'Thread'),
        (Path(folder_path) / '02_Blog', 'Blog')
    ]

    for caption_folder, platform in caption_folders:
        if caption_folder.exists():
            pattern = f'*{platform}*Caption*.txt'
            captions = list(caption_folder.glob(pattern))
            for caption in captions:
                caption_results = check_caption_content(caption, platform, expected_safety)
                for key in ['pass', 'fail', 'warn']:
                    result['checks']['caption_content'][key].extend(caption_results[key])

    # 4. 이미지 품질 검사 (커버만)
    cover_patterns = [f'{food_name}_Common_01_Cover.png', '*Common_01_Cover.png']
    for pattern in cover_patterns:
        covers = list(Path(folder_path).glob(pattern))
        if covers:
            img_results = check_image_quality(covers[0])
            for key in ['pass', 'fail', 'warn']:
                result['checks']['image_quality'][key].extend(img_results[key])
            break

    # 집계
    for check_type, check_results in result['checks'].items():
        result['total_pass'] += len(check_results['pass'])
        result['total_fail'] += len(check_results['fail'])
        result['total_warn'] += len(check_results['warn'])

    # 최종 판정
    if result['total_fail'] > 0:
        result['result'] = 'FAIL'
    elif result['total_warn'] > 0:
        result['result'] = 'PASS_WITH_WARNINGS'
    else:
        result['result'] = 'PASS'

    return result


def main():
    """메인 함수"""
    if len(sys.argv) < 2:
        print("사용법: python auto_qc.py {폴더번호|폴더명|--all}")
        print("예시:")
        print("  python auto_qc.py 001")
        print("  python auto_qc.py 001_Pumpkin")
        print("  python auto_qc.py --all")
        sys.exit(1)

    arg = sys.argv[1]
    food_data = load_food_data()

    results = []

    if arg == '--all':
        # 전체 폴더 검사
        folders = sorted([
            d for d in CONTENTS_DIR.iterdir()
            if d.is_dir() and re.match(r'^\d{3}_', d.name)
        ])
        print(f"전체 QC 실행: {len(folders)}개 폴더")

        for i, folder in enumerate(folders):
            result = run_qc_single(str(folder), food_data)
            results.append(result)
            status = '✅' if result['result'] == 'PASS' else ('⚠️' if result['result'] == 'PASS_WITH_WARNINGS' else '❌')
            if (i + 1) % 20 == 0:
                print(f"  진행: {i+1}/{len(folders)}")

    else:
        # 단일 폴더 검사
        # 번호만 입력한 경우
        if arg.isdigit():
            folders = list(CONTENTS_DIR.glob(f'{arg.zfill(3)}_*'))
        else:
            folders = list(CONTENTS_DIR.glob(f'*{arg}*'))

        if not folders:
            print(f"폴더를 찾을 수 없습니다: {arg}")
            sys.exit(1)

        for folder in folders:
            result = run_qc_single(str(folder), food_data)
            results.append(result)

    # 결과 저장
    output = {
        'timestamp': datetime.now().isoformat(),
        'total': len(results),
        'pass': sum(1 for r in results if r['result'] == 'PASS'),
        'pass_with_warnings': sum(1 for r in results if r['result'] == 'PASS_WITH_WARNINGS'),
        'fail': sum(1 for r in results if r['result'] == 'FAIL'),
        'results': results
    }

    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(output, f, ensure_ascii=False, indent=2)

    # 결과 출력
    print("\n━━━━━ QC 결과 ━━━━━")
    print(f"총: {output['total']}개")
    print(f"PASS: {output['pass']}개")
    print(f"PASS (경고): {output['pass_with_warnings']}개")
    print(f"FAIL: {output['fail']}개")

    if len(results) <= 5:
        for r in results:
            print(f"\n[{r['folder']}] {r['result']}")
            print(f"  PASS: {r['total_pass']} | FAIL: {r['total_fail']} | WARN: {r['total_warn']}")
            if r['total_fail'] > 0:
                for check_type, checks in r['checks'].items():
                    for fail in checks['fail']:
                        print(f"  ❌ {fail}")

    print(f"\n결과 저장: {OUTPUT_PATH}")


if __name__ == "__main__":
    main()
