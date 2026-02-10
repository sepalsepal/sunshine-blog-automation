#!/usr/bin/env python3
"""
음식 100개 구글시트 업데이트 스크립트
- topics_expanded.json에서 음식 목록 추출
- 기존 시트 항목과 중복 제거
- 신규 항목 추가 (게시상태: 표지대기)
"""

import json
import os
import sys
from pathlib import Path
from datetime import datetime

# 프로젝트 루트 추가
PROJECT_ROOT = Path(__file__).parent.parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from core.utils.google_sheets_manager import ContentSheetManager


def load_topics_expanded() -> list:
    """topics_expanded.json에서 모든 음식 추출"""
    topics_path = PROJECT_ROOT / 'config' / 'settings' / 'topics_expanded.json'

    with open(topics_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    all_foods = []

    # 각 카테고리에서 topics 추출
    for category_key, category_data in data.get('categories', {}).items():
        topics = category_data.get('topics', [])
        for topic in topics:
            # safety 매핑: safe → SAFE, caution → CAUTION, dangerous → DANGER/FORBIDDEN
            safety_map = {
                'safe': 'SAFE',
                'caution': 'CAUTION',
                'dangerous': 'DANGER'
            }
            safety = safety_map.get(topic.get('safety', 'safe'), 'SAFE')

            # _danger 접미사 제거하여 영문명 정리
            topic_id = topic.get('id', '').replace('_danger', '')

            all_foods.append({
                'id': topic_id,
                'ko': topic.get('ko', ''),
                'safety': safety,
                'note': topic.get('note', '')
            })

    return all_foods


def get_existing_topics(manager: ContentSheetManager) -> set:
    """기존 시트에서 영문명 목록 추출 (소문자)"""
    contents = manager.get_all_contents()
    existing = set()

    for content in contents:
        topic_en = content.get('영문명', '').lower().strip()
        if topic_en:
            existing.add(topic_en)

    return existing


def get_next_number(manager: ContentSheetManager) -> int:
    """다음 번호 가져오기"""
    contents = manager.get_all_contents()
    max_num = 0

    for content in contents:
        try:
            num = int(content.get('번호', 0))
            max_num = max(max_num, num)
        except (ValueError, TypeError):
            continue

    return max_num + 1


def main():
    print("=" * 60)
    print("📋 음식 100개 구글시트 업데이트")
    print("=" * 60)

    # 1. topics_expanded.json 로드
    print("\n[1/4] topics_expanded.json 로드...")
    all_foods = load_topics_expanded()
    print(f"  총 {len(all_foods)}개 음식 추출됨")

    # 2. Google Sheets 연결
    print("\n[2/4] Google Sheets 연결...")
    manager = ContentSheetManager()

    if not manager.connect():
        print("❌ Google Sheets 연결 실패")
        return

    # 3. 기존 항목 확인
    print("\n[3/4] 기존 항목 확인...")
    existing = get_existing_topics(manager)
    print(f"  기존 항목 수: {len(existing)}건")

    # 중복 확인
    duplicates = []
    new_foods = []

    for food in all_foods:
        food_id_lower = food['id'].lower()
        if food_id_lower in existing:
            duplicates.append(food['id'])
        else:
            new_foods.append(food)

    print(f"  중복 항목: {len(duplicates)}건")
    print(f"  신규 항목: {len(new_foods)}건")

    if duplicates:
        print("\n  중복 목록:")
        for d in duplicates[:20]:  # 처음 20개만 출력
            print(f"    - {d}")
        if len(duplicates) > 20:
            print(f"    ... 외 {len(duplicates) - 20}건")

    # 4. 신규 항목 추가
    print("\n[4/4] 신규 항목 추가...")

    if not new_foods:
        print("  추가할 신규 항목 없음")
        return

    next_num = get_next_number(manager)
    added_count = 0
    failed_count = 0

    for food in new_foods:
        num = next_num + added_count
        num_str = f"{num:03d}"

        folder_name = f"{num_str}_{food['id']}_{food['ko']}"

        row = [
            num_str,              # 번호
            food['id'],           # 영문명
            food['ko'],           # 한글명
            folder_name,          # 폴더명
            food['safety'],       # 안전도
            '표지대기',           # 게시상태
            '',                   # 게시일 (비움)
            ''                    # 인스타URL (비움)
        ]

        try:
            manager._worksheet.append_row(row)
            added_count += 1
            print(f"  ✅ [{num_str}] {food['ko']} ({food['id']}) - {food['safety']}")
        except Exception as e:
            failed_count += 1
            print(f"  ❌ [{num_str}] {food['ko']} 실패: {e}")

    # 결과 보고
    print("\n" + "=" * 60)
    print("📊 작업 완료 보고")
    print("=" * 60)
    print(f"□ 기존 항목 수: {len(existing)}건")
    print(f"□ 추가된 항목 수: {added_count}건")
    print(f"□ 중복 제외 항목: {len(duplicates)}건")
    print(f"□ 실패 항목: {failed_count}건")
    print(f"□ 최종 시트 총 건수: {len(existing) + added_count}건")
    print("=" * 60)


if __name__ == '__main__':
    main()
