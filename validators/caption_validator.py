#!/usr/bin/env python3
"""
WO-2026-0209-023: 캡션 검증기

파스타 규칙 8단계 검증:
1. 안전도 이모지 (필수)
2. 주의사항 리스트 (최소 3개)
3. 절대 금지 항목 (CAUTION 이상 필수)
4. 급여량 정보 (소/중/대형견)
5. 핵심 메시지 (💡 또는 인용)
6. CTA (저장/공유)
7. AI 고지 (필수)
8. 해시태그 (12~16개)

사용법:
    python validators/caption_validator.py --scan-all
    python validators/caption_validator.py --check 030
"""

import sys
import json
import argparse
from pathlib import Path
from typing import Dict, List, Any, Optional

PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))


def validate_instagram_caption(caption: str, safety_level: str) -> Dict[str, Any]:
    """
    Instagram 캡션 검증 (파스타 규칙 8단계)

    Args:
        caption: Instagram 캡션 텍스트
        safety_level: 안전도 (SAFE/CAUTION/DANGER/FORBIDDEN)

    Returns:
        {"valid": bool, "errors": list, "score": str, "details": dict}
    """
    errors = []
    details = {}
    score = 0

    # 1. 안전도 이모지 (필수)
    safety_emojis = {
        'SAFE': ('✅', '🟢'),
        'CAUTION': ('⚠️', '🟡'),
        'DANGER': ('🚨', '🔴'),
        'FORBIDDEN': ('⛔', '🔴')
    }
    expected = safety_emojis.get(safety_level.upper(), ())
    has_safety_emoji = any(e in caption for e in expected)
    details['safety_emoji'] = has_safety_emoji
    if has_safety_emoji:
        score += 1
    else:
        errors.append(f"1. 안전도 이모지 누락 (필요: {expected})")

    # 2. 주의사항 리스트 (필수, 최소 3개)
    bullet_count = caption.count('•')
    details['bullet_count'] = bullet_count
    if bullet_count >= 3:
        score += 1
    else:
        errors.append(f"2. 주의사항 리스트 부족 ({bullet_count}/3)")

    # 3. 절대 금지 항목 (CAUTION 이상 필수)
    if safety_level.upper() in ['CAUTION', 'DANGER', 'FORBIDDEN']:
        has_forbidden = '금지' in caption or '🚫' in caption or '절대' in caption
        details['has_forbidden'] = has_forbidden
        if has_forbidden:
            score += 1
        else:
            errors.append("3. 절대 금지 항목 누락")
    else:
        score += 1  # SAFE는 면제
        details['has_forbidden'] = 'N/A (SAFE)'

    # 4. 급여량 정보 (필수)
    size_keywords = ['소형견', '중형견', '대형견', '소형', '중형', '대형']
    has_size_info = any(kw in caption for kw in size_keywords)
    details['has_size_info'] = has_size_info
    if has_size_info:
        score += 1
    else:
        errors.append("4. 급여량 정보 누락 (소/중/대형견)")

    # 5. 핵심 메시지 (💡 또는 명확한 요약)
    has_key_message = '💡' in caption or '"' in caption or '📌' in caption
    details['has_key_message'] = has_key_message
    if has_key_message:
        score += 1
    else:
        errors.append("5. 핵심 메시지 누락 (💡 또는 인용)")

    # 6. CTA (필수)
    cta_keywords = ['저장', '공유', '💾', '📲', '북마크']
    has_cta = any(kw in caption for kw in cta_keywords)
    details['has_cta'] = has_cta
    if has_cta:
        score += 1
    else:
        errors.append("6. CTA 누락 (저장/공유)")

    # 7. AI 고지 (필수)
    has_ai_notice = 'AI' in caption and ('생성' in caption or 'generated' in caption.lower())
    details['has_ai_notice'] = has_ai_notice
    if has_ai_notice:
        score += 1
    else:
        errors.append("7. AI 고지 누락")

    # 8. 해시태그 (12~16개)
    hashtag_count = caption.count('#')
    details['hashtag_count'] = hashtag_count
    if 12 <= hashtag_count <= 16:
        score += 1
    else:
        errors.append(f"8. 해시태그 {hashtag_count}개 (필요: 12~16개)")

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "score": f"{score}/8",
        "score_num": score,
        "details": details
    }


def validate_threads_caption(caption: str) -> Dict[str, Any]:
    """
    Threads 캡션 검증

    Args:
        caption: Threads 캡션 텍스트

    Returns:
        {"valid": bool, "errors": list, "details": dict}
    """
    errors = []
    details = {}

    # 1. 길이 제한 (500자)
    char_count = len(caption)
    details['char_count'] = char_count
    if char_count > 500:
        errors.append(f"글자 수 초과 ({char_count}/500)")

    # 2. 해시태그 없어야 함 (권장, 3개 이하)
    hashtag_count = caption.count('#')
    details['hashtag_count'] = hashtag_count
    if hashtag_count > 3:
        errors.append(f"해시태그 과다 ({hashtag_count}개, 권장: 3개 이하)")

    # 3. AI 고지
    has_ai = 'AI' in caption
    details['has_ai_notice'] = has_ai
    if not has_ai:
        errors.append("AI 고지 누락")

    # 4. 인스타 유도 (선택)
    has_insta_ref = '@sunshinedogfood' in caption or 'instagram' in caption.lower()
    details['has_insta_ref'] = has_insta_ref
    # 선택 사항이므로 에러로 추가하지 않음

    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "details": details
    }


def find_caption_file(content_num: str, caption_type: str = 'instagram') -> Optional[Path]:
    """캡션 파일 찾기

    Args:
        content_num: 콘텐츠 번호 (예: "030")
        caption_type: 'instagram' 또는 'threads'

    Returns:
        캡션 파일 경로 또는 None
    """
    search_dirs = [
        PROJECT_ROOT / "contents" / "4_posted",
        PROJECT_ROOT / "contents" / "3_approved",
        PROJECT_ROOT / "contents" / "2_body_ready",
        PROJECT_ROOT / "contents" / "1_cover_only",
    ]

    filename = f"caption_{caption_type}.txt"

    for search_dir in search_dirs:
        if not search_dir.exists():
            continue
        for folder in search_dir.iterdir():
            if folder.is_dir() and folder.name.startswith(content_num):
                caption_path = folder / filename
                if caption_path.exists():
                    return caption_path
    return None


def read_caption_file(file_path: Path) -> str:
    """캡션 파일 읽기"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return f.read()
    except:
        return ''


def get_sheet_data() -> List[Dict[str, Any]]:
    """구글시트에서 데이터 가져오기 + 캡션 파일 읽기"""
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_path = PROJECT_ROOT / "config" / "google-credentials.json"
    creds = Credentials.from_service_account_file(str(creds_path), scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open("Sunshine").worksheet("게시콘텐츠")

    all_data = sheet.get_all_values()
    results = []

    # 열 인덱스 (0-based)
    COL_NUM = 0      # A열: 번호
    COL_ENG = 1      # B열: 영문명
    COL_SAFETY = 4   # E열: 안전도
    COL_STATUS = 5   # F열: 상태
    COL_P = 15       # P열: 인스타 캡션 상태
    COL_Q = 16       # Q열: 쓰레드 캡션 상태

    for idx, row in enumerate(all_data[1:], start=2):
        if len(row) < 6:
            continue

        num = row[COL_NUM] if len(row) > COL_NUM else ''
        if not (num.isdigit() and len(num) == 3):
            continue

        # 캡션 파일에서 실제 내용 읽기
        insta_file = find_caption_file(num, 'instagram')
        threads_file = find_caption_file(num, 'threads')

        p_caption = read_caption_file(insta_file) if insta_file else ''
        q_caption = read_caption_file(threads_file) if threads_file else ''

        results.append({
            'row': idx,
            'num': num,
            'eng_name': row[COL_ENG] if len(row) > COL_ENG else '',
            'safety_level': row[COL_SAFETY] if len(row) > COL_SAFETY else '',
            'status': row[COL_STATUS] if len(row) > COL_STATUS else '',
            'p_caption': p_caption,
            'q_caption': q_caption,
            'p_file': str(insta_file) if insta_file else None,
            'q_file': str(threads_file) if threads_file else None,
        })

    return results


def scan_all_captions(fix: bool = False) -> Dict[str, Any]:
    """
    전체 P열/Q열 캡션 스캔

    Args:
        fix: True면 실패 항목 롤백 (F열 → body_ready)

    Returns:
        스캔 결과 요약
    """
    print("=" * 70)
    print("🔍 캡션 전체 스캔 시작 (파스타 규칙 8단계)")
    print("=" * 70)

    data = get_sheet_data()

    results = {
        'total': 0,
        'passed': 0,
        'failed': 0,
        'skipped': 0,
        'failures': []
    }

    # 스캔 대상: approved, body_ready
    target_statuses = ['approved', 'body_ready']

    for item in data:
        if item['status'].lower() not in target_statuses:
            results['skipped'] += 1
            continue

        results['total'] += 1

        # P열 캡션 검증
        p_caption = item['p_caption']
        safety = item['safety_level']

        if not p_caption or p_caption == '-':
            results['skipped'] += 1
            continue

        p_result = validate_instagram_caption(p_caption, safety)

        print(f"\n[{item['num']}] {item['eng_name']} ({item['status']})")
        print(f"   안전도: {safety}")
        print(f"   점수: {p_result['score']}")

        if p_result['valid']:
            print(f"   ✅ 통과")
            results['passed'] += 1
        else:
            print(f"   ❌ 실패:")
            for err in p_result['errors']:
                print(f"      - {err}")
            results['failed'] += 1
            results['failures'].append({
                'num': item['num'],
                'eng_name': item['eng_name'],
                'row': item['row'],
                'status': item['status'],
                'errors': p_result['errors'],
                'score': p_result['score']
            })

    # 요약
    print("\n" + "=" * 70)
    print("📊 스캔 결과 요약")
    print("=" * 70)
    print(f"   총 검사: {results['total']}건")
    print(f"   ✅ 통과: {results['passed']}건")
    print(f"   ❌ 실패: {results['failed']}건")
    print(f"   ⏭️ 스킵: {results['skipped']}건")

    if results['failures']:
        print(f"\n📋 실패 목록:")
        for f in results['failures']:
            print(f"   [{f['num']}] {f['eng_name']} - {f['score']}")

    # 롤백 실행
    if fix and results['failures']:
        print(f"\n🔧 롤백 실행 ({len(results['failures'])}건)...")
        rollback_failed_items(results['failures'])

    return results


def rollback_failed_items(failures: List[Dict]) -> None:
    """실패 항목 롤백 (F열 → body_ready)"""
    import gspread
    from google.oauth2.service_account import Credentials

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_path = PROJECT_ROOT / "config" / "google-credentials.json"
    creds = Credentials.from_service_account_file(str(creds_path), scopes=scopes)
    client = gspread.authorize(creds)
    sheet = client.open("Sunshine").worksheet("게시콘텐츠")

    COL_STATUS = 6   # F열
    COL_P = 16       # P열

    for item in failures:
        row = item['row']

        # approved 상태만 롤백
        if item['status'].lower() != 'approved':
            continue

        # F열 → body_ready
        sheet.update_cell(row, COL_STATUS, 'body_ready')

        # P열에 오류 정보 추가
        error_summary = f"오류:{','.join([e.split('.')[0] for e in item['errors'][:3]])}"
        current_p = sheet.cell(row, COL_P).value or ''
        if not current_p.startswith('오류:'):
            sheet.update_cell(row, COL_P, error_summary)

        print(f"   [{item['num']}] {item['eng_name']} → body_ready")


def check_single(content_num: str) -> Dict[str, Any]:
    """단일 콘텐츠 검증"""
    data = get_sheet_data()

    for item in data:
        if item['num'] == content_num.zfill(3):
            p_result = validate_instagram_caption(item['p_caption'], item['safety_level'])
            q_result = validate_threads_caption(item['q_caption']) if item['q_caption'] else None

            print(f"\n[{item['num']}] {item['eng_name']}")
            print(f"상태: {item['status']}")
            print(f"안전도: {item['safety_level']}")

            print(f"\n📱 Instagram 캡션 (P열):")
            print(f"   점수: {p_result['score']}")
            if p_result['valid']:
                print(f"   ✅ 통과")
            else:
                print(f"   ❌ 실패:")
                for err in p_result['errors']:
                    print(f"      - {err}")

            if q_result:
                print(f"\n🧵 Threads 캡션 (Q열):")
                if q_result['valid']:
                    print(f"   ✅ 통과")
                else:
                    print(f"   ❌ 실패:")
                    for err in q_result['errors']:
                        print(f"      - {err}")

            return {
                'instagram': p_result,
                'threads': q_result,
                'item': item
            }

    print(f"❌ 콘텐츠 번호 {content_num} 없음")
    return None


def main():
    parser = argparse.ArgumentParser(description="캡션 검증기 (파스타 규칙 8단계)")
    parser.add_argument("--scan-all", action="store_true", help="전체 P열 스캔")
    parser.add_argument("--fix", action="store_true", help="실패 항목 롤백 (--scan-all과 함께 사용)")
    parser.add_argument("--check", type=str, help="단일 콘텐츠 검증 (번호)")

    args = parser.parse_args()

    if args.scan_all:
        scan_all_captions(fix=args.fix)
    elif args.check:
        check_single(args.check)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
